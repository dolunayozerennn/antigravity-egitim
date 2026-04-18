from __future__ import annotations

"""
Conversation Manager — State Machine + Doğal Sohbet
=====================================================
Telegram bot ile kullanıcı arasındaki konuşma akışını yönetir.
7 aşamalı state machine: IDLE → CHATTING → PHOTO_CONFIRMATION →
RESEARCHING → SCENARIO_APPROVAL → PRODUCING → DELIVERED.

GPT-4.1 Mini ile doğal sohbet — form doldurmak yerine akıllı bilgi çıkarma.
Kullanıcı tek mesajda birden fazla bilgi verebilir; LLM eksik olanları sorar.

v2.0 — Fotoğraf opsiyonel, URL'den fotoğraf çekme + teyit mekanizması
"""

import json
import re
import threading
from enum import Enum, auto

from logger import get_logger

log = get_logger("conversation_manager")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 CONVERSATION STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConversationState(Enum):
    IDLE = auto()
    CHATTING = auto()              # Bilgi toplama — doğal sohbet
    PHOTO_CONFIRMATION = auto()    # Kullanıcıya "Bu fotoğraf doğru mu?" soruluyor
    RESEARCHING = auto()           # Marka/ürün araştırma
    SCENARIO_APPROVAL = auto()     # Senaryo onayı bekleniyor
    PRODUCING = auto()             # Video üretim aşaması
    DELIVERED = auto()             # Teslim edildi


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📋 ZORUNLU + OPSİYONEL ALANLAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUIRED_FIELDS = [
    "brand_name",       # Marka adı
    "product_name",     # Ürün adı/açıklaması
    "ad_concept",       # Reklam konsepti/hikayesi
    "video_duration",   # Video süresi (saniye)
    "aspect_ratio",     # 9:16 (dikey) veya 16:9 (yatay)
    "resolution",       # 480p veya 720p
    "language",         # Türkçe veya İngilizce
]

