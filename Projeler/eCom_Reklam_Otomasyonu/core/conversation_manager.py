from __future__ import annotations

"""
Conversation Manager — Akıllı Agent + Deterministik Workflow
==============================================================
Telegram bot ile kullanıcı arasındaki konuşma akışını yönetir.

## Mimari Prensip: Agent ≠ Workflow
- WORKFLOW (teknik pipeline): Deterministik — URL → Scrape → Senaryo → Video
- AGENT (kullanıcı etkileşimi): Akıllı, bağlam-farkında, doğal

State machine:
IDLE → URL_PROCESSING → RESEARCHING → SCENARIO_APPROVAL → PRODUCING → DELIVERED

v3.1 — Akıllı agent katmanı: state-aware yanıtlar, bağlam koruması
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

        # Agent context — önceki işlem bilgisi (doğal yanıtlar için)
        self.last_brand: str | None = None
        self.last_product: str | None = None
        self.welcomed: bool = False  # /start karşılaması gösterildi mi

        # Bellek yönetimi
        import time as _time
        self._last_activity: float = _time.time()

    def reset(self):
        """Konuşmayı sıfırla — yeni video için hazırla (context KORUNUR)."""
        # Context'i koru — agent doğal yanıt verebilsin
        self.last_brand = self.collected_data.get("brand_name", self.last_brand)
        self.last_product = self.collected_data.get("product_name", self.last_product)

        self.state = ConversationState.IDLE
        self.collected_data = {}
        self.scenario = None
        self.production_result = None
        self.current_url = None
        import time as _time
        self._last_activity = _time.time()

    def soft_reset_for_new_url(self):
        """Yeni URL geldiğinde — sadece iş verisini temizle, context koru."""
        self.last_brand = self.collected_data.get("brand_name", self.last_brand)
        self.last_product = self.collected_data.get("product_name", self.last_product)

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

    @property
    def active_brand(self) -> str:
        """Aktif veya son bilinen marka adı."""
        return self.collected_data.get("brand_name") or self.last_brand or ""

    @property
    def active_product(self) -> str:
        """Aktif veya son bilinen ürün adı."""
        return self.collected_data.get("product_name") or self.last_product or ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🤖 CONVERSATION MANAGER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConversationManager:
    """
    Akıllı agent + deterministik workflow yöneticisi.

    Agent katmanı: bağlam-farkında, state-aware doğal yanıtlar.
    Workflow katmanı: URL → Scrape → Senaryo → Video (deterministik).
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
    # 🎬 /start KOMUTU
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def handle_start(self, user_id: int, user_name: str = "") -> str:
        """
        /start komutu → sohbeti başlat.

        Returns:
            str: Karşılama mesajı
        """
        session = self.get_session(user_id, user_name)
        session.reset()
        session.welcomed = True

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
    # 🧠 ANA MESAJ HANDLER — AGENT KATMANI
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def handle_text_message(self, user_id: int, text: str, user_name: str = "") -> dict:
        """
        Metin mesajını işle — akıllı agent katmanı.

        Agent, mevcut state'e göre bağlam-farkında yanıt verir.
        Workflow tetikleme (has_url=True) sadece uygun state'lerde yapılır.

        Returns:
            dict: {
                "reply": str,
                "state": ConversationState,
                "has_url": bool,           # URL bulundu mu — pipeline tetiklenir
                "url": str | None,         # Bulunan URL
                "action": str | None,      # "approve" / "cancel" (SCENARIO_APPROVAL'da)
            }
        """
        session = self.get_session(user_id, user_name)

        # URL var mı kontrol et (her state'de lazım)
        from core.url_data_extractor import URLDataExtractor
        url = URLDataExtractor.extract_url_from_text(text)

        # ── State: SCENARIO_APPROVAL → metin tabanlı onay/iptal (öncelikli) ──
        if session.state == ConversationState.SCENARIO_APPROVAL:
            # Senaryo onay state'inde URL gelirse → onay/iptal bekliyoruz uyarısı
            if url:
                return self._reply(session, (
                    "📋 Şu an bir senaryo onayı bekliyor.\n\n"
                    "Önce mevcut senaryoyu **onayla** veya **iptal et**, "
                    "sonra yeni bir link gönderebilirsin."
                ))
            return self._handle_scenario_text_response(session, text)

        # ── State: URL_PROCESSING / RESEARCHING / PRODUCING → işlem devam ediyor ──
        if session.state in (
            ConversationState.URL_PROCESSING,
            ConversationState.RESEARCHING,
            ConversationState.PRODUCING,
        ):
            return self._handle_busy_state(session, text, url)

        # ── State: IDLE → yeni iş kabul et veya sohbet ──
        if session.state == ConversationState.IDLE:
            return self._handle_idle_state(session, text, url, user_id, user_name)

        # ── State: DELIVERED → yeni iş veya teşekkür/sohbet ──
        if session.state == ConversationState.DELIVERED:
            return self._handle_delivered_state(session, text, url)

        # ── Fallback — bilinmeyen state ──
        if url:
            session.soft_reset_for_new_url()
            session.current_url = url
            session.state = ConversationState.URL_PROCESSING
            return self._reply(session, (
                "🔗 URL algılandı! Ürün bilgileri çıkarılıyor...\n"
                f"_{url[:60]}{'...' if len(url) > 60 else ''}_"
            ), has_url=True, url=url)

        return self._reply(session, self._idle_guidance())

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🧠 STATE HANDLER'LAR (Agent Zekası)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _handle_idle_state(self, session: UserSession, text: str,
                           url: str | None, user_id: int, user_name: str) -> dict:
        """IDLE state — yeni iş kabul et veya doğal sohbet."""
        if url:
            # İlk kez geliyorsa karşılama göster
            if not session.welcomed:
                session.welcomed = True
                prefix = (
                    "🎬 **Hoş geldin!** Reklam videonu hazırlıyorum.\n\n"
                )
            else:
                prefix = ""

            session.current_url = url
            session.state = ConversationState.URL_PROCESSING
            return self._reply(session, (
                f"{prefix}"
                f"🔗 URL algılandı! Ürün bilgileri çıkarılıyor...\n"
                f"_{url[:60]}{'...' if len(url) > 60 else ''}_"
            ), has_url=True, url=url)

        # URL yok — ilk mesaj mı yoksa devam eden sohbet mi?
        if not session.welcomed:
            session.welcomed = True
            return self._reply(session, (
                "🎬 **Merhaba!** Ben senin reklam video asistanınım.\n\n"
                "Bana bir **ürün linki** gönder, "
                "ben de o ürün için profesyonel bir reklam videosu hazırlayayım! 🚀\n\n"
                "📎 _Örnek: https://www.marka.com/urun-adi_"
            ))

        # Zaten karşılama gösterildi — doğal bir yönlendirme yap
        return self._reply(session, self._idle_guidance())

    def _handle_busy_state(self, session: UserSession, text: str,
                           url: str | None) -> dict:
        """İşlem devam ederken — bağlam-farkında durum bilgisi."""
        brand = session.active_brand
        product = session.active_product
        product_label = f"**{brand} {product}**" if brand else "ürün"

        state_messages = {
            ConversationState.URL_PROCESSING: (
                f"🔗 Şu an {product_label} için ürün bilgileri çıkarılıyor.\n"
                "Bu birkaç saniye sürer, biraz bekle! ⏳"
            ),
            ConversationState.RESEARCHING: (
                f"🔍 {product_label} için marka araştırması ve senaryo kurgulanıyor.\n"
                "Bu 15-30 saniye sürebilir, az kaldı! ⏳"
            ),
            ConversationState.PRODUCING: (
                f"🎬 {product_label} için video üretimi devam ediyor.\n"
                "Seedance ile video, ElevenLabs ile dış ses hazırlanıyor.\n"
                "Bu 2-5 dakika sürebilir — bitince haber vereceğim! 📹"
            ),
        }

        status_msg = state_messages.get(
            session.state,
            "⏳ Bir işlem devam ediyor, lütfen bekle."
        )

        if url:
            status_msg += (
                "\n\n📎 Yeni bir link gönderdiğini gördüm — "
                "mevcut işlem tamamlandıktan sonra yeni linki gönderebilirsin."
            )

        return self._reply(session, status_msg)

    def _handle_delivered_state(self, session: UserSession, text: str,
                                url: str | None) -> dict:
        """DELIVERED sonrası — yeni iş veya sohbet."""
        if url:
            # Yeni URL → soft reset (context koru) + yeni pipeline
            old_brand = session.active_brand
            session.soft_reset_for_new_url()
            session.current_url = url
            session.state = ConversationState.URL_PROCESSING

            prefix = ""
            if old_brand:
                prefix = f"👍 {old_brand} videosu tamamlandı.\n\n"

            return self._reply(session, (
                f"{prefix}"
                f"🔗 Yeni ürün linki algılandı! Bilgiler çıkarılıyor...\n"
                f"_{url[:60]}{'...' if len(url) > 60 else ''}_"
            ), has_url=True, url=url)

        # URL yok — sohbet/teşekkür/soru
        last_label = ""
        if session.last_brand:
            last_label = f" ({session.last_brand}"
            if session.last_product:
                last_label += f" — {session.last_product}"
            last_label += ")"

        return self._reply(session, (
            f"✅ Son video{last_label} teslim edildi!\n\n"
            "Yeni bir video için **ürün linkini** gönder 🚀"
        ))

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
            brand = session.active_brand
            product_info = f" ({brand})" if brand else ""
            return {
                "reply": (
                    f"📋 Senaryo onayı{product_info} bekliyor. Lütfen:\n"
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
    # 🛠️ YARDIMCI METOTLAR (Agent)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _reply(session: UserSession, reply: str, has_url: bool = False,
               url: str | None = None, action: str | None = None) -> dict:
        """Standart reply dict oluşturur."""
        import time as _time
        session._last_activity = _time.time()
        return {
            "reply": reply,
            "state": session.state,
            "has_url": has_url,
            "url": url,
            "action": action,
        }

    @staticmethod
    def _idle_guidance() -> str:
        """IDLE'da URL olmayan mesajlara kısa, doğal yanıt."""
        return (
            "Bana bir **ürün linki** gönder, "
            "gerisini ben halledeyim! 🚀\n\n"
            "📎 _Örnek: https://www.marka.com/urun-adi_"
        )

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
