import requests
import logging
from typing import List, Dict, Any, Optional
from .base_node import ana_retry_and_catch

logger = logging.getLogger(__name__)

class GroqNode:
    """
    ANA Standard Node for Groq API.
    A wrapper focusing on raw REST HTTP requests to bypass strict SDK dependency issues,
    offering granular control over timeouts and retries per ANA standard.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = 30  # ANA ZORUNLULUĞU: LLM'ler için uzun standart timeout
        
    @ana_retry_and_catch(node_name="Groq_API", max_retries=3)
    def _execute_chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2048, raw_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes a direct POST request to Groq OpenAI compatible endpoint.
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=self.timeout)
        
        if not response.ok:
            raise Exception(f"API Error {response.status_code}: {response.text}")
            
        return response.json()
        
    def safe_generate(self, model: str, messages: List[Dict[str, str]], fallback_message: str = "Geçici olarak LLM servisine ulaşılamıyor.", raw_payload: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """
        Safe generation loop that returns a fallback string if generation completely fails after 3 retries.
        """
        try:
            result = self._execute_chat(model=model, messages=messages, raw_payload=raw_payload, **kwargs)
            
            # OpenAI / Groq standard response parsing
            choices = result.get("choices", [])
            if choices and len(choices) > 0:
                return choices[0].get("message", {}).get("content", fallback_message)
            return fallback_message
            
        except Exception as e:
            logger.error(f"🚨 [Groq_Node] FALLBACK TRIGGERED - Generation definitely failed. Error: {str(e)}")
            # Fallback (B Planı): Akış patlamasın, default cevapla devam et
            return fallback_message