OPTIONAL_FIELDS = [
    "product_image",    # Ürün fotoğrafı URL'i (kullanıcı gönderdiyse)
    "product_url",      # Ürün web sitesi URL'i (fotoğraf çekmek için)
]

ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧠 SYSTEM PROMPT — BİLGİ ÇIKARMA v2
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXTRACTION_SYSTEM_PROMPT = """\
Sen bir e-ticaret reklam videosu üretim asistanısın. En önemli görevin KULLANICIYI YORMAMAK ve İNİSİYATİF ALMAKTIR. Doğal, samimi sohbet et ama zorunlu olmayan hiçbir detayı sorma.

## Görevin:
Kullanıcının verdiği kısıtlı bilgilerden (örneğin sadece bir link veya ürün adı) geri kalan her şeyi MANTIKLI ŞEKİLDE TAHMİN ET VE KENDİN DOLDUR.

## Gerekli Bilgiler:
Aşağıdaki bilgileri doldurmalısın. Eğer kullanıcı vermediyse SEN İNİSİYATİF AL veya URL'den/yazılan dilden mantıklı çıkarımlar yap:
1. **brand_name** — Marka adı. (Belirtilmediyse URL'den çıkar).
2. **product_name** — Ürün adı. (Belirtilmediyse link veya bağlamdan ürün adını çıkarıp yaz).
3. **ad_concept** — Reklam konsepti. SEN YARAT. (Örn: verilen ürün spor ayakkabıysa "Enerjik bir sabah koşusu" diyerek kendin profesyonel bir konsept oluştur, kullanıcıya KESİNLİKLE Sorma).
4. **video_duration** — Video süresi. Ürüne ve senaryona göre 5 ile 15 saniye arasında KENDİN karar ver. ASLA SORMA.
5. **aspect_ratio** — Dikey (9:16) veya Yatay (16:9). Kullanıcı genelde Reels/TikTok için dikey ister, bağlamdan çıkarabiliyorsan veya emin değilsen default 9:16 yap, ya da kısaca "Videoyu dikey mi tasarlayalım, yatay mı?" diye sadece bunu sorabilirsin.
6. **resolution** — Video çözünürlüğü: Her zaman "720p" DOLDUR, kullanıcıya asla sorma.
7. **language** — Dil tercihi: Kullanıcının yazdığı dilden anla. (Türkçe yazdıysa veya attığı link Türkçe ise otomatik "Türkçe" doldur. Sorma).

## Opsiyonel Bilgiler:
- **product_image** — "null" bırak. (Sistem yönetir).
- **product_url** — Kullanıcı bir web sitesi veya link verirse buraya yaz.

## Yanıt Formatı:
Her zaman aşağıdaki JSON formatında yanıt ver (başka bir format KULLANMA):

```json
{
  "extracted_fields": {
    "brand_name": "Nike" veya tahmin,
    "product_name": "Air Max 90" veya tahmin,
    "ad_concept": "Oluşturulan dinamik konsept..." veya tahmin,
    "video_duration": 10 veya tahmin,
    "aspect_ratio": "9:16" veya tahmin,
    "resolution": "720p",
    "language": "Türkçe" veya edilen tahmin,
    "product_url": "https://..." veya null
  },
  "reply_to_user": "Kullanıcıya gösterilecek doğal yanıt mesajı",
  "all_required_collected": false
}
```

## Kurallar:
- PARAMETRELERİ TAHMİN EDİP KENDİN DOLDUR. Kullanıcıya "Video kaç saniye olsun?", "Konsepti ne yapalım?", "Çözünürlük ne olsun?", "Dili İngilizce mi Türkçe mi olsun?" GİBİ SORULAR S-O-R-M-A. 
- Eğer format (Dikey/Yatay) belirtmemişse ve inisiyatif de alamadıysan yalnızca bunu sorabilirsin (bazen doğrudan dikey de verebilirsin). Yoksa hepsini tamamla ve üretimi başlat!
- Kullanıcının sadece ürün ismi veya URL göndermesi senin videoyu kurgulaman için YETERLİDİR.
- Eğer kullanıcının URL'si veya fotoğrafı yoksa, sadece "Fotoğrafını kullanmam için ürünün linkini veya görselini paylaşır mısın?" diyebilirsin.
- Tüm ZORUNLU alanları kendin doldurduğunda `all_required_collected`: `true` gönder!
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
        self.collected_data: dict = {field: None for field in ALL_FIELDS}
        self.chat_history: list[dict] = []
        self.scenario: dict | None = None          # Üretilen senaryo
        self.notion_page_id: str | None = None      # Notion log page ID
        self.production_result: dict | None = None   # Üretim sonucu
        # Fotoğraf teyit akışı
        self.scraped_images: list[dict] = []         # Web'den çekilen fotoğraflar
        self.current_photo_index: int = 0            # Şu an gösterilen fotoğraf index'i
        # Bellek yönetimi
        import time as _time
        self._last_activity: float = _time.time()

    def reset(self):
        """Konuşmayı sıfırla — yeni video için hazırla."""
        self.state = ConversationState.IDLE
        self.collected_data = {field: None for field in ALL_FIELDS}
        self.chat_history = []
        self.scenario = None
        self.notion_page_id = None
        self.production_result = None
        self.scraped_images = []
        self.current_photo_index = 0
        import time as _time
        self._last_activity = _time.time()

    def update_fields(self, extracted: dict):
        """Çıkarılan bilgilerle mevcut veriyi güncelle. None olanları atla."""
        for field, value in extracted.items():
            if value is not None and field in self.collected_data:
                # video_duration her zaman int olmalı — GPT bazen string döndürür
                if field == "video_duration":
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        value = 10  # Varsayılan
                # aspect_ratio validasyonu — Seedance 2.0 desteklenen formatlar
                if field == "aspect_ratio":
                    valid_ratios = {"9:16", "16:9", "1:1"}
                    if value not in valid_ratios:
                        # Yaygın alternatifler → normalize et
                        ratio_map = {
                            "vertical": "9:16", "dikey": "9:16",
                            "horizontal": "16:9", "yatay": "16:9",
                            "square": "1:1", "kare": "1:1",
                            "4:3": "16:9", "3:4": "9:16",
                        }
                        value = ratio_map.get(str(value).lower(), "9:16")
                # resolution validasyonu
                if field == "resolution":
                    valid_resolutions = {"480p", "720p"}
                    if value not in valid_resolutions:
                        value = "720p"  # Varsayılan
                # product_url validasyonu — sadece geçerli URL'leri kabul et
                if field == "product_url":
                    if isinstance(value, str) and not value.startswith("http"):
                        log.warning(f"Geçersiz product_url reddedildi: {str(value)[:80]}")
                        continue  # Bu değeri atla
                # product_image — desteklenmeyen formatları reddet
                if field == "product_image" and isinstance(value, str):
                    unsupported_exts = {".avif", ".svg", ".bmp", ".tiff", ".tif", ".ico", ".heic"}
                    url_path = value.lower().split("?")[0]
                    if any(url_path.endswith(ext) for ext in unsupported_exts):
                        log.warning(f"Desteklenmeyen görsel formatı reddedildi: {value[:80]}")
                        continue  # Bu değeri atla
                self.collected_data[field] = value
        import time as _time
        self._last_activity = _time.time()

    def get_missing_required_fields(self) -> list[str]:
        """Henüz toplanmamış zorunlu alanları döndür."""
        return [
            f for f in REQUIRED_FIELDS
            if self.collected_data.get(f) is None
        ]

    def has_all_required(self) -> bool:
        """Tüm zorunlu alanlar toplandı mı?"""
        return all(
            self.collected_data.get(f) is not None
            for f in REQUIRED_FIELDS
        )

    def has_photo(self) -> bool:
        """Ürün fotoğrafı var mı?"""
        return self.collected_data.get("product_image") is not None

    def has_url(self) -> bool:
        """Ürün web sitesi URL'i var mı?"""
        return bool(self.collected_data.get("product_url"))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🤖 CONVERSATION MANAGER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Metin tabanlı onay kelime listeleri
