"""Notion X Posts logger — yeni DB için.

DB schema:
  Title (title), Source (select), Score (number), Status (select),
  Tweet Text (rich_text), Thread (rich_text), Source URL (url),
  Skip Reason (rich_text), Typefully Draft URL (url), Date (date)
"""

from datetime import datetime, timezone, timedelta

import requests

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "NotionLogger")

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionLogger:
    def __init__(self):
        self.token = settings.NOTION_TOKEN
        self.db_id = settings.NOTION_X_DB_ID
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def _enabled(self) -> bool:
        if not self.db_id:
            ops.warning("NOTION_X_DB_ID set değil, log atlanıyor")
            return False
        return True

    def is_already_processed(self, source_url: str) -> bool:
        """Aynı kaynak son N gün içinde işlendiyse True."""
        if not self._enabled() or not source_url:
            return False
        cutoff = (datetime.now(timezone.utc) - timedelta(days=settings.DEDUP_DAYS)).date().isoformat()
        payload = {
            "filter": {
                "and": [
                    {"property": "Source URL", "url": {"equals": source_url}},
                    {"property": "Date", "date": {"on_or_after": cutoff}},
                ]
            },
            "page_size": 1,
        }
        try:
            r = requests.post(f"{API}/databases/{self.db_id}/query",
                              headers=self.headers, json=payload, timeout=15)
            r.raise_for_status()
            return len(r.json().get("results", [])) > 0
        except Exception as e:
            ops.warning(f"Dedup query hatası: {e}")
            return False

    def is_already_processed_by_title(self, source: str, title: str) -> bool:
        """Aynı title aynı source'tan son 30 günde işlenmiş mi?"""
        if not self._enabled() or not title:
            return False
        cutoff = (datetime.now(timezone.utc) - timedelta(days=settings.DEDUP_DAYS)).date().isoformat()
        payload = {
            "filter": {"and": [
                {"property": "Source", "select": {"equals": source}},
                {"property": "Title", "title": {"equals": title}},
                {"property": "Date", "date": {"on_or_after": cutoff}},
            ]},
            "page_size": 1,
        }
        try:
            r = requests.post(f"{API}/databases/{self.db_id}/query",
                              headers=self.headers, json=payload, timeout=15)
            r.raise_for_status()
            return len(r.json().get("results", [])) > 0
        except Exception:
            return False

    def get_last_youtube_video_id(self) -> str:
        """En son işlenen YouTube videosunun ID'sini döner (Source URL'den parse)."""
        if not self._enabled():
            return ""
        payload = {
            "filter": {"property": "Source", "select": {"equals": "YouTube"}},
            "sorts": [{"property": "Date", "direction": "descending"}],
            "page_size": 1,
        }
        try:
            r = requests.post(f"{API}/databases/{self.db_id}/query",
                              headers=self.headers, json=payload, timeout=15)
            r.raise_for_status()
            results = r.json().get("results", [])
            if not results:
                return ""
            url_prop = results[0]["properties"].get("Source URL", {})
            url = url_prop.get("url", "") or ""
            # YouTube URL: https://www.youtube.com/watch?v=VIDEOID
            if "watch?v=" in url:
                return url.split("watch?v=")[-1].split("&")[0]
            return ""
        except Exception as e:
            ops.warning(f"Last YT video query hatası: {e}")
            return ""

    def log_skipped(self, source: str, source_url: str, score: int,
                    skip_reason: str, title: str = ""):
        """Eşik altı içeriği logla."""
        title = (title or skip_reason or f"{source} skipped")[:200]
        self._create_page({
            "Title": {"title": [{"text": {"content": title}}]},
            "Source": {"select": {"name": source}},
            "Score": {"number": score},
            "Status": {"select": {"name": "Atlandı"}},
            "Source URL": {"url": source_url or None},
            "Skip Reason": {"rich_text": [{"text": {"content": skip_reason[:1990]}}]},
            "Date": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        })

    def log_draft(self, source: str, source_url: str, score: int,
                  tweet_text: str = "", thread_tweets: list = None,
                  draft_url: str = "", title: str = "", image_url: str = ""):
        """Draft olarak Typefully'ye gönderilmiş içeriği logla."""
        title = (title or tweet_text[:60] or f"{source} draft")[:200]
        thread_str = "\n\n---\n\n".join(thread_tweets) if thread_tweets else ""
        props = {
            "Title": {"title": [{"text": {"content": title}}]},
            "Source": {"select": {"name": source}},
            "Score": {"number": score},
            "Status": {"select": {"name": "Draft"}},
            "Tweet Text": {"rich_text": [{"text": {"content": tweet_text[:1990]}}]},
            "Thread": {"rich_text": [{"text": {"content": thread_str[:1990]}}]},
            "Source URL": {"url": source_url or None},
            "Typefully Draft URL": {"url": draft_url or None},
            "Date": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        }
        if image_url:
            props["Image URL"] = {"url": image_url}
        self._create_page(props)

    def fetch_recent_titles_by_source(self, source: str, days: int = 30, limit: int = 30) -> list[str]:
        """Son N gün içinde source'tan üretilmiş Title'ları döner (use case dedup için)."""
        if not self._enabled():
            return []
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
        payload = {
            "filter": {"and": [
                {"property": "Source", "select": {"equals": source}},
                {"property": "Date", "date": {"on_or_after": cutoff}},
            ]},
            "sorts": [{"property": "Date", "direction": "descending"}],
            "page_size": limit,
        }
        try:
            r = requests.post(f"{API}/databases/{self.db_id}/query",
                              headers=self.headers, json=payload, timeout=15)
            r.raise_for_status()
            results = r.json().get("results", [])
            titles = []
            for row in results:
                title_arr = row["properties"].get("Title", {}).get("title", [])
                title = "".join(t.get("plain_text", "") for t in title_arr)
                if title:
                    titles.append(title)
            return titles
        except Exception as e:
            ops.warning(f"recent_titles query hatası: {e}")
            return []

    def log_failed(self, source: str, source_url: str, error: str, title: str = ""):
        title = (title or f"{source} failed")[:200]
        self._create_page({
            "Title": {"title": [{"text": {"content": title}}]},
            "Source": {"select": {"name": source}},
            "Status": {"select": {"name": "Failed"}},
            "Source URL": {"url": source_url or None},
            "Skip Reason": {"rich_text": [{"text": {"content": error[:1990]}}]},
            "Date": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        })

    def _create_page(self, properties: dict):
        if not self._enabled():
            return
        payload = {
            "parent": {"database_id": self.db_id},
            "properties": properties,
        }
        try:
            r = requests.post(f"{API}/pages", headers=self.headers,
                              json=payload, timeout=20)
            if r.status_code not in (200, 201):
                ops.error(f"Notion log başarısız ({r.status_code}): {r.text[:300]}")
            else:
                ops.info("Notion'a loglandı")
        except Exception as e:
            ops.error("Notion log exception", exception=e)
