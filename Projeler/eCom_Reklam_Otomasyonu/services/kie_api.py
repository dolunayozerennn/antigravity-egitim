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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📐 ASPECT RATIO — Geçerli Değerler (Kie AI API)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VALID_ASPECT_RATIOS = {"9:16", "16:9", "1:1", "4:3", "3:4", "21:9"}
DEFAULT_ASPECT_RATIO = "9:16"


def normalize_aspect_ratio(raw: str) -> str:
    """
    Ham aspect_ratio string'ini Kie AI'ın kabul ettiği formata dönüştürür.

    Desteklenen girdi formatları:
    - Doğrudan geçerli: "9:16", "16:9", "1:1", "4:3", "3:4", "21:9"
    - Türkçe/İngilizce etiketler: "dikey", "yatay", "kare", "vertical", "horizontal", "square"
    - Buton etiketleri: "Dikey (9:16)", "Yatay (16:9)", "Kare (1:1)"
    - Separator varyasyonları: "9/16", "9x16"

    Returns:
        str: Kie AI'ın kabul ettiği geçerli aspect_ratio string'i
    """
    if not raw:
        return DEFAULT_ASPECT_RATIO

    cleaned = str(raw).strip().lower()

    # Direkt geçerli mi kontrol et
    if cleaned in VALID_ASPECT_RATIOS:
        return cleaned

    # Ratio pattern çıkar — parantez içi dahil: "Dikey (9:16)" → "9:16"
    import re
    ratio_match = re.search(r'(\d+)\s*[:x/]\s*(\d+)', cleaned)
    if ratio_match:
        candidate = f"{ratio_match.group(1)}:{ratio_match.group(2)}"
        if candidate in VALID_ASPECT_RATIOS:
            return candidate

    # Türkçe/İngilizce etiket mapping
    label_map = {
        "dikey": "9:16", "vertical": "9:16", "portrait": "9:16",
        "yatay": "16:9", "horizontal": "16:9", "landscape": "16:9", "widescreen": "16:9",
        "kare": "1:1", "square": "1:1",
        "ultrawide": "21:9", "cinematic": "21:9",
    }
    for keyword, ratio in label_map.items():
        if keyword in cleaned:
            return ratio

    log.warning(
        f"Bilinmeyen aspect_ratio normalize edildi: '{raw}' → '{DEFAULT_ASPECT_RATIO}' "
        f"(geçerli değerler: {VALID_ASPECT_RATIOS})"
    )
    return DEFAULT_ASPECT_RATIO


