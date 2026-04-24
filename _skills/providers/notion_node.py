import requests
import logging
from typing import Dict, Any, Optional
from .base_node import ana_retry_and_catch

logger = logging.getLogger(__name__)

class NotionNode:
    """
    ANA Standard Node for Notion API.
    Implements timeout, retry, observable catch, and fallback mechanisms for Notion integration.
    """
    def __init__(self, notion_token: str, notion_version: str = "2022-06-28"):
        self.notion_token = notion_token
        self.notion_version = notion_version
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": self.notion_version,
            "Content-Type": "application/json"
        }
        self.timeout = 20  # ANA ZORUNLULUĞU: Notion API bazen yavaş yanıt verebilir
        
    @ana_retry_and_catch(node_name="Notion_API", max_retries=3)
    def _execute_request(self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None, raw_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Core API caller with built-in ANA Retry mechanics.
        """
        url = f"{self.base_url}/{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
        elif method.upper() == "POST":
            response = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
        elif method.upper() == "PATCH":
            response = requests.patch(url, headers=self.headers, json=payload, timeout=self.timeout)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if not response.ok:
            raise Exception(f"API Error {response.status_code}: {response.text}")
            
        return response.json()

    def safe_query_database(self, database_id: str, filter_dict: Optional[Dict[str, Any]] = None, raw_payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Safe wrapper for querying a database. Returns None on complete failure instead of crashing.
        """
        payload = {}
        if filter_dict:
            payload["filter"] = filter_dict
            
        try:
            return self._execute_request(method="POST", endpoint=f"databases/{database_id}/query", payload=payload, raw_payload=raw_payload)
        except Exception as e:
            logger.error(f"🚨 [Notion_Node] FALLBACK TRIGGERED - DB Query {database_id} failed. Error: {str(e)}")
            return None

    def safe_create_page(self, parent_db_id: str, properties: Dict[str, Any], raw_payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Safe wrapper for creating a new page in a database.
        """
        payload = {
            "parent": {"database_id": parent_db_id},
            "properties": properties
        }
        try:
            return self._execute_request(method="POST", endpoint="pages", payload=payload, raw_payload=raw_payload)
        except Exception as e:
            logger.error(f"🚨 [Notion_Node] FALLBACK TRIGGERED - Page creation failed. Error: {str(e)}")
            return None
