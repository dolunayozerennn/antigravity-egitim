"""
Chat Logger — Telegram üzerindeki kullanıcı-bot etkileşimlerini Notion'a kaydeder.
Performansı düşürmemek için asenkron (asyncio.to_thread) olarak çalışır.
"""
import os
import asyncio
import logging
import requests
from config import settings

log = logging.getLogger("ChatLogger")

NOTION_VERSION = "2022-06-28"

class ChatTracker:
    def __init__(self):
        # Bu tablo Social Token üzerine yaratıldı, bu sebeple öncelikli onu kontrol et.
        self.token = os.environ.get("NOTION_SOCIAL_TOKEN", settings.NOTION_TOKEN)
        self.db_id = os.environ.get("NOTION_CHAT_DB_ID")
        self.enabled = bool(self.token and self.db_id)

    async def log_interaction(self, session_id: str, user_msg: str, bot_reply: str, bot_name: str = "YouTube Bot"):
        """
        Kullanıcı ve bot arasındaki konuşmayı tek satir olarak Notion'a kaydeder.
        Bloklamaması için arka planda çalıştırılır.
        """
        if not self.enabled:
            return

        def _do_request():
            payload = {
                "parent": {"database_id": self.db_id},
                "properties": {
                    "Session ID": {"title": [{"text": {"content": str(session_id)[:100]}}]},
                    "Kullanıcı Mesajı": {"rich_text": [{"text": {"content": str(user_msg)[:2000]}}]},
                    "Bot Yanıtı": {"rich_text": [{"text": {"content": str(bot_reply)[:2000]}}]},
                    "Bot": {"select": {"name": bot_name}}
                }
            }
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Notion-Version": NOTION_VERSION
            }
            try:
                # 5 saniye timeout verelim, uzun sürerse telegram'ı meşgul etmesin.
                res = requests.post("https://api.notion.com/v1/pages", json=payload, headers=headers, timeout=5)
                res.raise_for_status()
            except Exception as e:
                log.error(f"ChatLogger (Notion) hatası: {e}")

        # İsteği ayrı bir thread'de asenkron başlat
        try:
            await asyncio.to_thread(_do_request)
        except Exception as e:
            log.error(f"ChatLogger thread başlatma hatası: {e}")

# Global instance
chat_tracker = ChatTracker()
