"""
Notion Logger — Her pipeline çalışmasını Notion veritabanına kaydeder.
Adım adım durum güncellemesi destekler.

NOT: Notion DB erişimi hazır olmadığında sessizce log'a yazar, pipeline'ı durdurmaz.
"""
import requests
from datetime import datetime, timezone
from config import settings
from logger import get_logger

log = get_logger("NotionLogger")

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Durum değerleri
STATUS_TOPIC_SELECTED = "Konu Seçildi"
STATUS_PROMPT_GENERATED = "Prompt Üretildi"
STATUS_VIDEO_GENERATING = "Video Üretiliyor"
STATUS_VIDEO_READY = "Video Hazır"
STATUS_UPLOADED = "YouTube'a Yüklendi"
STATUS_ERROR = "Hata"


class NotionPageTracker:
    """Bir pipeline çalışması boyunca Notion sayfasını takip eder."""

    def __init__(self):
        self.page_id = None
        self.enabled = settings.NOTION_ENABLED

    def create_entry(self, topic: dict) -> str:
        """
        Yeni bir Notion entry oluşturur (pipeline başlangıcı).
        
        Args:
            topic: Seçilen konu
            
        Returns:
            str: Oluşturulan page ID
        """
        if not self.enabled:
            log.info("📝 Notion devre dışı — giriş oluşturulmadı (NOTION_DB_YOUTUBE_OTOMASYON ayarlanmamış)")
            return ""

        if settings.IS_DRY_RUN:
            log.info(f"🧪 DRY-RUN: Notion entry oluşturulacaktı — konu: {topic.get('title_hint', 'N/A')}")
            self.page_id = "dry-run-page-id"
            return self.page_id

        properties = {
            "Video Adı": {
                "title": [{"text": {"content": topic.get("title_hint", "Otomasyon Video")}}]
            },
            "Durum": {
                "select": {"name": STATUS_TOPIC_SELECTED}
            }
        }

        payload = {
            "parent": {"database_id": settings.NOTION_DB_ID},
            "properties": properties
        }

        try:
            response = _notion_request("POST", f"{NOTION_API_URL}/pages", json=payload)
            self.page_id = response.get("id", "")
            log.info(f"📋 Notion entry oluşturuldu: {self.page_id}")
            return self.page_id
        except Exception as e:
            log.warning(f"⚠️ Notion entry oluşturulamadı: {e}")
            return ""

    def update_status(self, status: str, extra_props: dict = None):
        """
        Mevcut entry'nin durumunu günceller.
        
        Args:
            status: Yeni durum değeri
            extra_props: Ek property güncellemeleri
        """
        if not self.enabled or not self.page_id:
            log.info(f"📝 Durum: {status}")
            return

        if settings.IS_DRY_RUN:
            log.info(f"🧪 DRY-RUN Notion güncelleme: {status}")
            return

        properties = {
            "Durum": {"select": {"name": status}}
        }

        if extra_props:
            properties.update(extra_props)

        payload = {"properties": properties}

        try:
            _notion_request("PATCH", f"{NOTION_API_URL}/pages/{self.page_id}", json=payload)
            log.info(f"📋 Notion durum güncellendi: {status}")
        except Exception as e:
            log.warning(f"⚠️ Notion güncelleme hatası: {e}")

    def update_with_content(self, content: dict):
        """Prompt üretildikten sonra içerik bilgilerini günceller."""
        extra = {}

        # Başlık güncelle
        title = content.get("title", "")
        if title:
            extra["Video Adı"] = {"title": [{"text": {"content": title[:100]}}]}

        self.update_status(STATUS_PROMPT_GENERATED, extra)

    def update_with_video(self, video_url: str):
        """Video URL'sini ekler."""
        extra = {}
        if video_url:
            extra["URL"] = {"url": video_url}

        self.update_status(STATUS_VIDEO_READY, extra)

    def update_with_youtube(self, youtube_url: str):
        """YouTube URL'sini ekler ve durumu tamamlandı olarak işaretler."""
        extra = {}
        if youtube_url:
            extra["URL"] = {"url": youtube_url}

        self.update_status(STATUS_UPLOADED, extra)

    def update_with_error(self, error_msg: str):
        """Hata durumunu kaydeder."""
        self.update_status(STATUS_ERROR)


def _notion_request(method: str, url: str, **kwargs) -> dict:
    """Notion API'ye istek gönderir."""
    headers = {
        "Authorization": f"Bearer {settings.NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    response = requests.request(method, url, headers=headers, timeout=15, **kwargs)

    if response.status_code not in (200, 201):
        raise RuntimeError(f"Notion API hatası: {response.status_code} — {response.text[:200]}")

    return response.json()
