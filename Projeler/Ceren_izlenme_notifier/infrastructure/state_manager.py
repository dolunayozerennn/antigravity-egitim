import os
import json
import logging
from datetime import datetime, timezone

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = logging.getLogger(__name__)

LOCAL_STATE_FILE = "notified_state.json"
NOTION_API = "https://api.notion.com/v1"


class NotionStateError(Exception):
    """Notion state'e yazma/okuma başarısız."""


class NotifiedVideosManager:
    def __init__(self):
        self.notion_token = os.environ.get("NOTION_SOCIAL_TOKEN") or os.environ.get("NOTION_API_TOKEN")
        self.db_id = os.environ.get("NOTION_DB_NOTIFIED_VIDEOS")
        self.local_cache = set()
        self.url_property_name = "URL"
        self.url_property_type = "url"  # default; init'te schema'dan override

        # Notion state'e gerçek erişim varsa onu, yoksa lokal JSON'a düş
        self.use_local = settings.IS_DRY_RUN or not (self.notion_token and self.db_id)

        if self.use_local:
            reason = "DRY_RUN" if settings.IS_DRY_RUN else "NOTION env eksik"
            logger.info(f"State: lokal JSON kullanılıyor ({reason})")
            self._load_local_state()
        else:
            logger.info("State: Notion DB kullanılıyor")
            try:
                self._detect_schema()
                self._load_notion_state()
            except Exception as e:
                logger.error(f"Notion state init başarısız, lokal fallback'e geçiliyor: {e}")
                self.use_local = True
                self._load_local_state()

    # ── Local fallback ────────────────────────────────────────────────
    def _load_local_state(self):
        if os.path.exists(LOCAL_STATE_FILE):
            try:
                with open(LOCAL_STATE_FILE) as f:
                    self.local_cache = set(json.load(f).get("notified_urls", []))
            except Exception as e:
                logger.error(f"Lokal state okunamadı: {e}")

    def _save_local_state(self):
        try:
            with open(LOCAL_STATE_FILE, "w") as f:
                json.dump({"notified_urls": sorted(self.local_cache)}, f)
        except Exception as e:
            logger.error(f"Lokal state kaydedilemedi: {e}")

    # ── Notion ────────────────────────────────────────────────────────
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    def _detect_schema(self):
        """DB schema'sını çek; URL property tipini ('url' / 'title' / 'rich_text') tespit et."""
        r = requests.get(f"{NOTION_API}/databases/{self.db_id}", headers=self._headers(), timeout=15)
        r.raise_for_status()
        props = r.json().get("properties", {})

        # Önce 'URL' adlı property'yi ara, yoksa title olan property'yi al
        if "URL" in props:
            self.url_property_name = "URL"
            self.url_property_type = props["URL"].get("type", "url")
        else:
            for name, meta in props.items():
                if meta.get("type") == "title":
                    self.url_property_name = name
                    self.url_property_type = "title"
                    break
            else:
                raise NotionStateError("DB'de 'URL' veya title property'si bulunamadı")

        logger.info(
            f"Notion schema detected: prop={self.url_property_name!r} type={self.url_property_type}"
        )

    def _extract_url(self, props):
        prop = props.get(self.url_property_name, {})
        ptype = prop.get("type")
        if ptype == "url":
            return prop.get("url")
        if ptype in ("rich_text", "title"):
            arr = prop.get(ptype, [])
            if arr:
                return arr[0].get("plain_text")
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    def _query_page(self, payload):
        r = requests.post(
            f"{NOTION_API}/databases/{self.db_id}/query",
            headers=self._headers(), json=payload, timeout=20,
        )
        r.raise_for_status()
        return r.json()

    def _load_notion_state(self):
        next_cursor = None
        while True:
            payload = {"page_size": 100}
            if next_cursor:
                payload["start_cursor"] = next_cursor
            data = self._query_page(payload)
            for item in data.get("results", []):
                val = self._extract_url(item.get("properties", {}))
                if val:
                    self.local_cache.add(val.strip())
            if not data.get("has_more"):
                break
            next_cursor = data.get("next_cursor")
        logger.info(f"Notion'dan {len(self.local_cache)} bildirilmiş URL yüklendi")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    def _save_to_notion(self, url, platform, views):
        url_value = (
            {"url": url} if self.url_property_type == "url"
            else {self.url_property_type: [{"text": {"content": url}}]}
        )
        properties = {
            self.url_property_name: url_value,
            "Platform": {"select": {"name": platform}},
            "Views": {"number": views},
            "Notified At": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        }
        # Eğer URL property "url" tipindeyse title da ayrıca dolmak ister; title prop'u ayrıca yoksa skip
        if self.url_property_type == "url":
            # Bazı şablonlar 'Name' veya 'Title' başlığı zorunlu kılar; sessizce dene
            properties.setdefault("Name", {"title": [{"text": {"content": url}}]})

        r = requests.post(
            f"{NOTION_API}/pages",
            headers=self._headers(),
            json={"parent": {"database_id": self.db_id}, "properties": properties},
            timeout=15,
        )
        if r.status_code >= 400:
            raise NotionStateError(f"Notion {r.status_code}: {r.text[:400]}")

    # ── Public API ────────────────────────────────────────────────────
    def is_notified(self, url):
        if not url:
            return False
        return url.strip() in self.local_cache

    def mark_as_notified(self, url, platform, views):
        """Başarılı: cache + Notion. Notion fail: cache'den de geri al ve raise."""
        url = (url or "").strip()
        if not url:
            return

        self.local_cache.add(url)

        if self.use_local:
            self._save_local_state()
            return

        try:
            self._save_to_notion(url, platform, views)
        except Exception as e:
            self.local_cache.discard(url)  # Notion'da yoksa cache'de de tutma — duplicate önle
            raise NotionStateError(f"URL Notion'a yazılamadı ({url}): {e}") from e
