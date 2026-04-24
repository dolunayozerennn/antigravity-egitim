"""
Ceren_Marka_Takip — E-posta Bildirim Sistemi
===============================================
- Ceren'e hatırlatma e-postası
- Ceren'e hata alert e-postası
- Ceren'e haftalık özet rapor
"""

import os
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any

from services.gmail_service import get_gmail_service

logger = logging.getLogger(__name__)

# E-posta Config — Gmail OAuth ile gönderim (Ceren hesabı üzerinden)
FROM_EMAIL = "ceren@dolunay.ai"

# Alıcılar — tüm bildirimler Ceren'e gider
CEREN_EMAIL = "ceren@dolunay.ai"
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "ceren@dolunay.ai")


def _send_email(to: str, subject: str, body_html: str):
    """Gmail API (OAuth) ile e-posta gönder."""
    msg = MIMEMultipart("alternative")
    msg["From"] = FROM_EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
    body = {'raw': raw_message}

    try:
        service = get_gmail_service("ceren")
        service.users().messages().send(userId='me', body=body).execute()
        logger.info(f"📧 E-posta gönderildi: {to} — {subject}")
    except Exception as e:
        logger.error(f"E-posta gönderilemedi: {to} — {e}", exc_info=True)
        raise


def send_reminder_to_ceren(threads: List[Dict[str, Any]]):
    """Ceren'e stale thread hatırlatması gönder."""
    if not threads:
        logger.info("Bildirilecek thread yok, Ceren'e mail gönderilmiyor")
        return

    count = len(threads)
    subject = f"🔔 Hatırlatma: {count} marka thread'i cevap bekliyor"

    thread_rows = ""
    for i, t in enumerate(threads, 1):
        brand = t.get("brand_name", "Bilinmeyen Marka")
        subj = t.get("subject", "(Konu yok)")
        reason = t.get("reason", "Cevap bekleniyor")
        days = t.get("stale_business_days", "?")
        link = t.get("gmail_link", "#")
        urgency = t.get("urgency", "medium")
        
        urgency_badge = {
            "high": "🔴 Acil",
            "medium": "🟡 Normal", 
            "low": "🟢 Düşük"
        }.get(urgency, "🟡 Normal")

        thread_rows += f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 12px;">{i}</td>
            <td style="padding: 12px;"><strong>{brand}</strong><br><span style="color:#666;font-size:13px;">{subj[:60]}</span></td>
            <td style="padding: 12px;">{reason}</td>
            <td style="padding: 12px;">{days} iş günü</td>
            <td style="padding: 12px;">{urgency_badge}</td>
            <td style="padding: 12px;"><a href="{link}" style="color:#1a73e8;text-decoration:none;">Aç →</a></td>
        </tr>
        """

    body_html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">🔔 Marka İşbirliği Hatırlatması</h2>
        <p style="color: #555; font-size: 15px;">
            Merhaba Ceren,<br><br>
            Aşağıdaki <strong>{count}</strong> marka thread'inde 48 saatten fazladır cevap bekleniyor:
        </p>

        <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
            <thead>
                <tr style="background: #f5f5f5;">
                    <th style="padding: 10px; text-align: left;">#</th>
                    <th style="padding: 10px; text-align: left;">Marka / Konu</th>
                    <th style="padding: 10px; text-align: left;">Durum</th>
                    <th style="padding: 10px; text-align: left;">Sessizlik</th>
                    <th style="padding: 10px; text-align: left;">Öncelik</th>
                    <th style="padding: 10px; text-align: left;">Link</th>
                </tr>
            </thead>
            <tbody>
                {thread_rows}
            </tbody>
        </table>

        <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 15px;">
            Bu otomatik bir hatırlatmadır. Zaten yanıtladıysan bu mesajı görmezden gelebilirsin.<br>
            Ceren Marka Takip Sistemi — Antigravity
        </p>
    </div>
    """

    _send_email(CEREN_EMAIL, subject, body_html)
    logger.info(f"✅ Ceren'e {count} thread için hatırlatma gönderildi")


def send_error_alert(error_message: str):
    """
    Ceren'e hata bildirimi gönder.
    Sistem çalışamadığında anında tetiklenir.
    """
    subject = "⚡ Ceren_Marka_Takip — Sistem Hatası"
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    body_html = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 600px; padding: 20px;">
        <h2 style="color: #d32f2f;">⚡ Sistem Hatası</h2>
        <p><strong>Proje:</strong> Ceren_Marka_Takip</p>
        <p><strong>Zaman:</strong> {now}</p>
        <p><strong>Hata:</strong></p>
        <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 13px;">{error_message}</pre>
        <p style="color: #666; font-size: 13px;">Bu e-posta sistem çalışamadığında otomatik gönderilir.</p>
    </div>
    """

    try:
        _send_email(ALERT_EMAIL, subject, body_html)
    except Exception as e:
        logger.critical(f"ALERT E-POSTASI DA GÖNDERİLEMEDİ: {e}", exc_info=True)


def send_weekly_report(stats: Dict[str, Any]):
    """
    Ceren'e haftalık özet rapor gönder (her Pazartesi).
    
    Args:
        stats: Çalışma istatistikleri
    """
    subject = "📊 Ceren_Marka_Takip — Haftalık Rapor"
    now = datetime.utcnow().strftime("%Y-%m-%d")

    body_html = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 600px; padding: 20px;">
        <h2 style="color: #1a73e8;">📊 Haftalık Sistem Raporu</h2>
        <p><strong>Tarih:</strong> {now}</p>
        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 8px; color: #666;">Toplam çalışma</td>
                <td style="padding: 8px; font-weight: bold;">{stats.get('total_runs', 0)}</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 8px; color: #666;">Gönderilen hatırlatma</td>
                <td style="padding: 8px; font-weight: bold;">{stats.get('total_reminders', 0)}</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 8px; color: #666;">Aktif takip edilen thread</td>
                <td style="padding: 8px; font-weight: bold;">{stats.get('active_threads', 0)}</td>
            </tr>
            <tr>
                <td style="padding: 8px; color: #666;">Son çalışma</td>
                <td style="padding: 8px; font-weight: bold;">{stats.get('last_run', 'N/A')}</td>
            </tr>
        </table>
        <p style="color: #4caf50;">✅ Sistem sorunsuz çalışıyor.</p>
        <p style="color: #999; font-size: 12px;">Ceren Marka Takip Sistemi — Antigravity</p>
    </div>
    """

    _send_email(ALERT_EMAIL, subject, body_html)
    logger.info("📊 Haftalık rapor gönderildi")
