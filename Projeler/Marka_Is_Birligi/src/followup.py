#!/usr/bin/env python3
"""
Follow-Up modülü — 1 hafta sonra cevap vermemiş markalara reply email atar.

Gmail API reply-in-thread özelliğini kullanarak aynı thread'de görünür.
Seçenek A: Markanın son Instagram paylaşımları + web sitesi analizi ile
kişiselleştirilmiş follow-up üretir.
"""

import csv
import json
import os
import time
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKALAR_CSV = os.path.join(BASE_DIR, "data", "markalar.csv")

TR_TZ = timezone(timedelta(hours=3))
FOLLOWUP_WAIT_DAYS = 7  # 7 gün sonra follow-up


def get_followup_candidates():
    """
    Follow-up gönderilmesi gereken markaları filtreler.
    
    Kriter:
    - outreach_status == "Sent"
    - followup_status boş (henüz follow-up gönderilmemiş)
    - outreach_date'ten bu yana en az FOLLOWUP_WAIT_DAYS gün geçmiş
    
    Returns:
        list[dict]: Follow-up adayları
    """
    if not os.path.exists(MARKALAR_CSV):
        print("[FOLLOWUP] markalar.csv bulunamadı!")
        return []

    now = datetime.now(TR_TZ)
    candidates = []

    with open(MARKALAR_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("outreach_status") != "Sent":
                continue
            if row.get("followup_status"):
                continue  # Zaten follow-up gönderilmiş
            
            outreach_date_str = row.get("outreach_date", "").strip()
            if not outreach_date_str:
                continue

            try:
                outreach_date = datetime.strptime(outreach_date_str, "%Y-%m-%d %H:%M")
                outreach_date = outreach_date.replace(tzinfo=TR_TZ)
            except ValueError:
                # Farklı format dene
                try:
                    outreach_date = datetime.strptime(outreach_date_str, "%Y-%m-%d")
                    outreach_date = outreach_date.replace(tzinfo=TR_TZ)
                except ValueError:
                    continue

            days_since = (now - outreach_date).days
            if days_since >= FOLLOWUP_WAIT_DAYS:
                row["_days_since_outreach"] = days_since
                candidates.append(row)

    print(f"[FOLLOWUP] {len(candidates)} follow-up adayı bulundu.")
    return candidates


def update_csv_followup(lead_id, updates):
    """Belirli bir satırın follow-up bilgilerini günceller."""
    from src.outreach import CSV_FIELDNAMES
    
    rows = []
    with open(MARKALAR_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("lead_id") == lead_id:
                row.update(updates)
            rows.append(row)

    with open(MARKALAR_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def send_followup_emails(dry_run=False):
    """
    Follow-up adaylarına kişiselleştirilmiş reply emaili gönderir.
    
    Returns:
        dict: {sent: int, failed: int, skipped: int}
    """
    from src.personalizer import generate_followup_email, research_brand_for_followup
    from src.gmail_sender import get_service, send_reply

    candidates = get_followup_candidates()
    if not candidates:
        print("[FOLLOWUP] Follow-up gönderilecek marka yok.")
        return {"sent": 0, "failed": 0, "skipped": 0}

    print(f"\n{'='*60}")
    print(f"📬 {len(candidates)} markaya follow-up gönderiliyor...")
    print(f"{'='*60}")

    if dry_run:
        for c in candidates:
            days = c.get("_days_since_outreach", "?")
            print(f"  [DRY-RUN] {c['marka_adi']} → {c['email']} ({days} gün önce)")
        return {"sent": 0, "failed": 0, "skipped": len(candidates)}

    service = get_service()
    stats = {"sent": 0, "failed": 0, "skipped": 0}
    now = datetime.now(TR_TZ).strftime("%Y-%m-%d %H:%M")

    for candidate in candidates:
        brand_info = {
            "marka_adi": candidate.get("marka_adi", ""),
            "instagram_handle": candidate.get("instagram_handle", ""),
            "website": candidate.get("website", ""),
            "sirket_aciklamasi": candidate.get("sirket_aciklamasi", ""),
        }

        thread_id = candidate.get("outreach_thread_id", "")
        message_id = candidate.get("outreach_message_id", "")
        original_subject = candidate.get("outreach_subject", "")

        if not thread_id or not message_id:
            print(f"  ⚠️ {brand_info['marka_adi']}: Thread bilgisi eksik, atlanıyor.")
            stats["skipped"] += 1
            continue

        print(f"\n  📬 {brand_info['marka_adi']} → {candidate['email']}")
        print(f"     ({candidate.get('_days_since_outreach', '?')} gün önce gönderildi)")

        # Seçenek A: Marka araştırması
        print(f"     🔍 Marka araştırılıyor...")
        brand_context = research_brand_for_followup(brand_info)

        # Kişiselleştirilmiş follow-up üret
        followup_content = generate_followup_email(brand_info, brand_context)
        body_html = followup_content.get("body_html", "")
        body_text = followup_content.get("body_text", "")

        # Reply olarak gönder
        result = send_reply(
            service,
            to=candidate["email"],
            subject=original_subject,
            body_html=body_html,
            thread_id=thread_id,
            message_id=message_id,
            body_text=body_text,
        )

        if result:
            update_csv_followup(candidate["lead_id"], {
                "followup_status": "Sent",
                "followup_date": now,
                "followup_message_id": result.get("message_id", ""),
            })
            print(f"     ✅ Follow-up gönderildi!")
            stats["sent"] += 1
        else:
            update_csv_followup(candidate["lead_id"], {
                "followup_status": "Failed",
                "followup_date": now,
                "notlar": f"{candidate.get('notlar', '')} | Follow-up gönderim hatası".strip(" |"),
            })
            print(f"     ❌ Follow-up başarısız!")
            stats["failed"] += 1

        time.sleep(15)  # Rate limiting

    print(f"\n{'='*60}")
    print(f"📊 FOLLOW-UP SONUÇ: {stats['sent']} gönderildi, {stats['failed']} başarısız, {stats['skipped']} atlandı")
    print(f"{'='*60}")
    return stats


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    send_followup_emails(dry_run=dry)
