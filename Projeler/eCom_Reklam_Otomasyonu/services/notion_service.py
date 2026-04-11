from __future__ import annotations

"""
Notion Service — Üretim Logları
=================================
eCom Reklam Otomasyonu üretim loglarını Notion'a yazar.
Database: 33f95514-0a32-8146-9cad-dbe66f07b15e
"""

from datetime import datetime, timezone

from notion_client import Client as NotionClient

from logger import get_logger

log = get_logger("notion_service")


class NotionService:
    """Notion API ile üretim loglama."""

    def __init__(self, token: str, database_id: str):
        self.client = NotionClient(auth=token)
        self.database_id = database_id

    def log_production(
        self,
        brand: str,
        product: str,
        concept: str,
        video_duration: int,
        aspect_ratio: str,
        resolution: str,
        language: str,
        estimated_cost: float,
        status: str,
        video_url: str = "",
        error_message: str = "",
        user_name: str = "",
    ) -> str | None:
        """
        Üretim logunu Notion database'ine yazar.

        Args:
            brand: Marka adı
            product: Ürün adı
            concept: Reklam konsepti
            video_duration: Video süresi (saniye)
            aspect_ratio: En/boy oranı
            resolution: Çözünürlük
            language: Dil (Türkçe/İngilizce)
            estimated_cost: Tahmini maliyet ($)
            status: Durum (Üretiliyor, Tamamlandı, Hata)
            video_url: Video URL (tamamlandığında)
            error_message: Hata mesajı (başarısız olursa)
            user_name: Telegram kullanıcı adı

        Returns:
            str | None: Notion page URL veya None (hata durumunda)
        """
        try:
            properties = {
                "Proje": {"title": [{"text": {"content": f"eCom — {brand}"}}]},
                "Marka": {"rich_text": [{"text": {"content": brand}}]},
                "Ürün": {"rich_text": [{"text": {"content": product}}]},
                "Konsept": {"rich_text": [{"text": {"content": concept[:2000]}}]},
                "Video Süresi": {"number": video_duration},
                "Aspect Ratio": {"select": {"name": aspect_ratio}},
                "Çözünürlük": {"select": {"name": resolution}},
                "Dil": {"select": {"name": language}},
                "Tahmini Maliyet ($)": {"number": round(estimated_cost, 3)},
                "Durum": {"select": {"name": status}},
                "Tarih": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
            }

            # Opsiyonel alanlar
            if video_url:
                properties["Video URL"] = {"url": video_url}
            if error_message:
                properties["Hata Mesajı"] = {
                    "rich_text": [{"text": {"content": error_message[:2000]}}]
                }
            if user_name:
                properties["Kullanıcı"] = {
                    "rich_text": [{"text": {"content": user_name}}]
                }

            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
            )

            page_url = page.get("url", "")
            log.info(f"Notion log oluşturuldu: {brand} — {status} → {page_url}")
            return page_url

        except Exception:
            log.error(f"Notion loglama hatası: {brand}", exc_info=True)
            return None

    def update_production_status(
        self,
        page_id: str,
        status: str,
        video_url: str = "",
        error_message: str = "",
    ) -> bool:
        """
        Mevcut bir üretim logunun durumunu günceller.

        Args:
            page_id: Notion page ID
            status: Yeni durum
            video_url: Video URL (tamamlandığında)
            error_message: Hata mesajı (başarısız olursa)

        Returns:
            bool: Güncelleme başarılı mı
        """
        try:
            properties = {
                "Durum": {"select": {"name": status}},
            }

            if video_url:
                properties["Video URL"] = {"url": video_url}
            if error_message:
                properties["Hata Mesajı"] = {
                    "rich_text": [{"text": {"content": error_message[:2000]}}]
                }

            self.client.pages.update(
                page_id=page_id,
                properties=properties,
            )

            log.info(f"Notion log güncellendi: {page_id} → {status}")
            return True

        except Exception:
            log.error(f"Notion güncelleme hatası: {page_id}", exc_info=True)
            return False
