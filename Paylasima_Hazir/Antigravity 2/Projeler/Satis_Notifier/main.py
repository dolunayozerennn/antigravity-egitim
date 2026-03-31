"""
Tele Satış Notifier — Ana Modül
Google Sheets'teki lead'lerin zamanlama tercihine göre Ece'ye email atar.

Mantık:
  1. "Gün içinde" → Anında mail at
  2. "Akşam 6'dan sonra" → Kuyruğa al, o gün TR saati 18:00'da topluca gönder
     - Saat 18'den sonra düştüyse → anında gönder (zaten müsait saat)
  3. "Haftasonu" → Kuyruğa al:
     - Haftaiçi geldiyse → Cumartesi sabah 10:00'da topluca gönder
     - Haftasonu geldiyse → Anında gönder (zaten haftasonu)
  4. "Aramayın mesaj atın" → Mail atılmaz, log yazılır

Gönderen: GONDEREN_EMAIL_BURAYA
Alıcı: ALICI_EMAIL_BURAYA

Kullanım:
    python main.py           # Sürekli polling (5 dk)
    python main.py --once    # Tek döngü çalıştır (test)
"""
import sys
import time
import signal
import logging
import argparse
from datetime import datetime, timedelta

import pytz

from config import Config
from sheets_reader import SheetsReader
from timing_parser import detect_timing_preference, extract_lead_info
from queue_manager import QueueManager
from email_sender import send_leads_email
from alerter import alert_sheets_error, alert_email_error, alert_auth_error, alert_system_crash, alert_recovered

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("TeleSatisNotifier")

# ── Graceful Shutdown ────────────────────────────────────────
_running = True


def _signal_handler(sig, frame):
    global _running
    logger.info("🛑 Kapatma sinyali alındı, döngü durduruluyor...")
    _running = False


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


# ── Yardımcı: Türkiye saati ─────────────────────────────────
def _now_tr() -> datetime:
    """Türkiye saatini döner."""
    tz = pytz.timezone(Config.TIMEZONE)
    return datetime.now(tz)


def _is_weekend(dt: datetime) -> bool:
    """Cumartesi(5) veya Pazar(6) mı?"""
    return dt.weekday() >= 5


def _next_saturday_10am() -> datetime:
    """Bir sonraki Cumartesi 10:00 TR saatini döner."""
    tz = pytz.timezone(Config.TIMEZONE)
    now = _now_tr()
    days_until_saturday = (5 - now.weekday()) % 7
    if days_until_saturday == 0 and now.hour >= 10:
        days_until_saturday = 7  # Bu cumartesi geçtiyse gelecek hafta
    next_sat = now + timedelta(days=days_until_saturday)
    return next_sat.replace(hour=10, minute=0, second=0, microsecond=0)


# ── Ana İş Mantığı ──────────────────────────────────────────

def process_new_leads(new_rows: list[dict], queue: QueueManager) -> dict:
    """
    Yeni lead'leri zamanlama tercihine göre işler.
    
    Returns:
        {"instant": N, "queued_evening": N, "queued_weekend": N, "skipped": N, "errors": N}
    """
    stats = {"instant": 0, "queued_evening": 0, "queued_weekend": 0, "skipped": 0, "errors": 0}
    now = _now_tr()
    today_str = now.strftime("%Y-%m-%d")

    instant_leads = []

    for row in new_rows:
        lead = extract_lead_info(row)
        timing = lead["timing"]

        if timing == "gun_icinde":
            # 🚀 Anında mail at
            instant_leads.append(lead)
            stats["instant"] += 1
            logger.info(f"🚀 Anlık gönderim: {lead['name']} (Gün içinde)")

        elif timing == "aksam_6":
            # Saat 18'den sonra mı?
            if now.hour >= Config.EVENING_SEND_HOUR:
                # Zaten akşam 6'dan sonra — anında gönder
                instant_leads.append(lead)
                stats["instant"] += 1
                logger.info(
                    f"🚀 Anlık gönderim: {lead['name']} "
                    f"(Akşam 6 istedi ama saat {now.hour}:{now.minute:02d}, zaten müsait)"
                )
            else:
                # Kuyruğa al
                queue.add_to_evening_queue(lead, today_str)
                stats["queued_evening"] += 1

        elif timing == "haftasonu":
            if _is_weekend(now):
                # Zaten haftasonu — anında gönder
                instant_leads.append(lead)
                stats["instant"] += 1
                logger.info(
                    f"🚀 Anlık gönderim: {lead['name']} "
                    f"(Haftasonu istedi ve zaten haftasonu)"
                )
            else:
                # Hafta içi — kuyruğa al
                queue.add_to_weekend_queue(lead)
                stats["queued_weekend"] += 1

        elif timing == "mesaj":
            # Aramayın mesaj atın — mail atılmaz
            logger.info(f"💬 SMS/mesaj tercihi: {lead['name']} — mail atılmıyor")
            stats["skipped"] += 1

        else:
            # Bilinmeyen tercih — anlık gönder (varsayılan)
            instant_leads.append(lead)
            stats["instant"] += 1
            logger.warning(
                f"⚠️ Bilinmeyen tercih ({timing}): {lead['name']} "
                f"— varsayılan olarak anlık gönderiliyor"
            )

    # Anlık lead'leri gönder
    if instant_leads:
        success = send_leads_email(instant_leads, "anlik")
        if not success:
            stats["errors"] += len(instant_leads)
            stats["instant"] = 0
            alert_email_error("Anlık lead e-postası gönderilemedi", len(instant_leads))

    return stats


