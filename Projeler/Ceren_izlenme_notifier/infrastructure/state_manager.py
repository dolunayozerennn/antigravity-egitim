import os
import json
import logging
from datetime import datetime, timezone
from config import settings
import requests

logger = logging.getLogger(__name__)

# Fallback for local dev/dry run
LOCAL_STATE_FILE = "notified_state.json"

class NotifiedVideosManager:
    def __init__(self):
        self.use_local = settings.IS_DRY_RUN
        self.notion_token = os.environ.get("NOTION_SOCIAL_TOKEN") or os.environ.get("NOTION_API_TOKEN")
        self.db_id = os.environ.get("NOTION_DB_NOTIFIED_VIDEOS")
        self.local_cache = set()
        
        if self.use_local or not self.db_id:
            logger.info("Lokal state yönetimi kullanılıyor (DRY_RUN veya DB_ID eksik).")
            self._load_local_state()
        else:
            logger.info("Notion state yönetimi kullanılıyor.")
            self._load_notion_state()

    def _load_local_state(self):
        if os.path.exists(LOCAL_STATE_FILE):
            try:
                with open(LOCAL_STATE_FILE, "r") as f:
                    data = json.load(f)
                    self.local_cache = set(data.get("notified_urls", []))
            except Exception as e:
                logger.error(f"Lokal state okunamadı: {e}")

    def _save_local_state(self):
        try:
            with open(LOCAL_STATE_FILE, "w") as f:
                json.dump({"notified_urls": list(self.local_cache)}, f)
        except Exception as e:
            logger.error(f"Lokal state kaydedilemedi: {e}")

    def _load_notion_state(self):
        if not self.notion_token or not self.db_id:
            return
            
        headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        # We query the DB and fetch all Video URLs
        try:
            url = f"https://api.notion.com/v1/databases/{self.db_id}/query"
            has_more = True
            next_cursor = None
            
            while has_more:
                payload = {}
                if next_cursor:
                    payload["start_cursor"] = next_cursor
                    
                resp = requests.post(url, headers=headers, json=payload, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                for item in data.get("results", []):
                    props = item.get("properties", {})
                    # Assume there's a property named 'URL' of type 'url' or 'title'
                    url_prop = props.get("URL", {})
                    val = None
                    if url_prop.get("type") == "url":
                        val = url_prop.get("url")
                    elif url_prop.get("type") == "rich_text":
                        rt = url_prop.get("rich_text", [])
                        if rt: val = rt[0].get("plain_text")
                    elif url_prop.get("type") == "title":
                        rt = url_prop.get("title", [])
                        if rt: val = rt[0].get("plain_text")
                        
                    if val:
                        self.local_cache.add(val.strip())
                        
                has_more = data.get("has_more", False)
                next_cursor = data.get("next_cursor")
                
            logger.info(f"Notion'dan {len(self.local_cache)} bildirilmiş URL yüklendi.")
        except Exception as e:
            logger.error(f"Notion state yüklenemedi: {e}")

    def is_notified(self, url: str) -> bool:
        return url.strip() in self.local_cache

    def mark_as_notified(self, url: str, platform: str, views: int):
        url = url.strip()
        if not url: return
        
        self.local_cache.add(url)
        
        if self.use_local or not self.db_id:
            self._save_local_state()
        else:
            self._save_to_notion(url, platform, views)

    def _save_to_notion(self, url: str, platform: str, views: int):
        if not self.notion_token or not self.db_id:
            return
            
        headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        payload = {
            "parent": {"database_id": self.db_id},
            "properties": {
                "URL": {"title": [{"text": {"content": url}}]},
                "Platform": {"select": {"name": platform}},
                "Views": {"number": views},
                "Notified At": {"date": {"start": datetime.now(timezone.utc).isoformat()}}
            }
        }
        
        try:
            resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload, timeout=15)
            resp.raise_for_status()
            logger.debug(f"URL Notion'a eklendi: {url}")
        except Exception as e:
            logger.error(f"Notion'a URL kaydedilemedi ({url}): {e}")
