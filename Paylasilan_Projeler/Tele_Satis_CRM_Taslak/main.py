"""
Tele Satış CRM — Ana Modül
Google Sheets'ten Notion'a lead aktarım otomasyonu.

Meta reklamlarından gelen lead'leri:
1. Google Sheets'ten okur (5 dk polling)
2. Veriyi temizler (telefon, isim, email, bütçe)
3. Duplikasyon kontrolü yapar (telefon/email filtresi)
4. Notion CRM'e ekler (Durum: Aranacak, Komisyon: Ödenmedi)
5. Hata durumunda bildirim gönderir

Kullanım:
    python main.py           # Sürekli polling (5 dk)
    python main.py --once    # Tek döngü çalıştır
"""
import re
import sys
import time
import signal
import logging
import argparse
from datetime import datetime

from requests.exceptions import ConnectionError, Timeout

from config import Config
from sheets_reader import SheetsReader
from data_cleaner import clean_lead
from notion_writer import NotionWriter
from notifier import send_error_notification

# ── Logging Yapılandırması ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("TeleSatisCRM")

# ── Graceful Shutdown ───────────────────────────────────────────────
_running = True


def _signal_handler(sig, frame):
    global _running
    logger.info("🛑 Kapatma sinyali alındı, döngü durduruluyor...")
    _running = False


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


# ── İş Mantığı ─────────────────────────────────────────────────────

def run_cycle(reader: SheetsReader, writer: NotionWriter) -> dict:
    """
    Tek bir polling döngüsü çalıştırır.
    
    Returns:
        {"total": N, "created": N, "skipped": N, "errors": N}
    """
    stats = {"total": 0, "created": 0, "skipped": 0, "errors": 0}

    # 1) Google Sheets'ten yeni satırları oku
    try:
        new_rows = reader.poll_all_tabs()
    except Exception as e:
        logger.error(f"❌ Google Sheets okunamadı: {e}")
        reader.rollback_pending()
        send_error_notification(
            {"clean_name": "SISTEM", "clean_email": "-", "clean_phone": "-"},
            f"Google Sheets okuma hatası: {e}",
        )
        return stats

    if not new_rows:
        reader.confirm_processed()
        logger.info("📭 Yeni lead yok")
        return stats

    stats["total"] = len(new_rows)
    logger.info(f"📥 {len(new_rows)} yeni satır alındı, işleniyor...")

    # Tüm lead'leri temizle (geçersizleri atla)
    cleaned_leads = []
    for row in new_rows:
        cleaned = clean_lead(row)
        if not cleaned["clean_name"]:
            logger.warning(f"⚠️ İsim boş, satır atlanıyor: {row}")
            stats["skipped"] += 1
        else:
            cleaned_leads.append(cleaned)

    if not cleaned_leads:
        reader.confirm_processed()
        return stats

    # Toplu Notion kontrolü
    logger.info(f"🔍 {len(cleaned_leads)} lead için toplu duplikasyon kontrolü yapılıyor...")
    try:
        existing_phones, existing_emails, existing_names = writer.bulk_check_duplicates(cleaned_leads)
    except Exception as e:
        logger.error(f"❌ Toplu duplikasyon kontrolü başarısız: {e}")
        reader.rollback_pending()
        raise

    # Batch içi dedup set — Notion verileriyle başlatıyoruz (cross-tab engellemek için de işe yarar)
    seen_phones: set[str] = existing_phones.copy()
    seen_emails: set[str] = existing_emails.copy()
    seen_names: set[str] = existing_names.copy()

    # 2) Her satırı işle
    for cleaned in cleaned_leads:
        phone_key = re.sub(r"[^\d]", "", cleaned["clean_phone"]) if cleaned["clean_phone"] else ""
        email_key = cleaned["clean_email"]
        name_key = cleaned["clean_name"]

        is_dup = False
        reason = ""

        if phone_key and phone_key in seen_phones:
            is_dup = True
            reason = f"Telefon eşleşti ({phone_key})"
        elif email_key and email_key in seen_emails:
            is_dup = True
            reason = f"Email eşleşti ({email_key})"
        elif not phone_key and not email_key and name_key and name_key in seen_names:
            is_dup = True
            reason = f"İsim eşleşti ({name_key})"

        if is_dup:
            logger.info(f"🔁 Duplike tespit: {cleaned['clean_name']} - {reason}, atlanıyor")
            stats["skipped"] += 1
            continue

        # Notion'a ekle (artık tekil kontrol atlancak)
        result = writer.process_lead(cleaned, skip_duplicate_check=True)

        if result["action"] == "created":
            stats["created"] += 1
        elif result["action"] == "skipped":
            stats["skipped"] += 1
        elif result["action"] == "error":
            stats["errors"] += 1
            send_error_notification(cleaned, result.get("error", "Bilinmeyen hata"))

        # Başarılı veya skip olan lead'leri de seen set'lere ekle
        # Böylece farklı tab'dan gelen aynı kişi için gereksiz işlem yapılmaz
        if result["action"] in ("created", "skipped"):
            if phone_key:
                seen_phones.add(phone_key)
            if email_key:
                seen_emails.add(email_key)
            if name_key:
                seen_names.add(name_key)

    # Tüm lead'ler işlendi — satır sayılarını onayla ve kaydet
    reader.confirm_processed()
    return stats


