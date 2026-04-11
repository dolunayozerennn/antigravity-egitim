"""
Replicate Service — Video + Ses Birleştirme
=============================================
Replicate API ile video ve ses dosyalarını birleştirir.
Model: lucataco/video-audio-merge
Cloud-based — Railway'de FFmpeg kurulumu gereksiz.
"""

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
                model="lucataco/video-audio-merge",
                input={
                    "video": video_url,
                    "audio": audio_url,
                    "replace_audio": replace_audio,
                },
            )

            log.info(f"Replicate prediction oluşturuldu: {prediction.id}")

            # Polling
            for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
                prediction.reload()

                if prediction.status == "succeeded":
                    output_url = prediction.output
                    if isinstance(output_url, list):
                        output_url = output_url[0]
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
