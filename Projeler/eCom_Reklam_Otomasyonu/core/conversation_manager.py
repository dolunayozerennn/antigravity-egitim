from __future__ import annotations

"""
Conversation Manager — Deterministik URL-Tabanlı Akış
========================================================
Telegram bot ile kullanıcı arasındaki konuşma akışını yönetir.

Basitleştirilmiş state machine (sohbet tabanlı bilgi toplama KALDIRILDI):
IDLE → URL_PROCESSING → RESEARCHING → SCENARIO_APPROVAL → PRODUCING → DELIVERED

Kullanıcıdan sadece ürün URL'i alınır. Geri kalan her şey otomatik:
- URLDataExtractor ile ürün verisi + görseller
- ScenarioEngine ile senaryo
- ProductionPipeline ile video üretimi

v3.0 — Deterministik pipeline: sohbet yok, soru yok, tek giriş noktası: URL
"""

import threading
from enum import Enum, auto

from logger import get_logger

log = get_logger("conversation_manager")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 CONVERSATION STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConversationState(Enum):
    IDLE = auto()
    URL_PROCESSING = auto()        # URL alındı, veri çıkarılıyor
    RESEARCHING = auto()           # Marka/ürün araştırma + senaryo üretimi
    SCENARIO_APPROVAL = auto()     # Senaryo onayı bekleniyor
    PRODUCING = auto()             # Video üretim aşaması
    DELIVERED = auto()             # Teslim edildi


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Metin tabanlı onay kelime listeleri
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

