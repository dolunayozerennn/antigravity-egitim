from __future__ import annotations

"""
Kie AI Service — Seedance 2.0 + Nano Banana 2
===============================================
Video üretimi (Seedance 2.0) ve görsel üretimi (Nano Banana 2).
Asenkron görev modeli: createTask → polling → resultUrls.
"""

import json
import time

import requests

from logger import get_logger
from utils.retry import retry_api_call

log = get_logger("kie_api")

# Polling ayarları
POLL_INTERVAL_SECONDS = 10
MAX_POLL_ATTEMPTS = 60  # ~10 dakika
REQUEST_TIMEOUT = 30


class KieAIService:
    """Kie AI API ile video ve görsel üretimi."""

    def __init__(self, api_key: str, base_url: str = "https://api.kie.ai/api/v1/"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🎬 VIDEO ÜRETİMİ — Seedance 2.0
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def create_video(
        self,
        prompt: str,
        duration: int = 8,
        resolution: str = "720p",
        aspect_ratio: str = "9:16",
        generate_audio: bool = False,
        first_frame_url: str | None = None,
    ) -> str:
        """
        Seedance 2.0 ile video üretim görevi oluşturur.

        Args:
            prompt: Video açıklaması (İngilizce önerilir)
            duration: Video süresi (4-15 saniye)
            resolution: "480p" veya "720p"
            aspect_ratio: "9:16", "16:9", "1:1" vb.
            generate_audio: Native ses üretimi (Türkçe dış ses varsa False)
            first_frame_url: İlk kare görseli URL'i (image-to-video)

        Returns:
            str: taskId
        """
        input_data = {
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "generate_audio": generate_audio,
            "web_search": False,
        }

        if first_frame_url:
            input_data["first_frame_url"] = first_frame_url

        payload = {
            "model": "bytedance/seedance-2",
            "input": input_data,
        }

        task_id = self._create_task(payload)
        log.info(f"Seedance 2.0 video görevi oluşturuldu: {task_id} "
                 f"({duration}s, {resolution}, {aspect_ratio})")
        return task_id

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🖼️ GÖRSEL ÜRETİMİ — Nano Banana 2
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def create_image(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        resolution: str = "2k",
        image_input: list[str] | None = None,
    ) -> str:
        """
        Nano Banana 2 ile görsel üretim görevi oluşturur.

        Args:
            prompt: Görsel açıklaması (İngilizce önerilir)
            aspect_ratio: "1:1", "4:5", "9:16", "16:9" vb.
            resolution: "1k", "2k", "4k"
            image_input: Referans görsel URL listesi

        Returns:
            str: taskId
        """
        input_data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }

        if image_input:
            input_data["image_input"] = image_input

        payload = {
            "model": "nano-banana-2",
            "input": input_data,
        }

        task_id = self._create_task(payload)
        log.info(f"Nano Banana 2 görsel görevi oluşturuldu: {task_id} ({aspect_ratio}, {resolution})")
        return task_id

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔊 TTS — ElevenLabs (via Kie AI)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def create_tts(
        self,
        text: str,
        voice: str = "Sarah",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        speed: float = 1.0,
    ) -> str:
        """
        Kie AI proxy üzerinden ElevenLabs TTS görevi oluşturur.
        NOT: Bu metot Kie AI bakiyesinden kullanır.
        Doğrudan ElevenLabs API için elevenlabs_service.py kullanın.

        Args:
            text: Seslendirilecek metin
            voice: Ses adı (Sarah, Charlie, Roger, Laura, George, Daniel, Liam)
            stability: Tutarlılık (0.0-1.0)
            similarity_boost: Ses benzerliği (0.0-1.0)
            speed: Konuşma hızı

        Returns:
            str: taskId
        """
        payload = {
            "model": "elevenlabs/text-to-speech-multilingual-v2",
            "input": {
                "text": text,
                "voice": voice,
                "stability": stability,
                "similarity_boost": similarity_boost,
                "speed": speed,
            },
        }

        task_id = self._create_task(payload)
        log.info(f"Kie AI TTS görevi oluşturuldu: {task_id} (voice={voice}, {len(text)} char)")
        return task_id

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔄 POLLING (Ortak)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def poll_task(self, task_id: str, callback=None) -> dict:
        """
        Görev tamamlanana kadar polling yapar.

        Args:
            task_id: Görev ID'si
            callback: Her polling iterasyonunda çağrılacak fonksiyon
                      callback(attempt, state) şeklinde

        Returns:
            dict: {"status": "success", "urls": [...]} veya
                  {"status": "failed", "error": "..."}
        """
        url = f"{self.base_url}/jobs/recordInfo"

        for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
            try:
                response = requests.get(
                    url,
                    params={"taskId": task_id},
                    headers=self.headers,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()

                state = data.get("data", {}).get("state", "unknown")

                if callback:
                    callback(attempt, state)

                if state == "success":
                    result_json = data["data"].get("resultJson", "{}")
                    parsed = json.loads(result_json) if isinstance(result_json, str) else result_json
                    urls = parsed.get("resultUrls", [])
                    log.info(f"Görev tamamlandı: {task_id} — {len(urls)} çıktı, "
                             f"{attempt} polling denemesi")
                    return {"status": "success", "urls": urls}

                if state in ("failed", "fail"):
                    fail_msg = data["data"].get("failMsg", "Bilinmeyen hata")
                    log.error(f"Görev başarısız: {task_id} — {fail_msg}")
                    return {"status": "failed", "error": fail_msg}

                # processing / waiting — devam et
                log.info(f"Polling {task_id}: [{attempt}/{MAX_POLL_ATTEMPTS}] state={state}")

            except Exception:
                log.error(f"Polling hatası ({attempt}): {task_id}", exc_info=True)

            time.sleep(POLL_INTERVAL_SECONDS)

        log.error(f"Polling timeout: {task_id} — {MAX_POLL_ATTEMPTS} deneme aşıldı")
        return {"status": "failed", "error": "Polling timeout — görev süre aşımına uğradı"}

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 💰 KREDİ SORGULAMA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_credit_balance(self) -> dict:
        """
        Kie AI hesap bakiyesini sorgular.

        Returns:
            dict: Kredi bilgisi
        """
        try:
            url = f"{self.base_url}/chat/credit"
            response = requests.get(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            log.info(f"Kredi bakiyesi sorgulandı: {data}")
            return data
        except Exception:
            log.error("Kredi sorgulama hatası", exc_info=True)
            return {}

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔧 INTERNAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @retry_api_call(max_retries=2, base_delay=2.0, operation_name="Kie AI createTask")
    def _create_task(self, payload: dict) -> str:
        """
        createTask endpoint'ine istek gönderir.

        Returns:
            str: taskId

        Raises:
            Exception: API hatası
        """
        url = f"{self.base_url}/jobs/createTask"

        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 200:
            error_msg = data.get("msg", "Bilinmeyen hata")
            raise ValueError(f"Kie AI createTask hatası: {error_msg} (code={data.get('code')})")

        task_id = data["data"]["taskId"]
        return task_id
