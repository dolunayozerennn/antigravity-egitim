"""
Tele Satış Notifier — E-posta Gönderim Modülü
GONDEREN_EMAIL_BURAYA'dan Ece'ye lead bilgilerini içeren mail atar.
Gmail API (OAuth2) kullanır.
"""
import os
import sys
import logging
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)


def _get_gmail_service():
    """Gmail API service objesi döndür (GONDEREN_EMAIL_BURAYA hesabı)."""
    # Railway (Production): env variable'dan token
    env_token = os.environ.get("GOOGLE_SECONDARY_TOKEN_JSON", "")
    if env_token:
        import json
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
            else:
                raise RuntimeError("Gmail token geçersiz ve yenilenemiyor (Railway)")
        return build('gmail', 'v1', credentials=creds)

    # Lokal: Merkezi google_auth kullan
    _antigravity_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    sys.path.insert(0, os.path.join(
        _antigravity_root, "_knowledge", "credentials", "oauth"
    ))
    from google_auth import get_gmail_service
    return get_gmail_service(Config.SENDER_ACCOUNT)


def _build_single_lead_html(lead: dict) -> str:
    """Tek bir lead için HTML kartı oluşturur."""
    name = lead.get("name", "İsimsiz")
    phone = lead.get("phone", "-")
    email = lead.get("email", "-")
    budget = lead.get("budget", "-")
    timing_raw = lead.get("timing", "-")
    source = lead.get("source_tab", "-")

    # Zamanlama tercihi görüntü adı
    timing_display = {
        "gun_icinde": "Gün içinde",
        "aksam_6": "Akşam 6'dan sonra",
        "haftasonu": "Haftasonu",
        "mesaj": "Aramayın, mesaj atın",
        "bilinmiyor": "Belirtilmemiş",
    }.get(timing_raw, timing_raw)

    return f"""
    <tr style="border-bottom: 1px solid #eee;">
        <td style="padding:10px 14px; font-weight:600; color:#1a1a2e;">{name}</td>
        <td style="padding:10px 14px;">{phone}</td>
        <td style="padding:10px 14px;">{email}</td>
        <td style="padding:10px 14px;">{budget if budget else '-'}</td>
        <td style="padding:10px 14px;">{timing_display}</td>
        <td style="padding:10px 14px; color:#888; font-size:12px;">{source}</td>
    </tr>"""


def build_email_html(leads: list[dict], batch_type: str = "anlik") -> str:
    """
    Lead listesini HTML email gövdesine çevirir.
    
    Args:
        leads: Lead bilgileri listesi
        batch_type: "anlik", "aksam_6", "haftasonu"
    """
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    title_map = {
        "anlik": "🚀 Yeni Lead — Hemen Aranabilir!",
        "aksam_6": f"📋 Akşam 6 Kuyruğu — {len(leads)} Lead Aranmayı Bekliyor",
        "haftasonu": f"📋 Haftasonu Kuyruğu — {len(leads)} Lead Aranmayı Bekliyor",
    }
    title = title_map.get(batch_type, f"📋 {len(leads)} Lead Bildirimi")

    subtitle_map = {
        "anlik": "Bu lead <strong>\"Gün içinde\"</strong> tercih etti — hemen aranabilir.",
        "aksam_6": "Aşağıdaki lead'ler <strong>\"Akşam 6'dan sonra\"</strong> tercih etti.",
        "haftasonu": "Aşağıdaki lead'ler <strong>\"Haftasonu\"</strong> tercih etti.",
    }
    subtitle = subtitle_map.get(batch_type, "")

    rows_html = ""
    for lead in leads:
        rows_html += _build_single_lead_html(lead)

    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif; max-width:800px; margin:0 auto; padding:20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding:24px 30px; border-radius:12px 12px 0 0;">
            <h1 style="color:white; margin:0; font-size:22px;">{title}</h1>
            <p style="color:rgba(255,255,255,0.85); margin:8px 0 0; font-size:14px;">{subtitle}</p>
        </div>
        
        <div style="background:#fff; border:1px solid #e0e0e0; border-top:none; border-radius:0 0 12px 12px; overflow:hidden;">
            <table style="width:100%; border-collapse:collapse; font-size:14px;">
                <thead>
                    <tr style="background:#f8f9fa; border-bottom:2px solid #dee2e6;">
                        <th style="padding:12px 14px; text-align:left; color:#495057;">İsim</th>
                        <th style="padding:12px 14px; text-align:left; color:#495057;">Telefon</th>
                        <th style="padding:12px 14px; text-align:left; color:#495057;">E-posta</th>
                        <th style="padding:12px 14px; text-align:left; color:#495057;">Bütçe</th>
                        <th style="padding:12px 14px; text-align:left; color:#495057;">Tercih</th>
                        <th style="padding:12px 14px; text-align:left; color:#495057;">Kaynak</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        
        <p style="color:#999; font-size:11px; margin-top:16px; text-align:center;">
            Bu bildirim {now} tarihinde Tele Satış Notifier tarafından otomatik gönderilmiştir.
            <br>Gönderen: {Config.SENDER_EMAIL}
        </p>
    </div>
    """


def build_email_subject(leads: list[dict], batch_type: str = "anlik") -> str:
    """E-posta konu satırını oluşturur."""
    if batch_type == "anlik":
        name = leads[0]["name"] if leads else "Yeni Lead"
        return f"🚀 Yeni Lead: {name} — Hemen Aranabilir"
    elif batch_type == "aksam_6":
        return f"📋 Akşam Arama Listesi — {len(leads)} Lead ({datetime.now().strftime('%d.%m.%Y')})"
    elif batch_type == "haftasonu":
        return f"📋 Haftasonu Arama Listesi — {len(leads)} Lead ({datetime.now().strftime('%d.%m.%Y')})"
    return f"📋 {len(leads)} Lead Bildirimi"


def send_leads_email(leads: list[dict], batch_type: str = "anlik") -> bool:
    """
    Lead listesini e-posta olarak gönderir.
    
    Args:
        leads: Lead bilgileri listesi
        batch_type: "anlik" | "aksam_6" | "haftasonu"
    
    Returns:
        True başarılıysa, False başarısızsa
    """
    if not leads:
        logger.info("📭 Gönderilecek lead yok, atlanıyor.")
        return True

    try:
        service = _get_gmail_service()
    except Exception as e:
        logger.error(f"❌ Gmail API bağlantısı kurulamadı: {e}")
        return False

    subject = build_email_subject(leads, batch_type)
    html_body = build_email_html(leads, batch_type)

    # MIME mesajı oluştur
    message = MIMEMultipart("alternative")
    message["From"] = f"KULLANICI_ADI_BURAYA AI <{Config.SENDER_EMAIL}>"
    message["To"] = Config.RECIPIENT_EMAIL
    message["Subject"] = subject

    # Plain text fallback
    plain_text = f"{subject}\n\n"
    for lead in leads:
        plain_text += f"• {lead['name']} | {lead['phone']} | {lead['email']}\n"

    message.attach(MIMEText(plain_text, "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        result = service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        logger.info(
            f"✅ E-posta gönderildi → {Config.RECIPIENT_EMAIL} | "
            f"Tip: {batch_type} | {len(leads)} lead | "
            f"Message ID: {result.get('id', '?')}"
        )
        return True
    except Exception as e:
        logger.error(f"❌ E-posta gönderilemedi: {e}")
        return False