APPROVAL_KEYWORDS = [
    "onayla", "onaylıyorum", "tamam", "evet", "başla",
    "kabul", "approve", "yes", "go", "devam",
]
CANCEL_KEYWORDS = [
    "iptal", "vazgeç", "cancel", "hayır", "yok", "dur",
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🗂️ USER SESSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class UserSession:
    """Tek bir kullanıcının konuşma durumunu tutar."""

    def __init__(self, user_id: int, user_name: str = ""):
        self.user_id = user_id
        self.user_name = user_name
        self.state = ConversationState.IDLE

        # URLDataExtractor'dan gelen yapısal veri
        self.collected_data: dict = {}

        # Senaryo ve üretim sonuçları
        self.scenario: dict | None = None
        self.production_result: dict | None = None

        # İşlenen URL
        self.current_url: str | None = None

        # Bellek yönetimi
        import time as _time
        self._last_activity: float = _time.time()

    def reset(self):
        """Konuşmayı sıfırla — yeni video için hazırla."""
        self.state = ConversationState.IDLE
        self.collected_data = {}
        self.scenario = None
        self.production_result = None
        self.current_url = None
        import time as _time
        self._last_activity = _time.time()

    def set_extracted_data(self, data: dict):
        """URLDataExtractor'dan gelen veriyi kaydet."""
        self.collected_data = data
        import time as _time
        self._last_activity = _time.time()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🤖 CONVERSATION MANAGER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConversationManager:
    """
    Deterministik URL-tabanlı konuşma yöneticisi.

    Eski sohbet tabanlı bilgi toplama kaldırıldı.
    Tek giriş noktası: ürün URL'i.
    """

    def __init__(self, openai_service=None):
        """
        Args:
            openai_service: Geriye uyumluluk için tutuldu, artık
                           ConversationManager tarafından doğrudan kullanılmıyor.
                           (URLDataExtractor kendi OpenAI instance'ını kullanır)
        """
        self.openai = openai_service
        self.sessions: dict[int, UserSession] = {}
        self._lock = threading.Lock()

    def get_session(self, user_id: int, user_name: str = "") -> UserSession:
        """Kullanıcı session'ını getir veya oluştur. Thread-safe."""
        with self._lock:
            if user_id not in self.sessions:
                self.sessions[user_id] = UserSession(user_id, user_name)
            session = self.sessions[user_id]
            if user_name:
                session.user_name = user_name
            return session

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STATE: IDLE → URL_PROCESSING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def handle_start(self, user_id: int, user_name: str = "") -> str:
        """
        /start komutu → sohbeti başlat.

        Returns:
            str: Karşılama mesajı
        """
        session = self.get_session(user_id, user_name)
        session.reset()

        welcome = (
            "🎬 **eCom Reklam Otomasyonu'na hoş geldin!**\n\n"
            "Profesyonel ürün reklam videoları üretmek için buradayım.\n\n"
            "Bana sadece **ürünün web sitesi linkini** gönder — "
            "geri kalan her şeyi (ürün bilgileri, görseller, konsept, "
            "dış ses, video) ben otomatik hallediyorum! 🚀\n\n"
            "📎 _Örnek: https://www.marka.com/urun-adi_"
        )

        log.info(f"Yeni sohbet başlatıldı: user={user_id} ({user_name})")
        return welcome

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STATE: CHATTING (URL Algılama)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def handle_text_message(self, user_id: int, text: str, user_name: str = "") -> dict:
        """
        Metin mesajını işle — URL ara, uygun state geçişi yap.

        Returns:
            dict: {
                "reply": str,
                "state": ConversationState,
                "has_url": bool,           # URL bulundu mu
                "url": str | None,         # Bulunan URL
                "action": str | None,      # "approve" / "cancel" (SCENARIO_APPROVAL'da)
            }
        """
        session = self.get_session(user_id, user_name)

        # ── State: IDLE → otomatik başlat ──
        if session.state == ConversationState.IDLE:
            welcome = self.handle_start(user_id, user_name)

            # İlk mesajda URL var mı kontrol et
            from core.url_data_extractor import URLDataExtractor
            url = URLDataExtractor.extract_url_from_text(text)

            if url:
                session.current_url = url
                session.state = ConversationState.URL_PROCESSING
                return {
                    "reply": (
                        f"{welcome}\n\n"
                        f"🔗 URL algılandı! Ürün bilgileri çıkarılıyor...\n"
                        f"_{url[:60]}{'...' if len(url) > 60 else ''}_"
                    ),
                    "state": session.state,
                    "has_url": True,
                    "url": url,
                    "action": None,
                }

            return {
                "reply": welcome,
                "state": ConversationState.IDLE,
                "has_url": False,
                "url": None,
                "action": None,
            }

        # ── State: SCENARIO_APPROVAL → metin tabanlı onay/iptal ──
        if session.state == ConversationState.SCENARIO_APPROVAL:
            return self._handle_scenario_text_response(session, text)

        # ── State: URL_PROCESSING / RESEARCHING / PRODUCING → işlem devam ediyor ──
        if session.state in (
            ConversationState.URL_PROCESSING,
            ConversationState.RESEARCHING,
            ConversationState.PRODUCING,
        ):
            return {
                "reply": "⏳ Şu an bir işlem devam ediyor. Lütfen bekle.",
                "state": session.state,
                "has_url": False,
                "url": None,
                "action": None,
            }

        # ── State: DELIVERED → yeni video için /start veya yeni URL ──
        if session.state == ConversationState.DELIVERED:
            # Delivered sonrası yeni URL gelirse otomatik yeniden başlat
            from core.url_data_extractor import URLDataExtractor
            url = URLDataExtractor.extract_url_from_text(text)

            if url:
                session.reset()
                session.current_url = url
                session.state = ConversationState.URL_PROCESSING
                return {
                    "reply": (
                        "🔗 Yeni URL algılandı! Ürün bilgileri çıkarılıyor...\n"
                        f"_{url[:60]}{'...' if len(url) > 60 else ''}_"
                    ),
                    "state": session.state,
                    "has_url": True,
                    "url": url,
                    "action": None,
                }

            return {
                "reply": (
                    "✅ Son video teslim edildi.\n\n"
                    "Yeni bir video için **ürün linkini** gönder veya /start yaz!"
                ),
                "state": session.state,
                "has_url": False,
                "url": None,
                "action": None,
            }

        # ── Herhangi bir state'de URL algıla ──
        from core.url_data_extractor import URLDataExtractor
        url = URLDataExtractor.extract_url_from_text(text)

        if url:
            session.current_url = url
            session.state = ConversationState.URL_PROCESSING
            return {
                "reply": (
                    "🔗 URL algılandı! Ürün bilgileri çıkarılıyor...\n"
                    f"_{url[:60]}{'...' if len(url) > 60 else ''}_"
                ),
                "state": session.state,
                "has_url": True,
                "url": url,
                "action": None,
            }

        # URL bulunamadı — kullanıcıyı yönlendir
        return {
            "reply": (
                "📎 Lütfen bir **ürün web sitesi linki** gönder.\n\n"
                "_Örnek: https://www.marka.com/urun-adi_\n\n"
                "Link göndermen yeterli — ürün bilgileri, görseller ve "
                "reklam konsepti otomatik çıkarılacak!"
            ),
            "state": session.state,
            "has_url": False,
            "url": None,
            "action": None,
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STATE: SCENARIO_APPROVAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _handle_scenario_text_response(self, session: UserSession, text: str) -> dict:
        """
        SCENARIO_APPROVAL state'inde metin mesajlarını işle.
        "Onaylıyorum" / "İptal" yazabilir.
        """
        lower = text.lower().strip()

        if any(w in lower for w in APPROVAL_KEYWORDS):
            log.info(f"Metin tabanlı senaryo onayı: user={session.user_id}")
            return {
                "reply": None,  # main.py kendi mesajını gönderecek
                "state": ConversationState.PRODUCING,
                "has_url": False,
                "url": None,
                "action": "approve",
            }
        elif any(w in lower for w in CANCEL_KEYWORDS):
            session.reset()
            log.info(f"Metin tabanlı senaryo iptali: user={session.user_id}")
            return {
                "reply": (
                    "❌ İptal edildi.\n\n"
                    "Yeni bir video için **ürün linkini** gönder veya /start yaz."
                ),
                "state": session.state,
                "has_url": False,
                "url": None,
                "action": "cancel",
            }
        else:
            return {
                "reply": (
                    "📋 Senaryo onayı bekliyor. Lütfen:\n"
                    "• **Onayla** / **Tamam** → Üretim başlar\n"
                    "• **İptal** / **Vazgeç** → İptal edilir\n\n"
                    "Ya da yukarıdaki butonları kullanabilirsin."
                ),
                "state": session.state,
                "has_url": False,
                "url": None,
                "action": None,
            }

    def handle_scenario_response(self, user_id: int, action: str) -> dict:
        """
        Senaryo onay/iptal yanıtını işle (inline butonlardan).

        Args:
            action: "approve" veya "cancel"

        Returns:
            dict: {"action": str, "state": ConversationState, "reply": str | None}
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
                "reply": (
                    "❌ İptal edildi.\n\n"
                    "Yeni bir video için **ürün linkini** gönder veya /start yaz."
                ),
            }

        return {"action": "unknown", "state": session.state}

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STATE GEÇİŞ METODLARİ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def mark_url_processing(self, user_id: int):
        """URL işleniyor state'ine geç."""
        session = self.get_session(user_id)
        session.state = ConversationState.URL_PROCESSING

    def mark_researching(self, user_id: int):
        """Araştırma aşamasına geç."""
        session = self.get_session(user_id)
        session.state = ConversationState.RESEARCHING

    def mark_scenario_approval(self, user_id: int):
        """Senaryo onayı bekleniyor."""
        session = self.get_session(user_id)
        session.state = ConversationState.SCENARIO_APPROVAL

    def mark_producing(self, user_id: int):
        """Video üretim aşamasına geç."""
        session = self.get_session(user_id)
        session.state = ConversationState.PRODUCING

    def mark_delivered(self, user_id: int):
        """Video teslim edildi — state'i güncelle."""
        session = self.get_session(user_id)
        session.state = ConversationState.DELIVERED
