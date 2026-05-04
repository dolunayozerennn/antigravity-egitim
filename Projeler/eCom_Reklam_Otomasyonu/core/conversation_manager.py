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
    URL_PROCESSING = auto()        # URL alındı, veri çıkarılıyor
    RESEARCHING = auto()           # Marka/ürün araştırma + senaryo üretimi
    SCENARIO_APPROVAL = auto()     # Senaryo onayı bekleniyor
    COLLECTING_PREFERENCES = auto() # Agent butonlarla tercih topluyor
    AWAITING_CUSTOM_NOTE = auto()  # Tercihler tamam, "ek not?" sorusuna cevap bekleniyor
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

        # Agent tarafından sunulan tercihler (buton yanıtları)
        self.preferences: dict = {}
        # Bekleyen buton sorusu (callback veya serbest metin routing için)
        self.pending_choice_key: str | None = None
        # Kullanıcının gönderdiği ancak henüz işlenmemiş URL (tercihler sorulurken tutulur)
        self.pending_url: str | None = None
        # Lite extract (hızlı kategori) sonucu — format butonları gösterilirken paralel doldurulur
        self.product_category: str | None = None
        self.lite_brand: str | None = None
        self.lite_product: str | None = None

        # Per-session asyncio.Lock — aynı kullanıcının paralel mesajlarında race önler.
        # Lazy: ilk erişimde oluşur (event loop'a bağlı olmamak için).
        self._lock: Optional[asyncio.Lock] = None

        # Üretim pipeline task referansı (iptal için)
        self.production_task: Optional[asyncio.Task] = None
        # Üretim progress mesajının ID'si (UI buton güncelleme için)
        self.production_progress_msg_id: Optional[int] = None
        self.production_chat_id: Optional[int] = None

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
        self.pending_url = None
        self.preferences = {}
        self.pending_choice_key = None
        self.product_category = None
        self.lite_brand = None
        self.lite_product = None
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
        self.product_category = None
        self.lite_brand = None
        self.lite_product = None
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
        # Sessions dict (üyelik / cleanup) için hafif sync lock — sadece
        # `_cleanup_idle_sessions` gibi sync iterasyon noktalarında kullanılır.
        # Asıl session field mutation'ları per-session asyncio.Lock altında yapılır.
        self._lock = threading.Lock()

    def get_session(self, user_id: int, user_name: str = "") -> UserSession:
        """Kullanıcı session'ını getir veya oluştur.

        Tek event loop modelinde dict get/set GIL ile atomiktir; çoklu adımlı
        mutasyonlar için ayrıca `async with self._lock` kullanılır.
        """
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

    async def handle_text_message(self, user_id: int, text: str, user_name: str = "") -> dict:
        """
        Metin mesajını işle — akıllı agent katmanı.

        Agent, GPT'nin tool_calling özelliğini kullanarak:
        - Kullanıcının bir ürün/link gönderip göndermediğini anlar (process_url tool)
        - Mevcut bir işlem varsa onay/iptal kararlarını algılar
        - Bunlar dışında doğal olarak sohbet edebilir.

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

        # Per-session lock — aynı kullanıcının paralel mesajlarını serileştirir,
        # farklı kullanıcılar etkilenmez. Tüm session mutation'ları bu blok altında.
        async with session.lock:
            return await self._handle_text_message_locked(session, text, user_name)

    async def _handle_text_message_locked(self, session: 'UserSession', text: str, user_name: str) -> dict:
        """handle_text_message'ın gövdesi — caller per-session lock altında çağırır."""
        # ── State: AWAITING_CUSTOM_NOTE ──
        # Tercihler tamam, kullanıcıya "ek not?" soruldu. Cevabı yakala ve pipeline'ı başlat.
        if session.state == ConversationState.AWAITING_CUSTOM_NOTE:
            note = (text or "").strip()
            skip_keywords = {"geç", "gec", "atla", "skip", "yok", "hayır", "hayir", "-", "."}
            if note.lower() in skip_keywords:
                log.info(f"Custom note atlandı: user={session.user_id}")
            elif note:
                session.preferences["custom_note"] = note
                log.info(f"Custom note kaydedildi: user={session.user_id} ({len(note)} char)")

            url = session.pending_url
            if not url:
                # Olmaması lazım ama emniyet
                session.state = ConversationState.IDLE
                return self._reply(session, "⚠️ İşlenecek URL bulunamadı. Lütfen tekrar gönder.")
            session.pending_url = None
            session.current_url = url
            session.state = ConversationState.URL_PROCESSING
            return self._reply(
                session,
                "✅ Not alındı! Şimdi ürün analizi ve senaryo oluşturma başlıyor..." if note and note.lower() not in skip_keywords
                else "👌 Atlandı! Şimdi ürün analizi ve senaryo oluşturma başlıyor...",
                has_url=True,
                url=url,
            )

        # Eğer mesajda yeni bir URL varsa, tercihler sorulduğunda kaybolmaması için hafızaya al
        from core.url_data_extractor import URLDataExtractor
        extracted_url = URLDataExtractor.extract_url_from_text(text)
        if extracted_url:
            session.pending_url = extracted_url

        prefs_str = ", ".join([f"{k}={v}" for k, v in session.preferences.items()]) if session.preferences else "Yok"

        category_hint = session.product_category or "henüz bilinmiyor"
        product_hint = session.lite_product or session.last_product or ""

        category_style_guide = (
            f"\n\n## ÜRÜN BAĞLAMI (lite analiz):\n"
            f"- Kategori: {category_hint}\n"
            f"- Ürün: {product_hint or '(bilinmiyor)'}\n"
            f"\n## TARZ ÖNERİSİ KURALLARI:\n"
            f"Eğer kategori biliniyorsa, `video_style` için STATİK 'UGC/Cinematic' SUNMA. Kategoriye uygun "
            f"ÜRÜNE-ÖZEL 3 dinamik öneri üret. Örnekler:\n"
            f"- skincare: 'Sabah rutini UGC' / 'Before-after dramatik' / 'Profesyonel reklam'\n"
            f"- tech: 'Unboxing reaction' / 'Kullanım senaryosu' / 'Sinematik tanıtım'\n"
            f"- fashion: 'Sokakta UGC' / 'Lookbook profesyonel' / 'Hikaye-driven'\n"
            f"- food/supplement: 'Günlük ritüel UGC' / 'Studio çekim' / 'Etki-odaklı hikaye'\n"
            f"- accessory/jewelry: 'Detay close-up' / 'Lifestyle UGC' / 'Sinematik tanıtım'\n"
            f"- home/fitness: 'Kullanım anı UGC' / 'Profesyonel demo' / 'Dönüşüm hikayesi'\n"
            f"Her seçeneğin `value` alanı KISA Türkçe başlık olsun (max 30 karakter, örn: "
            f"'Sabah Rutini UGC', 'Before-After Dramatik', 'Sinematik Tanıtım'). "
            f"`label` alanı emojili daha okunaklı versiyon olabilir. value alanı pipeline'a doğrudan "
            f"'Video Tarzı: {{value}}' olarak iletilecek.\n"
            f"\n## FORMAT ÖNERİSİ KURALLARI:\n"
            f"`video_format` için TAM 3 seçenek sun: 9:16 (Reels), 16:9 (YouTube), 1:1 (Kare/Feed). "
            f"value alanları sırasıyla '9:16', '16:9', '1:1'."
        )

        # Agent sistem talimatı
        messages = [
            {
                "role": "system",
                "content": (
                    "Sen eCom Reklam Otomasyonu'nun akıllı asistanısın. Kullanıcılar sana e-ticaret "
                    "ürün linkleri gönderir, sen de onlara profesyonel reklam videoları üretirsin. "
                    "GEREKLİ TERCİHLER: 1. Video formatı, 2. Video tarzı.\n"
                    "Eğer Sistem Verisinde 'URL Beklemede' bir link varsa süreci başlat:\n"
                    "1. Eksik Tercihleri Sor: Eğer 'Toplanan Tercihler' listesinde format veya tarz EKSİKSE, `present_choices` aracıyla BUTONLARLA kullanıcının eksik seçimini sor. "
                    "Aynı anda ikisini birden ya da sırayla sorabilirsin.\n"
                    "2. Tercihler Tamamlandıysa İŞLEME BAŞLA: Eğer hem format hem tarz 'Toplanan Tercihler' içinde MEVCUTSA, KESİNLİKLE tekrar soru sorma ve BEKLETMEDEN `process_url` aracını çağır. "
                    "`process_url` aracına 'URL Beklemede' olan linki parametre olarak ver.\n"
                    "Kullanıcı e-ticaret ürününü işlemeyi onaylarsa veya \"başla\" derse `approve_scenario` yetkisini kullan. "
                    "Hiçbiri değilse, kullanıcıya nazikçe yardım et ve konuşmayı sürdür."
                    + category_style_guide
                )
            },
            {
                "role": "user",
                "content": f"[SİSTEM VERİSİ - Durum: {session.state.name}, URL Beklemede: {session.pending_url}, Toplanan Tercihler: {prefs_str}, Kategori: {category_hint}]\nKullanıcı: {text}"
            }
        ]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "process_url",
                    "description": "Kullanıcı mesajında herhangi bir web sitesi veya ürün URL'si olduğunda bu fonksiyonu çağır. Parametre olarak bulduğun URL'yi vermelisin.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Mesajdaki veya en belirgin bağlantı URL'si"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "approve_scenario",
                    "description": "Kullanıcı hazırlanan senaryoyu/işlemi onaylarsa, tamam falan derse çağırılacak eylem."
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_action",
                    "description": "Kullanıcı üretimi iptal etmek isterse veya vazgeçerse çağırılır."
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "present_choices",
                    "description": (
                        "Kullanıcıya belirli seçenekler sunmak istediğinde buton olarak göster. "
                        "Her seçenek bir buton olur. İsteğe bağlı olarak serbest metin girişi de açılabilir."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Kullanıcıya gösterilecek soru metni"
                            },
                            "choice_key": {
                                "type": "string", 
                                "description": "Bu tercihin kaydedileceği anahtar (örn: video_format, video_style)"
                            },
                            "options": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "label": {"type": "string", "description": "Buton üzerinde gösterilecek metin"},
                                        "value": {"type": "string", "description": "Seçildiğinde kaydedilecek değer"}
                                    },
                                    "required": ["label", "value"]
                                },
                                "description": "Buton seçenekleri"
                            },
                            "allow_freetext": {
                                "type": "boolean",
                                "description": "Butonlara ek olarak serbest metin girişine izin verilsin mi"
                            }
                        },
                        "required": ["question", "choice_key", "options"]
                    }
                }
            }
        ]

        url = None
        action = None
        assistant_reply = None
        buttons_data = None

        # Serbest metin bekliyorsak
        if session.pending_choice_key and session.state == ConversationState.COLLECTING_PREFERENCES:
            session.preferences[session.pending_choice_key] = text
            session.pending_choice_key = None
            # Şimdi context'i tekrar değerlendirmek üzere tools olmadan veya normal prompt ile çağrı yapacağız
            # LLM'e yeni tercihi bildirmek için contexti güncelle:
            messages.append({"role": "system", "content": f"Kullanıcı {session.last_brand} için {text} seçimini yaptı."})
           
        try:
            if not self.openai:
                raise ValueError("OpenAI service bulunamadı, fallback'e geçiliyor.")
                
            import asyncio
            msg = await asyncio.to_thread(self.openai.chat_with_tools, messages, tools, max_tokens=1500)
            assistant_reply = getattr(msg, "content", "") or ""
            if getattr(msg, "tool_calls", None):
                for tool_item in msg.tool_calls:
                    tool_call = tool_item.function
                    if tool_call.name == "process_url":
                        import json
                        try:
                            args = json.loads(tool_call.arguments)
                            parsed_url = args.get("url")
                            if not parsed_url:
                                parsed_url = session.pending_url
                            if parsed_url:
                                url = parsed_url
                                session.pending_url = None # Tüketildi
                        except Exception as e:
                            log.error(f"process_url arguments parse error: {e}")
                            if session.pending_url:
                                url = session.pending_url
                    elif tool_call.name == "approve_scenario":
                        action = "approve"
                    elif tool_call.name == "cancel_action":
                        action = "cancel"
                    elif tool_call.name == "present_choices":
                        import json
                        try:
                            args = json.loads(tool_call.arguments)
                            buttons_data = args
                            session.state = ConversationState.COLLECTING_PREFERENCES
                        except Exception as e:
                            log.error(f"present_choices arguments parse error: {e}")
                            assistant_reply = (
                                (assistant_reply or "") +
                                "\n\n⚠️ Seçenekleri gösterirken bir sorun oluştu. "
                                "Lütfen tekrar dene veya /start ile yeniden başla."
                            )
        except Exception as e:
            log.error(f"Agent analiz hatası: {e}", exc_info=True)
            # Fallback (Regex URL çıkarıcı)
            from core.url_data_extractor import URLDataExtractor
            url = URLDataExtractor.extract_url_from_text(text)
            
            lower = text.lower().strip()
            if any(w in lower for w in APPROVAL_KEYWORDS):
                action = "approve"
            elif any(w in lower for w in CANCEL_KEYWORDS):
                action = "cancel"

        # ── State: SCENARIO_APPROVAL ──
        if session.state == ConversationState.SCENARIO_APPROVAL:
            if url:
                return self._reply(session, (
                    "📋 Şu an bir senaryo onayı bekliyor.\n\n"
                    "Önce mevcut senaryoyu **onayla** veya **iptal et**, "
                    "sonra yeni bir link gönderebilirsin."
                ))
            
            if action == "approve":
                log.info(f"Agent-based senaryo onayı: user={session.user_id}")
                return {
                    "reply": None,  # main.py kendi mesajını gönderecek
                    "state": ConversationState.PRODUCING,
                    "has_url": False,
                    "url": None,
                    "action": "approve",
                }
            elif action == "cancel":
                session.reset()
                log.info(f"Agent-based senaryo iptali: user={session.user_id}")
                return {
                    "reply": "❌ İptal edildi.\n\nYeni bir video için ürün linkini gönderebilirsin.",
                    "state": session.state,
                    "has_url": False,
                    "url": None,
                    "action": "cancel",
                }
                
            # Aksi halde agent'ın sohbet yanıtını döndür veya varsayılan mesaj
            return self._reply(session, assistant_reply or "Lütfen mevcut senaryoyu onayla ya da iptal et.")

        # ── State: İşlem devam ediyor (BUSY) ──
        if session.state in (
            ConversationState.URL_PROCESSING,
            ConversationState.RESEARCHING,
            ConversationState.PRODUCING,
        ):
            if action == "cancel":
                session.reset()
                return self._reply(session, "❌ İşlemler durduruldu ve iptal edildi.")
                
            # Eğer tool çağrılmadıysa ve bot cevap ürettiyse onu kullan. Değilse standart meşgul
            if not url and assistant_reply:
                return self._reply(session, assistant_reply)
            return self._handle_busy_state(session, text, url)

        # ── State: IDLE veya DELIVERED ──
        # Her ikisinde de yeni URL kabul edilir
        if url:
            if session.state == ConversationState.DELIVERED:
                session.soft_reset_for_new_url()
            elif session.state == ConversationState.IDLE and not session.welcomed:
                session.welcomed = True
                
            session.current_url = url
            session.state = ConversationState.URL_PROCESSING
            return self._reply(session, (
                "🔗 URL algılandı! Akıllı agent sistemi devreye giriyor...\n"
                f"_{url[:60]}{'...' if len(url) > 60 else ''}_"
            ), has_url=True, url=url)

        # Gelen yanıtta buton varsa
        if buttons_data:
            return self._reply(session, "", buttons=buttons_data)

        # Eğer URL yoksa, Agent'ın verdiği yanıtı dön
        if assistant_reply:
            session.welcomed = True
            return self._reply(session, assistant_reply)
            
        return self._reply(session, self._idle_guidance())

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🧠 STATE HANDLER'LAR (Agent Zekası)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STATE: SCENARIO_APPROVAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

    async def handle_preference_set(self, user_id: int, choice_key: str, choice_value: str) -> dict:
        """Kullanıcının tercih seçimini kaydeder ve LLM'ye bildirir."""
        session = self.get_session(user_id)
        async with session.lock:
            session.preferences[choice_key] = choice_value
            session.pending_choice_key = None

            # ── Deterministik Tercih Tamamlama Kontrolü ──
            # Gerekli tercihler tamam VE bekleyen URL var → LLM'e sormadan pipeline başlat
            REQUIRED_PREFS = {"video_format", "video_style"}
            collected = set(session.preferences.keys()) & REQUIRED_PREFS

            if collected >= REQUIRED_PREFS and session.pending_url:
                # Pipeline'a girmeden önce kullanıcıya "ek not?" sor.
                session.state = ConversationState.AWAITING_CUSTOM_NOTE
                log.info(
                    f"Tercihler tamam — custom_note bekleniyor: user={user_id}"
                )
                return self._reply(
                    session,
                    (
                        "✍️ İstersen brief'e ek bir not bırakabilirsin "
                        "(örn. 'rakipler X yapıyor, biz farklı duralım' veya "
                        "'tone biraz daha eğlenceli').\n\n"
                        "Atlamak için **geç** yaz."
                    ),
                )

        # Tercihler eksik → LLM'e danış (mevcut davranış) — handle_text_message kendi lock'unu alır
        prompt = f"Şu seçim yapıldı: {choice_key} = {choice_value}. Bu bilgiye dayanarak süreci devam ettir."
        return await self.handle_text_message(user_id, prompt)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🛠️ YARDIMCI METOTLAR (Agent)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _reply(session: UserSession, reply: str, has_url: bool = False,
               url: str | None = None, action: str | None = None, buttons: dict = None) -> dict:
        """Standart reply dict oluşturur."""
        import time as _time
        session._last_activity = _time.time()
        return {
            "reply": reply,
            "state": session.state,
            "has_url": has_url,
            "url": url,
            "action": action,
            "buttons": buttons, # Yeni eklendi
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

    def find_stuck_collecting_preferences(self, max_idle_seconds: int = 300) -> list[int]:
        """5 dakikadan uzun süre COLLECTING_PREFERENCES'da kalmış kullanıcı id'lerini döndürür.

        Çağıran taraf (main.py cleanup loop) her bir id için kullanıcıya
        nazik bir bildirim gönderip session'ı IDLE'a alır.
        """
        import time as _time
        now = _time.time()
        stuck: list[int] = []
        with self._lock:
            for uid, session in self.sessions.items():
                if session.state not in (
                    ConversationState.COLLECTING_PREFERENCES,
                    ConversationState.AWAITING_CUSTOM_NOTE,
                ):
                    continue
                if not hasattr(session, "_last_activity"):
                    continue
                if (now - session._last_activity) > max_idle_seconds:
                    stuck.append(uid)
        return stuck

    def soft_reset_to_idle(self, user_id: int):
        """COLLECTING_PREFERENCES watchdog için — state IDLE'a alınır, pending_url temizlenir.

        Context (last_brand, last_product, welcomed) korunur.
        """
        session = self.get_session(user_id)
        session.state = ConversationState.IDLE
        session.pending_url = None
        session.pending_choice_key = None
        session.preferences = {}
        import time as _time
        session._last_activity = _time.time()
