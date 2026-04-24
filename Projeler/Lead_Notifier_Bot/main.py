"""
Lead Notifier Bot v3 — Ana Modül

Google Sheets'te yeni lead tespit edildiğinde Savaş'a
Telegram + Email ile anlık bildirim gönderir.

v3 Değişiklikler:
  - ID tabanlı state (satır sayısı sorunu kökten çözüldü)
  - lead_status filtresi (sadece CREATED lead'ler)
  - Batch size limiti (tek döngüde max bildirim)
  - Fail-fast config validation

Kullanım:
    python main.py           # Sürekli polling (varsayılan 5 dk)
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

# Logger
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
    """Tek bir polling döngüsü çalıştırır."""
    stats = {"total": 0, "notified": 0, "errors": 0, "processed_row_indices": []}

    # 1. Yeni lead'leri tespit et
    try:
        new_leads = reader.get_new_leads()
    except Exception as e:
        logger.error(f"❌ Google Sheets okunamadı: {e}", exc_info=True)
        return stats

    if not new_leads:
        logger.info("📭 Yeni lead yok")
        return stats

    stats["total"] = len(new_leads)

    # 2. Batch size kontrolü — spam koruması
    if len(new_leads) > Config.MAX_BATCH_SIZE:
        logger.warning(
            f"⚠️ {len(new_leads)} yeni lead bulundu, "
            f"batch limiti {Config.MAX_BATCH_SIZE}. "
            f"İlk {Config.MAX_BATCH_SIZE} lead bildirilecek."
        )
        new_leads = new_leads[:Config.MAX_BATCH_SIZE]

    logger.info(f"📥 {len(new_leads)} yeni lead bildiriliyor...")

    # 3. Her lead için bildirim gönder
    for lead in new_leads:
        try:
            result = process_and_notify(lead)
            if result.get("telegram") or result.get("email"):
                stats["notified"] += 1
                row_idx = lead.get("__row_index__")
                if row_idx:
                    stats["processed_row_indices"].append(row_idx)
            else:
                stats["errors"] += 1
        except Exception as e:
            logger.error(f"❌ Lead işlenirken hata: {e}", exc_info=True)
            stats["errors"] += 1

    # 4. State güncelle
    # Sadece başarılı olanların Sheet satırları update edilir.
    if stats["errors"] > 0:
        logger.warning(
            f"⚠️ {stats['errors']} lead bildirilemedi. "
            "Başarısız olanlar bir sonraki döngüde tekrar denenecek."
        )

    if stats["processed_row_indices"]:
        reader.mark_as_notified(stats["processed_row_indices"])
    return stats


def main():
    parser = argparse.ArgumentParser(description="Lead Notifier Bot v3")
    parser.add_argument("--once", action="store_true", help="Tek döngü çalıştır")
    args = parser.parse_args()

    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Lead Notifier Bot v3")
    logger.info(f"   Spreadsheet  : {Config.SPREADSHEET_ID}")
    logger.info(f"   Tab           : {Config.SHEET_TAB}")
    logger.info(f"   Telegram Bot  : {'✅' if Config.TELEGRAM_BOT_TOKEN else '⚠️ Eksik'}")
    logger.info(f"   Telegram Chat : {'✅' if Config.TELEGRAM_CHAT_ID else '⚠️ Eksik'}")
    logger.info(f"   Email (To)    : {Config.NOTIFY_EMAIL}")
    logger.info(f"   Email (From)  : {Config.SENDER_EMAIL}")
    logger.info(f"   Polling       : {Config.POLL_INTERVAL_SECONDS}s")
    logger.info(f"   Batch Limit   : {Config.MAX_BATCH_SIZE}")
    logger.info("=" * 60)

    try:
        Config.validate()
    except EnvironmentError as e:
        logger.critical(f"❌ {e}")
        sys.exit(1)

    reader = SheetsReader()

    try:
        reader.authenticate()
    except Exception as e:
        logger.critical(f"❌ Sheets Auth başarısız: {e}", exc_info=True)
        sys.exit(1)

    # Once modu
    if args.once:
        logger.info("🔂 Tek döngü (once) modu")
        stats = run_cycle(reader)
        logger.info(
            f"📊 Sonuç: {stats['total']} yeni, "
            f"{stats['notified']} bildirim, "
            f"{stats['errors']} hata"
        )
        return

    # Sürekli polling
    logger.info(f"♻️ Polling başlıyor ({Config.POLL_INTERVAL_SECONDS}s aralık)")

    cycle_idx = 0
    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 10

    while _running:
        cycle_idx += 1
        logger.info(f"── Döngü #{cycle_idx} ── {datetime.now().strftime('%H:%M:%S')}")

        try:
            stats = run_cycle(reader)
            consecutive_failures = 0
        except Exception as e:
            consecutive_failures += 1
            logger.error(
                f"❌ Çekirdek hata (ardışık #{consecutive_failures}): {e}",
                exc_info=True
            )
            stats = {"total": 0, "notified": 0, "errors": 0}

        if stats["total"] > 0:
            logger.info(
                f"📊 Döngü #{cycle_idx} => "
                f"Okunan: {stats['total']}, "
                f"Bildirilen: {stats['notified']}, "
                f"Hata: {stats['errors']}"
            )

        # Backoff
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            backoff = min(consecutive_failures * 60, 600)
            logger.warning(
                f"⚠️ {consecutive_failures} ardışık hata! "
                f"Bekleme {backoff}s'ye çıkarıldı."
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
