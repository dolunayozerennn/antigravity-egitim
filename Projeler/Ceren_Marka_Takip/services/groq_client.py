"""
Ceren_Marka_Takip — Groq LLM Client
======================================
Groq API üzerinden LLM çağrıları yapar.
Model: openai/gpt-oss-120b
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Groq config
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = "openai/gpt-oss-120b"


def _get_client():
    """Groq client oluştur (lazy init)."""
    from groq import Groq
    
    api_key = GROQ_API_KEY
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY tanımlanmamış. master.env'den yükle veya env'e set et."
        )
    
    return Groq(api_key=api_key)


def analyze_thread(thread_messages: str, system_prompt: str) -> Optional[Dict[str, Any]]:
    """
    Thread mesajlarını LLM ile analiz et.
    
    Args:
        thread_messages: Thread'deki mesajların metin hali
        system_prompt: Sistem promptu (analiz talimatları)
    
    Returns:
        JSON parse edilmiş analiz sonucu veya None (hata durumunda)
    """
    try:
        client = _get_client()
        
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": thread_messages},
            ],
            temperature=0.1,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        result = json.loads(content)
        logger.debug(f"LLM analiz sonucu: {result}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"LLM yanıtı JSON parse edilemedi: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Groq API hatası: {e}", exc_info=True)
        return None
