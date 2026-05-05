"""Sabah Draft Özet Maili.

Cron sonu adımı: Notion X Posts DB'sinden bugün üretilmiş Draft satırlarını çeker.
Varsa HTML mail at — yoksa hiçbir şey yapma. Mail saati ana cron'un bitiş saatidir
(TR ~10:30, ana cron 07:30 UTC).

Sender: ozerendolunay@gmail.com (outreach hesabı)
Receiver: ozerendolunay@gmail.com (kendine)
"""

import os
import sys
import json
import hmac
import base64
import hashlib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests

from ops_logger import get_ops_logger
from config import settings


APPROVAL_BASE_URL = os.environ.get("APPROVAL_BASE_URL", "").rstrip("/")
APPROVAL_SECRET = os.environ.get("APPROVAL_SECRET", "")


def _make_approval_url(draft_id: str, row_id: str, title: str) -> str:
    if not (APPROVAL_BASE_URL and APPROVAL_SECRET and draft_id and row_id):
        return ""
    payload = {"d": str(draft_id), "r": row_id, "title": title[:80]}
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload, ensure_ascii=False).encode()
    ).decode().rstrip("=")
    sig = hmac.new(
        APPROVAL_SECRET.encode(), payload_b64.encode(), hashlib.sha256
    ).hexdigest()
    return f"{APPROVAL_BASE_URL}/approve?t={payload_b64}.{sig}"

ops = get_ops_logger("Twitter_Text_Paylasim", "MailSender")

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
RECIPIENT = "ozerendolunay@gmail.com"

SOURCE_EMOJI = {
    "GitHub": "🐙",
    "YouTube": "📺",
    "Perplexity": "📰",
    "AI Use Case": "💼",
}


def _gmail_service():
    """Merkezi google_auth ile Gmail service döner."""
    antigravity_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    sys.path.insert(0, os.path.join(
        antigravity_root, "_knowledge", "credentials", "oauth"
    ))
    from google_auth import get_gmail_service
    return get_gmail_service("outreach")


def _fetch_today_drafts() -> list[dict]:
    """Bugün (UTC) Status=Draft olan tüm satırları çek."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    payload = {
        "filter": {
            "and": [
                {"property": "Status", "select": {"equals": "Draft"}},
                {"property": "Date", "date": {"on_or_after": today_start[:10]}},
            ]
        },
        "sorts": [{"property": "Score", "direction": "descending"}],
        "page_size": 50,
    }
    headers = {
        "Authorization": f"Bearer {settings.NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(f"{NOTION_API}/databases/{settings.NOTION_X_DB_ID}/query",
                          headers=headers, json=payload, timeout=20)
        r.raise_for_status()
        results = r.json().get("results", [])
    except Exception as e:
        ops.error("Notion sorgu hatası", exception=e)
        return []

    drafts = []
    for row in results:
        props = row.get("properties", {})
        title = "".join(t.get("plain_text", "") for t in props.get("Title", {}).get("title", []))
        score = props.get("Score", {}).get("number") or 0
        source = (props.get("Source", {}).get("select") or {}).get("name") or "?"
        draft_url = props.get("Typefully Draft URL", {}).get("url") or ""
        tweet_text = "".join(t.get("plain_text", "") for t in props.get("Tweet Text", {}).get("rich_text", []))
        draft_id = "".join(t.get("plain_text", "") for t in props.get("Typefully Draft ID", {}).get("rich_text", []))
        drafts.append({
            "title": title, "score": score, "source": source,
            "draft_url": draft_url, "tweet_text": tweet_text,
            "draft_id": draft_id, "row_id": row.get("id", ""),
        })
    return drafts


def _build_html(drafts: list[dict]) -> str:
    rows = []
    for d in drafts:
        emoji = SOURCE_EMOJI.get(d["source"], "📝")
        link = d["draft_url"] or "https://typefully.com/"
        preview = (d["tweet_text"][:160] + "…") if len(d["tweet_text"]) > 160 else d["tweet_text"]
        approve_url = _make_approval_url(d.get("draft_id", ""), d.get("row_id", ""), d["title"])
        approve_btn = ""
        if approve_url:
            approve_btn = f"""<a href="{approve_url}" style="display:inline-block;background:#16a34a;color:#fff;text-decoration:none;padding:8px 16px;border-radius:8px;font-size:14px;font-weight:600;margin-left:8px;">✓ Onayla ve yayına al</a>"""
        rows.append(f"""
<tr>
  <td style="padding:14px 0;border-bottom:1px solid #eee;">
    <div style="font-size:14px;color:#666;">{emoji} {d['source']} · Skor {d['score']}/10</div>
    <div style="font-size:16px;font-weight:600;margin:6px 0;color:#111;">{d['title']}</div>
    <div style="font-size:14px;color:#444;line-height:1.5;margin-bottom:10px;">{preview}</div>
    <a href="{link}" style="display:inline-block;background:#1da1f2;color:#fff;text-decoration:none;padding:8px 16px;border-radius:8px;font-size:14px;font-weight:600;">Typefully'de Aç →</a>
    {approve_btn}
  </td>
</tr>""")

    today = datetime.now().strftime("%d %B %Y")
    return f"""<!DOCTYPE html>
<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f6f8fa;margin:0;padding:24px;">
  <table style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
    <tr><td>
      <div style="font-size:13px;color:#888;text-transform:uppercase;letter-spacing:1px;">{today}</div>
      <h1 style="font-size:22px;color:#111;margin:6px 0 4px;">Bugünün X Draft'ları</h1>
      <p style="font-size:14px;color:#666;margin:0 0 16px;">{len(drafts)} draft hazır. İncele, beğendiğini at.</p>
    </td></tr>
    {''.join(rows)}
    <tr><td style="padding-top:16px;font-size:12px;color:#999;">
      twitter-text-cron · Antigravity
    </td></tr>
  </table>
</body></html>"""


def send_summary_mail(drafts: list[dict] | None = None) -> bool:
    """Bugünün Draft satırlarını mail olarak at. Boş günde mail atmaz."""
    if drafts is None:
        drafts = _fetch_today_drafts()
    if not drafts:
        ops.info("Bugün draft yok, mail atılmıyor")
        return False

    if settings.IS_DRY_RUN:
        ops.info(f"[DRY-RUN] Mail atılacaktı: {len(drafts)} draft")
        return False

    try:
        service = _gmail_service()
    except Exception as e:
        ops.error("Gmail auth hatası", exception=e)
        return False

    subject = "X Postunuz hazır"
    html = _build_html(drafts)

    message = MIMEMultipart("alternative")
    message["to"] = RECIPIENT
    message["subject"] = subject
    message["from"] = "ozerendolunay@gmail.com"
    text_fallback = "\n\n".join(f"{d['source']} (skor {d['score']}/10): {d['title']}\n{d['draft_url']}" for d in drafts)
    message.attach(MIMEText(text_fallback, "plain", "utf-8"))
    message.attach(MIMEText(html, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        ops.success(f"Mail atıldı (id={result.get('id','?')})")
        return True
    except Exception as e:
        ops.error("Gmail send hatası", exception=e)
        return False
