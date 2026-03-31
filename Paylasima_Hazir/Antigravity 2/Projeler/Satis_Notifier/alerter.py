"""
Tele Satış Notifier — Alarm Modülü
Sistem hata verdiğinde Telegram üzerinden KULLANICI_ADI_BURAYA'a bildirim gönderir.
"""
import os
import logging
import urllib.request
import urllib.parse
import json
from datetime import datetime

import pytz

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "")
TIMEZONE = pytz.timezone(os.environ.get("TIMEZONE", "Europe/Istanbul"))

# Spam önleme — aynı tip alarm için minimum bekleme süresi (saniye)
_COOLDOWN_SECONDS = 1800  # 30 dakika
_last_alert_times: dict[str, float] = {}


def _can_send(alert_type: str) -> bool:
    """Aynı tip alarmı spam yapmamak için cooldown kontrol."""
    import time
    now = time.time()
    last = _last_alert_times.get(alert_type, 0)
    if now - last < _COOLDOWN_SECONDS:
        return False
    _last_alert_times[alert_type] = now
    return True


def send_telegram_alert(message: str, alert_type: str = "generic") -> bool:
    """Telegram üzerinden alarm gönderir.
    
    Args:
        message: Gönderilecek mesaj
        alert_type: Alarm tipi (cooldown için)
    
    Returns:
        True = başarılı, False = başarısız
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram token/chat_id ayarlanmamış, alarm gönderilemedi")
        return False

    if not _can_send(alert_type):
        logger.debug(f"⏳ '{alert_type}' alarmı cooldown'da, atlanıyor")
        return False

    now = datetime.now(TIMEZONE).strftime("%d.%m.%Y %H:%M")
    full_message = f"🚨 *Tele Satış Notifier*\n{now}\n\n{message}"

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": full_message,
            "parse_mode": "Markdown"
        }).encode()

        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                logger.info(f"✅ Telegram alarmı gönderildi: {alert_type}")
                return True
            else:
                logger.error(f"❌ Telegram API hatası: {result}")
                return False

    except Exception as e:
        logger.error(f"❌ Telegram alarmı gönderilemedi: {e}")
        return False


# ── HAZIR ALARM FONKSİYONLARI ───────────────────────────

def alert_sheets_error(error_msg: str, consecutive_count: int):
    """Google Sheets okunamıyor."""
    send_telegram_alert(
        f"📊 *Google Sheets okunamıyor!*\n"
        f"Ardışık hata: {consecutive_count}\n"
        f"Hata: `{error_msg[:200]}`\n\n"
        f"Ece'ye lead bildirimi *durmuş olabilir*.",
        alert_type="sheets_error"
    )


def alert_email_error(error_msg: str, lead_count: int):
    """E-posta gönderilemedi."""
    send_telegram_alert(
        f"📧 *E-posta gönderilemedi!*\n"
        f"Gönderilemeyen lead sayısı: {lead_count}\n"
        f"Hata: `{error_msg[:200]}`\n\n"
        f"Ece bu lead'lerden *haberdar değil*.",
        alert_type="email_error"
    )


def alert_auth_error(error_msg: str):
    """Authentication hatası."""
    send_telegram_alert(
        f"🔑 *Authentication hatası!*\n"
        f"Hata: `{error_msg[:200]}`\n\n"
        f"OAuth token süresi dolmuş veya geçersiz olabilir.\n"
        f"Sistem *tamamen durmuş* durumda.",
        alert_type="auth_error"
    )


def alert_system_crash(error_msg: str):
    """Sistem çöktü."""
    send_telegram_alert(
        f"💥 *Sistem çöktü!*\n"
        f"Hata: `{error_msg[:200]}`\n\n"
        f"Lead zamanlayıcı *durdu*. Acil müdahale gerekiyor.",
        alert_type="system_crash"
    )


def alert_recovered():
    """Sistem toparlandı."""
    send_telegram_alert(
        f"✅ *Sistem toparlandı!*\n"
        f"Lead zamanlayıcı tekrar çalışıyor.",
        alert_type="recovered"
    )
