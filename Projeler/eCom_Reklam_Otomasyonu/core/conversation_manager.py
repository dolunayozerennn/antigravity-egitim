from __future__ import annotations

"""
Conversation Manager — Deterministik Brief Akışı + Üretim Workflow
====================================================================
Telegram bot ile kullanıcı arasındaki konuşma akışını yönetir.

## Mimari Prensip: Brief Akışı = Deterministik State Machine
Eski sürümde brief toplama LLM tool-calling ile yapılıyordu; LLM tek turda birden
fazla `present_choices` üretip butonları eziyor, kullanıcıya butonsuz mesajlar
gönderiyordu. Bu sürümde brief tamamen statik:

IDLE
  → ASKING_FORMAT     (URL gelir, format butonları, lite_extract paralel)
  → ASKING_STYLE      (format seçildi → 3 dinamik tarz LLM ile üretilir)
  → ASKING_CUSTOM_NOTE (tarz seçildi → "Not yaz / Atla" butonları)
  → WAITING_CUSTOM_NOTE_TEXT (kullanıcı serbest metin yazıyor)
  → URL_PROCESSING → RESEARCHING → SCENARIO_APPROVAL → PRODUCING → DELIVERED

LLM SADECE kategoriye göre 3 tarz seçeneği üretmek için kullanılır (single-purpose).
"""

import asyncio
import threading
from enum import Enum, auto
from typing import Optional

from logger import get_logger

log = get_logger("conversation_manager")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 CONVERSATION STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConversationState(Enum):
    IDLE = auto()
    ASKING_FORMAT = auto()              # Format butonları gönderildi, kullanıcı seçim bekleniyor
    ASKING_STYLE = auto()               # Tarz butonları gönderildi
    WAITING_STYLE_TEXT = auto()         # Kullanıcı 'Kendim yazacağım' dedi, tarz metni bekleniyor
    ASKING_CUSTOM_NOTE = auto()         # "Not yaz / Atla" butonları
    WAITING_CUSTOM_NOTE_TEXT = auto()   # Kullanıcı serbest metin yazıyor
    URL_PROCESSING = auto()             # URL alındı, veri çıkarılıyor
    RESEARCHING = auto()                # Marka/ürün araştırma + senaryo üretimi
    SCENARIO_APPROVAL = auto()          # Senaryo onayı bekleniyor
    PRODUCING = auto()                  # Video üretim aşaması
    DELIVERED = auto()                  # Teslim edildi


APPROVAL_KEYWORDS = [
    "onayla", "onaylıyorum", "tamam", "evet", "başla",
    "kabul", "approve", "yes", "go", "devam",
]
CANCEL_KEYWORDS = [
    "iptal", "vazgeç", "cancel", "hayır", "yok", "dur",
]


# Statik buton şablonları
FORMAT_OPTIONS = [
    {"label": "📱 Reels / TikTok (9:16)", "value": "9:16"},
    {"label": "🖥️ YouTube (16:9)", "value": "16:9"},
    {"label": "⬜ Feed Kare (1:1)", "value": "1:1"},
]

