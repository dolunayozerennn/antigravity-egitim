from __future__ import annotations

"""
Notion Logger V2 — Her video üretimini Notion veritabanına kaydeder.
Adım adım durum güncellemesi, model/maliyet/süre takibi.
Inline database property'leriyle uyumlu.

NOT: Notion DB erişimi hazır olmadığında sessizce log'a yazar, pipeline'ı durdurmaz.
"""
import time
import logging
import requests
from datetime import datetime, timezone
from config import settings

log = logging.getLogger("NotionLogger")

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Durum değerleri (Notion Select)
STATUS_STARTED = "Başlatıldı"
STATUS_PROMPT_DONE = "Prompt Hazır"
STATUS_VIDEO_GENERATING = "Video Üretiliyor"
STATUS_VIDEO_READY = "Video Hazır"
STATUS_MERGING = "Birleştiriliyor"
STATUS_UPLOADING = "Yükleniyor"
STATUS_COMPLETED = "✅ Tamamlandı"
STATUS_ERROR = "❌ Hata"


class NotionTracker:
    """Bir video üretim pipeline'ı boyunca Notion entry'sini yönetir."""

    def __init__(self):
        self.page_id = None
        self.enabled = settings.NOTION_ENABLED
        self._start_time = time.time()

    def create_entry(self, config: dict, trigger: str = "telegram") -> str:
        """
        Yeni Notion entry oluşturur (pipeline başlangıcı).

        Args:
            config: Üretim config'i (topic, model, clip_count, vb.)
            trigger: "telegram" veya "manual"
        """
        if not self.enabled:
            log.info("📝 Notion devre dışı — giriş oluşturulmadı")
            return ""

        if settings.IS_DRY_RUN:
            log.info(f"🧪 DRY-RUN: Notion entry — konu: {config.get('topic', 'N/A')}")
            self.page_id = "dry-run-page-id"
            return self.page_id

        model_name = config.get("model", settings.DEFAULT_MODEL)

        properties = {
            "Video Adı": {"title": [{"text": {"content": config.get("topic", "YouTube Video")[:100]}}]},
            "Durum": {"select": {"name": STATUS_STARTED}},
            "Model": {"select": {"name": model_name}},
            "Tetikleyici": {"select": {"name": trigger}},
            "Konu": {"rich_text": [{"text": {"content": config.get("topic", "")[:2000]}}]},
            "Klip Sayısı": {"number": config.get("clip_count", 1)},
            "Tarih": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        }

        # V3: Combo key — tekrar önleme sistemi
        combo_key = config.get("combo_key", "")
        if combo_key:
            properties["Combo Key"] = {"rich_text": [{"text": {"content": combo_key}}]}

        payload = {
            "parent": {"database_id": settings.NOTION_DB_ID},
            "properties": properties,
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
        """Mevcut entry'nin durumunu günceller."""
        if not self.enabled or not self.page_id:
            log.info(f"📝 Durum: {status}")
            return

        if settings.IS_DRY_RUN:
            log.info(f"🧪 DRY-RUN Notion güncelleme: {status}")
            return

        properties = {"Durum": {"select": {"name": status}}}
        if extra_props:
            properties.update(extra_props)

        try:
            _notion_request("PATCH", f"{NOTION_API_URL}/pages/{self.page_id}", json={"properties": properties})
            log.info(f"📋 Notion durum güncellendi: {status}")
        except Exception as e:
            log.warning(f"⚠️ Notion güncelleme hatası: {e}")

    def update_with_prompts(self, prompt_data: dict):
        """Prompt üretildikten sonra günceller."""
        extra = {}
        title = prompt_data.get("youtube_title", "")
        if title:
            extra["Video Adı"] = {"title": [{"text": {"content": title[:100]}}]}

        # İlk sahne promptunu kaydet
        scenes = prompt_data.get("scenes", [])
        if scenes:
            first_prompt = scenes[0].get("prompt", "")[:2000]
            extra["Prompt"] = {"rich_text": [{"text": {"content": first_prompt}}]}

        self.update_status(STATUS_PROMPT_DONE, extra)

    def update_with_video(self, video_url: str):
        """Video URL'sini ekler."""
        extra = {}
        if video_url and video_url.startswith("http"):
            extra["Video URL"] = {"url": video_url}
        self.update_status(STATUS_VIDEO_READY, extra)

    def update_with_youtube(self, youtube_url: str):
        """YouTube URL'sini ekler ve tamamlandı olarak işaretler."""
        elapsed = time.time() - self._start_time
        extra = {"Süre (sn)": {"number": round(elapsed, 1)}}
        if youtube_url and youtube_url.startswith("http"):
            extra["YouTube URL"] = {"url": youtube_url}
        self.update_status(STATUS_COMPLETED, extra)

    def update_with_error(self, error_msg: str):
        """Hata durumunu kaydeder."""
        elapsed = time.time() - self._start_time
        extra = {
            "Hata": {"rich_text": [{"text": {"content": str(error_msg)[:2000]}}]},
            "Süre (sn)": {"number": round(elapsed, 1)},
        }
        self.update_status(STATUS_ERROR, extra)

    def get_used_combos(self, days: int = 60) -> list[str]:
        """
        Son N günde kullanılmış combo_key'leri Notion'dan çeker.
        Tekrar önleme sistemi için kullanılır.

        Args:
            days: Kaç gün geriye bakılacak

        Returns:
            list[str]: ["animal|talent", ...] formatında combo_key listesi
        """
        if not self.enabled or settings.IS_DRY_RUN:
            return []

        from datetime import timedelta

        try:
            since = datetime.now(timezone.utc) - timedelta(days=days)
            since_iso = since.isoformat()

            payload = {
                "filter": {
                    "and": [
                        {
                            "property": "Tarih",
                            "date": {"on_or_after": since_iso}
                        },
                        {
                            "property": "Durum",
                            "select": {"equals": STATUS_COMPLETED}
                        }
                    ]
                },
                "sorts": [{"property": "Tarih", "direction": "descending"}],
                "page_size": 100,
            }

            response = _notion_request(
                "POST",
                f"{NOTION_API_URL}/databases/{settings.NOTION_DB_ID}/query",
                json=payload,
            )

            combos = []
            for page in response.get("results", []):
                props = page.get("properties", {})
                combo_rt = props.get("Combo Key", {}).get("rich_text", [])
                if combo_rt:
                    combo_text = combo_rt[0].get("text", {}).get("content", "")
                    if combo_text:
                        combos.append(combo_text)

            log.info(f"📋 Notion'dan {len(combos)} kullanılmış combo yüklendi")
            return combos

        except Exception as e:
            log.warning(f"⚠️ Notion combo sorgusu başarısız (devam ediliyor): {e}")
            return []

    def update_with_safety_info(self, safety_data: dict):
        """
        İçerik güvenliği telemetrisi — pre-flight, retry ve fallback bilgilerini kaydeder.

        Args:
            safety_data: {
                "preflight_risk_score": 1-10,
                "preflight_rewritten": True/False,
                "content_retries": 0-3,
                "model_fallback_used": True/False,
                "rejection_reasons": ["reason1", ...],
                "original_prompt": "...",
                "final_prompt": "...",
            }
        """
        if not self.enabled or not self.page_id:
            return

        if settings.IS_DRY_RUN:
            log.info(f"🧪 DRY-RUN Notion güvenlik telemetrisi: {safety_data}")
            return

        # Güvenlik bilgilerini tek bir metin alanında birleştir
        parts = []
        risk_score = safety_data.get("preflight_risk_score", 0)
        if risk_score > 0:
            parts.append(f"Pre-flight Risk: {risk_score}/10")
        if safety_data.get("preflight_rewritten"):
            parts.append("Pre-flight: GPT Rewrite uygulandı")
        retries = safety_data.get("content_retries", 0)
        if retries > 0:
            parts.append(f"Content Filter Retry: {retries}x")
        if safety_data.get("model_fallback_used"):
            parts.append("Model Fallback kullanıldı")
        reasons = safety_data.get("rejection_reasons", [])
        if reasons:
            parts.append(f"Ret sebepleri: {', '.join(reasons[:3])}")

        if not parts:
            return  # Güvenlik olayı yok — güncelleme gerek yok

        safety_text = " | ".join(parts)

        extra = {
            "Güvenlik": {"rich_text": [{"text": {"content": safety_text[:2000]}}]},
        }

        try:
            _notion_request("PATCH", f"{NOTION_API_URL}/pages/{self.page_id}", json={"properties": extra})
            log.info(f"📋 Notion güvenlik telemetrisi kaydedildi: {safety_text[:80]}")
        except Exception as e:
            log.warning(f"⚠️ Notion güvenlik telemetrisi hatası: {e}")


def _notion_request(method: str, url: str, **kwargs) -> dict:
    """Notion API'ye istek gönderir — geçici ağ hataları için retry mekanizmalı."""
    headers = {
        "Authorization": f"Bearer {settings.NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    _TRANSIENT_KEYWORDS = ("eof", "ssl", "broken pipe", "connection reset", "timeout", "connection aborted")
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.request(method, url, headers=headers, timeout=15, **kwargs)
        except requests.RequestException as e:
            err_lower = str(e).lower()
            if attempt < max_retries and any(kw in err_lower for kw in _TRANSIENT_KEYWORDS):
                wait = 2 ** attempt
                log.warning(f"⚠️ Notion geçici ağ hatası (deneme {attempt}/{max_retries}): {e} — {wait}s bekliyor...")
                time.sleep(wait)
                continue
            raise RuntimeError(f"Notion API bağlantı hatası: {e}")

        if response.status_code not in (200, 201):
            raise RuntimeError(f"Notion API hatası: {response.status_code} — {response.text[:200]}")

        return response.json()

    raise RuntimeError(f"Notion API {max_retries} denemede de başarısız")
