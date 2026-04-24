import requests
import json
import logging
from typing import Dict, Any, Optional
from .base_node import ana_retry_and_catch

logger = logging.getLogger(__name__)

class SupabaseLoggerNode:
    """
    ANA Standard Node for Supabase MCP Logging.
    Implements timeout, retry, observable catch, and fallback mechanisms.
    """
    def __init__(self, supabase_url: str, supabase_key: str, table_name: str = "antigravity_logs"):
        self.supabase_url = supabase_url.rstrip("/")
        self.supabase_key = supabase_key
        self.table_name = table_name
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        self.timeout = 10  # ANA ZORUNLULUĞU: Standart timeout

    @ana_retry_and_catch(node_name="Supabase_Logger", max_retries=3)
    def _execute_log(self, project_name: str, status: str, message: str, details: Dict[str, Any], raw_payload: Optional[Dict[str, Any]] = None) -> bool:
        """
        API ile iletişime geçen ve hata fırlatabilen core fonksiyon.
        """
        endpoint = f"{self.supabase_url}/rest/v1/{self.table_name}"
        
        payload = {
            "project_name": project_name,
            "status": status,
            "message": message,
            "details": details,
            # Sistem hata ayıklamaları için raw payload ("Kıyamet Testi" / Gölge Modu desteği)
            "raw_payload": raw_payload 
        }
        
        response = requests.post(endpoint, headers=self.headers, json=payload, timeout=self.timeout)
        
        if not response.ok:
            raise Exception(f"API Error {response.status_code}: {response.text}")
            
        return True
        
    def safe_log(self, project_name: str, status: str, message: str, details: Dict[str, Any] = None, raw_payload: Optional[Dict[str, Any]] = None) -> bool:
        """
        Fallback Wrapper: Loglamanın hata verip ana akışı kitlemesini engelleyen Fallback yöntemi.
        Eğer Supabase çökerse veriyi lokal JSON append formatında kaydeder.
        """
        if details is None:
            details = {}
            
        try:
            return self._execute_log(project_name, status, message, details, raw_payload)
        except Exception as e:
            logger.error(f"🚨 [Supabase_Logger] FALLBACK TRIGGERED - Logging completely failed. Error: {str(e)}")
            
            # Fallback (B Planı): Lokal dosyaya Append
            fallback_data = {
                "project_name": project_name,
                "status": status,
                "message": message,
                "details": details,
                "raw_payload": raw_payload,
                "fallback_error": str(e)
            }
            try:
                with open("fallback_antigravity_logs.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(fallback_data, ensure_ascii=False) + "\n")
            except Exception as io_err:
                logger.error(f"❌ [Supabase_Logger] Fallback IO Error: {str(io_err)}")
                
            return False
