"""
Ceren_Marka_Takip — E-posta Bildirim Sistemi
===============================================
Tek bir digest mail gönderir: iki bölüm halinde.
- Yeni: bu run'da ilk kez hatırlatılan açık collab'lar
- Hala bekleyen: önceki digest'lerde de geçmiş, hala kapanmamış collab'lar
"""

import os
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

from services.gmail_service import get_gmail_service

logger = logging.getLogger(__name__)

# Gmail OAuth ile gönderim — Ceren hesabı üzerinden
FROM_EMAIL = "ceren@dolunay.ai"

# Alıcı (izleme modu: Dolunay)
REPORT_EMAIL = os.environ.get("ALERT_EMAIL", "ozerendolunay@gmail.com")


def _send_email(to: str, subject: str, body_html: str):
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


def _row_html(idx: int, item: Dict[str, Any]) -> str:
    """Tek satır HTML üretir. item = digest entry dict."""
    brand = item.get("brand") or "Bilinmeyen Marka"
    subj = item.get("subject") or "(Konu yok)"
    reason = item.get("reason") or "Cevap bekleniyor"
    days = item.get("business_days_open", "?")
    link = item.get("gmail_link") or "#"
    reminder_count = int(item.get("reminder_count") or 0)
    counter_label = (
        f"{reminder_count + 1}. kez hatırlatılıyor" if reminder_count > 0 else "İlk hatırlatma"
    )

    return f"""
    <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 10px 8px; vertical-align: top; color:#999;">{idx}</td>
        <td style="padding: 10px 8px; vertical-align: top;">
            <strong>{brand}</strong>
            <div style="color:#666; font-size:13px; margin-top:2px;">{subj[:80]}</div>
            <div style="color:#999; font-size:11px; margin-top:2px;">{counter_label}</div>
        </td>
        <td style="padding: 10px 8px; vertical-align: top; color:#444; font-size:13px;">{reason}</td>
        <td style="padding: 10px 8px; vertical-align: top; white-space:nowrap;">{days} iş günü</td>
        <td style="padding: 10px 8px; vertical-align: top;">
            <a href="{link}" style="color:#1a73e8; text-decoration:none;">Aç →</a>
        </td>
    </tr>
    """


def _section_html(title: str, color: str, items: List[Dict[str, Any]]) -> str:
    if not items:
        return ""
    rows = "".join(_row_html(i + 1, item) for i, item in enumerate(items))
    return f"""
    <h3 style="color: {color}; margin-top: 28px; margin-bottom: 8px;">{title} ({len(items)})</h3>
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
        <thead>
            <tr style="background: #f7f7f7; text-align:left;">
                <th style="padding: 8px;">#</th>
                <th style="padding: 8px;">Marka / Konu</th>
                <th style="padding: 8px;">Durum</th>
                <th style="padding: 8px;">Sessizlik</th>
                <th style="padding: 8px;">Link</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """


def send_digest(new_items: List[Dict[str, Any]], ongoing_items: List[Dict[str, Any]]):
    """
    İki bölümlü digest gönder.
    new_items: Reminder Count == 0 olanlar (ilk kez hatırlatılıyor).
    ongoing_items: Reminder Count > 0 olanlar (carry-forward — hala açık).
    """
    total = len(new_items) + len(ongoing_items)
    if total == 0:
        logger.info("Digest gönderilmiyor: ne yeni ne devam eden açık collab var.")
        return

    parts = []
    if new_items:
        parts.append(f"{len(new_items)} yeni")
    if ongoing_items:
        parts.append(f"{len(ongoing_items)} devam eden")
    subject = f"🔔 Marka Takip: {' + '.join(parts)} açık collab"

    new_section = _section_html("🆕 Yeni gelenler", "#1a73e8", new_items)
    ongoing_section = _section_html("⏳ Hala bekleyenler", "#d97706", ongoing_items)

    body_html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 760px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333; margin-bottom: 6px;">🔔 Marka İşbirliği Digest'i</h2>
        <p style="color: #666; font-size: 14px; margin-top: 0;">
            48+ iş saati cevapsız kalmış açık collab'lar. Bir thread "Ceren cevap yazdı" durumuna geçince
            otomatik olarak listeden çıkar; "false_positive / closed_won / closed_lost" olarak işaretlenirse
            de bir daha listeye girmez.
        </p>

        {new_section}
        {ongoing_section}

        <p style="color: #999; font-size: 12px; margin-top: 32px; border-top: 1px solid #eee; padding-top: 14px;">
            Yanlış sınıflandırma gördüğünde ilgili kaydı Notion'da
            <strong>Ceren — Marka Collab Thread Tracker</strong> DB'sinde
            <code>Status = false_positive</code> yap; bir daha gelmez.<br>
            Ceren Marka Takip — Antigravity
        </p>
    </div>
    """

    _send_email(REPORT_EMAIL, subject, body_html)
    logger.info(
        f"✅ Digest gönderildi: {len(new_items)} yeni + {len(ongoing_items)} devam eden → {REPORT_EMAIL}"
    )
