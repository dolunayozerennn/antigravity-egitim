"""
Perplexity Service — Marka Araştırması
=======================================
Perplexity API ile marka/ürün araştırması yapar.
Sonuçları yapılandırılmış formatta döndürür.
"""

import requests

from logger import get_logger

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

        try:
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

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            log.info(f"Marka araştırması tamamlandı: '{brand_name}' — {len(content)} karakter")
            return content

        except requests.exceptions.Timeout:
            log.error(f"Perplexity timeout: '{brand_name}'")
            raise RuntimeError(f"Marka araştırması zaman aşımına uğradı: {brand_name}")
        except requests.exceptions.HTTPError as e:
            log.error(f"Perplexity HTTP hatası: {e}", exc_info=True)
            raise RuntimeError(f"Marka araştırmasında HTTP hatası: {e}")
        except Exception:
            log.error("Perplexity genel hata", exc_info=True)
            raise RuntimeError("Marka araştırması yapılamadı.")
