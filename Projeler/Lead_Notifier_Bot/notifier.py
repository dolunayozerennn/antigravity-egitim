"""
Bildirim Modülü
Yeni lead düştüğünde Telegram ve E-Posta üzerinden haber verir.
"""
import os
import sys
import json
import base64
import logging
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import Config

logger = logging.getLogger(__name__)

def _get_gmail_service():
    """Gmail API service objesi döndür."""
    env_token = os.environ.get("GOOGLE_OUTREACH_TOKEN_JSON", "")
    if env_token:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        try:
            token_data = json.loads(env_token)
        except json.JSONDecodeError:
            logger.error("❌ GOOGLE_OUTREACH_TOKEN_JSON parse edilemedi!")
            raise

        scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify',
        ]
        creds = Credentials.from_authorized_user_info(token_data, scopes)
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                logger.info("🔄 Gmail OAuth token yenilendi (Railway)")
            else:
                raise RuntimeError("Gmail token geçersiz ve yenilenemiyor (Railway)")
        return build('gmail', 'v1', credentials=creds)

    # Lokal: Merkezi google_auth kullan
    _antigravity_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    oauth_dir = os.path.join(_antigravity_root, "_knowledge", "credentials", "oauth")
    if oauth_dir not in sys.path:
        sys.path.insert(0, oauth_dir)
        
    try:
        from google_auth import get_gmail_service
        return get_gmail_service("outreach")
    except ImportError as e:
        logger.error(f"❌ Merkezi google_auth modülü bulunamadı: {e}")
        raise

def build_message_text(lead_data: dict) -> str:
    """Lead sözlüğünü okunabilir bir metin formatına çevirir."""
    lines = ["Yeni Lead Düştü! 🚀\n"]
    for key, value in lead_data.items():
        if key == "_source_tab":
            lines.append(f"📌 Kaynak: {value}")
        else:
            lines.append(f"👤 {key}: {value}")
    
    return "\n".join(lines)

def send_telegram_notification(msg_text: str) -> bool:
    """Telegram API üzerinden mesaj gönderir."""
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram bildirimleri kapalı (Token veya Chat ID eksik).")
        return False

    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": Config.TELEGRAM_CHAT_ID,
        "text": msg_text,
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("✅ Telegram bildirimi gönderildi.")
        return True
    except Exception as e:
        logger.error(f"❌ Telegram bildirimi gönderilirken hata oluştu: {e}")
        return False

def send_email_notification(msg_text: str) -> bool:
    """Gmail API kullanarak E-Posta bildirimi gönderir."""
    if not Config.NOTIFY_EMAIL:
        logger.warning("⚠️ E-Posta bildirimleri kapalı (Notify Email eksik).")
        return False

    try:
        service = _get_gmail_service()
    except Exception as e:
        logger.error(f"❌ Gmail API bağlantısı kurulamadı: {e}")
        return False

    msg = MIMEMultipart()
    msg['From'] = f"Lead Notifier <{Config.SENDER_EMAIL}>"
    msg['To'] = Config.NOTIFY_EMAIL
    msg['Subject'] = "Yeni Lead Bildirimi! 🚀"

    msg.attach(MIMEText(msg_text, 'plain', 'utf-8'))

    try:
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        logger.info(f"✅ E-Posta bildirimi gönderildi -> {Config.NOTIFY_EMAIL} | Message ID: {result.get('id', '?')}")
        return True
    except Exception as e:
        logger.error(f"❌ E-Posta bildirimi gönderilirken hata oluştu: {e}")
        return False

def process_and_notify(lead_data: dict) -> dict:
    """Her yeni lead için hem Telegram hem de E-posta üzerinden bildirim yollar."""
    msg_text = build_message_text(lead_data)
    
    # Her ikisini de parallel (veya ardışık) çalıştır
    telegram_ok = send_telegram_notification(msg_text)
    email_ok = send_email_notification(msg_text)
    
    if not telegram_ok and not email_ok:
        logger.error("❌ Hiçbir bildirim gönderilemedi!")
    elif not telegram_ok:
        logger.warning("⚠️ Telegram gönderilemedi ama E-posta başarıyla gönderildi.")
    elif not email_ok:
        logger.warning("⚠️ Telegram gönderildi ama E-posta gönderilemedi.")
    else:
        logger.info("✅ Hem Telegram hem E-posta başarıyla gönderildi!")
        
    return {"telegram": telegram_ok, "email": email_ok}
