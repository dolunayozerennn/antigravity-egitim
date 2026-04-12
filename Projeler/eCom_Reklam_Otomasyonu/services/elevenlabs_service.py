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
from utils.retry import retry_api_call

log = get_logger("elevenlabs_service")

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
REQUEST_TIMEOUT = 60  # TTS uzun sürebilir

# Önerilen ses ID'leri (ElevenLabs varsayılan sesler — API'den doğrulanmış)
DEFAULT_VOICES = {
    "Sarah": "EXAVITQu4vr4xnSDxMaL",        # Kadın, olgun, güven verici — reklam dış sesi
    "Charlie": "IKne3meq5aSn9XLyUdCD",       # Erkek, derin, enerjik
    "Roger": "CwhRBWXzGAHq8TQ4Fs17",         # Erkek, rahat, doğal
    "Laura": "FGY2WhTYpPnrIDTdsKH5",         # Kadın, enerjik
    "George": "JBFqnCBsd6RMkjVDRZzb",        # Erkek, sıcak hikaye anlatıcısı
    "Daniel": "onwK4e9ZLuTAKqWW03F9",        # Erkek, spiker
    "Liam": "TX3LPaxmHKxFdv7VOQHJ",          # Erkek, genç
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
        voice_name: str = "Sarah",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.4,
        output_format: str = "mp3_44100_128",
    ) -> bytes:
        """
        Metin → ses dosyası üretir.

        Args:
            text: Seslendirilecek metin (Türkçe destekli)
            voice_name: Ses adı (Sarah, Charlie, Roger, Laura, George, Daniel, Liam)
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
            # Fallback: isim içinde geçiyor mu diye kontrol et
            voice_name_lower = voice_name.lower()
            for name, vid in DEFAULT_VOICES.items():
                if name.lower() == voice_name_lower or voice_name_lower in name.lower():
                    voice_id = vid
                    break
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

        return self._call_tts_api(url, payload)

    @retry_api_call(max_retries=2, base_delay=2.0, operation_name="ElevenLabs TTS")
    def _call_tts_api(self, url: str, payload: dict) -> bytes:
        """TTS API çağrısı — retry mekanizmalı."""
        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        audio_bytes = response.content
        if len(audio_bytes) < 100:
            raise RuntimeError("ElevenLabs boş/çok kısa ses döndürdü")
        log.info(
            f"ElevenLabs TTS tamamlandı: "
            f"{len(audio_bytes)} bytes"
        )
        return audio_bytes

    def upload_audio_to_hosting(self, audio_bytes: bytes, imgbb_api_key: str = "") -> str:
        """
        Ses dosyasını Replicate'in erişebileceği bir URL'e yükler.

        NOT: Replicate video-audio-merge modeli doğrudan URL bekler.

        Sıralama:
        1. ImgBB (base64 — kalıcı, güvenilir)
        2. tmpfiles.org fallback (24 saat TTL)

        Args:
            audio_bytes: MP3 ses verisi
            imgbb_api_key: ImgBB API anahtarı (pipeline'dan geçilir)

        Returns:
            str: Public erişimli audio URL
        """
        import base64

        # ── 1. ImgBB (birincil — kalıcı hosting) ──
        # ImgBB aslında görsel servisi ama base64 ile her türlü dosya yüklenebilir
        if imgbb_api_key:
            try:
                b64 = base64.b64encode(audio_bytes).decode("utf-8")
                response = requests.post(
                    "https://api.imgbb.com/1/upload",
                    data={
                        "key": imgbb_api_key,
                        "image": b64,
                        "name": "voiceover_audio",
                    },
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()
                if data.get("success"):
                    direct_url = data["data"]["url"]
                    log.info(f"Ses dosyası yüklendi (ImgBB): {direct_url} ({len(audio_bytes)} bytes)")
                    return direct_url
            except Exception:
                log.warning("ImgBB audio upload başarısız, tmpfiles fallback...", exc_info=True)

        # ── 2. tmpfiles.org (fallback) ──
        try:
            response = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": ("voiceover.mp3", audio_bytes, "audio/mpeg")},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            tmp_url = data["data"]["url"]
            direct_url = tmp_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
            log.info(f"Ses dosyası yüklendi (tmpfiles): {direct_url} ({len(audio_bytes)} bytes)")
            return direct_url

        except Exception:
            log.warning("tmpfiles.org başarısız, file.io deneniyor...", exc_info=True)

        # ── 3. file.io (son çare) ──
        try:
            response = requests.post(
                "https://file.io",
                files={"file": ("voiceover.mp3", audio_bytes, "audio/mpeg")},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                direct_url = data["link"]
                log.info(f"Ses dosyası yüklendi (file.io): {direct_url} ({len(audio_bytes)} bytes)")
                return direct_url
            raise ValueError(f"file.io upload failed: {data}")
        except Exception:
            log.error("Ses dosyası hosting hatası (3 yöntem de başarısız)", exc_info=True)
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
