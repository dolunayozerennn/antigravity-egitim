"""
Replicate Service — Video + Ses Birleştirme
=============================================
Replicate API ile video ve ses dosyalarını birleştirir.
Model: lucataco/video-audio-merge
Cloud-based — Railway'de FFmpeg kurulumu gereksiz.
"""

import io
import time

import replicate

from logger import get_logger

log = get_logger("replicate_service")

# Polling ayarları
POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 120  # ~10 dakika


class ReplicateService:
    """Replicate API ile video + ses birleştirme."""

    def __init__(self, api_token: str):
        self.client = replicate.Client(api_token=api_token)

    def upload_audio(self, audio_bytes: bytes, filename: str = "audio.mp3") -> str:
        """
        Ses dosyasını Replicate file storage'a yükler ve URL döner.
        Data URI yerine gerçek URL kullanmak için zorunlu.

        Returns:
            str: Replicate'in erişebileceği ses dosyası URL'i
        """
        file_obj = io.BytesIO(audio_bytes)
        uploaded = self.client.files.create(file_obj, filename=filename)
        url = uploaded.urls.get("get") if hasattr(uploaded, "urls") else str(uploaded)
        log.info(f"Ses Replicate storage'a yüklendi: {str(url)[:80]}")
        return str(url)

    async def async_upload_audio(self, audio_bytes: bytes, filename: str = "audio.mp3") -> str:
        """Async wrapper — event loop'u bloke etmez."""
        import asyncio as _asyncio
        return await _asyncio.to_thread(self.upload_audio, audio_bytes, filename)

    def merge_video_audio(
        self,
        video_url: str,
        audio_url: str,
        replace_audio: bool = False,
    ) -> str:
        """
        Video ve ses dosyalarını birleştirir.

        Args:
            video_url: Video dosyası URL'i (mp4)
            audio_url: Ses dosyası URL'i (mp3, wav)
            replace_audio: True = videonun orijinal sesini kaldır,
                          False = dış sesi video ambient sesinin üzerine ekle

        Returns:
            str: Birleştirilmiş video URL'i

        Raises:
            Exception: Birleştirme başarısız olursa
        """
        try:
            log.info(
                f"Video+ses birleştirme başlatılıyor: "
                f"replace_audio={replace_audio}"
            )

            prediction = self.client.predictions.create(
                version="8c3d57c9c9a1aaa05feabafbcd2dff9f68a5cb394e54ec020c1c2dcc42bde109",
                input={
                    "video_file": video_url,
                    "audio_file": audio_url,
                    "replace_audio": replace_audio,
                    "duration_mode": "video",
                },
            )

            log.info(f"Replicate prediction oluşturuldu: {prediction.id}")

            # Polling
            for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
                prediction.reload()

                if prediction.status == "succeeded":
                    output_url = prediction.output
                    if output_url is None:
                        raise RuntimeError(f"Replicate succeeded ama output None: {prediction.id}")
                    if isinstance(output_url, list):
                        output_url = output_url[0] if output_url else None
                    if output_url is None:
                        raise RuntimeError(f"Replicate succeeded ama output boş liste: {prediction.id}")
                    # Replicate SDK v1.x FileOutput objesi dönebilir — str cast
                    output_url = str(output_url)
                    # URL validasyonu
                    if not output_url.startswith("http"):
                        raise RuntimeError(f"Replicate geçersiz output URL: {output_url[:100]}")
                    log.info(
                        f"Video+ses birleştirme tamamlandı: {prediction.id} "
                        f"({attempt} deneme)"
                    )
                    return output_url

                if prediction.status == "failed":
                    error = prediction.error or "Bilinmeyen hata"
                    log.error(f"Replicate başarısız: {prediction.id} — {error}")
                    raise RuntimeError(f"Replicate merge başarısız: {error}")

                if prediction.status == "canceled":
                    raise RuntimeError("Replicate görev iptal edildi")

                log.info(
                    f"Replicate polling [{attempt}/{MAX_POLL_ATTEMPTS}]: "
                    f"status={prediction.status}"
                )
                time.sleep(POLL_INTERVAL_SECONDS)

            raise TimeoutError(
                f"Replicate timeout: {prediction.id} — "
                f"{MAX_POLL_ATTEMPTS} deneme aşıldı"
            )

        except (RuntimeError, TimeoutError):
            raise
        except Exception:
            log.error("Replicate birleştirme genel hatası", exc_info=True)
            raise

    async def async_merge_video_audio(
        self,
        video_url: str,
        audio_url: str,
        replace_audio: bool = False,
    ) -> str:
        """
        Video ve ses dosyalarını async olarak birleştirir.
        
        time.sleep() yerine asyncio.sleep() kullanır →
        event loop'u BLOKE ETMEZ, thread pool tüketmez.
        
        Production pipeline bu metodu doğrudan (await ile) çağırmalı.
        asyncio.to_thread() ile sarmalamanıza GEREK YOKTUR.

        Returns:
            str: Birleştirilmiş video URL'i
        """
        import asyncio as _asyncio

        try:
            log.info(
                f"Async video+ses birleştirme başlatılıyor: "
                f"replace_audio={replace_audio}"
            )

            # prediction oluşturma kısa süreli — thread'de çalıştır
            prediction = await _asyncio.to_thread(
                self.client.predictions.create,
                version="8c3d57c9c9a1aaa05feabafbcd2dff9f68a5cb394e54ec020c1c2dcc42bde109",
                input={
                    "video_file": video_url,
                    "audio_file": audio_url,
                    "replace_audio": replace_audio,
                    "duration_mode": "video",
                },
            )

            log.info(f"Replicate prediction oluşturuldu: {prediction.id}")

            # Async Polling
            for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
                # reload() kısa süreli HTTP isteği — thread'de çalıştır
                await _asyncio.to_thread(prediction.reload)

                if prediction.status == "succeeded":
                    output_url = prediction.output
                    if output_url is None:
                        raise RuntimeError(f"Replicate succeeded ama output None: {prediction.id}")
                    if isinstance(output_url, list):
                        output_url = output_url[0] if output_url else None
                    if output_url is None:
                        raise RuntimeError(f"Replicate succeeded ama output boş liste: {prediction.id}")
                    output_url = str(output_url)
                    if not output_url.startswith("http"):
                        raise RuntimeError(f"Replicate geçersiz output URL: {output_url[:100]}")
                    log.info(
                        f"Video+ses birleştirme tamamlandı: {prediction.id} "
                        f"({attempt} deneme)"
                    )
                    return output_url

                if prediction.status == "failed":
                    error = prediction.error or "Bilinmeyen hata"
                    log.error(f"Replicate başarısız: {prediction.id} — {error}")
                    raise RuntimeError(f"Replicate merge başarısız: {error}")

                if prediction.status == "canceled":
                    raise RuntimeError("Replicate görev iptal edildi")

                log.info(
                    f"Replicate polling [{attempt}/{MAX_POLL_ATTEMPTS}]: "
                    f"status={prediction.status}"
                )
                # ✅ asyncio.sleep — event loop'u bloke etmez
                await _asyncio.sleep(POLL_INTERVAL_SECONDS)

            raise TimeoutError(
                f"Replicate timeout: {prediction.id} — "
                f"{MAX_POLL_ATTEMPTS} deneme aşıldı"
            )

        except (RuntimeError, TimeoutError):
            raise
        except Exception:
            log.error("Replicate async birleştirme genel hatası", exc_info=True)
            raise

    def get_prediction_status(self, prediction_id: str) -> dict:
        """
        Mevcut prediction durumunu sorgular.

        Args:
            prediction_id: Prediction ID

        Returns:
            dict: {"status": "...", "output": "...", "error": "..."}
        """
        try:
            prediction = self.client.predictions.get(prediction_id)
            return {
                "status": prediction.status,
                "output": prediction.output,
                "error": prediction.error,
            }
        except Exception:
            log.error(f"Prediction sorgulama hatası: {prediction_id}", exc_info=True)
            return {"status": "error", "output": None, "error": "Sorgulama başarısız"}

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔗 VIDEO CONCAT — Multi-Scene Birleştirme
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Model: lucataco/video-merge
    # UGC pipeline oturumundan (23 Nisan 2026) öğrenilen model ve format.
    # Input: pipe-separated video URL'leri (video1|video2|video3)

    VIDEO_MERGE_VERSION = "14273448a57117b5d424410e2e79700ecde6cc7d60bf522a769b9c7cf989eba7"

    def concat_videos(self, video_urls: list[str]) -> str:
        """
        Birden fazla video dosyasını sırayla birleştirir (concat).

        Args:
            video_urls: Video URL'leri listesi (en az 2, max 10)

        Returns:
            str: Birleştirilmiş video URL'i

        Raises:
            ValueError: 2'den az video verilirse
            RuntimeError: Birleştirme başarısız olursa
        """
        if len(video_urls) < 2:
            raise ValueError(f"Concat için en az 2 video gerekli, {len(video_urls)} verildi")

        log.info(f"Video concat başlatılıyor: {len(video_urls)} video")

        try:
            prediction = self.client.predictions.create(
                version=self.VIDEO_MERGE_VERSION,
                input={"video_files": video_urls},
            )
            log.info(f"Concat prediction oluşturuldu: {prediction.id}")

            for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
                prediction.reload()

                if prediction.status == "succeeded":
                    output_url = prediction.output
                    if isinstance(output_url, list):
                        output_url = output_url[0] if output_url else None
                    output_url = str(output_url) if output_url else None
                    if not output_url or not output_url.startswith("http"):
                        raise RuntimeError(f"Concat geçersiz output: {output_url}")
                    log.info(f"Video concat tamamlandı: {prediction.id} ({attempt} deneme)")
                    return output_url

                if prediction.status in ("failed", "canceled"):
                    error = prediction.error or "Bilinmeyen hata"
                    raise RuntimeError(f"Video concat başarısız: {error}")

                log.info(f"Concat polling [{attempt}/{MAX_POLL_ATTEMPTS}]: status={prediction.status}")
                time.sleep(POLL_INTERVAL_SECONDS)

            raise TimeoutError(f"Concat timeout: {prediction.id}")

        except (RuntimeError, TimeoutError, ValueError):
            raise
        except Exception:
            log.error("Video concat genel hatası", exc_info=True)
            raise

    async def async_concat_videos(self, video_urls: list[str]) -> str:
        """
        Birden fazla video dosyasını async olarak birleştirir.
        asyncio.sleep() kullanır → event loop'u bloke etmez.

        Args:
            video_urls: Video URL'leri listesi (en az 2)

        Returns:
            str: Birleştirilmiş video URL'i
        """
        import asyncio as _asyncio

        if len(video_urls) < 2:
            raise ValueError(f"Concat için en az 2 video gerekli, {len(video_urls)} verildi")

        log.info(f"Async video concat başlatılıyor: {len(video_urls)} video")

        try:
            prediction = await _asyncio.to_thread(
                self.client.predictions.create,
                version=self.VIDEO_MERGE_VERSION,
                input={"video_files": video_urls},
            )
            log.info(f"Concat prediction oluşturuldu: {prediction.id}")

            for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
                await _asyncio.to_thread(prediction.reload)

                if prediction.status == "succeeded":
                    output_url = prediction.output
                    if isinstance(output_url, list):
                        output_url = output_url[0] if output_url else None
                    output_url = str(output_url) if output_url else None
                    if not output_url or not output_url.startswith("http"):
                        raise RuntimeError(f"Concat geçersiz output: {output_url}")
                    log.info(f"Async concat tamamlandı: {prediction.id} ({attempt} deneme)")
                    return output_url

                if prediction.status in ("failed", "canceled"):
                    error = prediction.error or "Bilinmeyen hata"
                    raise RuntimeError(f"Video concat başarısız: {error}")

                log.info(f"Concat polling [{attempt}/{MAX_POLL_ATTEMPTS}]: status={prediction.status}")
                await _asyncio.sleep(POLL_INTERVAL_SECONDS)

            raise TimeoutError(f"Concat timeout: {prediction.id}")

        except (RuntimeError, TimeoutError, ValueError):
            raise
        except Exception:
            log.error("Async video concat genel hatası", exc_info=True)
            raise
