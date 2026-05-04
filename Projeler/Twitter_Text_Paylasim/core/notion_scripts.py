"""Notion 'Dolunay Reels & YouTube' DB okuyucu.

Status='Yayınlandı' + page icon=youtube_logo olan videoların page body'sini
script metni olarak çeker. YouTube transkriptinden çok daha temiz olduğu için
tweet üretiminin birincil kaynağı.

Port edildi: Projeler/Dolunay_Otonom_Kapak/core/notion_service.py
"""

import re

import requests

from env_loader import get_env
from ops_logger import get_ops_logger

ops = get_ops_logger("Twitter_Text_Paylasim", "NotionScripts")

YOUTUBE_ICON_NAME = "youtube_logo"
PUBLISHED_STATUS = "Yayınlandı"

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _get_token() -> str:
    return get_env("NOTION_SOCIAL_TOKEN") or get_env("NOTION_API_TOKEN") or get_env("NOTION_TOKEN")


def _get_db_id() -> str:
    return get_env("NOTION_DB_REELS_KAPAK")


def _is_youtube_page(item: dict) -> bool:
    icon = item.get("icon") or {}
    if icon.get("type") != "custom_emoji":
        return False
    return (icon.get("custom_emoji") or {}).get("name") == YOUTUBE_ICON_NAME


def _extract_video_id(props: dict, name: str) -> str:
    """Page property'lerinden veya title'dan YouTube video_id çıkarır.
    Bulamazsa boş string döner; çağıran fallback'a düşer.
    """
    candidates = []
    for key in ("URL", "userDefined:URL", "Drive"):
        prop = props.get(key) or {}
        url = prop.get("url")
        if url:
            candidates.append(url)
    if name:
        candidates.append(name)
    for s in candidates:
        m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})", s or "")
        if m:
            return m.group(1)
    return ""


def get_page_content(page_id: str, token: str | None = None) -> str:
    """Page body'sindeki paragraph/heading/bulleted_list_item rich_text'ini birleştirir."""
    token = token or _get_token()
    if not token:
        return ""
    url = f"{NOTION_API}/blocks/{page_id}/children?page_size=100"
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION}
    try:
        text_parts = []
        next_cursor = None
        while True:
            full_url = url + (f"&start_cursor={next_cursor}" if next_cursor else "")
            r = requests.get(full_url, headers=headers, timeout=30)
            if r.status_code != 200:
                ops.warning(f"Notion blocks fetch {r.status_code} ({page_id})")
                break
            data = r.json()
            for block in data.get("results", []):
                btype = block.get("type")
                content = block.get(btype) if btype else None
                if not content:
                    continue
                rt = content.get("rich_text") if isinstance(content, dict) else None
                if not rt:
                    continue
                text_parts.append("".join(t.get("plain_text", "") for t in rt))
            if not data.get("has_more"):
                break
            next_cursor = data.get("next_cursor")
        return "\n".join(p for p in text_parts if p).strip()
    except Exception as e:
        ops.error(f"Notion page content error ({page_id})", exception=e)
        return ""


def get_published_youtube_videos(limit: int = 20) -> list[dict]:
    """Status='Yayınlandı' + icon='youtube_logo' olan videoların listesi.

    Returns: [{page_id, title, page_url, video_id, video_url, script_text}, ...]
    En yeni ilk (Notion default created_time desc).
    """
    token = _get_token()
    db_id = _get_db_id()
    if not token or not db_id:
        ops.warning("NOTION_SOCIAL_TOKEN veya NOTION_DB_REELS_KAPAK eksik")
        return []

    url = f"{NOTION_API}/databases/{db_id}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }
    payload = {
        "filter": {"property": "Status", "select": {"equals": PUBLISHED_STATUS}},
        "sorts": [{"timestamp": "created_time", "direction": "descending"}],
        "page_size": max(limit * 3, 30),  # icon-filter sonrası limit'e ulaşabilmek için fazla çekelim
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code != 200:
            ops.error(f"Notion DB query {r.status_code}", message=r.text[:300])
            return []
        results = r.json().get("results", [])
    except Exception as e:
        ops.error("Notion DB query exception", exception=e)
        return []

    videos = []
    for item in results:
        if not _is_youtube_page(item):
            continue
        props = item.get("properties", {})
        title_prop = props.get("Name", {}).get("title", []) or []
        title = "".join(t.get("plain_text", "") for t in title_prop) or "(başlıksız)"
        page_id = item.get("id", "")
        page_url = item.get("url", "")
        video_id = _extract_video_id(props, title)
        if not video_id:
            # KRİTİK: page_url (internal Notion link) tweet'e bulaşmasın diye
            # video_id çıkaramadığımız sayfaları tamamen atlıyoruz.
            ops.warning(f"video_id çıkarılamadı, atlanıyor: {title[:80]}")
            continue
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        videos.append({
            "page_id": page_id,
            "title": title,
            "page_url": page_url,
            "video_id": video_id,
            "video_url": video_url,
            "script_text": "",  # lazy: çağıran fetch ediyor
        })
        if len(videos) >= limit:
            break

    # Script body'lerini doldur
    for v in videos:
        v["script_text"] = get_page_content(v["page_id"], token)

    return videos
