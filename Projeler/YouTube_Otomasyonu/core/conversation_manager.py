"""
Conversation Manager — Botun beyni.
GPT-4.1 ile kullanıcı mesajlarını analiz eder, video üretim bilgilerini toplar,
hazır olunca pipeline'ı tetikler.
"""
import json
import logging
from dataclasses import dataclass, field, asdict
from openai import OpenAI
from config import settings

log = logging.getLogger("ConversationManager")

# ── Model bilgileri ──
MODEL_INFO = {
    "seedance-2": {
        "display": "Seedance 2.0",
        "provider": "ByteDance",
        "quality": "720p",
        "duration_range": "4-15s",
        "price": "💰 Uygun",
        "strengths": "Kamera kontrolü, native ses, hızlı üretim",
    },
    "veo3.1": {
        "display": "Veo 3.1",
        "provider": "Google DeepMind",
        "quality": "1080p",
        "duration_range": "Değişken",
        "price": "💰💰💰 Premium (~4x)",
        "strengths": "Sinematik kalite, insan yüzlerinde üstün, senkron ses",
    },
}

SYSTEM_PROMPT = """Sen Dolunay'ın YouTube video üretim asistanısın. Telegram üzerinden sohbet ediyorsun.

GÖREV:
Kullanıcıdan video fikri al, gerekli bilgileri topla ve üretim için hazır hale getir.

ENERJİ-VERİMLİ SOHBET PRENSİPLERİ:
- Maksimum 2 turda bilgi toplamayı bitir. Gereksiz soru SORMA.
- Kullanıcı konu belirttiyse ve net ise → hemen özet sun (confirm).
- Opsiyonel alanlar (ses, format, model) için SORU SORMA — default'ları kullan, özette göster.
- Sadece konu belirsizse ek soru sor.

KURALLAR:
1. Samimi, kısa ve Türkçe konuş. Emoji kullan ama abartma.
2. Kullanıcı video fikri söylediğinde, çıkar:
   - Konu/konsept (ZORUNLU — tek zorunlu bilgi)
   - Model tercihi → Belirtmezse SEN SEÇ (sinematik/insan yüzü=veo3.1, diğerleri=seedance-2)
   - Klip sayısı → Belirtmezse 1 (Shorts)
   - Dikey/yatay → Belirtmezse dikey
   - Ses → Belirtmezse evet
3. Eğer kullanıcının mesajı video talebi DEĞİLSE → normal sohbet et.
4. Tüm bilgiler toplandığında → bir özet sun ve onay iste (action=confirm).
5. Kullanıcı "evet/başla/onay/tamam/onayla" derse → HEMEN action=start_pipeline döndür.
   ⚠️ DİKKAT: Onay aldıktan sonra ASLA ek soru sorma, tereddüt etme. Direkt start_pipeline.
6. Kullanıcı "hayır/değiştir" derse → action=ask ile ne değiştirmek istediğini sor.

MODEL SEÇİM MANTIGI (kullanıcı belirtmezse):
- Doğa, hayvan, manzara, soyut, atmosferik → seedance-2 (hızlı, uygun fiyat)
- İnsan yüzü gereken, sinematik, filmsel, dramatik → veo3.1 (premium)
- Kullanıcı açıkça "Seedance/Veo" derse → onu kullan

OUTPUT FORMAT (KESİNLİKLE JSON):
{"action": "ask", "reply": "...", "config": null}
{"action": "confirm", "reply": "Özet ve onay mesajı", "config": {"topic": "...", "model": "seedance-2", "clip_count": 1, "orientation": "portrait", "audio": true, "youtube_title": "...", "youtube_description": "..."}}
{"action": "start_pipeline", "reply": "Üretim başlıyor mesajı", "config": {aynı config}}
{"action": "chat", "reply": "Normal sohbet yanıtı", "config": null}

ÖNEMLİ:
- orientation: "portrait" = 9:16 (dikey), "landscape" = 16:9 (yatay)
- model: SADECE "seedance-2" veya "veo3.1" (başka değer YAZMA)
- youtube_title: Kısa, çekici, İNGİLİZCE başlık (max 60 karakter)
- youtube_description: 1-3 cümle İngilizce açıklama
- Yanıtın her zaman geçerli JSON olmalı, asla düz metin döndürme.
"""


