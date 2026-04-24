import requests
import logging
from typing import Dict, Any, Optional
from .base_node import ana_retry_and_catch

logger = logging.getLogger(__name__)

class TelegramNode:
    """
    ANA Standard Node for Telegram Bot API.
    Provides robust communication with Telegram, implementing retries and timeouts.
    """
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.timeout = 15  # ANA ZORUNLULUĞU: Standart timeout
        
    @ana_retry_and_catch(node_name="Telegram_API", max_retries=3)
    def _execute_request(self, method: str, payload: Dict[str, Any], raw_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Core API caller with built-in ANA Retry mechanics.
        """
        endpoint = f"{self.base_url}/{method}"
        
        # raw_payload is optionally logged in shadow mode or before critical crashes.
        # But for network optimization, we don't send it to Telegram.
        response = requests.post(endpoint, json=payload, timeout=self.timeout)
        
        if not response.ok:
            raise Exception(f"API Error {response.status_code}: {response.text}")
            
        return response.json()

    def safe_send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown", reply_to_message_id: Optional[int] = None, raw_payload: Optional[Dict[str, Any]] = None) -> bool:
        """
        Safe wrapper for sending a text message. If it fails, it logs an observable catch and prevents crashing.
        """
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
            
        try:
            self._execute_request(method="sendMessage", payload=payload, raw_payload=raw_payload)
            return True
        except Exception as e:
            logger.error(f"🚨 [Telegram_Node] FALLBACK TRIGGERED - Message to {chat_id} completely failed. Error: {str(e)}")
            # Fallback: Can't really send if Telegram is down, but we avoid crashing the pipeline.
            return False
