"""
Ceren_Marka_Takip — Ana Orkestrasyon
======================================
Railway CronJob entry point. Günlük 07:00 UTC (TR 10:00).

Akış:
1. Gmail'i son 30 gün için tara (pre-filter dahil).
2. Notion DB'den her thread'in mevcut durumunu çek (reconcile).
3. Yeni thread'ler veya yeni mesajı olan açık thread'ler için LLM analiz et.
4. LLM çıktısı → core.decision ile Status'e dönüştür, Notion'da upsert.
5. Notion'dan tüm Status=open thread'leri çek (carry-forward kalbi).
6. Açık thread'leri stale (48+ iş saati) filtresinden geçir.
7. Digest mail gönder (yeni + hala bekleyenler ayrı bölüm).
8. Gönderilen her thread için Reminder Count++ ve Last Reminded At güncelle.

Kullanım:
    python main.py              # Normal
    python main.py --dry-run    # Tara/analiz et, mail gönderme, Notion'a yazma
"""

import os
import sys
import argparse
import traceback
import logging
import socket
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

socket.setdefaulttimeout(60)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import setup_logging
from utils.business_hours import is_stale, business_days_since
from core import gmail_scanner, thread_analyzer, notifier, decision
from services import notion_threads


SCAN_DAYS = 30
STALE_THRESHOLD_HOURS = 48.0


def _check_environment():
    required = ["GROQ_API_KEY", "NOTION_DB_CEREN_COLLAB_THREADS"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        raise EnvironmentError(
            f"Gerekli environment variable'lar eksik: {', '.join(missing)}"
        )
    if not (os.environ.get("NOTION_SOCIAL_TOKEN") or os.environ.get("NOTION_API_TOKEN")):
        raise EnvironmentError(
            "Notion token yok (NOTION_SOCIAL_TOKEN veya NOTION_API_TOKEN gerekli)."
        )


def _normalize_iso(dt) -> str:
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def main(dry_run: bool = False):
    logger = setup_logging("INFO")
    tag = "(DRY-RUN) " if dry_run else ""
    logger.info("=" * 60)
    logger.info(f"🔍 Ceren Marka Takip — Başlatılıyor {tag}")
    logger.info(f"Zaman (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
    logger.info("=" * 60)

    _check_environment()

    # ── 1. Gmail tara ──
    logger.info(f"📨 Gmail taranıyor (son {SCAN_DAYS} gün)...")
    threads = gmail_scanner.scan_all_inboxes(days=SCAN_DAYS)
    logger.info(f"Pre-filter sonrası thread: {len(threads)}")

    # ── 2-4. Reconcile + LLM (sadece gerekli olanlar) + Notion upsert ──
    llm_runs = 0
    skipped_unchanged = 0

    for thread in threads:
        thread_id = thread["thread_id"]
        notion_record = notion_threads.find_by_thread_id(thread_id)
        fresh_last_msg_iso = _normalize_iso(thread.get("last_message_date"))

        if not decision.should_run_llm(notion_record, fresh_last_msg_iso):
            skipped_unchanged += 1
            continue

        llm_result = thread_analyzer.analyze(thread)
        if llm_result is None:
            continue
        llm_runs += 1

        current_status = notion_record.get("status") if notion_record else None
        new_status, reason = decision.llm_to_status(llm_result, current_status)

        if dry_run:
            logger.info(
                f"[DRY-RUN] {thread_id[:12]} '{thread['subject'][:40]}' "
                f"→ status={new_status} (cat={llm_result.get('category')}, "
                f"conf={llm_result.get('confidence')})"
            )
            continue

        notion_threads.upsert_thread(
            thread_id=thread_id,
            subject=thread["subject"],
            brand=llm_result.get("brand_name") or "",
            status=new_status,
            category=llm_result.get("category"),
            last_message_from=llm_result.get("last_sender"),
            last_message_at=thread.get("last_message_date"),
            confidence=llm_result.get("confidence"),
            gmail_link=thread.get("gmail_link"),
            reason=reason,
            llm_just_ran=True,
            is_new=(notion_record is None),
        )

    logger.info(f"LLM çağrısı: {llm_runs}, atlanan (değişiklik yok): {skipped_unchanged}")

    # ── 5. Tüm açık thread'leri Notion'dan çek ──
    open_records = notion_threads.query_all_open()
    logger.info(f"Açık thread (Status=open): {len(open_records)}")

    if not open_records:
        logger.info("✅ Açık collab yok — digest gönderilmiyor.")
        return

    # ── 6. Stale filtresi ──
    now = datetime.utcnow()
    stale_entries = []
    for rec in open_records:
        last_msg_str = rec.get("last_message_at")
        if not last_msg_str:
            continue
        try:
            last_msg_dt = datetime.fromisoformat(last_msg_str.replace("Z", "+00:00"))
            if last_msg_dt.tzinfo:
                last_msg_dt = last_msg_dt.replace(tzinfo=None)
        except ValueError:
            logger.warning(f"Geçersiz tarih: {rec.get('thread_id')} — {last_msg_str}")
            continue

        if not is_stale(last_msg_dt, STALE_THRESHOLD_HOURS, now):
            continue

        days = business_days_since(last_msg_dt, now)
        stale_entries.append({
            "thread_id": rec["thread_id"],
            "page_id": rec["_page_id"],
            "subject": rec.get("subject"),
            "brand": rec.get("brand"),
            "reason": rec.get("reason"),
            "gmail_link": rec.get("gmail_link"),
            "reminder_count": int(rec.get("reminder_count") or 0),
            "business_days_open": days,
        })

    logger.info(f"Stale (48+ iş saati): {len(stale_entries)} / {len(open_records)}")

    if not stale_entries:
        logger.info("✅ Açık iş var ama hiçbiri stale değil — digest yok.")
        return

    # ── 7. Digest gönder (yeni + devam eden iki bölüm) ──
    new_items = [e for e in stale_entries if e["reminder_count"] == 0]
    ongoing_items = [e for e in stale_entries if e["reminder_count"] > 0]
    new_items.sort(key=lambda e: -e["business_days_open"])
    ongoing_items.sort(key=lambda e: -e["business_days_open"])

    if dry_run:
        logger.info(f"[DRY-RUN] Digest: {len(new_items)} yeni + {len(ongoing_items)} devam eden")
        for e in new_items + ongoing_items:
            logger.info(
                f"  → {e['brand']} | {e['subject'][:50]} | "
                f"{e['business_days_open']} gün | reminded={e['reminder_count']}"
            )
        return

    notifier.send_digest(new_items, ongoing_items)

    # ── 8. State güncelle ──
    for e in new_items + ongoing_items:
        notion_threads.mark_reminded(e["page_id"], e["reminder_count"])

    logger.info("=" * 60)
    logger.info("📊 ÖZET")
    logger.info(f"   Tarana thread: {len(threads)}")
    logger.info(f"   LLM çalıştı: {llm_runs}")
    logger.info(f"   Açık thread: {len(open_records)}")
    logger.info(f"   Stale: {len(stale_entries)} (yeni {len(new_items)} + devam {len(ongoing_items)})")
    logger.info("=" * 60)
    logger.info("✅ Çalışma tamamlandı.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ceren Marka Takip — Stale Thread Detector")
    parser.add_argument("--dry-run", action="store_true",
                        help="Sadece analiz et, Notion'a yazma ve mail gönderme")
    args = parser.parse_args()

    try:
        main(dry_run=args.dry_run)
    except Exception:
        logging.getLogger(__name__).critical(f"FATAL: {traceback.format_exc()}")
        sys.exit(1)
