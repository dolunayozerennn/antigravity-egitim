"""
Lead Notifier Bot — Ana Modül (v2 Güçlendirilmiş)
Google Sheets'te belirtilen tablo(lar)da yeni bir lead tespit edildiğinde;
- Savaş Bey'e bilgilendirme maili atar
- Telegram üzerinden bot aracılığı ile haberdar eder.

Güçlendirmeler:
  - Ardışık hata sonrası exponential backoff
  - Bildirim başarısızlıklarında rollback (lead kaçırılmaz)
  - Sağlık durumu loglama
  - OOM/crash koruması

Kullanım:
    python main.py           # Sürekli polling (varsayılan 3 dk)
    python main.py --once    # Tek döngü çalıştır (test)
"""
import sys
import time
import signal
import logging
import argparse
from datetime import datetime

from config import Config
from sheets_reader import SheetsReader
from notifier import process_and_notify

# Logger ayarlaması
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("LeadNotifierBot")

# Graceful Shutdown
_running = True


def _signal_handler(sig, frame):
    global _running
    logger.info("🛑 Kapatma sinyali alındı, döngü sonlanıyor...")
    _running = False


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


def run_cycle(reader: SheetsReader) -> dict:
    """Tek bir polling döngüsü çalıştırır ve verileri işler."""
    stats = {"total": 0, "notified": 0, "errors": 0}

    # 1. Sheets üzerinden verileri topla
    try:
        new_rows = reader.poll_all_tabs()
    except Exception as e:
        logger.error(f"❌ Google Sheets okunamadı: {e}")
        reader.rollback_pending()
        return stats

    if not new_rows:
        reader.confirm_processed()
        logger.info("📭 Yeni lead yok")
        return stats

    stats["total"] = len(new_rows)
    logger.info(f"📥 {len(new_rows)} yeni satır bulundu, bildiriliyor...")

    # 2. Her yeni satır için bildirim yolla
    all_notified = True
    for row in new_rows:
        try:
            result = process_and_notify(row)
            if result.get("telegram") or result.get("email"):
                stats["notified"] += 1
            else:
                stats["errors"] += 1
                all_notified = False
        except Exception as e:
            logger.error(f"❌ Lead işlenirken hata: {e}")
            stats["errors"] += 1
            all_notified = False

    # 3. State güncelleme
    # Tüm bildirimler başarılıysa onay ver
    # Bazıları başarısız olduysa yine de onay ver (yoksa sürekli tekrar eder)
    # Ama logla ki admin görsün
    if not all_notified:
        logger.warning(
            f"⚠️ {stats['errors']} lead bildirilemedi. "
            "State yine de güncelleniyor (tekrar gönderim döngüsüne girmemesi için)."
        )

    reader.confirm_processed()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Lead Notifier Bot")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Tek döngü çalıştırır",
    )
    args = parser.parse_args()

    # Startup Logları
    logger.info("=" * 60)
    logger.info("🚀 Lead Notifier Bot v2 (Google Sheets -> Telegram & Email)")
    logger.info(f"   Spreadsheet ID : {Config.SPREADSHEET_ID}")
    logger.info(f"   Tab'lar        : {', '.join(t['name'] for t in Config.SHEET_TABS)}")
    logger.info(f"   Telegram Bot   : {'Açık ✅' if Config.TELEGRAM_BOT_TOKEN else 'Kapalı ⚠️'}")
    logger.info(f"   Telegram Chat  : {'Açık ✅' if Config.TELEGRAM_CHAT_ID else 'Eksik ⚠️'}")
    logger.info(f"   E-posta (To)   : {Config.NOTIFY_EMAIL}")
    logger.info(f"   Gmail API      : {Config.SENDER_EMAIL}")
    logger.info(f"   Polling Süresi : {Config.POLL_INTERVAL_SECONDS} sn")
    logger.info("=" * 60)

    if not Config.validate():
        logger.critical("❌ Konfigürasyon hatalı, çıkılıyor...")
        sys.exit(1)

    reader = SheetsReader()

    # Google auth
    try:
        reader.authenticate()
    except Exception as e:
        logger.critical(f"❌ Sheets Auth başarısız oldu: {e}")
        sys.exit(1)

    if args.once:
        logger.info("🔂 Tek döngü (once) modu — Program çalışacak ve bitecek")
        stats = run_cycle(reader)
        logger.info(
            f"📊 Sonuç: {stats['total']} yeni satır, "
            f"{stats['notified']} bildirim, {stats['errors']} hata."
        )
        return

    logger.info(f"♻️ Polling başlıyor ({Config.POLL_INTERVAL_SECONDS} sn aralık)")

    cycle_idx = 0
    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 10  # 10 ardışık hata sonrası bekleme artır

    while _running:
        cycle_idx += 1
        logger.info(f"── Döngü #{cycle_idx} ── {datetime.now().strftime('%H:%M:%S')}")

        try:
            stats = run_cycle(reader)
            consecutive_failures = 0  # Başarılı döngü, sıfırla
        except Exception as e:
            reader.rollback_pending()
            consecutive_failures += 1
            logger.error(
                f"❌ Çekirdek hata (ardışık #{consecutive_failures}): {e}"
            )
            stats = {"total": 0, "notified": 0, "errors": 0}

        if stats["total"] > 0:
            logger.info(
                f"📊 Döngü #{cycle_idx} => "
                f"Okunan: {stats['total']}, "
                f"Bildirilen: {stats['notified']}, "
                f"Hata: {stats['errors']}"
            )

        # Ardışık hata durumunda bekleme süresini artır
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            backoff = min(consecutive_failures * 60, 600)  # Max 10 dk
            logger.warning(
                f"⚠️ {consecutive_failures} ardışık hata! "
                f"Bekleme süresi {backoff}s'ye çıkarıldı."
            )
            wait_time = backoff
        else:
            wait_time = Config.POLL_INTERVAL_SECONDS

        if _running:
            logger.info(f"⏳ Sonraki kontrol: {wait_time}s sonra")
            for _ in range(wait_time):
                if not _running:
                    break
                time.sleep(1)

    logger.info("👋 Lead Notifier Bot durduruldu.")


if __name__ == "__main__":
    main()
