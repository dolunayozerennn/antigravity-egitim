"""
Perplexity Service — Marka Araştırması
=======================================
Perplexity API ile marka/ürün araştırması yapar.
Sonuçları yapılandırılmış formatta döndürür.
"""

import requests

from logger import get_logger
from utils.retry import retry_api_call

log = get_logger("perplexity_service")

# Perplexity API timeout
REQUEST_TIMEOUT = 30


class PerplexityService:
    """Perplexity API ile marka/ürün araştırması."""

    def __init__(self, api_key: str, base_url: str = "https://api.perplexity.ai"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def research_brand(self, brand_name: str, product_name: str = "",
                       language: str = "tr") -> str:
        """
        Marka ve ürün hakkında güncel web araştırması yapar.

        Args:
            brand_name: Marka adı
            product_name: Ürün adı (opsiyonel)
            language: Yanıt dili ('tr' veya 'en')

        Returns:
            str: Araştırma sonuçları (metin)
        """
        lang_note = "Yanıtını Türkçe ver." if language == "tr" else "Answer in English."

        product_part = f"ve '{product_name}' ürünü" if product_name else ""
        query = (
            f"'{brand_name}' markası {product_part} hakkında detaylı bilgi ver. "
            f"Şunları öğrenmek istiyorum:\n"
            f"1. Marka nedir, ne iş yapar?\n"
            f"2. Hedef kitlesi kim?\n"
            f"3. Ürün kategorisi ve fiyat aralığı\n"
            f"4. Markanın tonu ve kimliği (lüks, genç, spor vb.)\n"
            f"5. Rakipleri kimler?\n"
            f"{lang_note}"
        )

        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Sen bir marka araştırma asistanısın. Verilen marka hakkında "
                        "güncel, doğrulanmış bilgiler sun. Özgün bilgi yoksa bunu belirt."
                    ),
                },
                {"role": "user", "content": query},
            ],
            "temperature": 0.3,
            "max_tokens": 1500,
        }

        return self._call_perplexity(payload, brand_name)

    @retry_api_call(max_retries=2, base_delay=2.0, operation_name="Perplexity research")
    def _call_perplexity(self, payload: dict, brand_name: str) -> str:
        """Perplexity API çağrısı — retry mekanizmalı."""
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        # Güvenli erişim — eksik key'lerde KeyError önlenir
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(f"Perplexity boş yanıt döndü: {brand_name}")
        content = choices[0].get("message", {}).get("content", "")
        if not content.strip():
            raise RuntimeError(f"Perplexity boş content döndü: {brand_name}")

        log.info(f"Marka araştırması tamamlandı: '{brand_name}' — {len(content)} karakter")
        return content
