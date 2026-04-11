from __future__ import annotations

"""
OpenAI Service — GPT-5 Mini Chat + Vision
==========================================
Kullanıcıyla doğal sohbet yönetimi ve ürün görseli analizi.
Senaryo üretimi, bilgi çıkarma, prompt oluşturma.
"""

import base64
import json

import openai

from logger import get_logger

log = get_logger("openai_service")


class OpenAIService:
    """GPT-5 Mini tabanlı chat + vision servisi."""

    def __init__(self, api_key: str, model: str = "gpt-5-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    # ── Chat (Metin Tabanlı) ──

    def chat(self, messages: list[dict], temperature: float = 1.0, max_tokens: int = 2000) -> str:
        """
        OpenAI chat completion çağrısı.

        Args:
            messages: OpenAI format mesaj listesi [{"role": "...", "content": "..."}]
            temperature: Yaratıcılık seviyesi (NOT: GPT-5 Mini sadece 1.0 destekler)
            max_tokens: Maximum yanıt uzunluğu

        Returns:
            str: Modelin yanıtı
        """
        try:
            # GPT-5 Mini sadece temperature=1 destekler, parametre gönderme
            create_kwargs = {
                "model": self.model,
                "messages": messages,
                "max_completion_tokens": max_tokens,
            }
            # GPT-5 Mini bazen boş content döndürüyor — retry mekanizması
            for attempt in range(3):
                response = self.client.chat.completions.create(**create_kwargs)
                content = response.choices[0].message.content or ""
                if content.strip():
                    break
                log.warning(f"OpenAI boş content döndürdü (deneme {attempt+1}/3)")
            log.info(f"Chat yanıt alındı — {len(content)} karakter, "
                     f"tokens: {response.usage.total_tokens}")
            return content

        except openai.RateLimitError:
            log.error("OpenAI rate limit aşıldı!", exc_info=True)
            raise
        except openai.APIError as e:
            log.error(f"OpenAI API hatası: {e}", exc_info=True)
            raise

    # ── Vision (Görsel Analiz) ──

    def analyze_image(self, image_url: str, prompt: str, max_tokens: int = 1500) -> str:
        """
        Ürün görselini GPT-5 Mini Vision ile analiz eder.

        Args:
            image_url: Public erişimli görsel URL'i
            prompt: Analiz talimatı

        Returns:
            str: Modelin görsel analiz yanıtı
        """
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url, "detail": "high"},
                        },
                    ],
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            log.info(f"Vision analiz tamamlandı — {len(content)} karakter")
            return content

        except Exception:
            log.error("Görsel analiz hatası", exc_info=True)
            raise

    def analyze_image_bytes(self, image_bytes: bytes, mime_type: str, prompt: str,
                            max_tokens: int = 1500) -> str:
        """
        Telegram'dan gelen raw image bytes'ı analiz eder.
        Base64 encode ederek Vision API'ye gönderir.

        Args:
            image_bytes: Ham görsel verisi
            mime_type: MIME tipi (image/jpeg, image/png vb.)
            prompt: Analiz talimatı

        Returns:
            str: Modelin yanıtı
        """
        try:
            b64 = base64.b64encode(image_bytes).decode("utf-8")
            data_url = f"data:{mime_type};base64,{b64}"

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url, "detail": "high"},
                        },
                    ],
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            log.info(f"Image bytes analiz tamamlandı — {len(content)} karakter")
            return content

        except Exception:
            log.error("Image bytes analiz hatası", exc_info=True)
            raise

    # ── JSON Çıktı ──

    def chat_json(self, messages: list[dict], temperature: float = 1.0,
                  max_tokens: int = 3000) -> dict:
        """
        Chat completion çağrısı — JSON response_format ile.

        Returns:
            dict: Parse edilmiş JSON yanıt
        """
        try:
            # GPT-5 Mini sadece temperature=1 destekler, parametre gönderme
            create_kwargs = {
                "model": self.model,
                "messages": messages,
                "max_completion_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }
            # GPT-5 Mini bazen boş content döndürüyor — retry mekanizması
            for attempt in range(3):
                response = self.client.chat.completions.create(**create_kwargs)
                content = response.choices[0].message.content or ""
                if content.strip():
                    break
                log.warning(f"OpenAI JSON boş content döndürdü (deneme {attempt+1}/3)")
            log.info(f"JSON yanıt alındı — tokens: {response.usage.total_tokens}")
            if not content.strip():
                log.warning("OpenAI 3 denemede de boş content döndürdü — boş dict dönülecek")
                return {}
            return json.loads(content)

        except json.JSONDecodeError:
            log.error("OpenAI JSON parse hatası", exc_info=True)
            raise
        except Exception:
            log.error("OpenAI JSON chat hatası", exc_info=True)
            raise
