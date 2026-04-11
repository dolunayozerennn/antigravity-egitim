from __future__ import annotations

"""
ElevenLabs Service — Doğrudan API Entegrasyonu
================================================
Türkçe dış ses (voiceover) üretimi.
Doğrudan api.elevenlabs.io kullanır (Kie AI proxy DEĞİL).
Plandaki karar: Doğrudan ElevenLabs API ile üretim.
"""

import requests

from logger import get_logger

log = get_logger("elevenlabs_service")

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
REQUEST_TIMEOUT = 60  # TTS uzun sürebilir

# Önerilen ses ID'leri (ElevenLabs varsayılan sesler)
DEFAULT_VOICES = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",     # Kadın, sıcak — reklam dış sesi
    "Charlie": "IKne3meq5aSn9XLyUdCD",     # Erkek, doğal
    "Callum": "N2lVS1w4EtoT3dr4eOWO",      # Erkek, tok
    "Daniel": "onwK4e9ZLuTAKqWW03F9",      # Erkek, spiker
    "Liam": "TX3LPaxmHKxFdv7VOQHJ",        # Erkek, genç
}


class ElevenLabsService:
    """ElevenLabs doğrudan TTS API servisi."""

    def __init__(self, api_key: str, model_id: str = "eleven_multilingual_v2"):
        self.api_key = api_key
        self.model_id = model_id
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def generate_speech(
        self,
        text: str,
        voice_name: str = "Rachel",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.4,
        output_format: str = "mp3_44100_128",
    ) -> bytes:
        """
        Metin → ses dosyası üretir.

        Args:
            text: Seslendirilecek metin (Türkçe destekli)
            voice_name: Ses adı (Rachel, Charlie, Callum, Daniel, Liam)
            stability: Tutarlılık (0.0-1.0)
            similarity_boost: Ses benzerliği (0.0-1.0)
            style: Stil ekstrapolasyonu (0.0-1.0)
            output_format: Çıktı formatı

        Returns:
            bytes: MP3 ses verisi

        Raises:
            ValueError: Geçersiz ses adı
            Exception: API hatası
        """
        voice_id = DEFAULT_VOICES.get(voice_name)
        if not voice_id:
            available = ", ".join(DEFAULT_VOICES.keys())
            raise ValueError(
                f"Geçersiz ses adı: '{voice_name}'. "
                f"Kullanılabilir sesler: {available}"
            )

        url = (
            f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"
            f"?output_format={output_format}"
        )

        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": True,
            },
        }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            audio_bytes = response.content
            log.info(
                f"ElevenLabs TTS tamamlandı: voice={voice_name}, "
                f"{len(text)} char → {len(audio_bytes)} bytes"
            )
            return audio_bytes

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "?"
            log.error(f"ElevenLabs HTTP hatası ({status}): {e}", exc_info=True)
            raise
        except Exception:
            log.error("ElevenLabs TTS genel hatası", exc_info=True)
            raise

    def upload_audio_to_hosting(self, audio_bytes: bytes, imgbb_api_key: str) -> str:
        """
        Ses dosyasını Replicate'in erişebileceği bir URL'e yükler.
        ImgBB görsel destekli olduğundan, bunun yerine geçici bir file
        hosting servisi kullanılır.

        NOT: Replicate video-audio-merge modeli doğrudan URL bekler.
        Bu fonksiyon ses dosyasını geçici hosting'e atar.

        Returns:
            str: Public erişimli audio URL
        """
        # tmpfiles.org üzerinden geçici hosting (24 saat geçerli)
        try:
            response = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": ("voiceover.mp3", audio_bytes, "audio/mpeg")},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            # tmpfiles.org URL formatını doğrudan erişime çevir
            tmp_url = data["data"]["url"]
            # https://tmpfiles.org/12345/file.mp3 → https://tmpfiles.org/dl/12345/file.mp3
            direct_url = tmp_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")

            log.info(f"Ses dosyası yüklendi: {direct_url} ({len(audio_bytes)} bytes)")
            return direct_url

        except Exception:
            log.error("Ses dosyası hosting hatası", exc_info=True)
            raise

    def list_voices(self) -> list[dict]:
        """
        Kullanılabilir sesleri listeler.

        Returns:
            list: Ses bilgisi listesi
        """
        try:
            url = f"{ELEVENLABS_BASE_URL}/voices"
            response = requests.get(
                url,
                headers={"xi-api-key": self.api_key},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            voices = [
                {"name": v["name"], "voice_id": v["voice_id"], "labels": v.get("labels", {})}
                for v in data.get("voices", [])
            ]
            log.info(f"ElevenLabs {len(voices)} ses listelendi")
            return voices
        except Exception:
            log.error("Ses listesi alınamadı", exc_info=True)
            return []

    @staticmethod
    def estimate_duration_seconds(text: str, words_per_second: float = 2.5) -> float:
        """
        Metin uzunluğundan tahmini ses süresini hesaplar.
        Türkçe ortalama: ~2.5 kelime/saniye

        Args:
            text: Ses metni
            words_per_second: Kelime/saniye oranı

        Returns:
            float: Tahmini süre (saniye)
        """
        word_count = len(text.split())
        return word_count / words_per_second
