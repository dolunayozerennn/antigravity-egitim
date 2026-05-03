"""
Ceren_Marka_Takip — Notion Collab Thread Tracker
==================================================
Yeni state mimarisi: her Gmail thread için bir Notion satırı.
Status (open / responded_by_ceren / closed_won / closed_lost / false_positive)
ile lifecycle takibi yapılır. Carry-forward mantığının kaynağı budur.

DB ID: NOTION_DB_CEREN_COLLAB_THREADS env var'ından okunur.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _token() -> Optional[str]:
    return os.environ.get("NOTION_SOCIAL_TOKEN") or os.environ.get("NOTION_API_TOKEN")


def _db_id() -> Optional[str]:
    return os.environ.get("NOTION_DB_CEREN_COLLAB_THREADS")


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_token()}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _request(method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    if not _token():
        logger.error("Notion token yok — thread tracker devre dışı")
        return None

    url = f"{NOTION_API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in _headers().items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        logger.error(f"Notion {method} {path} {e.code}: {body[:300]}")
        return None
    except Exception as e:
        logger.error(f"Notion {method} {path} hata: {e}")
        return None


# ── Property dönüştürücüleri ──

def _title(value: str) -> Dict[str, Any]:
    return {"title": [{"text": {"content": value[:2000]}}]}


def _rich_text(value: Optional[str]) -> Dict[str, Any]:
    if not value:
        return {"rich_text": []}
    return {"rich_text": [{"text": {"content": str(value)[:2000]}}]}


def _select(value: Optional[str]) -> Dict[str, Any]:
    if not value:
        return {"select": None}
    return {"select": {"name": value}}


def _date(value: Optional[datetime]) -> Dict[str, Any]:
    if not value:
        return {"date": None}
    if isinstance(value, datetime):
        iso = value.isoformat()
    else:
        iso = str(value)
    return {"date": {"start": iso}}


def _number(value: Optional[float]) -> Dict[str, Any]:
    if value is None:
        return {"number": None}
    return {"number": float(value)}


def _url(value: Optional[str]) -> Dict[str, Any]:
    if not value:
        return {"url": None}
    return {"url": value}


# ── Page → dict parse ──

def _parse_page(page: Dict[str, Any]) -> Dict[str, Any]:
    """Notion page objesini düz dict'e çevir."""
    props = page.get("properties", {})

    def get_title(p):
        arr = p.get("title", []) if p else []
        return arr[0].get("text", {}).get("content", "") if arr else ""

    def get_rt(p):
        arr = p.get("rich_text", []) if p else []
        return arr[0].get("text", {}).get("content", "") if arr else ""

    def get_select(p):
        s = (p or {}).get("select")
        return s.get("name") if s else None

    def get_date(p):
        d = (p or {}).get("date")
        return d.get("start") if d else None

    def get_number(p):
        return (p or {}).get("number")

    def get_url(p):
        return (p or {}).get("url")

    return {
        "_page_id": page.get("id"),
        "thread_id": get_title(props.get("Thread ID")),
        "subject": get_rt(props.get("Subject")),
        "brand": get_rt(props.get("Brand")),
        "status": get_select(props.get("Status")),
        "category": get_select(props.get("Category")),
        "last_message_from": get_select(props.get("Last Message From")),
        "last_message_at": get_date(props.get("Last Message At")),
        "first_seen_at": get_date(props.get("First Seen At")),
        "last_reminded_at": get_date(props.get("Last Reminded At")),
        "last_llm_run_at": get_date(props.get("Last LLM Run At")),
        "reminder_count": get_number(props.get("Reminder Count")) or 0,
        "confidence": get_number(props.get("Confidence")),
        "gmail_link": get_url(props.get("Gmail Link")),
        "reason": get_rt(props.get("Reason")),
    }


# ── Public API ──

