"""
Bildirim Modülü
Yeni lead düştüğünde Telegram ve E-Posta üzerinden haber verir.
"""
import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import Config

logger = logging.getLogger(__name__)

def build_message_text(lead_data: dict) -> str:
    """Lead sözlüğünü okunabilir bir metin formatına çevirir."""
    lines = ["Yeni Lead Düştü! 🚀\n"]
    for key, value in lead_data.items():
        if key == "_source_tab":
            lines.append(f"📌 Kaynak: {value}")
        else:
            lines.append(f"👤 {key}: {value}")
    
    return "\n".join(lines)

def send_telegram_notification(msg_text: str):
    """Telegram API üzerinden mesaj gönderir."""
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram bildirimleri kapalı (Token veya Chat ID eksik).")
        return

    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": Config.TELEGRAM_CHAT_ID,
        "text": msg_text,
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("✅ Telegram bildirimi gönderildi.")
    except Exception as e:
        logger.error(f"❌ Telegram bildirimi gönderilirken hata oluştu: {e}")

def send_email_notification(msg_text: str):
    """SMTP kullanarak E-Posta bildirimi gönderir."""
    if not Config.SMTP_USER or not Config.SMTP_APP_PASSWORD or not Config.NOTIFY_EMAIL:
        logger.warning("⚠️ E-Posta bildirimleri kapalı (SMTP bilgileri veya Notify Email eksik).")
        return

    msg = MIMEMultipart()
    msg['From'] = Config.SMTP_USER
    msg['To'] = Config.NOTIFY_EMAIL
    msg['Subject'] = "Yeni Lead Bildirimi! 🚀"

    msg.attach(MIMEText(msg_text, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"✅ E-Posta bildirimi gönderildi -> {Config.NOTIFY_EMAIL}.")
    except Exception as e:
        logger.error(f"❌ E-Posta bildirimi gönderilirken hata oluştu: {e}")

def process_and_notify(lead_data: dict):
    """Her yeni lead için hem Telegram hem de E-posta üzerinden bildirim yollar."""
    msg_text = build_message_text(lead_data)
    
    # Her ikisini de parallel (veya ardışık) çalıştır
    send_telegram_notification(msg_text)
    send_email_notification(msg_text)
