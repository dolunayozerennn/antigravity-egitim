"""
Ceren_Marka_Takip — Ana Orkestrasyon
======================================
CronJob entry point. Her gün 10:00 TR'de çalışır.

Akış:
1. Ceren'in Gmail inbox'ını tara (son 15 gün)
2. Stale thread'leri filtrele (48+ iş saati)
3. LLM ile marka işbirliği analizi
4. Duplicate hatırlatma kontrolü (2 gün cooldown)
5. Ceren'e hatırlatma e-postası gönder
6. Hata durumunda Ceren'e alert
7. Her Pazartesi haftalık rapor

Kullanım:
    python main.py              # Normal çalıştır
    python main.py --dry-run    # Sadece tara ve analiz et, e-posta gönderme
"""

import os
import sys
import argparse
import traceback
import logging
import socket
from datetime import datetime
from dotenv import load_dotenv

# .env dosyasını yükle (lokal geliştirme için)
load_dotenv()

# Global socket timeout to prevent infinite blocking on external API calls
socket.setdefaulttimeout(60)

# Proje kökünü PYTHONPATH'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import setup_logging
from utils import state_manager
from core import gmail_scanner, thread_analyzer, stale_detector, notifier


def main(dry_run: bool = False):
    """
    Ana orkestrasyon fonksiyonu.
    
    Args:
        dry_run: True ise sadece tara/analiz et, e-posta gönderme
    """
    logger = setup_logging("INFO")
    logger.info("=" * 60)
    logger.info(f"🔍 Ceren Marka Takip — Başlatılıyor {'(DRY-RUN)' if dry_run else ''}")
    logger.info(f"Zaman: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    logger.info("=" * 60)

    # ── 1. Fail-Fast: Gerekli env var'ları kontrol et ──
    _check_environment(dry_run)

    # ── 2. Gmail inbox'larını tara ──
    logger.info("📨 Gmail inbox'ları taranıyor (son 15 gün)...")
    threads = gmail_scanner.scan_all_inboxes(days=15)
    logger.info(f"Toplam unique thread: {len(threads)}")

    if not threads:
        logger.info("⚠️ Hiç thread bulunamadı. Çıkılıyor.")
        return

    # ── 3. Stale thread'leri filtrele ──
    logger.info("⏰ Stale thread filtresi uygulanıyor (48+ iş saati)...")
    stale_threads = stale_detector.filter_stale(threads, threshold_hours=48.0)
    logger.info(f"Stale thread sayısı: {len(stale_threads)}")

    if not stale_threads:
        logger.info("✅ Stale thread yok. Her şey yolunda!")
        return

    # ── 4. LLM ile analiz et ──
    logger.info(f"🤖 {len(stale_threads)} thread LLM ile analiz ediliyor...")
    actionable_threads = []

    for thread in stale_threads:
        result = thread_analyzer.analyze(thread)
        if result is None:
            continue

        # Sadece marka işbirliği + Ceren aksiyonu gereken thread'ler
        if result.get("is_brand_collaboration") and result.get("action_needed_by_ceren"):
            actionable_threads.append(result)
        else:
            reason = []
            if not result.get("is_brand_collaboration"):
                reason.append("marka işbirliği değil")
            if not result.get("action_needed_by_ceren"):
                reason.append("Ceren aksiyonu gerekmiyor")
            logger.debug(
                f"ATLA: '{thread['subject'][:40]}' — {', '.join(reason)}"
            )

    logger.info(f"Aksiyonel thread: {len(actionable_threads)}")

    if not actionable_threads:
        logger.info("✅ Aksiyon gerektiren thread yok. Her şey yolunda!")
        return

    # ── 5. Duplicate hatırlatma kontrolü ──
    to_notify = state_manager.filter_already_notified(actionable_threads, cooldown_days=2)
    logger.info(f"Bildirilecek (cooldown sonrası): {len(to_notify)}")

    # ── 6. Ceren'e hatırlatma gönder ──
    if to_notify and not dry_run:
        logger.info(f"📧 Ceren'e {len(to_notify)} hatırlatma gönderiliyor...")
        notifier.send_reminder_to_ceren(to_notify)
        state_manager.update_state(to_notify)
    elif to_notify and dry_run:
        logger.info(f"[DRY-RUN] {len(to_notify)} hatırlatma gönderilecekti:")
        for t in to_notify:
            logger.info(f"  → {t.get('brand_name', '?')}: {t.get('subject', '?')[:50]}")
    else:
        logger.info("ℹ️ Tüm thread'ler zaten bildirilmiş (cooldown aktif)")


    # ── Özet ──
    logger.info("=" * 60)
    logger.info(f"📊 ÖZET")
    logger.info(f"   Thread taranan: {len(threads)}")
    logger.info(f"   Stale: {len(stale_threads)}")
    logger.info(f"   Marka işbirliği + aksiyon: {len(actionable_threads)}")
    logger.info(f"   Bildirim gönderilen: {len(to_notify)}")
    logger.info("=" * 60)
    logger.info("✅ Çalışma tamamlandı.")


def _check_environment(dry_run: bool):
    """Fail-Fast: Gerekli ortam değişkenlerini kontrol et."""
    required = ["GROQ_API_KEY"]

    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        raise EnvironmentError(
            f"Gerekli environment variable'lar eksik: {', '.join(missing)}\n"
            f"Bu değişkenleri .env dosyasından veya Railway'den set et."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ceren Marka Takip — Stale Thread Detector")
    parser.add_argument("--dry-run", action="store_true", help="Sadece tara/analiz et, e-posta gönderme")
    args = parser.parse_args()

    try:
        main(dry_run=args.dry_run)
    except Exception as e:
        error_msg = traceback.format_exc()
        logging.getLogger(__name__).critical(f"FATAL: {error_msg}")
        sys.exit(1)