def check_scheduled_queues(queue: QueueManager) -> dict:
    """
    Zamanlı kuyrukları kontrol eder ve uygun saatte topluca gönderir.
    
    Returns:
        {"evening_sent": N, "weekend_sent": N}
    """
    result = {"evening_sent": 0, "weekend_sent": 0}
    now = _now_tr()
    today_str = now.strftime("%Y-%m-%d")

    # ── Akşam 6 Kuyruğu ──────────────────────────────────
    if now.hour >= Config.EVENING_SEND_HOUR:
        evening_leads = queue.get_evening_leads(today_str)
        if evening_leads:
            logger.info(
                f"⏰ Akşam 6 kuyruğu gönderiliyor: {len(evening_leads)} lead"
            )
            success = send_leads_email(evening_leads, "aksam_6")
            if success:
                queue.clear_evening_queue(today_str)
                result["evening_sent"] = len(evening_leads)
            else:
                logger.error("❌ Akşam 6 kuyruğu gönderilemedi, sonraki döngüde tekrar denenecek")
                alert_email_error("Akşam 6 kuyruğu gönderilemedi", len(evening_leads))

    # ── Haftasonu Kuyruğu ─────────────────────────────────
    if _is_weekend(now) and now.hour >= Config.WEEKEND_SEND_HOUR:
        weekend_leads = queue.get_weekend_leads()
        if weekend_leads:
            logger.info(
                f"⏰ Haftasonu kuyruğu gönderiliyor: {len(weekend_leads)} lead"
            )
            success = send_leads_email(weekend_leads, "haftasonu")
            if success:
                queue.clear_weekend_queue()
                result["weekend_sent"] = len(weekend_leads)
            else:
                logger.error("❌ Haftasonu kuyruğu gönderilemedi, sonraki döngüde tekrar denenecek")
                alert_email_error("Haftasonu kuyruğu gönderilemedi", len(weekend_leads))

    return result


# ── Polling Döngüsü ─────────────────────────────────────────

def run_cycle(reader: SheetsReader, queue: QueueManager) -> dict:
    """Tek bir polling döngüsü."""
    stats = {
        "total": 0, "instant": 0, "queued_evening": 0,
        "queued_weekend": 0, "skipped": 0, "errors": 0,
        "evening_sent": 0, "weekend_sent": 0,
    }

    # 1) Yeni lead'leri oku
    try:
        new_rows = reader.poll_all_tabs()
    except Exception as e:
        logger.error(f"❌ Google Sheets okunamadı: {e}")
        alert_sheets_error(str(e), reader._consecutive_errors)
        reader.rollback_pending()
        return stats

    # 2) Yeni lead'leri işle
    if new_rows:
        stats["total"] = len(new_rows)
        logger.info(f"📥 {len(new_rows)} yeni lead bulundu, zamanlama kontrolü yapılıyor...")
        
        lead_stats = process_new_leads(new_rows, queue)
        stats.update(lead_stats)

    # 3) Zamanlı kuyrukları kontrol et
    queue_result = check_scheduled_queues(queue)
    stats.update(queue_result)

    # 4) State'i onayla
    reader.confirm_processed()

    if not new_rows:
        logger.info("📭 Yeni lead yok")

    return stats


