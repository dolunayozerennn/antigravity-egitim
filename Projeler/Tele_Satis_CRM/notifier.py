"""
Tele Satış CRM — Hata Bildirim Modülü
Hata durumunda SMTP ile e-posta gönderir.
Gmail App Password kullanır (OAuth gerektirmez).
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import Config

logger = logging.getLogger(__name__)


def send_error_notification(lead_info: dict, error_message: str):
    """
    Hata durumunda e-posta bildirimi gönderir.
    SMTP_USER ve SMTP_APP_PASSWORD tanımlı değilse sadece log yazar.
    
    Args:
        lead_info: Temizlenmiş lead verisi
        error_message: Hata mesajı
    """
    name = lead_info.get("clean_name", "Bilinmiyor")
    email = lead_info.get("clean_email", "-")
    phone = lead_info.get("clean_phone", "-")
    budget = lead_info.get("clean_budget", "-")

    log_msg = (
        f"⚠️ Lead Aktarım Hatası | {name}\n"
        f"  Email: {email}\n"
        f"  Telefon: {phone}\n"
        f"  Bütçe: {budget}\n"
        f"  Hata: {error_message}"
    )
    logger.error(log_msg)

    # SMTP ayarları yoksa sadece log ile yetinir
    if not Config.SMTP_USER or not Config.SMTP_APP_PASSWORD:
        logger.warning(
            "📧 SMTP ayarları tanımlı değil — hata bildirimi sadece log'a yazıldı"
        )
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = Config.SMTP_USER
        msg["To"] = Config.ERROR_NOTIFY_EMAIL
        msg["Subject"] = f"⚠️ Lead Aktarım Hatası | {name}"

        body = (
            f"Notion'a lead aktarılırken hata oluştu.\n\n"
            f"📋 Lead Bilgileri:\n"
            f"İsim: {name}\n"
            f"Email: {email}\n"
            f"Telefon: {phone}\n"
            f"Bütçe: {budget}\n\n"
            f"❌ Hata:\n{error_message}\n\n"
            f"Bu e-posta Tele Satış CRM otomasyonu tarafından gönderildi."
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(Config.SMTP_USER, Config.SMTP_APP_PASSWORD)
            server.sendmail(
                Config.SMTP_USER, Config.ERROR_NOTIFY_EMAIL, msg.as_string()
            )

        logger.info(f"📧 Hata bildirimi gönderildi → {Config.ERROR_NOTIFY_EMAIL}")

    except Exception as e:
        logger.error(f"📧 Hata bildirimi gönderilemedi: {e}")