APPROVAL_KEYWORDS = ["onayla", "onaylıyorum", "tamam", "evet", "başla", "kabul", "approve", "yes", "go", "devam"]
REJECTION_KEYWORDS = ["düzelt", "değiştir", "hayır", "iptal", "vazgeç", "yok", "cancel"]


class ConversationManager:
    """
    State machine + doğal sohbet yöneticisi.

    Servis instance'ları main.py'den enjekte edilir.
    Bu sınıf sadece konuşma mantığına odaklanır.
    """

    def __init__(self, openai_service):
        self.openai = openai_service
        self.sessions: dict[int, UserSession] = {}
        self._lock = threading.Lock()  # Thread-safe session erişimi

    def get_session(self, user_id: int, user_name: str = "") -> UserSession:
        """Kullanıcı session'ını getir veya oluştur. Thread-safe."""
        with self._lock:
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
            "Profesyonel ürün reklam videoları üretmek için buradayım.\n\n"
            "Bana sadece **ürünün linkini** göndermen veya **ürün fotoğrafıyla beraber adını** yazman yeterli. Geri kalan her şeyi (konsept, süre, dil vb.) ben senin için en kaliteli şekilde kurgulayacağım! 🚀\n\n"
            "*(Videonu dikey mi yatay mı tercih ettiğini veya özel bir konsept istediğini de eklersen sevinirim)*"
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
                "needs_url_scrape": bool,    # URL'den fotoğraf çekilecek mi
                "action": str | None,        # "approve" / "edit" / "cancel" (SCENARIO_APPROVAL'da)
            }
        """
        session = self.get_session(user_id, user_name)

        # ── State: IDLE → otomatik başlat ──
        if session.state == ConversationState.IDLE:
            return {
                "reply": self.handle_start(user_id, user_name),
                "state": ConversationState.CHATTING,
                "ready_for_research": False,
                "needs_url_scrape": False,
                "action": None,
            }

        # ── State: SCENARIO_APPROVAL → metin tabanlı onay/red ──
        if session.state == ConversationState.SCENARIO_APPROVAL:
            return self._handle_scenario_text_response(session, text)

        # ── State: PHOTO_CONFIRMATION → "evet"/"hayır" ile teyit ──
        if session.state == ConversationState.PHOTO_CONFIRMATION:
            return self._handle_photo_confirmation_text(session, text)

        # ── State: PRODUCING veya RESEARCHING → işlem devam ediyor ──
        if session.state in (
            ConversationState.PRODUCING,
            ConversationState.RESEARCHING,
        ):
            return {
                "reply": "⏳ Şu an bir işlem devam ediyor. Lütfen bekle.",
                "state": session.state,
                "ready_for_research": False,
                "needs_url_scrape": False,
                "action": None,
            }

        # ── State: DELIVERED → yeni video için /start gerekli ──
        if session.state == ConversationState.DELIVERED:
            return {
                "reply": "✅ Son video teslim edildi. Yeni bir video için /start yaz!",
                "state": session.state,
                "ready_for_research": False,
                "needs_url_scrape": False,
                "action": None,
            }

        # ── State: CHATTING — ana bilgi toplama akışı ──
        if session.state != ConversationState.CHATTING:
            return {
                "reply": "⚠️ Beklenmeyen durum. /start ile sıfırdan başlayalım.",
                "state": session.state,
                "ready_for_research": False,
                "needs_url_scrape": False,
                "action": None,
            }

        # Chat history'e ekle
        session.chat_history.append({"role": "user", "content": text})
        # Bellek sızıntısını önle — son 20 mesajı tut
        if len(session.chat_history) > 20:
            session.chat_history = session.chat_history[-20:]

        # Mevcut toplanan bilgilerle context oluştur
        context = self._build_context(session)

        # GPT-4.1 Mini'ye gönder — bilgi çıkarma
        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "system", "content": f"Şu ana kadar toplanan bilgiler:\n{context}"},
        ] + session.chat_history[-10:]  # Son 10 mesajı gönder (context window yönetimi)

        try:
            response = self.openai.chat_json(messages, temperature=0.7, max_tokens=1500)
        except RuntimeError as e:
            log.warning(f"OpenAI boş yanıt döndü: {e}")
            return {
                "reply": "⚠️ AI şu an meşgul, tekrar dene.",
                "state": session.state,
                "ready_for_research": False,
                "needs_url_scrape": False,
                "action": None,
            }
        except Exception:
            log.error("Chat yanıt hatası", exc_info=True)
            return {
                "reply": "⚠️ Bir hata oluştu, tekrar dene.",
                "state": session.state,
                "ready_for_research": False,
                "needs_url_scrape": False,
                "action": None,
            }

        # Çıkarılan bilgileri güncelle
        extracted = response.get("extracted_fields", {})
        session.update_fields(extracted)

        reply = response.get("reply_to_user", "Devam edelim mi?")
        session.chat_history.append({"role": "assistant", "content": reply})

        # ── HAZIRLIK KONTROLÜ ──
        ready = False
        needs_url_scrape = False

        if session.has_all_required():
            if session.has_photo():
                # Yol 1: Fotoğraf zaten var → araştırmaya geç
                ready = True
            elif session.has_url():
                # Yol 2: URL var, fotoğraf yok → URL'den fotoğraf çek
                needs_url_scrape = True
            else:
                # Yol 3: Ne fotoğraf ne URL → text-to-video ile ilerle
                ready = True

        log.info(
            f"Bilgi çıkarma: user={user_id}, "
            f"eksik={session.get_missing_required_fields()}, "
            f"fotoğraf={'✅' if session.has_photo() else '❌'}, "
            f"url={'✅' if session.has_url() else '❌'}, "
            f"ready={ready}, needs_scrape={needs_url_scrape}"
        )

        return {
            "reply": reply,
            "state": session.state,
            "ready_for_research": ready,
            "needs_url_scrape": needs_url_scrape,
            "action": None,
        }

    # ── FOTOĞRAF İŞLEME (Doğrudan gönderim) ──

    def handle_photo(self, user_id: int, photo_url: str, user_name: str = "") -> dict:
        """
        Kullanıcının doğrudan gönderdiği ürün fotoğrafını işle.

        Args:
            photo_url: ImgBB'ye yüklenmiş public URL

        Returns:
            dict: {"reply": str, "state": ..., "ready_for_research": bool,
                   "needs_url_scrape": bool, "action": None}
        """
        session = self.get_session(user_id, user_name)

        if session.state == ConversationState.IDLE:
            return {
                "reply": self.handle_start(user_id, user_name),
                "state": ConversationState.CHATTING,
                "ready_for_research": False,
                "needs_url_scrape": False,
                "action": None,
            }

        session.collected_data["product_image"] = photo_url
        log.info(f"Ürün fotoğrafı alındı: user={user_id}, url={photo_url[:60]}...")

        # Fotoğraf hariç tüm zorunlu bilgiler tamamsa araştırmaya geç
        if session.has_all_required():
            reply = (
                "📸 **Ürün fotoğrafı alındı!** ✅\n\n"
                "Tüm bilgiler tamam — şimdi marka ve ürün araştırmasına geçiyorum... 🔍"
            )
            return {
                "reply": reply,
                "state": session.state,
                "ready_for_research": True,
                "needs_url_scrape": False,
                "action": None,
            }

        # Henüz eksik alan var
        missing = session.get_missing_required_fields()
        reply = (
            "📸 **Ürün fotoğrafı alındı!** ✅\n\n"
            f"Birkaç bilgi daha lazım. {self._describe_missing(missing)}"
        )
        return {
            "reply": reply,
            "state": session.state,
            "ready_for_research": False,
            "needs_url_scrape": False,
            "action": None,
        }

    # ── PHOTO CONFIRMATION (URL'den çekilenler) ──

    def start_photo_confirmation(self, user_id: int, images: list[dict]):
        """
        URL'den çekilmiş fotoğrafları teyit akışına sokar.

        Args:
            images: [{"url": "...", "alt": "...", "source": "..."}]
        """
        session = self.get_session(user_id)
        session.state = ConversationState.PHOTO_CONFIRMATION
        session.scraped_images = images
        session.current_photo_index = 0
        log.info(
            f"Fotoğraf teyit akışı başlatıldı: user={user_id}, "
            f"{len(images)} fotoğraf"
        )

    def handle_photo_confirmation(self, user_id: int, action: str) -> dict:
        """
        Fotoğraf teyit butonlarını işle.

        Args:
            action: "photo_confirm" | "photo_next" | "photo_skip"

        Returns:
            dict: {
                "reply": str,
                "state": ConversationState,
                "ready_for_research": bool,
                "show_next_photo": bool,
                "next_photo": dict | None,
            }
        """
        session = self.get_session(user_id)

        if action == "photo_confirm":
            # Kullanıcı bu fotoğrafı onayladı
            idx = session.current_photo_index
            if idx < len(session.scraped_images):
                selected = session.scraped_images[idx]
                session.collected_data["product_image"] = selected["url"]
                log.info(f"Fotoğraf onaylandı: user={user_id}, url={selected['url'][:60]}...")

            session.state = ConversationState.CHATTING  # Araştırmaya geçmeden önce
            return {
                "reply": "✅ Fotoğraf onaylandı! Şimdi araştırmaya geçiyorum... 🔍",
                "state": session.state,
                "ready_for_research": True,
                "show_next_photo": False,
                "next_photo": None,
            }

        elif action == "photo_next":
            # Sonraki fotoğrafı göster
            session.current_photo_index += 1
            idx = session.current_photo_index

            if idx < len(session.scraped_images):
                next_img = session.scraped_images[idx]
                remaining = len(session.scraped_images) - idx - 1
                return {
                    "reply": f"📸 Fotoğraf {idx + 1}/{len(session.scraped_images)} — _{next_img['alt']}_",
                    "state": session.state,
                    "ready_for_research": False,
                    "show_next_photo": True,
                    "next_photo": next_img,
                }
            else:
                # Tüm fotoğraflar reddedildi
                session.state = ConversationState.CHATTING
                return {
                    "reply": (
                        "📸 Bulunan fotoğrafların hiçbiri uygun değildi.\n\n"
                        "Şu seçeneklerin var:\n"
                        "• Doğrudan **ürün fotoğrafı gönder** 📤\n"
                        "• **Fotoğrafsız devam et** — text-to-video ile çalışırız\n\n"
                        "Ne yapmak istersin?"
                    ),
                    "state": session.state,
                    "ready_for_research": False,
                    "show_next_photo": False,
                    "next_photo": None,
                }

        elif action == "photo_skip":
            # Fotoğrafsız devam et
            session.state = ConversationState.CHATTING
            return {
                "reply": (
                    "👌 Fotoğrafsız devam ediyoruz — **text-to-video** modunda çalışacağız.\n"
                    "Araştırmaya geçiyorum... 🔍"
                ),
                "state": session.state,
                "ready_for_research": True,
                "show_next_photo": False,
                "next_photo": None,
            }

        return {
            "reply": "⚠️ Bilinmeyen aksiyon.",
            "state": session.state,
            "ready_for_research": False,
            "show_next_photo": False,
            "next_photo": None,
        }

    def _handle_photo_confirmation_text(self, session: UserSession, text: str) -> dict:
        """PHOTO_CONFIRMATION state'inde metin mesaj — evet/hayır."""
        lower = text.lower().strip()

        if any(w in lower for w in ["evet", "bu", "doğru", "tamam", "onay", "kabul"]):
            result = self.handle_photo_confirmation(session.user_id, "photo_confirm")
            return {
                "reply": result["reply"],
                "state": result["state"],
                "ready_for_research": result["ready_for_research"],
                "needs_url_scrape": False,
                "action": None,
            }
        elif any(w in lower for w in ["hayır", "değil", "yanlış", "başka", "sonraki", "diğer"]):
            result = self.handle_photo_confirmation(session.user_id, "photo_next")
            # Sonraki fotoğraf varsa main.py gösterecek — burada sinyali dönüyoruz
            return {
                "reply": result["reply"],
                "state": result["state"],
                "ready_for_research": result["ready_for_research"],
                "needs_url_scrape": False,
                "action": "show_next_photo" if result.get("show_next_photo") else None,
                "_next_photo": result.get("next_photo"),
            }
        elif any(w in lower for w in ["atla", "geç", "fotoğrafsız", "devam"]):
            result = self.handle_photo_confirmation(session.user_id, "photo_skip")
            return {
                "reply": result["reply"],
                "state": result["state"],
                "ready_for_research": result["ready_for_research"],
                "needs_url_scrape": False,
                "action": None,
            }
        else:
            return {
                "reply": (
                    "Lütfen bu fotoğraf hakkında karar ver:\n"
                    "• **Evet** — bu fotoğrafı kullan\n"
                    "• **Hayır** / **Sonraki** — diğer fotoğrafa bak\n"
                    "• **Atla** — fotoğrafsız devam et"
                ),
                "state": session.state,
                "ready_for_research": False,
                "needs_url_scrape": False,
                "action": None,
            }

    # ── STATE: SCENARIO_APPROVAL ──

    def _handle_scenario_text_response(self, session: UserSession, text: str) -> dict:
        """
        SCENARIO_APPROVAL state'inde metin mesajlarını işle.
        Inline buton yerine "onaylıyorum" / "düzelt" yazabilir.
        """
        lower = text.lower().strip()

        if any(w in lower for w in APPROVAL_KEYWORDS):
            log.info(f"Metin tabanlı senaryo onayı: user={session.user_id}")
            return {
                "reply": None,  # main.py kendi mesajını gönderecek
                "state": ConversationState.PRODUCING,
                "ready_for_research": False,
                "needs_url_scrape": False,
                "action": "approve",
            }
        elif any(w in lower for w in REJECTION_KEYWORDS):
            session.state = ConversationState.CHATTING
            session.scenario = None
            log.info(f"Metin tabanlı senaryo reddi: user={session.user_id}")
            return {
                "reply": (
                    "✏️ Senaryoyu düzenleyelim.\n"
                    "Ne değiştirmek istiyorsun? Konsepti, süreyi, dili veya formatı değiştirebiliriz."
                ),
                "state": session.state,
                "ready_for_research": False,
                "needs_url_scrape": False,
                "action": "edit",
            }
        else:
            return {
                "reply": (
                    "📋 Senaryo onayı bekliyor. Lütfen:\n"
                    "• **Onayla** / **Tamam** → Üretim başlar\n"
                    "• **Düzelt** / **Değiştir** → Senaryo düzenlenir\n"
                    "• **İptal** / **Vazgeç** → İptal edilir\n\n"
                    "Ya da yukarıdaki butonları kullanabilirsin."
                ),
                "state": session.state,
                "ready_for_research": False,
                "needs_url_scrape": False,
                "action": None,
            }

    def handle_scenario_response(self, user_id: int, action: str) -> dict:
        """
        Senaryo onay/düzelt/iptal yanıtını işle (inline butonlardan).

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
        """Toplanan bilgileri ve mevcut durumu okunabilir metin haline getir."""
        lines = []

        # State bilgisi
        state_labels = {
            ConversationState.IDLE: "Boşta",
            ConversationState.CHATTING: "Bilgi toplama",
            ConversationState.PHOTO_CONFIRMATION: "Fotoğraf teyidi",
            ConversationState.RESEARCHING: "Araştırma",
            ConversationState.SCENARIO_APPROVAL: "Senaryo onayı",
            ConversationState.PRODUCING: "Video üretimi",
            ConversationState.DELIVERED: "Teslim edildi",
        }
        lines.append(f"📊 Mevcut durum: {state_labels.get(session.state, '?')}")
        lines.append("")

        field_labels = {
            "brand_name": "Marka",
            "product_name": "Ürün",
            "ad_concept": "Reklam Konsepti",
            "video_duration": "Video Süresi",
            "aspect_ratio": "Format",
            "resolution": "Çözünürlük",
            "language": "Dil",
            "product_image": "Ürün Fotoğrafı",
            "product_url": "Ürün Web Sayfası",
        }

        lines.append("── Zorunlu Bilgiler ──")
        for field in REQUIRED_FIELDS:
            value = session.collected_data.get(field)
            label = field_labels.get(field, field)
            if value is not None:
                lines.append(f"✅ {label}: {value}")
            else:
                lines.append(f"❌ {label}: Henüz belirtilmedi")

        lines.append("")
        lines.append("── Opsiyonel Bilgiler ──")
        for field in OPTIONAL_FIELDS:
            value = session.collected_data.get(field)
            label = field_labels.get(field, field)
            if value is not None:
                display_val = value[:60] + "..." if len(str(value)) > 60 else value
                lines.append(f"✅ {label}: {display_val}")
            else:
                lines.append(f"⬜ {label}: Belirtilmedi (opsiyonel)")

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
            "resolution": "video çözünürlüğü (480p/720p)",
            "language": "dil tercihi",
        }
        if not missing:
            return "Tüm bilgiler tamam!"
        human_names = [descriptions.get(f, f) for f in missing]
        if len(human_names) == 1:
            return f"Bir de **{human_names[0]}** bilgisini paylaşır mısın?"
        return "Şunları da öğrenebilir miyim: " + ", ".join(f"**{n}**" for n in human_names) + "?"
