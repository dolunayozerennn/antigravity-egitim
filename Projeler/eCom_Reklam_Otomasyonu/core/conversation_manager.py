from __future__ import annotations

"""
Conversation Manager — State Machine + Doğal Sohbet
=====================================================
Telegram bot ile kullanıcı arasındaki konuşma akışını yönetir.
6 aşamalı state machine: IDLE → CHATTING → RESEARCHING →
SCENARIO_APPROVAL → PRODUCING → DELIVERED.

GPT-5 Mini ile doğal sohbet — form doldurmak yerine akıllı bilgi çıkarma.
Kullanıcı tek mesajda birden fazla bilgi verebilir; LLM eksik olanları sorar.
"""

import json
from enum import Enum, auto

from logger import get_logger

log = get_logger("conversation_manager")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 CONVERSATION STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConversationState(Enum):
    IDLE = auto()
    CHATTING = auto()         # Bilgi toplama — doğal sohbet
    RESEARCHING = auto()      # Marka/ürün araştırma
    SCENARIO_APPROVAL = auto() # Senaryo onayı bekleniyor
    PRODUCING = auto()        # Video üretim aşaması
    DELIVERED = auto()        # Teslim edildi


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📋 TOPLANAN BİLGİLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUIRED_FIELDS = [
    "brand_name",       # Marka adı
    "product_name",     # Ürün adı/açıklaması
    "product_image",    # Ürün fotoğrafı URL'i
    "ad_concept",       # Reklam konsepti/hikayesi
    "video_duration",   # Video süresi (saniye)
    "aspect_ratio",     # 9:16 (dikey) veya 16:9 (yatay)
    "language",         # Türkçe veya İngilizce
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧠 SYSTEM PROMPT — BİLGİ ÇIKARMA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXTRACTION_SYSTEM_PROMPT = """Sen bir e-ticaret reklam videosu üretim asistanısın. Kullanıcıyla doğal ve samimi bir şekilde sohbet ederek video üretimi için gerekli bilgileri topluyorsun.

## Görevin:
Kullanıcının mesajlarından aşağıdaki bilgileri çıkar. Birden fazla bilgi tek mesajda gelebilir — hepsini yakala.

## Gerekli Bilgiler:
1. **brand_name** — Marka adı (örn: "Nike", "Dyson", "Samsung")
2. **product_name** — Ürün adı/açıklaması (örn: "Air Max 90", "V15 Detect süpürge")
3. **product_image** — Ürün fotoğrafı (**bu alan sadece kullanıcı fotoğraf gönderdiğinde dolar, metin mesajlarında bu alanı "null" bırak**)
4. **ad_concept** — Reklam konsepti/hikayesi (örn: "Spor salonu ortamında enerji dolu sahne")
5. **video_duration** — Video süresi (4-15 saniye arası, varsayılan: 10)
6. **aspect_ratio** — Dikey (9:16 — Reels/TikTok) veya Yatay (16:9 — YouTube) — varsayılan: 9:16
7. **language** — Dil tercihi: "Türkçe" veya "İngilizce" — varsayılan: Türkçe

## Yanıt Formatı:
Her zaman aşağıdaki JSON formatında yanıt ver:

```json
{
  "extracted_fields": {
    "brand_name": "Nike" veya null,
    "product_name": "Air Max 90" veya null,
    "product_image": null,
    "ad_concept": "Spor atmosferi..." veya null,
    "video_duration": 10 veya null,
    "aspect_ratio": "9:16" veya null,
    "language": "Türkçe" veya null
  },
  "reply_to_user": "Kullanıcıya gösterilecek doğal yanıt mesajı",
  "all_collected": false
}
```

## Kurallar:
- Kullanıcıyla HER ZAMAN Türkçe konuş. Samimi, profesyonel ve yardımsever ol.
- Kullanıcı tek mesajda birden fazla bilgi verirse hepsini çıkar.
- Eksik alanları doğal bir şekilde sor — listelemek yerine konuşma akışına entegre et.
- Video süresi sorulurken maliyet bilgisi ver:
  - 10 saniye, 720p: ~$1.25 (image-to-video)
  - 10 saniye, 480p: ~$0.58 (image-to-video)
  - 15 saniye, 720p: ~$3.08 (text-to-video)
- Aspect ratio sorulurken platform önerisi ver (9:16 → Instagram/TikTok, 16:9 → YouTube)
- `all_collected` sadece TÜM alanlar dolduğunda `true` olur (product_image hariç — o fotoğraf ile gelir)
- Konsept sorarken kullanıcıya 2-3 fikir öner (örn: "Beyaz arka plan ürün tanıtımı", "Yaşam tarzı sahnesi", "Dramatik ışık atmosferi")
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🗂️ USER SESSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class UserSession:
    """Tek bir kullanıcının konuşma durumunu tutar."""

    def __init__(self, user_id: int, user_name: str = ""):
        self.user_id = user_id
        self.user_name = user_name
        self.state = ConversationState.IDLE
        self.collected_data: dict = {field: None for field in REQUIRED_FIELDS}
        self.chat_history: list[dict] = []
        self.scenario: dict | None = None       # Üretilen senaryo
        self.notion_page_id: str | None = None  # Notion log page ID
        self.production_result: dict | None = None  # Üretim sonucu

    def reset(self):
        """Konuşmayı sıfırla — yeni video için hazırla."""
        self.state = ConversationState.IDLE
        self.collected_data = {field: None for field in REQUIRED_FIELDS}
        self.chat_history = []
        self.scenario = None
        self.notion_page_id = None
        self.production_result = None

    def update_fields(self, extracted: dict):
        """Çıkarılan bilgilerle mevcut veriyi güncelle. None olanları atla."""
        for field, value in extracted.items():
            if value is not None and field in self.collected_data:
                self.collected_data[field] = value

    def get_missing_fields(self) -> list[str]:
        """Henüz toplanmamış alanları döndür (product_image hariç)."""
        return [
            f for f in REQUIRED_FIELDS
            if f != "product_image" and self.collected_data.get(f) is None
        ]

    def is_complete(self) -> bool:
        """Fotoğraf dahil tüm bilgiler toplandı mı?"""
        return all(
            self.collected_data.get(f) is not None
            for f in REQUIRED_FIELDS
        )

    def has_text_info_complete(self) -> bool:
        """Fotoğraf HARİÇ metin bilgileri tam mı?"""
        return all(
            self.collected_data.get(f) is not None
            for f in REQUIRED_FIELDS
            if f != "product_image"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🤖 CONVERSATION MANAGER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConversationManager:
    """
    State machine + doğal sohbet yöneticisi.

    Servis instance'ları main.py'den enjekte edilir.
    Bu sınıf sadece konuşma mantığına odaklanır.
    """

    def __init__(self, openai_service):
        self.openai = openai_service
        self.sessions: dict[int, UserSession] = {}

    def get_session(self, user_id: int, user_name: str = "") -> UserSession:
        """Kullanıcı session'ını getir veya oluştur."""
        if user_id not in self.sessions:
            self.sessions[user_id] = UserSession(user_id, user_name)
        session = self.sessions[user_id]
        if user_name:
            session.user_name = user_name
        return session

    # ── STATE: IDLE → CHATTING ──

    def handle_start(self, user_id: int, user_name: str = "") -> str:
        """
        /start komutu veya ilk mesaj → sohbeti başlat.

        Returns:
            str: Karşılama mesajı
        """
        session = self.get_session(user_id, user_name)
        session.reset()
        session.state = ConversationState.CHATTING

        welcome = (
            "🎬 **eCom Reklam Otomasyonu'na hoş geldin!**\n\n"
            "Profesyonel ürün reklam videoları üretmek için buradayım. "
            "Seedance 2.0 ile sinematik kalitede videolar, "
            "Türkçe dış sesle birlikte hazırlanıyor.\n\n"
            "📋 Sana birkaç soru soracağım:\n"
            "• Hangi marka ve ürün için video istiyorsun?\n"
            "• Bir ürün fotoğrafın var mı?\n"
            "• Nasıl bir reklam konsepti hayal ediyorsun?\n\n"
            "Hazırsan, **marka adı ve ürün bilgisiyle** başlayabilirsin! 🚀"
        )

        log.info(f"Yeni sohbet başlatıldı: user={user_id} ({user_name})")
        return welcome

    # ── STATE: CHATTING (Bilgi Toplama) ──

    def handle_text_message(self, user_id: int, text: str, user_name: str = "") -> dict:
        """
        Metin mesajını işle — bilgi çıkar, eksik olanları sor.

        Returns:
            dict: {
                "reply": str,               # Kullanıcıya gösterilecek mesaj
                "state": ConversationState,  # Güncel state
                "ready_for_research": bool,  # Araştırmaya geçilecek mi
            }
        """
        session = self.get_session(user_id, user_name)

        # State kontrolü
        if session.state == ConversationState.IDLE:
            return {
                "reply": self.handle_start(user_id, user_name),
                "state": ConversationState.CHATTING,
                "ready_for_research": False,
            }

        if session.state != ConversationState.CHATTING:
            return {
                "reply": "⏳ Şu an bir işlem devam ediyor. Lütfen bekle.",
                "state": session.state,
                "ready_for_research": False,
            }

        # Chat history'e ekle
        session.chat_history.append({"role": "user", "content": text})

        # Mevcut toplanan bilgilerle context oluştur
        context = self._build_context(session)

        # GPT-5 Mini'ye gönder
        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "system", "content": f"Şu ana kadar toplanan bilgiler:\n{context}"},
        ] + session.chat_history[-10:]  # Son 10 mesajı gönder (context window yönetimi)

        try:
            response = self.openai.chat_json(messages, temperature=0.7, max_tokens=1500)
        except Exception:
            log.error("Chat yanıt hatası", exc_info=True)
            return {
                "reply": "⚠️ Bir hata oluştu, tekrar dene.",
                "state": session.state,
                "ready_for_research": False,
            }

        # Çıkarılan bilgileri güncelle
        extracted = response.get("extracted_fields", {})
        session.update_fields(extracted)

        reply = response.get("reply_to_user", "Devam edelim mi?")
        session.chat_history.append({"role": "assistant", "content": reply})

        # Fotoğraf hariç tüm metin bilgiler tam mı?
        ready = session.has_text_info_complete() and session.collected_data.get("product_image") is not None

        log.info(
            f"Bilgi çıkarma: user={user_id}, "
            f"eksik={session.get_missing_fields()}, "
            f"fotoğraf={'✅' if session.collected_data.get('product_image') else '❌'}, "
            f"ready={ready}"
        )

        return {
            "reply": reply,
            "state": session.state,
            "ready_for_research": ready,
        }

    # ── FOTOĞRAF İŞLEME ──

    def handle_photo(self, user_id: int, photo_url: str, user_name: str = "") -> dict:
        """
        Kullanıcının gönderdiği ürün fotoğrafını işle.

        Args:
            photo_url: ImgBB'ye yüklenmiş public URL

        Returns:
            dict: {"reply": str, "state": ..., "ready_for_research": bool}
        """
        session = self.get_session(user_id, user_name)

        if session.state == ConversationState.IDLE:
            return {
                "reply": self.handle_start(user_id, user_name),
                "state": ConversationState.CHATTING,
                "ready_for_research": False,
            }

        session.collected_data["product_image"] = photo_url
        log.info(f"Ürün fotoğrafı alındı: user={user_id}, url={photo_url[:60]}...")

        # Fotoğraf hariç tüm bilgiler tamamsa araştırmaya geç
        if session.has_text_info_complete():
            reply = (
                "📸 **Ürün fotoğrafı alındı!** ✅\n\n"
                "Tüm bilgiler tamam — şimdi marka ve ürün araştırmasına geçiyorum... 🔍"
            )
            return {
                "reply": reply,
                "state": session.state,
                "ready_for_research": True,
            }

        # Henüz eksik alan var
        missing = session.get_missing_fields()
        reply = (
            "📸 **Ürün fotoğrafı alındı!** ✅\n\n"
            f"Birkaç bilgi daha lazım. {self._describe_missing(missing)}"
        )
        return {
            "reply": reply,
            "state": session.state,
            "ready_for_research": False,
        }

    # ── STATE: SCENARIO_APPROVAL ──

    def handle_scenario_response(self, user_id: int, action: str) -> dict:
        """
        Senaryo onay/düzelt/iptal yanıtını işle.

        Args:
            action: "approve", "edit", "cancel"

        Returns:
            dict: {"action": str, "state": ConversationState}
        """
        session = self.get_session(user_id)

        if action == "approve":
            session.state = ConversationState.PRODUCING
            return {"action": "approve", "state": session.state}

        elif action == "cancel":
            session.reset()
            return {
                "action": "cancel",
                "state": session.state,
                "reply": "❌ İptal edildi. Yeni bir video için /start yaz."
            }

        elif action == "edit":
            session.state = ConversationState.CHATTING
            session.scenario = None
            return {
                "action": "edit",
                "state": session.state,
                "reply": (
                    "✏️ Senaryoyu düzenleyelim.\n"
                    "Ne değiştirmek istiyorsun? Konsepti, süreyi, dili veya formatı değiştirebiliriz."
                ),
            }

        return {"action": "unknown", "state": session.state}

    # ── TESLIM ──

    def mark_delivered(self, user_id: int):
        """Video teslim edildi — state'i güncelle."""
        session = self.get_session(user_id)
        session.state = ConversationState.DELIVERED

    def mark_researching(self, user_id: int):
        """Araştırma aşamasına geç."""
        session = self.get_session(user_id)
        session.state = ConversationState.RESEARCHING

    def mark_scenario_approval(self, user_id: int):
        """Senaryo onayı bekleniyor."""
        session = self.get_session(user_id)
        session.state = ConversationState.SCENARIO_APPROVAL

    # ── YARDIMCI METODLAR ──

    def _build_context(self, session: UserSession) -> str:
        """Toplanan bilgileri okunabilir metin haline getir."""
        lines = []
        field_labels = {
            "brand_name": "Marka",
            "product_name": "Ürün",
            "product_image": "Ürün Fotoğrafı",
            "ad_concept": "Reklam Konsepti",
            "video_duration": "Video Süresi",
            "aspect_ratio": "Format",
            "language": "Dil",
        }
        for field in REQUIRED_FIELDS:
            value = session.collected_data.get(field)
            label = field_labels.get(field, field)
            if value is not None:
                lines.append(f"✅ {label}: {value}")
            else:
                lines.append(f"❌ {label}: Henüz belirtilmedi")
        return "\n".join(lines)

    @staticmethod
    def _describe_missing(missing: list[str]) -> str:
        """Eksik alanları kullanıcı dostu şekilde tanımla."""
        descriptions = {
            "brand_name": "marka adı",
            "product_name": "ürün bilgisi",
            "ad_concept": "reklam konsepti",
            "video_duration": "video süresi",
            "aspect_ratio": "video formatı (dikey/yatay)",
            "language": "dil tercihi",
        }
        if not missing:
            return "Tüm bilgiler tamam!"
        human_names = [descriptions.get(f, f) for f in missing]
        if len(human_names) == 1:
            return f"Bir de **{human_names[0]}** bilgisini paylaşır mısın?"
        return "Şunları da öğrenebilir miyim: " + ", ".join(f"**{n}**" for n in human_names) + "?"