def find_by_thread_id(thread_id: str) -> Optional[Dict[str, Any]]:
    """Tek bir thread'i ID ile bul. None döner yoksa."""
    db_id = _db_id()
    if not db_id:
        return None
    payload = {
        "filter": {"property": "Thread ID", "title": {"equals": thread_id}},
        "page_size": 1,
    }
    res = _request("POST", f"/databases/{db_id}/query", payload)
    if not res:
        return None
    pages = res.get("results", [])
    return _parse_page(pages[0]) if pages else None


def query_all_open() -> List[Dict[str, Any]]:
    """Status == open olan tüm thread'ler."""
    db_id = _db_id()
    if not db_id:
        return []

    results: List[Dict[str, Any]] = []
    cursor = None
    while True:
        payload: Dict[str, Any] = {
            "filter": {"property": "Status", "select": {"equals": "open"}},
            "page_size": 100,
        }
        if cursor:
            payload["start_cursor"] = cursor
        res = _request("POST", f"/databases/{db_id}/query", payload)
        if not res:
            break
        for page in res.get("results", []):
            results.append(_parse_page(page))
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")
    logger.info(f"Notion: {len(results)} açık thread çekildi")
    return results


def upsert_thread(
    thread_id: str,
    *,
    subject: Optional[str] = None,
    brand: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    last_message_from: Optional[str] = None,
    last_message_at: Optional[datetime] = None,
    confidence: Optional[float] = None,
    gmail_link: Optional[str] = None,
    reason: Optional[str] = None,
    llm_just_ran: bool = False,
    is_new: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Thread satırını oluştur veya güncelle.

    is_new=True ise First Seen At = now atanır (sadece create'te).
    llm_just_ran=True ise Last LLM Run At = now atanır.
    None geçilen alanlar update'te dokunulmaz.
    """
    db_id = _db_id()
    if not db_id:
        return None

    now = datetime.utcnow()

    existing = find_by_thread_id(thread_id)

    props: Dict[str, Any] = {}
    if subject is not None:
        props["Subject"] = _rich_text(subject)
    if brand is not None:
        props["Brand"] = _rich_text(brand)
    if status is not None:
        props["Status"] = _select(status)
    if category is not None:
        props["Category"] = _select(category)
    if last_message_from is not None:
        props["Last Message From"] = _select(last_message_from)
    if last_message_at is not None:
        props["Last Message At"] = _date(last_message_at)
    if confidence is not None:
        props["Confidence"] = _number(confidence)
    if gmail_link is not None:
        props["Gmail Link"] = _url(gmail_link)
    if reason is not None:
        props["Reason"] = _rich_text(reason)
    if llm_just_ran:
        props["Last LLM Run At"] = _date(now)

    if existing:
        page_id = existing["_page_id"]
        res = _request("PATCH", f"/pages/{page_id}", {"properties": props})
        if res:
            logger.debug(f"Notion update: {thread_id} ({status or 'no-status-change'})")
        return _parse_page(res) if res else None

    # Yeni satır — zorunlu alanları doldur
    props["Thread ID"] = _title(thread_id)
    if "Status" not in props:
        props["Status"] = _select(status or "open")
    props["First Seen At"] = _date(now)
    props["Reminder Count"] = _number(0)

    res = _request(
        "POST",
        "/pages",
        {"parent": {"database_id": db_id}, "properties": props},
    )
    if res:
        logger.info(f"Notion create: {thread_id} (status={status or 'open'})")
    return _parse_page(res) if res else None


def mark_reminded(page_id: str, current_count: int) -> bool:
    """Last Reminded At = now, Reminder Count += 1."""
    now = datetime.utcnow()
    payload = {
        "properties": {
            "Last Reminded At": _date(now),
            "Reminder Count": _number(current_count + 1),
        }
    }
    res = _request("PATCH", f"/pages/{page_id}", payload)
    return res is not None


def update_status(page_id: str, new_status: str, reason: Optional[str] = None) -> bool:
    """Sadece status (ve opsiyonel reason) günceller."""
    props: Dict[str, Any] = {"Status": _select(new_status)}
    if reason is not None:
        props["Reason"] = _rich_text(reason)
    res = _request("PATCH", f"/pages/{page_id}", {"properties": props})
    return res is not None