def _is_kie_native_url(url: str) -> bool:
    """URL'nin Kie AI sunucularinda olup olmadigini kontrol eder (domain-level)."""
    if not url:
        return False
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or ""
        native_domains = ("kieai.redpandaai.co", "templateb.aiquickdraw.com", "kie.ai")
        return any(hostname == domain or hostname.endswith(f".{domain}") for domain in native_domains)
    except Exception:
        return False


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
            aspect_ratio: "9:16", "16:9", "1:1" vb. Referans görsel kullanıldığında
                          otomatik olarak "adaptive" kullanılır (API kısıtı).
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

        # Referans görsel kullanıldığında aspect_ratio "adaptive" olmalı
        # (Kie AI Seedance 2.0: sabit oran + referans görsel kombinasyonu 422 verir)
        has_reference = bool(reference_images or first_frame_url)
        if has_reference:
            safe_aspect = "adaptive"
            log.info(f"Referans görsel modu: aspect_ratio '{aspect_ratio}' → 'adaptive'")
        else:
            safe_aspect = normalize_aspect_ratio(aspect_ratio)
            if safe_aspect != aspect_ratio:
                log.info(f"Aspect ratio normalize edildi: '{aspect_ratio}' → '{safe_aspect}'")

        input_data = {
            "prompt": prompt,
            "duration": int(duration),
            "aspect_ratio": safe_aspect,
            "generate_audio": generate_audio,
            "web_search": False,
        }

        # Opsiyonel parametreler — sadece değer varsa ekle
        if resolution:
            input_data["resolution"] = resolution
            
        if reference_images:
            processed_images = []
            for img_url in reference_images:
                if _is_kie_native_url(img_url):
                    log.info(f"Referans gorsel zaten Kie-native: {img_url}")
                    processed_images.append(img_url)
                else:
                    try:
                        new_url = self.upload_file_from_url(img_url)
                        processed_images.append(new_url)
                    except Exception as e:
                        log.warning(f"Referans gorsel yukleme basarisiz (atlanarak devam ediliyor): {img_url} - {e}")
            
            if processed_images:
                log.info(f"Referans gorseller Kie AI sunucusuna yuklendi: {len(processed_images)}/{len(reference_images)} basarili")
                input_data["reference_image_urls"] = processed_images
            else:
                log.warning("Hicbir referans gorsel yuklenemedi, isleme referanssiz devam ediliyor.")

        if first_frame_url:
            if _is_kie_native_url(first_frame_url):
                log.info(f"Ilk kare gorseli zaten Kie-native: {first_frame_url}")
                input_data["first_frame_url"] = first_frame_url
            else:
                try:
                    new_url = self.upload_file_from_url(first_frame_url)
                    log.info("Ilk kare gorseli Kie AI sunucusuna yuklendi.")
                    input_data["first_frame_url"] = new_url
                except Exception as e:
                    log.warning(f"Ilk kare gorsel yukleme basarisiz (atlanarak devam ediliyor): {first_frame_url} - {e}")

        if last_frame_url:
            if _is_kie_native_url(last_frame_url):
                log.info(f"Son kare gorseli zaten Kie-native: {last_frame_url}")
                input_data["last_frame_url"] = last_frame_url
            else:
                try:
                    new_url = self.upload_file_from_url(last_frame_url)
                    log.info("Son kare gorseli Kie AI sunucusuna yuklendi.")
                    input_data["last_frame_url"] = new_url
                except Exception as e:
                    log.warning(f"Son kare gorsel yukleme basarisiz (atlanarak devam ediliyor): {last_frame_url} - {e}")

        if reference_videos:
            processed_videos = []
            for vid_url in reference_videos:
                if _is_kie_native_url(vid_url):
                    log.info(f"Referans video zaten Kie-native: {vid_url}")
                    processed_videos.append(vid_url)
                else:
                    try:
                        new_url = self.upload_file_from_url(vid_url)
                        processed_videos.append(new_url)
                    except Exception as e:
                        log.warning(f"Referans video yukleme basarisiz (atlanarak devam ediliyor): {vid_url} - {e}")
            
            if processed_videos:
                log.info(f"Referans videolar Kie AI sunucusuna yuklendi: {len(processed_videos)}/{len(reference_videos)} basarili")
                input_data["reference_video_urls"] = processed_videos

        if reference_audios:
            processed_audios = []
            for aud_url in reference_audios:
                if _is_kie_native_url(aud_url):
                    log.info(f"Referans ses zaten Kie-native: {aud_url}")
                    processed_audios.append(aud_url)
                else:
                    try:
                        new_url = self.upload_file_from_url(aud_url)
                        processed_audios.append(new_url)
                    except Exception as e:
                        log.warning(f"Referans ses yukleme basarisiz (atlanarak devam ediliyor): {aud_url} - {e}")
            
            if processed_audios:
                log.info(f"Referans sesler Kie AI sunucusuna yuklendi: {len(processed_audios)}/{len(reference_audios)} basarili")
                input_data["reference_audio_urls"] = processed_audios

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
        # Aspect ratio'yu Kie AI'ın kabul ettiği değere normalize et
        safe_aspect = normalize_aspect_ratio(aspect_ratio)
        if safe_aspect != aspect_ratio:
            log.info(f"Görsel aspect ratio normalize edildi: '{aspect_ratio}' → '{safe_aspect}'")

        input_data = {
            "prompt": prompt,
            "aspect_ratio": safe_aspect,
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
        start_time = time.monotonic()
        prev_state: str | None = None

        for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
            try:
                response = requests.get(
                    url,
                    params={"taskId": task_id},
                    headers=self.headers,
                    timeout=REQUEST_TIMEOUT,
                )

                # Permanent auth/not-found hataları → loop kır (boşa polling önle)
                if response.status_code in (401, 403, 404):
                    raise RuntimeError(
                        f"permanent: HTTP {response.status_code} polling — "
                        f"task={task_id}, body={response.text[:200]}"
                    )

                response.raise_for_status()
                data = response.json()

                # Wrapper error kontrolü (Kie AI API)
                code = data.get("code")
                if code is not None and str(code) not in ("200", "0"):
                    code_int = int(code) if str(code).isdigit() else 0
                    if code_int in (401, 403, 404):
                        raise RuntimeError(
                            f"permanent: wrapper code={code} — "
                            f"{data.get('msg', 'Bilinmeyen hata')}"
                        )
                    raise ValueError(f"Polling API Wrapper Hatası (code={code}): {data.get('msg', 'Bilinmeyen hata')}")

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

                # processing / waiting — sadece state değişiminde INFO logla
                if state != prev_state:
                    log.info(f"Polling {task_id}: state {prev_state}→{state} "
                             f"(attempt {attempt}/{MAX_POLL_ATTEMPTS})")
                    prev_state = state
                else:
                    log.debug(f"Polling {task_id}: [{attempt}/{MAX_POLL_ATTEMPTS}] state={state}")

            except RuntimeError as e:
                # Permanent error → boşa polling yapma, hemen kır
                if str(e).startswith("permanent:"):
                    log.error(f"Polling kalıcı hata, loop kırılıyor: {task_id} — {e}")
                    raise
                log.error(f"Polling hatası ({attempt}): {task_id}", exc_info=True)
            except Exception:
                log.error(f"Polling hatası ({attempt}): {task_id}", exc_info=True)

            # Adaptif interval: ilk 30s yoğun başlangıç (20s), sonra hızlı (8s)
            elapsed = time.monotonic() - start_time
            interval = 20 if elapsed < 30 else 8
            time.sleep(interval)

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
        start_time = time.monotonic()
        prev_state: str | None = None

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

                # Permanent auth/not-found hataları → loop kır (boşa polling önle)
                if response.status_code in (401, 403, 404):
                    raise RuntimeError(
                        f"permanent: HTTP {response.status_code} polling — "
                        f"task={task_id}, body={response.text[:200]}"
                    )

                response.raise_for_status()
                data = response.json()

                # Wrapper error kontrolü (Kie AI API)
                code = data.get("code")
                if code is not None and str(code) not in ("200", "0"):
                    code_int = int(code) if str(code).isdigit() else 0
                    if code_int in (401, 403, 404):
                        raise RuntimeError(
                            f"permanent: wrapper code={code} — "
                            f"{data.get('msg', 'Bilinmeyen hata')}"
                        )
                    raise ValueError(f"Polling API Wrapper Hatası (code={code}): {data.get('msg', 'Bilinmeyen hata')}")

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

                # processing / waiting — sadece state değişiminde INFO logla
                if state != prev_state:
                    log.info(f"Polling {task_id}: state {prev_state}→{state} "
                             f"(attempt {attempt}/{MAX_POLL_ATTEMPTS})")
                    prev_state = state
                else:
                    log.debug(f"Polling {task_id}: [{attempt}/{MAX_POLL_ATTEMPTS}] state={state}")

            except RuntimeError as e:
                # Permanent error → boşa polling yapma, hemen kır
                if str(e).startswith("permanent:"):
                    log.error(f"Async polling kalıcı hata, loop kırılıyor: {task_id} — {e}")
                    raise
                log.error(f"Polling hatası ({attempt}): {task_id}", exc_info=True)
            except Exception:
                log.error(f"Polling hatası ({attempt}): {task_id}", exc_info=True)

            # Adaptif interval: ilk 30s yoğun başlangıç (20s), sonra hızlı (8s)
            elapsed = time.monotonic() - start_time
            interval = 20 if elapsed < 30 else 8
            # ✅ asyncio.sleep — event loop'u bloke etmez
            await _asyncio.sleep(interval)

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

    @retry_api_call(max_retries=2, base_delay=2.0, operation_name="Kie AI file upload")
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

        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=60,  # Dosya yükleme daha uzun sürebilir
        )
        response.raise_for_status()
        data = response.json()

        # 200 OK dönüp JSON içinde hata kodu dönme durumu (API Wrapper hatası)
        code = data.get("code")
        if code is not None and str(code) not in ("200", "0"):
            code_int = int(code) if str(code).isdigit() else 400
            if code_int in {401, 408, 429} or (500 <= code_int <= 599):
                response.status_code = code_int
                raise requests.exceptions.HTTPError(f"Upload API hatası: {data.get('msg', 'Bilinmeyen hata')} (code={code})", response=response)
            raise ValueError(f"Kie AI file upload hatası: {data.get('msg', 'Bilinmeyen hata')} (code={code})")

        download_url = data.get("downloadUrl") or data.get("data", {}).get("downloadUrl")
        if not download_url:
            raise ValueError(f"File upload yanıtında downloadUrl bulunamadı: {data}")

        log.info(f"Dosya yüklendi: {file_name} → {download_url[:80]}...")
        return download_url

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

        # Son savunma hattı: payload içindeki aspect_ratio'yu doğrula
        input_block = payload.get("input", {})
        if "aspect_ratio" in input_block:
            validated = normalize_aspect_ratio(input_block["aspect_ratio"])
            if validated != input_block["aspect_ratio"]:
                log.warning(
                    f"_create_task son savunma: aspect_ratio '{input_block['aspect_ratio']}' → '{validated}'"
                )
                input_block["aspect_ratio"] = validated

        log.debug(
            f"createTask payload: model={payload.get('model')}, "
            f"aspect_ratio={input_block.get('aspect_ratio')}, "
            f"duration={input_block.get('duration')}"
        )

        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        # 422 hatası için detaylı loglama (debug kolaylığı)
        if response.status_code == 422:
            log.error(
                f"Kie AI 422 Validation Error — "
                f"payload_input={json.dumps(input_block, ensure_ascii=False)[:500]}, "
                f"response={response.text[:500]}"
            )

        # 5xx / 512 upstream proxy hatası için detaylı loglama
        if response.status_code >= 500:
            log.error(
                f"Kie AI upstream hatası: HTTP {response.status_code} — "
                f"model={payload.get('model')}, "
                f"aspect_ratio={input_block.get('aspect_ratio')}, "
                f"duration={input_block.get('duration')}, "
                f"response_body={response.text[:500]}"
            )

        response.raise_for_status()
        data = response.json()

        # 200 OK dönüp JSON içinde hata kodu dönme durumu (API Wrapper hatası)
        code = data.get("code")
        if code is not None and str(code) not in ("200", "0"):
            error_msg = data.get("msg", "Bilinmeyen hata")
            code_int = int(code) if str(code).isdigit() else 400
            if code_int in {401, 408, 429} or (500 <= code_int <= 599):
                response.status_code = code_int
                raise requests.exceptions.HTTPError(f"Kie AI createTask API hatası: {error_msg} (code={code})", response=response)
            raise ValueError(f"Kie AI createTask hatası: {error_msg} (code={code})")

        task_id = data.get("data", {}).get("taskId")
        if not task_id:
            raise ValueError(f"Kie AI createTask yanıtında taskId bulunamadı: {data}")
            
        return task_id
