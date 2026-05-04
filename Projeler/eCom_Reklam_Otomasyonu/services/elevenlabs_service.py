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

# Türkçe Professional Voice Clone (PVC / Studio Quality) ses kataloğu
# — Senaryo LLM bu metadata'ya bakarak ürün/tonlama'ya göre dinamik ses seçer.
# Format: voice_name → (voice_id, gender, use_case, age, persona)
TURKISH_VOICE_CATALOG = {
    "Ahu":     ("xyqF3vGMQlPk3e7yA4DI", "kadın",  "conversational",   "orta-yaş", "Doğal, samimi, arkadaş tonu — UGC ideal"),
    "Filiz":   ("PHNT5rJxxIZ4i7JkGLjC", "kadın",  "conversational",   "orta-yaş", "Konuşma tarzı, sıcak — günlük tavsiye tonu"),
    "İrem":    ("uvU9jrgGLWNPeNA4NgNT", "kadın",  "narrative_story",  "orta-yaş", "Profesyonel anlatıcı — bilgi/eğitim/narrative"),
    "Nisa":    ("bj1uMlYGikistcXNmFoh", "kadın",  "entertainment_tv", "genç",     "Enerjik, genç, eğlenceli — Z kuşağı/spor"),
    "Adam":    ("RXCCWbOxP7Hisa63Xsv5", "erkek",  "narrative_story",  "orta-yaş", "Sakin, derin Türkçe erkek — guide/anlatıcı"),
}

# Geriye dönük uyumluluk için düz dict — tüm sesler (Türkçe + İngilizce)
DEFAULT_VOICES = {
    # 🇹🇷 Türkçe Professional Voice Clone (Studio Quality)
    "Ahu":     "xyqF3vGMQlPk3e7yA4DI",
    "Filiz":   "PHNT5rJxxIZ4i7JkGLjC",
    "İrem":    "uvU9jrgGLWNPeNA4NgNT",
    "Nisa":    "bj1uMlYGikistcXNmFoh",
    "Adam":    "RXCCWbOxP7Hisa63Xsv5",
    "Dolunay": "lR8i9ML52TYdcTkZm9sE",       # Kişisel clone
    # 🇬🇧 İngilizce premade (yedek)
    "Brian":   "nPczCjzI2devNBz1zQrb",
    "George":  "JBFqnCBsd6RMkjVDRZzb",
    "Bill":    "pqHfZKP75CvOlQylNhV4",
    "Lily":    "pFZP5JQG7iQjIQuC4Bku",
    "Sarah":   "EXAVITQu4vr4xnSDxMaL",
    "Charlie": "IKne3meq5aSn9XLyUdCD",
    "Laura":   "FGY2WhTYpPnrIDTdsKH5",
    "Daniel":  "onwK4e9ZLuTAKqWW03F9",
    "Liam":    "TX3LPaxmHKxFdv7VOQHJ",
}


class ElevenLabsService:
    """ElevenLabs doğrudan TTS API servisi."""

    def __init__(self, api_key: str, model_id: str = "eleven_v3"):
        self.api_key = api_key
        self.model_id = model_id
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def generate_speech(
        self,
        text: str,
        voice_name: str = "Ahu",
        stability: float = 0.3,
        similarity_boost: float = 0.75,
        style: float = 0.7,
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
            voice_name_lower = (voice_name or "").lower()
            # 1) Exact match (case-insensitive)
            for name, vid in DEFAULT_VOICES.items():
                if name.lower() == voice_name_lower:
                    voice_id = vid
                    break
            # 2) Substring fallback — sadece yeterince uzun stringler için
            #    ("ar" gibi kısa stringler "Sarah"/"Charlie" ile yanlış eşleşmesin)
            if not voice_id and len(voice_name_lower) >= 4:
                for name, vid in DEFAULT_VOICES.items():
                    if voice_name_lower in name.lower():
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

        # Hata durumunda response body'yi logla (debug için kritik)
        if response.status_code != 200:
            try:
                error_body = response.text[:500]
            except Exception:
                error_body = "(okunamadı)"
            log.error(
                f"ElevenLabs API hatası: HTTP {response.status_code} | "
                f"model={payload.get('model_id')} | "
                f"body={error_body}"
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
    def estimate_duration_seconds(text: str, words_per_second: float = 1.7) -> float:
        """
        Metin uzunluğundan TAHMİNİ ses süresi (kararsız — gerçek üretim için
        measure_audio_duration kullan).
        """
        word_count = len(text.split())
        return word_count / words_per_second

    @staticmethod
    def measure_audio_duration(audio_bytes: bytes) -> float:
        """
        Üretilen MP3'ün GERÇEK süresini saniye cinsinden döndür.
        mutagen ile saf-Python — ffmpeg gerekmiyor.

        Args:
            audio_bytes: MP3 ses verisi

        Returns:
            float: Süre (saniye). Ölçüm başarısızsa 0.0.
        """
        import io
        try:
            from mutagen.mp3 import MP3
            mp3 = MP3(io.BytesIO(audio_bytes))
            return float(mp3.info.length)
        except Exception:
            log.warning("MP3 süre ölçümü başarısız", exc_info=True)
            return 0.0
