"""
Tele Satış CRM — WhatsApp Link Backfill Scripti

Mevcut tüm lead kayıtlarının WhatsApp Link alanını
Notion formula'dan URL property'e geçiş sonrası doldurur.

Kullanım:
    python backfill_whatsapp.py          # Dry-run (değişiklik yapmaz)
    python backfill_whatsapp.py --apply  # Gerçek güncelleme
"""
import re
import sys
import time
import logging
import requests

from config import Config

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

NOTION_API_URL = "https://api.notion.com/v1"
WHATSAPP_BASE = "https://wa.me/"
NOTION_VERSION = "2022-06-28"

HEADERS = {
    "Authorization": f"Bearer {Config.NOTION_API_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}


def build_whatsapp_link(phone: str) -> str:
    """Telefon numarasından WhatsApp linki üretir."""
    if not phone:
        return ""
    digits = re.sub(r"[^\d]", "", phone)
    return f"{WHATSAPP_BASE}{digits}" if digits else ""


def fetch_all_leads() -> list[dict]:
    """Tüm lead'leri Notion'dan çeker (pagination destekli)."""
    url = f"{NOTION_API_URL}/databases/{Config.NOTION_DATABASE_ID}/query"
    all_results = []
    has_more = True
    start_cursor = None

    while has_more:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor

        resp = requests.post(url, headers=HEADERS, json=payload)
        resp.raise_for_status()
        data = resp.json()

        all_results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return all_results


def update_whatsapp_link(page_id: str, wa_link: str) -> bool:
    """Tek bir sayfanın WhatsApp Link property'sini günceller."""
    url = f"{NOTION_API_URL}/pages/{page_id}"
    payload = {
        "properties": {
            "WhatsApp Link": {"url": wa_link if wa_link else None}
        }
    }

    resp = requests.patch(url, headers=HEADERS, json=payload)
    if resp.status_code == 200:
        return True
    else:
        logger.error(f"  ❌ Hata ({resp.status_code}): {resp.text[:200]}")
        return False


def main():
    dry_run = "--apply" not in sys.argv

    if dry_run:
        logger.info("🔍 DRY-RUN modu — değişiklik yapılmayacak")
        logger.info("   Gerçek güncelleme için: python backfill_whatsapp.py --apply\n")
    else:
        logger.info("🚀 APPLY modu — WhatsApp linkleri güncellenecek\n")

    # Tüm lead'leri çek
    logger.info("📋 Lead'ler çekiliyor...")
    leads = fetch_all_leads()
    logger.info(f"   Toplam {len(leads)} kayıt bulundu\n")

    updated = 0
    skipped = 0
    errors = 0

    for lead in leads:
        props = lead.get("properties", {})
        page_id = lead["id"]

        # İsim
        title_arr = props.get("İsim", {}).get("title", [])
        name = title_arr[0]["plain_text"] if title_arr else "İsimsiz"

        # Telefon numarasını al
        phone = props.get("Phone", {}).get("phone_number", "")

        # Mevcut WhatsApp Link (varsa)
        existing_wa = props.get("WhatsApp Link", {})
        # Formula ise .formula.string, URL ise .url
        if existing_wa.get("type") == "formula":
            existing_url = existing_wa.get("formula", {}).get("string", "")
        elif existing_wa.get("type") == "url":
            existing_url = existing_wa.get("url", "") or ""
        else:
            existing_url = ""

        # Yeni link hesapla
        new_link = build_whatsapp_link(phone)

        if not phone:
            skipped += 1
            continue

        if existing_url == new_link:
            skipped += 1
            continue

        if dry_run:
            logger.info(f"  📝 {name}: {new_link}")
            updated += 1
        else:
            success = update_whatsapp_link(page_id, new_link)
            if success:
                logger.info(f"  ✅ {name}: {new_link}")
                updated += 1
                # Rate limit koruması (Notion: 3 req/sn)
                time.sleep(0.35)
            else:
                errors += 1

    logger.info(f"\n{'='*50}")
    logger.info(f"📊 Sonuç:")
    logger.info(f"   Güncellenecek: {updated}")
    logger.info(f"   Atlandı:       {skipped}")
    if errors:
        logger.info(f"   Hata:          {errors}")

    if dry_run and updated > 0:
        logger.info(f"\n💡 Uygulamak için: python backfill_whatsapp.py --apply")


if __name__ == "__main__":
    main()
