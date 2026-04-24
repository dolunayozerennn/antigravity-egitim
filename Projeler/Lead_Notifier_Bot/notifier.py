"""
Bildirim Modülü — v3 (Telegram + Gmail API)
Yeni lead düştüğünde Telegram ve Email ile bildirim gönderir.

Dedup, sheets_reader'daki ID tabanlı state ile sağlanır —
aynı lead için asla ikinci kez ne Telegram ne de email gitmez.
"""
import os
import sys
import json
import logging
import base64
import time
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)

_TELEGRAM_TIMEOUT = 15
_MAX_RETRIES = 2


# ── YARDIMCI FONKSİYONLAR ──────────────────────────────────

def _clean_phone(raw_phone: str) -> str:
    """Telefon numarasındaki 'p:' prefix'ini temizler."""
    phone = raw_phone.replace("p:", "").strip()
    if phone and not phone.startswith("+"):
        if len(phone) == 10:
            phone = "+90" + phone
    return phone or "-"


def _format_time(raw_time: str) -> str:
    """ISO 8601 tarihini Türkçe formata çevirir."""
    if not raw_time:
        return "-"
    try:
        dt = datetime.fromisoformat(raw_time)
        return dt.strftime("%d.%m.%Y %H:%M")
    except (ValueError, TypeError):
        return raw_time


# ── GMAIL API ────────────────────────────────────────────────

def _get_gmail_service():
    """Gmail API service objesi döndür.

    Öncelik:
      1. Railway (prod): GOOGLE_OUTREACH_TOKEN_JSON env variable
      2. Lokal (dev): Merkezi google_auth modülü
    """
    env_token = Config.GOOGLE_OUTREACH_TOKEN_JSON
    if env_token:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        token_data = json.loads(env_token)
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
                raise RuntimeError("Gmail token geçersiz ve yenilenemiyor")
        return build('gmail', 'v1', credentials=creds)

    # Lokal: Merkezi google_auth kullan
    _root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    sys.path.insert(0, os.path.join(
        _root, "_knowledge", "credentials", "oauth"
    ))
    from google_auth import get_gmail_service
    return get_gmail_service("outreach")


# ── MESAJ OLUŞTURMA ──────────────────────────────────────────

def build_telegram_message(lead: dict) -> str:
    """Lead verisini Telegram mesaj formatına çevirir."""
    full_name = lead.get("full_name", "-")
    company = lead.get("company_name", "-")
    email = lead.get("email", "-")
    phone = _clean_phone(lead.get("phone", ""))
    created = _format_time(lead.get("created_time", ""))
    platform = lead.get("platform", "").upper()
    campaign = lead.get("campaign_name", "")

    lines = [
        "🚀 *Yeni Lead Düştü!*",
        "",
        f"👤 *İsim:* {full_name}",
        f"🏢 *Şirket:* {company}",
        f"📧 *E-posta:* {email}",
        f"📞 *Telefon:* {phone}",
    ]

    if platform:
        lines.append(f"📱 *Platform:* {platform}")
    if campaign:
        lines.append(f"📢 *Kampanya:* {campaign}")

    lines.extend([
        f"⏰ *Tarih:* {created}",
        f"📋 *Kaynak:* {Config.SHEET_TAB}",
    ])

    return "\n".join(lines)


