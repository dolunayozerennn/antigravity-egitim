#!/usr/bin/env python3
"""
Outreach modülü — Yeni markalar için ilk outreach email gönderimi.

Pipeline: scrape → analyze → find contacts → kişiselleştir → gönder
"""

import json
import os
import random
import time
from datetime import datetime, timezone, timedelta

from src.notion_service import add_brands_batch, update_brand, get_brands_by_status

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DAILY_SEND_LIMIT = 20  # Günlük max email gönderim limiti

TR_TZ = timezone(timedelta(hours=3))


def send_outreach_emails(dry_run=False):
    """
    CSV'deki 'New' statüsündeki markalara outreach emaili gönderir.
    
    Returns:
        dict: {sent: int, failed: int, skipped: int}
    """
    from src.personalizer import generate_outreach_email
    from src.gmail_sender import get_service, send_email

    # Notion'dan yeni markaları oku
    pending_brands = get_brands_by_status("New")
    pending = [b for b in pending_brands if b.get("email")]

    if not pending:
        print("[OUTREACH] Gönderilecek yeni marka yok.")
        return {"sent": 0, "failed": 0, "skipped": 0, "queued": 0}

    # Günlük gönderim limiti uygula
    if len(pending) > DAILY_SEND_LIMIT:
        queued_count = len(pending) - DAILY_SEND_LIMIT
        print(f"  ⚠️ {len(pending)} marka var ama günlük limit {DAILY_SEND_LIMIT}. {queued_count} marka 'Queued' olarak bekletiliyor.")
        pending = pending[:DAILY_SEND_LIMIT]
    else:
        queued_count = 0

    print(f"\n{'='*60}")
    print(f"📧 {len(pending)} markaya outreach gönderiliyor (limit: {DAILY_SEND_LIMIT}/gün)...")
    print(f"{'='*60}")

    if dry_run:
        for p in pending:
            print(f"  [DRY-RUN] {p.get('marka_adi')} → {p.get('email')}")
            # Generate email to ensure OpenAI / logic works
            email_content = generate_outreach_email({
                "marka_adi": p.get("marka_adi", ""),
                "instagram_handle": p.get("instagram_handle", ""),
                "website": p.get("website", ""),
                "sirket_aciklamasi": p.get("sirket_aciklamasi", ""),
            })
            print(f"    ↳ MOCK SUBJECT: {email_content['subject']}")
        return {"sent": 0, "failed": 0, "skipped": len(pending), "queued": queued_count}

    service = get_service()
    stats = {"sent": 0, "failed": 0, "skipped": 0, "queued": queued_count}
    now = datetime.now(TR_TZ).strftime("%Y-%m-%d %H:%M")

    for brand_row in pending:
        brand_info = {
            "marka_adi": brand_row.get("marka_adi", ""),
            "instagram_handle": brand_row.get("instagram_handle", ""),
            "website": brand_row.get("website", ""),
            "sirket_aciklamasi": brand_row.get("sirket_aciklamasi", ""),
        }

        # Kişiselleştirilmiş email üret
        email_content = generate_outreach_email(brand_info)
        subject = email_content["subject"]
        body_html = email_content.get("body_html", "")
        body_text = email_content.get("body_text", "")

        print(f"\n  📧 {brand_info['marka_adi']} → {brand_row['email']}")
        print(f"     Konu: {subject}")

        # Gönder
        result = send_email(service, brand_row["email"], subject, body_html, body_text, plain_text_only=False)

        if result:
            update_brand(brand_row["notion_page_id"], {
                "outreach_status": "Sent",
                "outreach_date": now,
                "message_id": result.get("message_id", ""),
                "thread_id": result.get("thread_id", ""),
                "subject": subject,
            })
            print(f"     ✅ Gönderildi (Thread: {result.get('thread_id', '')})")
            stats["sent"] += 1
        else:
            update_brand(brand_row["notion_page_id"], {
                "outreach_status": "Failed",
                "outreach_date": now,
                "notlar": "Email gönderim hatası",
            })
            print(f"     ❌ Başarısız")
            stats["failed"] += 1

        wait_time = random.uniform(45, 120)
        print(f"     ⏳ Sonraki mail için {wait_time:.0f}sn bekleniyor...")
        time.sleep(wait_time)  # Anti-spam: rastgele aralıklar

    print(f"\n{'='*60}")
    print(f"📊 OUTREACH SONUÇ: {stats['sent']} gönderildi, {stats['failed']} başarısız")
    print(f"{'='*60}")
    return stats


def run_full_pipeline(dry_run=False):
    """
    Tam pipeline: scrape → analyze → find contacts → add to DB → send outreach.
    
    Bu fonksiyon scheduler tarafından haftalık çağrılır.
    """
    from src.scraper import scrape_reels
    from src.analyzer import find_new_brands
    from src.contact_finder import enrich_new_brands

    print("\n" + "═" * 60)
    print("🚀 MARKA İŞ BİRLİĞİ — HAFTALIK PİPELİNE BAŞLADI")
    print("═" * 60)

    # Adım 1: Scrape
    print("\n📌 ADIM 1: Influencer reels'leri scrape ediliyor...")
    reels = scrape_reels(dry_run=dry_run)

    if not reels:
        print("[PIPELINE] Reel verisi bulunamadı, pipeline durduruluyor.")
        return

    # Adım 2: Analyze
    print("\n📌 ADIM 2: Marka mention'ları analiz ediliyor...")
    new_brands = find_new_brands(reels)

    if not new_brands:
        print("\n✅ Yeni marka bulunamadı. Pipeline tamamlandı.")
        return

    # Adım 3: Find contacts
    print(f"\n📌 ADIM 3: {len(new_brands)} yeni marka için iletişim aranıyor...")
    enriched = enrich_new_brands(new_brands)

    # Adım 4: Add to DB
    print("\n📌 ADIM 4: Yeni markalar veritabanına ekleniyor (Notion)...")
    if dry_run:
        print("[DRY-RUN] Notion'a yazma atlandı. Bulunan markalar:")
        for b in enriched:
            print(f"  • {b.get('marka_adi')} -> email: {b.get('email_status')}")
    else:
        add_brands_batch(enriched)

    # Adım 5: Send outreach
    print("\n📌 ADIM 5: Outreach e-postaları gönderiliyor...")
    stats = send_outreach_emails(dry_run=dry_run)

    print("\n" + "═" * 60)
    print("✅ HAFTALIK PİPELİNE TAMAMLANDI")
    print(f"   Yeni marka: {len(new_brands)}")
    print(f"   Email gönderilen: {stats['sent']}")
    print("═" * 60)


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    if "--send-only" in sys.argv:
        send_outreach_emails(dry_run=dry)
    else:
        run_full_pipeline(dry_run=dry)
