from __future__ import annotations

"""
Kie AI Service — Seedance 2.0 + Nano Banana 2
===============================================
Video üretimi (Seedance 2.0) ve görsel üretimi (Nano Banana 2).
Asenkron görev modeli: createTask → polling → resultUrls.
"""

import json
import os
import time

import requests

from logger import get_logger
from utils.retry import retry_api_call

log = get_logger("kie_api")

# Polling ayarları
POLL_INTERVAL_SECONDS = 10
MAX_POLL_ATTEMPTS = 60  # ~10 dakika
REQUEST_TIMEOUT = 30

# File Upload
FILE_UPLOAD_BASE_URL = "https://kieai.redpandaai.co"


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
        duration: int = 10,
        aspect_ratio: str = "9:16",
        generate_audio: bool = True,
        resolution: str | None = None,
        reference_images: list[str] | None = None,
        first_frame_url: str | None = None,
        last_frame_url: str | None = None,
        reference_videos: list[str] | None = None,
        reference_audios: list[str] | None = None,
        return_last_frame: bool = False,
    ) -> str:
        """
        Seedance 2.0 ile video üretim görevi oluşturur.

        Args:
            prompt: Video açıklaması (İngilizce önerilir)
            duration: Video süresi (4-15 saniye)
            aspect_ratio: "9:16", "16:9", "1:1" vb.
            generate_audio: Native ses üretimi (ambient sesler için True)
            resolution: Video çözünürlüğü ("720p" vb.)
            reference_images: Referans görseller URL listesi (1-3 adet).
                              Modele "bu görselleri referans al, özgürce üret" der.
                              first_frame_url ile AYNI ANDA KULLANILAMAZ.
            first_frame_url: İlk kare görseli URL (Image-to-Video modu).
                             reference_images ile AYNI ANDA KULLANILAMAZ.
            last_frame_url: Son kare görseli URL.
            reference_videos: Referans video URL listesi (stil/hareket rehberi).
            reference_audios: Referans ses URL listesi.
            return_last_frame: True ise son kareyi ayrıca döndürür.

        Returns:
            str: taskId

        Raises:
            ValueError: first_frame_url ve reference_images aynı anda verilirse.
        """
        # Doğrulama: first_frame_url ve reference_images birlikte kullanılamaz
        if first_frame_url and reference_images:
            raise ValueError(
                "Seedance 2.0: first_frame_url ve reference_images "
                "aynı anda kullanılamaz. Birini seçin."
            )

        input_data = {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "generate_audio": generate_audio,
            "web_search": False,
        }

        # Opsiyonel parametreler — sadece değer varsa ekle
        if resolution:
            input_data["resolution"] = resolution
        if reference_images:
            input_data["reference_image_urls"] = reference_images
        if first_frame_url:
            input_data["first_frame_url"] = first_frame_url
        if last_frame_url:
            input_data["last_frame_url"] = last_frame_url
        if reference_videos:
            input_data["reference_video_urls"] = reference_videos
        if reference_audios:
            input_data["reference_audio_urls"] = reference_audios
        if return_last_frame:
            input_data["return_last_frame"] = True

        payload = {
            "model": "bytedance/seedance-2",
            "input": input_data,
        }

        task_id = self._create_task(payload)
        ref_count = len(reference_images) if reference_images else 0
        mode = "I2V" if first_frame_url else f"ref_images={ref_count}"
        log.info(f"Seedance 2.0 video görevi oluşturuldu: {task_id} "
                 f"({duration}s, {aspect_ratio}, {mode})")
        return task_id

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🖼️ GÖRSEL ÜRETİMİ — Nano Banana 2
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def create_image(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        resolution: str = "1k",
        image_input: list[str] | None = None,
    ) -> str:
        """
        Nano Banana 2 ile görsel üretim görevi oluşturur.

        Args:
            prompt: Görsel açıklaması (İngilizce önerilir)
            aspect_ratio: "1:1", "4:5", "9:16", "16:9" vb.
            resolution: "1k", "4k"  # (2k model tarafindan artik desteklenmiyor)
            image_input: Referans görsel URL listesi

        Returns:
            str: taskId
        """
        input_data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
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

    async def async_poll_task(self, task_id: str, callback=None) -> dict:
        """
        Görev tamamlanana kadar async polling yapar.
        
        time.sleep() yerine asyncio.sleep() kullanır →
        event loop'u BLOKE ETMEZ, thread pool tüketmez.
        
        Production pipeline bu metodu doğrudan (await ile) çağırmalı.
        asyncio.to_thread() ile sarmalamanıza GEREK YOKTUR.

        Args:
            task_id: Görev ID'si
            callback: Her polling iterasyonunda çağrılacak fonksiyon
                      callback(attempt, state) şeklinde

        Returns:
            dict: {"status": "success", "urls": [...]} veya
                  {"status": "failed", "error": "..."}
        """
        import asyncio as _asyncio
        url = f"{self.base_url}/jobs/recordInfo"

        for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
            try:
                # HTTP isteği kısa süreli — thread'de çalıştır
                response = await _asyncio.to_thread(
                    requests.get,
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

            # ✅ asyncio.sleep — event loop'u bloke etmez
            await _asyncio.sleep(POLL_INTERVAL_SECONDS)

        log.error(f"Async polling timeout: {task_id} — {MAX_POLL_ATTEMPTS} deneme aşıldı")
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
    # 📤 DOSYA YÜKLEME — File Upload API
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def upload_file_from_url(self, file_url: str, file_name: str | None = None) -> str:
        """
        Harici URL'deki dosyayı Kie AI'ın dosya sunucusuna yükler.

        Seedance 2.0'a verilecek referans görseller/videolar/sesler için
        harici kaynakları önce Kie AI sistemine yüklemek gerekebilir.

        Endpoint: POST https://kieai.redpandaai.co/api/file-url-upload

        Args:
            file_url: Yüklenecek dosyanın harici URL'si
            file_name: Dosya adı (verilmezse URL'den çıkarılır)

        Returns:
            str: Kie AI üzerindeki downloadUrl

        Raises:
            ValueError: API hatası
        """
        if not file_name:
            # URL'den dosya adını çıkar
            from urllib.parse import urlparse
            parsed = urlparse(file_url)
            file_name = os.path.basename(parsed.path) or "uploaded_file"

        url = f"{FILE_UPLOAD_BASE_URL}/api/file-url-upload"
        payload = {
            "fileUrl": file_url,
            "fileName": file_name,
        }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=60,  # Dosya yükleme daha uzun sürebilir
            )
            response.raise_for_status()
            data = response.json()

            download_url = data.get("downloadUrl") or data.get("data", {}).get("downloadUrl")
            if not download_url:
                raise ValueError(f"File upload yanıtında downloadUrl bulunamadı: {data}")

            log.info(f"Dosya yüklendi: {file_name} → {download_url[:80]}...")
            return download_url

        except requests.exceptions.RequestException as e:
            log.error(f"Dosya yükleme hatası: {file_url} — {e}", exc_info=True)
            raise ValueError(f"Kie AI file upload başarısız: {e}") from e

    def upload_files_from_urls(self, file_urls: list[str]) -> list[str]:
        """
        Birden fazla harici URL'yi Kie AI'a toplu yükler.

        Args:
            file_urls: Yüklenecek dosya URL'leri listesi

        Returns:
            list[str]: Kie AI downloadUrl'leri listesi
        """
        download_urls = []
        for i, url in enumerate(file_urls, 1):
            try:
                dl_url = self.upload_file_from_url(url)
                download_urls.append(dl_url)
                log.info(f"Toplu yükleme [{i}/{len(file_urls)}]: başarılı")
            except Exception:
                log.error(f"Toplu yükleme [{i}/{len(file_urls)}] başarısız: {url}", exc_info=True)
                # Başarısız olanı atla, diğerlerine devam et
                continue
        return download_urls

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