@dataclass
class ConversationState:
    """Her kullanıcı için sohbet durumu."""
    user_id: int
    messages: list = field(default_factory=list)
    topic: str | None = None
    model: str | None = None
    clip_count: int = 1
    orientation: str = "portrait"
    audio: bool = True
    pipeline_running: bool = False


class ConversationManager:
    """GPT-4.1 ile kullanıcı mesajlarını parse eder ve pipeline'ı yönetir."""

    def __init__(self):
        self._states: dict[int, ConversationState] = {}
        self._client = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def get_state(self, user_id: int) -> ConversationState:
        if user_id not in self._states:
            self._states[user_id] = ConversationState(user_id=user_id)
        return self._states[user_id]

    def reset_state(self, user_id: int):
        """Konuşma durumunu sıfırla (yeni video üretimi için)."""
        if user_id in self._states:
            del self._states[user_id]

    async def process_message(self, user_id: int, text: str) -> dict:
        """
        Kullanıcı mesajını GPT-4.1 ile analiz eder.

        Returns:
            dict: {
                "action": "ask" | "confirm" | "start_pipeline" | "chat",
                "reply": "Bot'un Türkçe yanıtı",
                "config": {...} | None
            }
        """
        state = self.get_state(user_id)

        if state.pipeline_running:
            return {
                "action": "chat",
                "reply": "⏳ Şu an bir video üretimi devam ediyor. Tamamlanınca yeni bir talep gönderebilirsin!",
                "config": None
            }

        # Mesajı sohbet geçmişine ekle
        state.messages.append({"role": "user", "content": text})

        # GPT'ye gönder
        try:
            result = await self._call_gpt(state)
        except Exception as e:
            log.error(f"GPT çağrısı başarısız: {e}", exc_info=True)
            return {
                "action": "chat",
                "reply": "🤖 Bir hata oluştu, tekrar dener misin?",
                "config": None
            }

        # GPT yanıtını geçmişe ekle
        state.messages.append({"role": "assistant", "content": json.dumps(result, ensure_ascii=False)})

        # State güncelle
        if result.get("config"):
            cfg = result["config"]
            state.topic = cfg.get("topic", state.topic)
            state.model = cfg.get("model", state.model)
            state.clip_count = cfg.get("clip_count", state.clip_count)
            state.orientation = cfg.get("orientation", state.orientation)
            state.audio = cfg.get("audio", state.audio)

        return result

    async def process_voice_transcription(self, user_id: int, audio_bytes: bytes) -> dict:
        """Whisper ile sesli mesajı transkript eder, sonra process_message'a verir."""
        try:
            client = self._get_client()
            import io
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "voice.ogg"

            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="tr"
            )
            transcribed_text = transcript.text
            log.info(f"🎤 Sesli mesaj transkript: '{transcribed_text[:80]}...'")

            # Transkript edilen metni normal mesaj olarak işle
            return await self.process_message(user_id, transcribed_text)

        except Exception as e:
            log.error(f"Whisper transkript hatası: {e}", exc_info=True)
            return {
                "action": "chat",
                "reply": "🎤 Sesli mesajını anlayamadım, tekrar gönderir misin?",
                "config": None
            }

    async def _call_gpt(self, state: ConversationState) -> dict:
        """GPT-4.1'i çağır ve yanıtı parse et."""
        import asyncio

        client = self._get_client()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *state.messages
        ]

        # Sync çağrıyı thread'de çalıştır
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4.1",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)

        # Zorunlu alanları doğrula
        if "action" not in result or "reply" not in result:
            log.warning(f"GPT yanıtında zorunlu alan eksik: {raw}")
            return {"action": "chat", "reply": raw, "config": None}

        return result
