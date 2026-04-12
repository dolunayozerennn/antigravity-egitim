from __future__ import annotations

"""
OpenAI Service — GPT-4.1 Mini Chat + Vision
=============================================
Kullanıcıyla doğal sohbet yönetimi ve ürün görseli analizi.
Senaryo üretimi, bilgi çıkarma, prompt oluşturma.
"""

import base64
import json

import openai

from logger import get_logger

log = get_logger("openai_service")


class OpenAIService:
    """GPT-4.1 Mini tabanlı chat + vision servisi."""

    def __init__(self, api_key: str, model: str = "gpt-4.1-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    # ── Chat (Metin Tabanlı) ──

    def chat(self, messages: list[dict], temperature: float = 1.0, max_tokens: int = 2000) -> str:
        """
        OpenAI chat completion çağrısı.

        Args:
            messages: OpenAI format mesaj listesi [{"role": "...", "content": "..."}]
            temperature: Yaratıcılık seviyesi (geçmişe dönük uyumluluk için tutuldu)
            max_tokens: Maximum yanıt uzunluğu

        Returns:
            str: Modelin yanıtı
        """
        try:
            # temperature parametresi gönderilmiyor (model uyumu)
            # Çok kısa max_tokens'da boş content döndürebilir — minimum 100
            effective_max_tokens = max(max_tokens, 100)
            create_kwargs = {
                "model": self.model,
                "messages": messages,
                "max_completion_tokens": effective_max_tokens,
            }
            # Bazen boş content döndürebiliyor — retry mekanizması
            content = ""
            for attempt in range(3):
                response = self.client.chat.completions.create(**create_kwargs)
                content = response.choices[0].message.content or ""
                if content.strip():
                    break
                log.warning(f"OpenAI boş content döndürdü (deneme {attempt+1}/3)")
                if attempt < 2:
                    import time
                    time.sleep(0.5)  # Kısa bekleme — rate limit / cache sorunlarını aşmak için

            if not content.strip():
                log.error("OpenAI 3 denemede de boş content döndürdü (chat)")
                raise RuntimeError("OpenAI API 3 denemede de boş yanıt döndürdü. Lütfen tekrar deneyin.")

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
        Ürün görselini GPT-4.1 Mini Vision ile analiz eder.

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
            if not content:
                log.warning("Vision API boş yanıt döndü — retry")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_completion_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                if not content:
                    raise RuntimeError("Vision API 2 denemede de boş yanıt döndü")
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
            if not content:
                log.warning("Image bytes API boş yanıt döndü — retry")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_completion_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                if not content:
                    raise RuntimeError("Image bytes API 2 denemede de boş yanıt döndü")
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
            # temperature parametresi gönderilmiyor (model uyumu)
            # Çok kısa max_tokens'da boş content döndürebilir — minimum 200
            effective_max_tokens = max(max_tokens, 200)
            create_kwargs = {
                "model": self.model,
                "messages": messages,
                "max_completion_tokens": effective_max_tokens,
                "response_format": {"type": "json_object"},
            }
            # Bazen boş content döndürebiliyor — retry mekanizması
            content = ""
            for attempt in range(3):
                response = self.client.chat.completions.create(**create_kwargs)
                content = response.choices[0].message.content or ""
                if content.strip():
                    break
                log.warning(f"OpenAI JSON boş content döndürdü (deneme {attempt+1}/3)")
                if attempt < 2:
                    import time
                    time.sleep(0.5)
            log.info(f"JSON yanıt alındı — tokens: {response.usage.total_tokens}")
            if not content.strip():
                log.error("OpenAI JSON 3 denemede de boş content döndürdü")
                raise RuntimeError("OpenAI API 3 denemede de boş JSON yanıt döndürdü.")
            return json.loads(content)

        except json.JSONDecodeError:
            log.error("OpenAI JSON parse hatası", exc_info=True)
            raise
        except Exception:
            log.error("OpenAI JSON chat hatası", exc_info=True)
            raise
