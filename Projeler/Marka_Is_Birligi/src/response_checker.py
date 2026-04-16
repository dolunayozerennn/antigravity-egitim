#!/usr/bin/env python3
"""
Response Checker — Outreach thread'lerinde gelen cevapları tespit eder.

- Gönderilen outreach email'lerine gelen yanıtları kontrol eder
- Cevap gelenleri CSV'de outreach_status = "Replied" olarak işaretler
- Follow-up modülünün cevap verenlere mail atmasını engeller
- Bounce olan mailleri tespit eder ve "Bounced" olarak işaretler

Çalışma zamanı: Haftalık Pipeline'dan önce (Pazartesi 06:30 UTC)
                ve Follow-up'tan önce (Perşembe 06:30 UTC)
"""

import os
import time
from datetime import datetime, timezone, timedelta
from src.notion_service import get_brands_by_status, update_brand

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TR_TZ = timezone(timedelta(hours=3))

# Bounce gönderici adresleri
BOUNCE_SENDERS = [
    "mailer-daemon@",
    "postmaster@",
    "mail-daemon@",
    "noreply@google.com",
    "delivery-notification",
]

# Bounce konu satırı kalıpları
BOUNCE_SUBJECTS = [
    "delivery status notification",
    "failure notice",
    "returned mail",
    "undeliverable",
    "undelivered mail",
    "mail delivery failed",
    "delivery has failed",
]


def check_responses(dry_run=False):
    """
    Tüm outreach thread'lerini tarar, gelen yanıt veya bounce varsa CSV'yi günceller.

    Returns:
        dict: {replied: int, bounced: int, checked: int}
    """
    from src.gmail_sender import get_service, SENDER_EMAIL

    # Sadece 'Sent' olanları kontrol et (Follow-up atılmış olanlar da 'Sent' durumundadır)
    sent_brands = get_brands_by_status("Sent")
    
    check_list = []  # (brand, thread_id)
    for brand in sent_brands:
        thread_id = brand.get("outreach_thread_id", "")
        if thread_id:
            check_list.append((brand, thread_id))

    if not check_list:
        print("[RESPONSE] Kontrol edilecek thread yok.")
        return {"replied": 0, "bounced": 0, "checked": 0}

    print(f"\n{'='*60}")
    print(f"🔍 {len(check_list)} outreach thread'i kontrol ediliyor...")
    print(f"{'='*60}")

    if dry_run:
        for b, tid in check_list:
            print(f"  [DRY-RUN] {b.get('marka_adi', '')} → Thread: {tid}")
        return {"replied": 0, "bounced": 0, "checked": len(check_list)}

    service = get_service()
    stats = {"replied": 0, "bounced": 0, "checked": 0}
    now = datetime.now(TR_TZ).strftime("%Y-%m-%d %H:%M")
    updated = False

    for brand, thread_id in check_list:
        brand_name = brand.get("marka_adi", "Bilinmeyen")

        try:
            thread = service.users().threads().get(
                userId="me", id=thread_id, format="metadata",
                metadataHeaders=["From", "Subject"]
            ).execute()
            messages = thread.get("messages", [])

            for msg in messages:
                headers = msg.get("payload", {}).get("headers", [])
                sender = ""
                subject = ""
                for h in headers:
                    if h["name"].lower() == "from":
                        sender = h["value"].lower()
                    if h["name"].lower() == "subject":
                        subject = h["value"].lower()

                # Kendi mesajımız mı kontrol et
                if SENDER_EMAIL.lower() in sender:
                    continue
                if "ozerendolunay@gmail.com" in sender:
                    continue

                # Bounce kontrolü
                is_bounce = False
                for bp in BOUNCE_SENDERS:
                    if bp in sender:
                        is_bounce = True
                        break
                if not is_bounce:
                    for bs in BOUNCE_SUBJECTS:
                        if bs in subject:
                            is_bounce = True
                            break

                if is_bounce:
                    print(f"  📛 BOUNCE: {brand_name} → {brand.get('email', '')}")
                    update_brand(brand.get("notion_page_id"), {
                        "outreach_status": "Bounced",
                        # email_status in Notion could theoretically be updated too, but outreach_status is enough
                        "notlar": f"{brand.get('notlar', '')} | Bounce detected {now}".strip(" |")
                    })
                    stats["bounced"] += 1
                    break  # Thread'deki diğer mesajlara bakmaya gerek yok
                else:
                    # Gerçek yanıt!
                    print(f"  💬 REPLY: {brand_name} → Yanıt gelmiş! (from: {sender[:50]})")
                    update_brand(brand.get("notion_page_id"), {
                        "outreach_status": "Replied",
                        "notlar": f"{brand.get('notlar', '')} | Reply detected {now}".strip(" |")
                    })
                    stats["replied"] += 1
                    break  # İlk yanıt yeterli

        except Exception as e:
            print(f"  ⚠️ {brand_name}: Thread kontrol hatası — {e}")

        stats["checked"] += 1
        time.sleep(0.5)  # Gmail API rate limit



    print(f"\n{'='*60}")
    print(f"📊 RESPONSE CHECK: {stats['checked']} kontrol, {stats['replied']} yanıt, {stats['bounced']} bounce")
    print(f"{'='*60}")
    return stats


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    check_responses(dry_run=dry)
