import asyncio
import re
import requests
from config import settings
from logger import get_logger

log = get_logger("chat_logger")


# ── PII Maskeleme Regex'leri ──
# URL'ler maskelenmez (ürün linkleri analizde lazım).
_PII_PATTERNS = [
    # Kart no (4-4-4-4) — telefondan ÖNCE çalışmalı
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[card]"),
    # E-mail
    (re.compile(r"\b[\w._%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[email]"),
    # TR cep telefonu (+90 / 0 / direkt 5xx)
    (re.compile(r"\b(?:\+?90)?[\s-]?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b"), "[phone]"),
    # TC kimlik (11 hane, ilk hane 0 olamaz)
    (re.compile(r"\b[1-9]\d{10}\b"), "[tckn]"),
]


def _redact_pii(text: str) -> str:
    """Kullanıcı mesajındaki PII'yi maskeler. URL'ler dokunulmaz."""
    if not text:
        return text
    out = text
    for pattern, replacement in _PII_PATTERNS:
        out = pattern.sub(replacement, out)
    return out

class ChatLogger:
    """
    Sends bot-user interaction telemetry to Notion asynchronously
    to prevent event loop blocking.
    """
    def __init__(self, token: str, chat_db_id: str):
        self.token = token
        self.chat_db_id = chat_db_id
        if not self.token or not self.chat_db_id:
            log.warning("ChatLogger eksik ENV ile başlatıldı. Loglama devre dışı.")

    def _do_request(self, session_id: str, user_msg: str, bot_reply: str, bot_name: str):
        if not self.token or not self.chat_db_id:
            return

        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # 2000 chars limit per block
        user_msg = str(user_msg)[:2000] if user_msg else " "
        bot_reply = str(bot_reply)[:2000] if bot_reply else " "

        data = {
            "parent": {
                "type": "database_id",
                "database_id": self.chat_db_id
            },
            "properties": {
                "Session ID": {
                    "title": [
                        {
                            "text": {
                                "content": str(session_id)
                            }
                        }
                    ]
                },
                "Kullanıcı Mesajı": {
                    "rich_text": [
                        {
                            "text": {
                                "content": user_msg
                            }
                        }
                    ]
                },
                "Bot Yanıtı": {
                    "rich_text": [
                        {
                            "text": {
                                "content": bot_reply
                            }
                        }
                    ]
                },
                "Bot": {
                    "select": {
                        "name": bot_name
                    }
                }
            }
        }

        try:
            resp = requests.post(url, headers=headers, json=data, timeout=5)
            # Log failure but do not crash the app
            if resp.status_code != 200:
                log.warning(f"ChatLogger başarısız (HTTP {resp.status_code}): {resp.text}")
        except Exception as e:
            log.error(f"ChatLogger network hatası: {e}")

    async def log_interaction(self, session_id: str, user_msg: str, bot_reply: str, bot_name: str = "E-Com Bot"):
        """Asynchronous wrapper for Notion logging."""
        # Kullanıcı mesajında PII maskele (e-mail, telefon, TC, kart no).
        # Bot yanıtı bot tarafından üretildiği için maskelenmez.
        safe_user_msg = _redact_pii(user_msg) if user_msg else user_msg
        await asyncio.to_thread(self._do_request, session_id, safe_user_msg, bot_reply, bot_name)

# Singleton initialization
chat_tracker = ChatLogger(token=settings.NOTION_TOKEN, chat_db_id=settings.NOTION_CHAT_DB_ID)