def main():
    """Ana giriş noktası."""
    parser = argparse.ArgumentParser(description="Tele Satış CRM — Lead Otomasyonu")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Tek döngü çalıştır (polling loop yerine)",
    )
    args = parser.parse_args()

    # Banner
    logger.info("=" * 60)
    logger.info("🚀 Tele Satış CRM — Lead Aktarım Otomasyonu")
    logger.info(f"   Spreadsheet: {Config.SPREADSHEET_ID}")
    logger.info(f"   Notion DB:   {Config.NOTION_DATABASE_ID}")
    logger.info(f"   Polling:     {Config.POLL_INTERVAL_SECONDS}s aralık")
    logger.info(f"   Tab'lar:     {', '.join(t['name'] for t in Config.SHEET_TABS)}")
    logger.info("=" * 60)

    # Konfigürasyon doğrulama
    if not Config.validate():
        logger.critical("❌ Konfigürasyon hatalı, çıkılıyor...")
        sys.exit(1)

    # Modülleri başlat
    reader = SheetsReader()
    writer = NotionWriter()

    # Google Sheets authentication
    try:
        reader.authenticate()
    except Exception as e:
        logger.critical(f"❌ Google Sheets authentication başarısız: {e}")
        sys.exit(1)

    if args.once:
        # Tek döngü modu
        logger.info("🔂 Tek döngü modu — bir kez çalışıp çıkacak")
        stats = run_cycle(reader, writer)
        logger.info(
            f"📊 Sonuç: {stats['total']} toplam | "
            f"{stats['created']} oluşturuldu | "
            f"{stats['skipped']} atlandı | "
            f"{stats['errors']} hata"
        )
        return

    # Sürekli polling loop
    logger.info(
        f"♻️ Polling başlıyor — {Config.POLL_INTERVAL_SECONDS} saniye aralıkla"
    )

    cycle_count = 0
    while _running:
        cycle_count += 1
        logger.info(f"─── Döngü #{cycle_count} ─── {datetime.now().strftime('%H:%M:%S')}")

        try:
            stats = run_cycle(reader, writer)
        except (ConnectionError, Timeout) as e:
            reader.rollback_pending()
            logger.error(
                f"❌ Geçici ağ hatası, sonraki döngüde tekrar denenecek: {e}"
            )
            send_error_notification(
                {"clean_name": "SISTEM", "clean_email": "-", "clean_phone": "-"},
                f"Geçici ağ hatası: {e}",
            )
            stats = {"total": 0, "created": 0, "skipped": 0, "errors": 0}

        if stats["total"] > 0:
            logger.info(
                f"📊 Döngü #{cycle_count}: "
                f"{stats['total']} toplam | "
                f"{stats['created']} oluşturuldu | "
                f"{stats['skipped']} atlandı | "
                f"{stats['errors']} hata"
            )

        # Sonraki döngüyü bekle
        if _running:
            logger.info(
                f"⏳ Sonraki kontrol: {Config.POLL_INTERVAL_SECONDS}s sonra"
            )
            # Bekleme süresini küçük parçalara böl (graceful shutdown için)
            for _ in range(Config.POLL_INTERVAL_SECONDS):
                if not _running:
                    break
                time.sleep(1)

    logger.info("👋 Tele Satış CRM kapatıldı")


if __name__ == "__main__":
    main()