def build_html_email(lead: dict) -> str:
    """Lead bilgilerini HTML e-posta formatına çevirir."""
    full_name = lead.get("full_name", "-")
    company = lead.get("company_name", "-")
    email = lead.get("email", "-")
    phone = _clean_phone(lead.get("phone", ""))
    created = _format_time(lead.get("created_time", ""))
    platform = lead.get("platform", "").upper() or "-"
    campaign = lead.get("campaign_name", "") or "-"
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif; max-width:600px; margin:0 auto; padding:20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding:24px 30px; border-radius:12px 12px 0 0;">
            <h1 style="color:white; margin:0; font-size:22px;">🚀 Yeni Lead Düştü!</h1>
            <p style="color:rgba(255,255,255,0.85); margin:8px 0 0; font-size:14px;">Kaynak: {Config.SHEET_TAB}</p>
        </div>

        <div style="background:#fff; border:1px solid #e0e0e0; border-top:none; border-radius:0 0 12px 12px; overflow:hidden;">
            <table style="width:100%; border-collapse:collapse; font-size:14px;">
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding:12px 16px; font-weight:bold; color:#555; width:120px;">👤 İsim</td>
                    <td style="padding:12px 16px; color:#1a1a2e; font-weight:600;">{full_name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding:12px 16px; font-weight:bold; color:#555;">🏢 Şirket</td>
                    <td style="padding:12px 16px;">{company}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding:12px 16px; font-weight:bold; color:#555;">📧 E-posta</td>
                    <td style="padding:12px 16px;">{email}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding:12px 16px; font-weight:bold; color:#555;">📞 Telefon</td>
                    <td style="padding:12px 16px;">{phone}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding:12px 16px; font-weight:bold; color:#555;">📱 Platform</td>
                    <td style="padding:12px 16px;">{platform}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding:12px 16px; font-weight:bold; color:#555;">📢 Kampanya</td>
                    <td style="padding:12px 16px;">{campaign}</td>
                </tr>
                <tr>
                    <td style="padding:12px 16px; font-weight:bold; color:#555;">⏰ Tarih</td>
                    <td style="padding:12px 16px;">{created}</td>
                </tr>
            </table>
        </div>

        <p style="color:#999; font-size:11px; margin-top:16px; text-align:center;">
            Bu bildirim {now} tarihinde Lead Notifier Bot tarafından otomatik gönderilmiştir.
        </p>
    </div>
    """


def build_plain_email(lead: dict) -> str:
    """Lead verisini düz metin e-posta gövdesi olarak döner."""
    full_name = lead.get("full_name", "-")
    company = lead.get("company_name", "-")
    email = lead.get("email", "-")
    phone = _clean_phone(lead.get("phone", ""))
    created = _format_time(lead.get("created_time", ""))

    return (
        f"🚀 Yeni Lead Düştü!\n\n"
        f"👤 İsim: {full_name}\n"
        f"🏢 Şirket: {company}\n"
        f"📧 E-posta: {email}\n"
        f"📞 Telefon: {phone}\n"
        f"⏰ Tarih: {created}\n"
        f"📋 Kaynak: {Config.SHEET_TAB}\n"
    )


# ── TELEGRAM ─────────────────────────────────────────────────

def send_telegram(msg_text: str) -> bool:
    """Telegram API üzerinden mesaj gönderir."""
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram kapalı (Token veya Chat ID eksik)")
        return False

    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": Config.TELEGRAM_CHAT_ID,
        "text": msg_text,
        "parse_mode": "Markdown",
    }

    for attempt in range(_MAX_RETRIES):
        try:
            resp = requests.post(url, json=payload, timeout=_TELEGRAM_TIMEOUT)

            if resp.status_code == 429:
                retry_after = resp.json().get("parameters", {}).get("retry_after", 5)
                logger.warning(f"⚠️ Telegram rate limit, {retry_after}s bekleniyor...")
                time.sleep(retry_after)
                continue

            resp.raise_for_status()
            logger.info("✅ Telegram bildirimi gönderildi")
            return True
        except requests.exceptions.Timeout:
            logger.warning(
                f"⚠️ Telegram timeout (deneme {attempt + 1}/{_MAX_RETRIES})"
            )
        except Exception as e:
            logger.error(f"❌ Telegram hatası: {e}", exc_info=True)
            if attempt < _MAX_RETRIES - 1:
                time.sleep(2)

    return False


# ── E-POSTA (Gmail API) ─────────────────────────────────────

def send_email(lead: dict) -> bool:
    """Gmail API ile e-posta bildirimi gönderir."""
    if not Config.NOTIFY_EMAIL:
        logger.warning("⚠️ Email kapalı (NOTIFY_EMAIL eksik)")
        return False

    try:
        service = _get_gmail_service()
    except Exception as e:
        logger.error(f"❌ Gmail API bağlantısı kurulamadı: {e}", exc_info=True)
        return False

    plain_text = build_plain_email(lead)
    html_body = build_html_email(lead)

    message = MIMEMultipart("alternative")
    message["From"] = f"Lead Notifier <{Config.SENDER_EMAIL}>"
    message["To"] = Config.NOTIFY_EMAIL
    message["Subject"] = "🚀 Yeni Lead Bildirimi!"

    message.attach(MIMEText(plain_text, "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    for attempt in range(_MAX_RETRIES):
        try:
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            result = service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()
            logger.info(
                f"✅ Email gönderildi → {Config.NOTIFY_EMAIL} | "
                f"Message ID: {result.get('id', '?')}"
            )
            return True
        except Exception as e:
            logger.error(
                f"❌ Email gönderilemedi (deneme {attempt + 1}/{_MAX_RETRIES}): {e}",
                exc_info=True
            )
            if attempt < _MAX_RETRIES - 1:
                time.sleep(3)

    return False


# ── ANA ORCHESTRATOR ─────────────────────────────────────────

def process_and_notify(lead: dict) -> dict:
    """Her yeni lead için Telegram + Email bildirimi gönderir."""
    tg_msg = build_telegram_message(lead)

    telegram_ok = send_telegram(tg_msg)
    email_ok = send_email(lead)

    lead_name = lead.get("full_name", "?")

    if not telegram_ok and not email_ok:
        logger.error(f"❌ [{lead_name}] Hiçbir bildirim gönderilemedi!")
    elif not telegram_ok:
        logger.warning(f"⚠️ [{lead_name}] Telegram gitmedi, Email gitti")
    elif not email_ok:
        logger.warning(f"⚠️ [{lead_name}] Telegram gitti, Email gitmedi")
    else:
        logger.info(f"✅ [{lead_name}] Telegram + Email başarılı!")

    return {"telegram": telegram_ok, "email": email_ok}