def main():
    """Ana giriş noktası."""
    parser = argparse.ArgumentParser(description="Tele Satış Notifier")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Tek döngü çalıştır (test)",
    )
    args = parser.parse_args()

    # Banner
    now = _now_tr()
    logger.info("=" * 65)
    logger.info("📞 Tele Satış Notifier — Ece'ye Zamanlı Lead Bildirimi")
    logger.info(f"   Spreadsheet:  {Config.SPREADSHEET_ID}")
    logger.info(f"   Tab'lar:      {', '.join(t['name'] for t in Config.SHEET_TABS)}")
    logger.info(f"   Gönderen:     {Config.SENDER_EMAIL}")
    logger.info(f"   Alıcı:        {Config.RECIPIENT_EMAIL}")
    logger.info(f"   Polling:      {Config.POLL_INTERVAL_SECONDS}s aralık")
    logger.info(f"   Akşam saati:  {Config.EVENING_SEND_HOUR}:00 TR")
    logger.info(f"   Haftasonu:    Cumartesi {Config.WEEKEND_SEND_HOUR}:00 TR")
    logger.info(f"   Şu an:        {now.strftime('%Y-%m-%d %H:%M:%S %Z')} "
                f"({'Haftasonu' if _is_weekend(now) else 'Haftaiçi'})")
    logger.info("=" * 65)

    if not Config.validate():
        logger.critical("❌ Konfigürasyon hatalı, çıkılıyor...")
        sys.exit(1)

    # Modülleri başlat
    reader = SheetsReader()

    try:
        reader.authenticate()
    except Exception as e:
        logger.critical(f"❌ Google Sheets authentication başarısız: {e}")
        alert_auth_error(str(e))
        sys.exit(1)

    # QueueManager — SheetsReader'ın service nesnesini paylaşır (ayrı auth gerekmez)
    queue = QueueManager(sheets_service=reader.service)

    # Kuyruk durumunu göster
    q_status = queue.get_status()
    if q_status["aksam_6"] > 0 or q_status["haftasonu"] > 0:
        logger.info(
            f"📋 Mevcut kuyruk: Akşam 6={q_status['aksam_6']} | "
            f"Haftasonu={q_status['haftasonu']}"
        )

    if args.once:
        logger.info("🔂 Tek döngü modu — çalışıp çıkacak")
        stats = run_cycle(reader, queue)
        _log_stats(stats)
        return

    # Sürekli polling loop
    logger.info(f"♻️ Polling başlıyor ({Config.POLL_INTERVAL_SECONDS}s aralık)")

    cycle_idx = 0
    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 10

    while _running:
        cycle_idx += 1
        logger.info(f"── Döngü #{cycle_idx} ── {_now_tr().strftime('%H:%M:%S %Z')}")

        try:
            stats = run_cycle(reader, queue)
            if consecutive_failures > 0:
                alert_recovered()
            consecutive_failures = 0
            wait_time = Config.POLL_INTERVAL_SECONDS
        except Exception as e:
            reader.rollback_pending()
            consecutive_failures += 1
            logger.error(f"❌ Çekirdek hata (ardışık #{consecutive_failures}): {e}", exc_info=True)
            if consecutive_failures >= 3:
                alert_system_crash(f"Ardışık {consecutive_failures} hata: {e}")
            stats = {}
            # Exception backoff
            backoff = min(consecutive_failures * 60, 600)
            logger.warning(f"⚠️ Hata sonrası {backoff}s bekleme uygulanıyor...")
            wait_time = backoff

        if stats.get("total", 0) > 0 or stats.get("evening_sent", 0) > 0 or stats.get("weekend_sent", 0) > 0:
            _log_stats(stats)

        if _running:
            logger.info(f"⏳ Sonraki kontrol: {wait_time}s sonra")
            # Uyku döngüsünü kırılabilir hale getir
            for _ in range(wait_time):
                if not _running:
                    break
                time.sleep(1)

    logger.info("👋 Tele Satış Notifier durduruldu.")


def _log_stats(stats: dict):
    """İstatistikleri loglar."""
    parts = []
    if stats.get("total", 0) > 0:
        parts.append(f"{stats['total']} yeni lead")
    if stats.get("instant", 0) > 0:
        parts.append(f"{stats['instant']} anlık gönderildi")
    if stats.get("queued_evening", 0) > 0:
        parts.append(f"{stats['queued_evening']} akşam 6 kuyruğunda")
    if stats.get("queued_weekend", 0) > 0:
        parts.append(f"{stats['queued_weekend']} haftasonu kuyruğunda")
    if stats.get("skipped", 0) > 0:
        parts.append(f"{stats['skipped']} atlandı (mesaj)")
    if stats.get("evening_sent", 0) > 0:
        parts.append(f"📤 Akşam kuyruğu: {stats['evening_sent']} lead gönderildi")
    if stats.get("weekend_sent", 0) > 0:
        parts.append(f"📤 Haftasonu kuyruğu: {stats['weekend_sent']} lead gönderildi")
    if stats.get("errors", 0) > 0:
        parts.append(f"❌ {stats['errors']} hata")

    logger.info(f"📊 Sonuç: {' | '.join(parts)}")


if __name__ == "__main__":
    main()