DEFAULT_STYLE_OPTIONS = [
    {"label": "🎬 Sinematik Tanıtım", "value": "Sinematik Tanıtım"},
    {"label": "📱 UGC Doğal Anlatım", "value": "UGC Doğal"},
    {"label": "✨ Hikaye Driven", "value": "Hikaye Driven"},
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

        self.collected_data: dict = {}
        self.scenario: dict | None = None
        self.production_result: dict | None = None
        self.current_url: str | None = None

        self.last_brand: str | None = None
        self.last_product: str | None = None
        self.welcomed: bool = False

        self.preferences: dict = {}
        self.pending_url: str | None = None

        # Lite extract (paralel kategori analizi)
        self.product_category: str | None = None
        self.lite_brand: str | None = None
        self.lite_product: str | None = None
        self.lite_extract_task: Optional[asyncio.Task] = None

        # Style options için index → {label, value} eşleşmesi
        # callback_data 64 byte sınırını aşmasın diye style butonları s0/s1/s2 indeksiyle gönderiliyor
        self.pending_style_options: list[dict] = []

        self._lock: Optional[asyncio.Lock] = None

        self.production_task: Optional[asyncio.Task] = None
        self.production_progress_msg_id: Optional[int] = None
        self.production_chat_id: Optional[int] = None

        import time as _time
        self._last_activity: float = _time.time()

    def reset(self):
        """Konuşmayı sıfırla — yeni video için hazırla (context KORUNUR)."""
        self.last_brand = self.collected_data.get("brand_name", self.last_brand)
        self.last_product = self.collected_data.get("product_name", self.last_product)

        self.state = ConversationState.IDLE
        self.collected_data = {}
        self.scenario = None
        self.production_result = None
        self.current_url = None
        self.pending_url = None
        self.preferences = {}
        self.product_category = None
        self.lite_brand = None
        self.lite_product = None
        self.pending_style_options = []
        self.lite_extract_task = None
        self.production_task = None
        self.production_progress_msg_id = None
        self.production_chat_id = None

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
        self.pending_url = None
        self.preferences = {}
        self.product_category = None
        self.lite_brand = None
        self.lite_product = None
        self.pending_style_options = []
        self.lite_extract_task = None
        import time as _time
        self._last_activity = _time.time()

    def set_extracted_data(self, data: dict):
        """URLDataExtractor'dan gelen veriyi kaydet."""
        self.collected_data = data
        import time as _time
        self._last_activity = _time.time()

    @property
    def lock(self) -> asyncio.Lock:
        """Lazy per-session asyncio.Lock."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    @property
    def active_brand(self) -> str:
        return self.collected_data.get("brand_name") or self.last_brand or ""

    @property
    def active_product(self) -> str:
        return self.collected_data.get("product_name") or self.last_product or ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🤖 CONVERSATION MANAGER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConversationManager:
    """
    Brief akışı: deterministik state machine.
    Üretim akışı: deterministik pipeline (mevcut).
    LLM kullanımı: sadece kategoriye göre 3 tarz seçeneği üretmek.
    """

    def __init__(self, openai_service=None):
        self.openai = openai_service
        self.sessions: dict[int, UserSession] = {}
        self._lock = threading.Lock()

    def get_session(self, user_id: int, user_name: str = "") -> UserSession:
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
    # 📨 ANA MESAJ HANDLER (text)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def handle_text_message(self, user_id: int, text: str, user_name: str = "") -> dict:
        """
        Metin mesajını işle.

        Returns:
            dict: {
                "reply": str,
                "state": ConversationState,
                "has_url": bool,
                "url": str | None,
                "action": str | None,
                "buttons": dict | None,   # {"question", "choice_key", "options", "allow_freetext"?}
                "note_buttons": bool,     # True ise main.py "Not yaz / Atla" butonları render eder
            }
        """
        session = self.get_session(user_id, user_name)
        async with session.lock:
            return await self._handle_text_locked(session, text)

    async def _handle_text_locked(self, session: UserSession, text: str) -> dict:
        text = (text or "").strip()

        # 0) WAITING_STYLE_TEXT — kullanıcı kendi tarzını yazıyor → custom_note adımına geç
        if session.state == ConversationState.WAITING_STYLE_TEXT:
            self.set_style(session.user_id, (text or "Özel Tarz")[:80])
            return self._reply(
                session,
                "✅ Tarz alındı.\n\n✍️ **3/3 — Ek Not:** Brief'e ek bir not bırakmak ister misin?\n"
                "_(Örn. 'tone biraz daha eğlenceli', 'rakipler X yapıyor biz farklı olalım')_",
                note_buttons=True,
            )

        # 1) WAITING_CUSTOM_NOTE_TEXT — kullanıcı not yazıyor → pipeline başlat
        if session.state == ConversationState.WAITING_CUSTOM_NOTE_TEXT:
            note = text
            if note:
                session.preferences["custom_note"] = note
                log.info(f"Custom note kaydedildi: user={session.user_id} ({len(note)} char)")
            url = session.pending_url
            if not url:
                session.state = ConversationState.IDLE
                return self._reply(session, "⚠️ İşlenecek URL bulunamadı. Lütfen tekrar gönder.")
            session.pending_url = None
            session.current_url = url
            session.state = ConversationState.URL_PROCESSING
            return self._reply(
                session,
                "✅ Not alındı! Şimdi ürün analizi ve senaryo oluşturma başlıyor...",
                has_url=True, url=url,
            )

        # 2) SCENARIO_APPROVAL — keyword-bazlı approve/cancel (butonlar zaten ana yol)
        if session.state == ConversationState.SCENARIO_APPROVAL:
            lower = text.lower()
            if any(w in lower for w in APPROVAL_KEYWORDS):
                return {
                    "reply": None,
                    "state": ConversationState.PRODUCING,
                    "has_url": False, "url": None, "action": "approve",
                    "buttons": None, "note_buttons": False,
                }
            if any(w in lower for w in CANCEL_KEYWORDS):
                session.reset()
                return {
                    "reply": "❌ İptal edildi.\n\nYeni bir video için **ürün linkini** gönder.",
                    "state": session.state,
                    "has_url": False, "url": None, "action": "cancel",
                    "buttons": None, "note_buttons": False,
                }
            from core.url_data_extractor import URLDataExtractor
            if URLDataExtractor.extract_url_from_text(text):
                return self._reply(
                    session,
                    "📋 Şu an bir senaryo onayı bekliyor.\n\n"
                    "Önce mevcut senaryoyu **onayla** veya **iptal et**, "
                    "sonra yeni bir link gönderebilirsin.",
                )
            return self._reply(session, "Lütfen yukarıdaki **✅ Onayla** veya **❌ İptal** butonunu kullan.")

        # 3) BUSY states
        if session.state in (
            ConversationState.URL_PROCESSING,
            ConversationState.RESEARCHING,
            ConversationState.PRODUCING,
        ):
            return self._handle_busy_state(session, text, None)

        # 4) Brief akışı sürerken (buton bekleniyorken) metin gelirse → butonlara yönlendir
        if session.state in (
            ConversationState.ASKING_FORMAT,
            ConversationState.ASKING_STYLE,
            ConversationState.ASKING_CUSTOM_NOTE,
        ):
            return self._reply(
                session,
                "👇 Lütfen yukarıdaki butonlardan birini seç. "
                "Yeniden başlamak için /start yazabilirsin.",
            )

        # 5) IDLE / DELIVERED — URL var mı?
        from core.url_data_extractor import URLDataExtractor
        url = URLDataExtractor.extract_url_from_text(text)
        if url:
            if session.state == ConversationState.DELIVERED:
                session.soft_reset_for_new_url()
            return self._start_brief_internal(session, url)

        return self._reply(session, self._idle_guidance())

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🎯 BRIEF AKIŞI — Deterministik
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _start_brief_internal(self, session: UserSession, url: str) -> dict:
        """URL alındı → brief akışını başlat: format butonları gönder."""
        session.pending_url = url
        session.preferences = {}
        session.pending_style_options = []
        session.welcomed = True
        session.state = ConversationState.ASKING_FORMAT

        log.info(f"Brief başlatıldı: user={session.user_id} url={url[:60]}")

        return self._reply(
            session,
            f"🔗 Link aldım! Birkaç hızlı soruyla brief'i tamamlayalım.",
            buttons={
                "question": "📐 **1/3 — Format:** Hangi formatta olsun?",
                "choice_key": "video_format",
                "options": FORMAT_OPTIONS,
            },
        )

    async def start_brief_for_url(self, user_id: int, url: str) -> dict:
        """Public — main.py'nin çağırması için (manuel URL işleme yolu)."""
        session = self.get_session(user_id)
        async with session.lock:
            return self._start_brief_internal(session, url)

    def set_format(self, user_id: int, value: str) -> None:
        """Format seçimini kaydet, state ASKING_STYLE'a geç."""
        session = self.get_session(user_id)
        session.preferences["video_format"] = value
        session.state = ConversationState.ASKING_STYLE
        log.info(f"Format seçildi: user={user_id} format={value}")

    def category_ready(self, user_id: int) -> bool:
        """Lite extract bitti mi?"""
        session = self.get_session(user_id)
        return bool(session.product_category)

    async def await_lite_extract(self, user_id: int, timeout: float = 10.0) -> None:
        """Lite extract task'ı bekleyebildiğin kadar bekle (timeout sonrası fallback'e düş)."""
        session = self.get_session(user_id)
        task = session.lite_extract_task
        if task is None or task.done():
            return
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
        except asyncio.TimeoutError:
            log.warning(f"Lite extract {timeout}s içinde dönmedi: user={user_id}")
        except Exception as exc:
            log.warning(f"Lite extract bekleme hatası: {exc}")

    async def build_style_buttons(self, user_id: int) -> dict:
        """3 dinamik tarz seçeneği üret (LLM tek-amaçlı çağrı). Buton dict döner."""
        session = self.get_session(user_id)
        category = session.product_category
        brand = session.lite_brand or session.last_brand or ""
        product = session.lite_product or session.last_product or ""

        options = await asyncio.to_thread(self._llm_style_options, category, brand, product)

        # callback_data 64-byte limiti için index-based: pref:video_style:s0/s1/s2
        session.pending_style_options = options
        button_options = []
        for idx, opt in enumerate(options):
            button_options.append({
                "label": opt["label"],
                "value": f"s{idx}",
            })

        question = "🎨 **2/3 — Tarz:** Hangi tarzda olsun?"
        if category:
            question += f"\n_Kategori: {category}_"

        return {
            "question": question,
            "choice_key": "video_style",
            "options": button_options,
            "allow_freetext": True,
        }

    def resolve_style_value(self, user_id: int, callback_value: str) -> str:
        """`s0`/`s1`/... index callback'ini gerçek value'ya çevir."""
        session = self.get_session(user_id)
        if callback_value.startswith("s") and callback_value[1:].isdigit():
            idx = int(callback_value[1:])
            if 0 <= idx < len(session.pending_style_options):
                return session.pending_style_options[idx]["value"]
        # Index değilse direkt string olarak kabul et (freetext fallback)
        return callback_value

    def set_style(self, user_id: int, full_value: str) -> dict:
        """Tarz seçimini kaydet, state ASKING_CUSTOM_NOTE; not butonları döndür."""
        session = self.get_session(user_id)
        session.preferences["video_style"] = full_value
        session.pending_style_options = []
        session.state = ConversationState.ASKING_CUSTOM_NOTE
        log.info(f"Style seçildi: user={user_id} style={full_value}")

        return self._reply(
            session,
            "✍️ **3/3 — Ek Not:** Brief'e ek bir not bırakmak ister misin?\n"
            "_(Örn. 'tone biraz daha eğlenceli', 'rakipler X yapıyor biz farklı olalım')_",
            note_buttons=True,
        )

    def handle_note_skip(self, user_id: int) -> dict:
        """Atla → pipeline başlat."""
        session = self.get_session(user_id)
        url = session.pending_url
        if not url:
            session.state = ConversationState.IDLE
            return self._reply(session, "⚠️ İşlenecek URL bulunamadı. Lütfen tekrar gönder.")
        session.pending_url = None
        session.current_url = url
        session.state = ConversationState.URL_PROCESSING
        log.info(f"Custom note atlandı: user={user_id}")
        return self._reply(
            session,
            "👌 Atlandı! Ürün analizi ve senaryo oluşturma başlıyor...",
            has_url=True, url=url,
        )

    def handle_note_write_request(self, user_id: int) -> dict:
        """Not yaz → serbest metin bekle."""
        session = self.get_session(user_id)
        session.state = ConversationState.WAITING_CUSTOM_NOTE_TEXT
        return self._reply(
            session,
            "✍️ Notunu yaz, gönder. Pipeline notu aldıktan sonra başlayacak.",
        )

    def set_custom_style_freetext(self, user_id: int, text: str) -> dict:
        """Stil için 'Kendim yazacağım' sonrası gelen serbest metin → tarz olarak kaydet."""
        session = self.get_session(user_id)
        cleaned = (text or "").strip()
        if not cleaned:
            cleaned = "Özel Tarz"
        return self.set_style(user_id, cleaned[:80])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🤖 STİL ÜRETİMİ (tek LLM call)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _llm_style_options(self, category: str | None, brand: str, product: str) -> list[dict]:
        """Kategoriye göre 3 dinamik tarz seçeneği üret. Hata/eksik veride fallback."""
        if not self.openai or not category:
            return list(DEFAULT_STYLE_OPTIONS)
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Sen bir reklam yönetmeni asistanısın. Verilen ürün için 3 farklı "
                        "video TARZI öner. Sadece JSON döndür."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Kategori: {category}\n"
                        f"Marka: {brand or '(bilinmiyor)'}\n"
                        f"Ürün: {product or '(bilinmiyor)'}\n\n"
                        "Bu ürün için 3 farklı reklam video tarzı öner. Her tarz:\n"
                        "- label: emojili kısa Türkçe başlık (max 40 karakter)\n"
                        "- value: scenario engine'e iletilecek kısa Türkçe başlık (max 30 karakter)\n\n"
                        "Örnek (skincare): Sabah Rutini UGC / Before-After Dramatik / Sinematik Tanıtım\n"
                        "Örnek (fitness): Antrenman UGC / Performans Demosu / Dönüşüm Hikayesi\n"
                        "Örnek (tech): Unboxing Reaction / Kullanım Senaryosu / Sinematik Tanıtım\n\n"
                        "JSON şeması: {\"options\": [{\"label\": \"...\", \"value\": \"...\"}, ...]}\n"
                        "TAM 3 seçenek olmalı."
                    ),
                },
            ]
            resp = self.openai.chat_json(messages=messages, max_tokens=400)
            opts = resp.get("options") if isinstance(resp, dict) else None
            if isinstance(opts, list) and len(opts) >= 1:
                cleaned = []
                for o in opts[:3]:
                    if not isinstance(o, dict):
                        continue
                    lbl = (o.get("label") or "").strip()[:60]
                    val = (o.get("value") or lbl).strip()[:30]
                    if lbl and val:
                        cleaned.append({"label": lbl, "value": val})
                if len(cleaned) >= 1:
                    # Eksik gelirse fallback'lerle 3'e tamamla
                    while len(cleaned) < 3:
                        for default in DEFAULT_STYLE_OPTIONS:
                            if not any(c["value"] == default["value"] for c in cleaned):
                                cleaned.append(default)
                                break
                        else:
                            break
                    return cleaned[:3]
        except Exception as e:
            log.warning(f"Style options LLM hatası: {e} — fallback kullanılıyor")
        return list(DEFAULT_STYLE_OPTIONS)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🧠 BUSY HANDLER
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _handle_busy_state(self, session: UserSession, text: str,
                           url: str | None) -> dict:
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
                "Bu 2-5 dakika sürebilir — bitince haber vereceğim! 📹"
            ),
        }

        status_msg = state_messages.get(
            session.state, "⏳ Bir işlem devam ediyor, lütfen bekle."
        )
        return self._reply(session, status_msg)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📋 SENARYO ONAYI (inline button)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def handle_scenario_response(self, user_id: int, action: str) -> dict:
        session = self.get_session(user_id)

        if action == "approve":
            session.state = ConversationState.PRODUCING
            return {"action": "approve", "state": session.state}

        if action == "cancel":
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
    # 🛠️ YARDIMCI METOTLAR
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _reply(session: UserSession, reply: str, has_url: bool = False,
               url: str | None = None, action: str | None = None,
               buttons: dict | None = None, note_buttons: bool = False) -> dict:
        import time as _time
        session._last_activity = _time.time()
        return {
            "reply": reply,
            "state": session.state,
            "has_url": has_url,
            "url": url,
            "action": action,
            "buttons": buttons,
            "note_buttons": note_buttons,
        }

    @staticmethod
    def _idle_guidance() -> str:
        return (
            "Bana bir **ürün linki** gönder, "
            "gerisini ben halledeyim! 🚀\n\n"
            "📎 _Örnek: https://www.marka.com/urun-adi_"
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STATE GEÇİŞ METODLARİ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def mark_url_processing(self, user_id: int):
        session = self.get_session(user_id)
        session.state = ConversationState.URL_PROCESSING

    def mark_researching(self, user_id: int):
        session = self.get_session(user_id)
        session.state = ConversationState.RESEARCHING

    def mark_scenario_approval(self, user_id: int):
        session = self.get_session(user_id)
        session.state = ConversationState.SCENARIO_APPROVAL

    def mark_producing(self, user_id: int):
        session = self.get_session(user_id)
        session.state = ConversationState.PRODUCING

    def mark_delivered(self, user_id: int):
        session = self.get_session(user_id)
        session.state = ConversationState.DELIVERED

    def find_stuck_brief(self, max_idle_seconds: int = 300) -> list[int]:
        """Brief akışında 5dk+ kalmış kullanıcı id'lerini döndürür (watchdog)."""
        import time as _time
        now = _time.time()
        stuck: list[int] = []
        with self._lock:
            for uid, session in self.sessions.items():
                if session.state not in (
                    ConversationState.ASKING_FORMAT,
                    ConversationState.ASKING_STYLE,
                    ConversationState.WAITING_STYLE_TEXT,
                    ConversationState.ASKING_CUSTOM_NOTE,
                    ConversationState.WAITING_CUSTOM_NOTE_TEXT,
                ):
                    continue
                if not hasattr(session, "_last_activity"):
                    continue
                if (now - session._last_activity) > max_idle_seconds:
                    stuck.append(uid)
        return stuck

    def soft_reset_to_idle(self, user_id: int):
        """Watchdog → state IDLE'a alınır, brief verisi temizlenir."""
        session = self.get_session(user_id)
        session.state = ConversationState.IDLE
        session.pending_url = None
        session.preferences = {}
        session.pending_style_options = []
        import time as _time
        session._last_activity = _time.time()
