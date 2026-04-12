"""
eCom Reklam Otomasyonu — Telegram Bot Entry Point
====================================================
Seedance 2.0 ile profesyonel ürün reklam videoları üreten
Telegram bot. Doğal sohbet ile bilgi toplar, senaryo üretir,
video üretim pipeline'ını çalıştırır.

v2.0 — Fotoğraf opsiyonel, URL'den fotoğraf çekme + teyit mekanizması

Author: Antigravity Ecosystem
"""

import asyncio
import io
import os
import sys

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ── Config (Fail-fast boot) ──
from config import settings
from logger import get_logger

# ── Services ──
from services.openai_service import OpenAIService
from services.perplexity_service import PerplexityService
from services.imgbb_service import ImgBBService
from services.kie_api import KieAIService
from services.elevenlabs_service import ElevenLabsService
from services.replicate_service import ReplicateService
from services.notion_service import NotionService
from services.web_scraper_service import WebScraperService

# ── Core Logic ──
from core.conversation_manager import ConversationManager, ConversationState
from core.scenario_engine import ScenarioEngine
from core.production_pipeline import ProductionPipeline

log = get_logger("main")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🏗️ SERVİS BAŞLATMA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Servis instance'ları — tüm handler'lar tarafından kullanılır
openai_svc = OpenAIService(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
perplexity_svc = PerplexityService(api_key=settings.PERPLEXITY_API_KEY, base_url=settings.PERPLEXITY_BASE_URL)
imgbb_svc = ImgBBService(api_key=settings.IMGBB_API_KEY)
kie_svc = KieAIService(api_key=settings.KIE_API_KEY, base_url=settings.KIE_BASE_URL)
elevenlabs_svc = ElevenLabsService(api_key=settings.ELEVENLABS_API_KEY, model_id=settings.ELEVENLABS_MODEL)
replicate_svc = ReplicateService(api_token=settings.REPLICATE_API_TOKEN)
notion_svc = NotionService(token=settings.NOTION_TOKEN, database_id=settings.NOTION_DB_ID)
web_scraper_svc = WebScraperService()

# Core modüller — DI ile servisler enjekte edilir
conversation_mgr = ConversationManager(openai_service=openai_svc)
scenario_engine = ScenarioEngine(openai_service=openai_svc, perplexity_service=perplexity_svc)
pipeline = ProductionPipeline(
    kie_service=kie_svc,
    elevenlabs_service=elevenlabs_svc,
    replicate_service=replicate_svc,
    notion_service=notion_svc,
    imgbb_service=imgbb_svc,
    is_dry_run=settings.IS_DRY_RUN,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡️ ASYNC TASK HATA YÖNETİMİ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _handle_task_exception(task: asyncio.Task):
    """asyncio.create_task ile oluşturulan task'ların sessizce çökmesini önler."""
    try:
        exc = task.exception()
        if exc:
            log.error(f"Background task çöktü: {task.get_name()}", exc_info=exc)
    except asyncio.CancelledError:
        pass


async def _cleanup_idle_sessions():
    """Bellek sızıntısını önle — inaktif session'ları periyodik temizle."""
    while True:
        await asyncio.sleep(300)  # 5 dakikada bir kontrol et
        try:
            import time as _time
            now = _time.time()
            to_delete = []
            with conversation_mgr._lock:
                for uid, session in conversation_mgr.sessions.items():
                    if not hasattr(session, '_last_activity'):
                        continue
                    idle_seconds = now - session._last_activity
                    state_name = session.state.name

                    # PRODUCING ve RESEARCHING korunur (aktif pipeline olabilir)
                    if state_name in ("PRODUCING", "RESEARCHING"):
                        # 1 saatten eski bile olsa çalışıyor olabilir — 2 saat sınır
                        if idle_seconds > 7200:
                            to_delete.append(uid)
                        continue

                    # IDLE/DELIVERED → 10 dakika sonra temizle
                    if state_name in ("IDLE", "DELIVERED") and idle_seconds > 600:
                        to_delete.append(uid)
                    # CHATTING/PHOTO_CONFIRMATION/SCENARIO_APPROVAL → 30 dakika sonra temizle
                    elif state_name in ("CHATTING", "PHOTO_CONFIRMATION", "SCENARIO_APPROVAL") and idle_seconds > 1800:
                        to_delete.append(uid)

                for uid in to_delete:
                    del conversation_mgr.sessions[uid]
            if to_delete:
                log.info(f"Session temizliği: {len(to_delete)} session kaldırıldı, "
                         f"kalan: {len(conversation_mgr.sessions)}")
        except Exception:
            log.error("Session temizleme hatası", exc_info=True)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡️ ERİŞİM KONTROLÜ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def is_authorized(user_id: int) -> bool:
    """Sadece izin verilen kullanıcıları kabul et."""
    return user_id in settings.ALLOWED_USER_IDS


async def unauthorized_reply(update: Update):
    """Yetkisiz kullanıcıya yanıt."""
    await update.effective_message.reply_text(
        "⛔ Bu botu kullanma yetkiniz yok.\n"
        "Bu bot sadece yönetici tarafından kullanılabilir."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📋 KOMUT HANDLER'LARI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komutu — sohbeti başlatır."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    reply = conversation_mgr.handle_start(user.id, user.first_name or user.username or "")
    await update.message.reply_text(reply, parse_mode="Markdown")


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/cancel komutu — mevcut işlemi iptal eder."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    session = conversation_mgr.get_session(user.id)
    session.reset()
    await update.message.reply_text(
        "❌ İptal edildi.\n/start yazarak yeni bir video üretimine başlayabilirsin.",
        parse_mode="Markdown",
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status komutu — mevcut durumu gösterir."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    session = conversation_mgr.get_session(user.id)
    state_labels = {
        ConversationState.IDLE: "⚪ Boşta",
        ConversationState.CHATTING: "💬 Bilgi toplama",
        ConversationState.PHOTO_CONFIRMATION: "📸 Fotoğraf teyidi",
        ConversationState.RESEARCHING: "🔍 Araştırma",
        ConversationState.SCENARIO_APPROVAL: "📋 Senaryo onayı",
        ConversationState.PRODUCING: "🎬 Video üretimi",
        ConversationState.DELIVERED: "✅ Teslim edildi",
    }
    status_text = state_labels.get(session.state, "❓ Bilinmiyor")

    msg = f"📊 **Durum:** {status_text}\n"
    if session.state == ConversationState.CHATTING:
        missing = session.get_missing_required_fields()
        if missing:
            msg += f"📋 Eksik bilgiler: {', '.join(missing)}\n"
        if session.has_photo():
            msg += "📸 Ürün fotoğrafı: ✅\n"
        elif session.has_url():
            msg += "🔗 Ürün URL: ✅ (fotoğraf çekilecek)\n"
        else:
            msg += "📸 Ürün fotoğrafı: ❌ (text-to-video)\n"

    mode = "🏜️ DRY-RUN" if settings.IS_DRY_RUN else "🟢 PRODUCTION"
    msg += f"\n⚙️ **Mod:** {mode}"

    await update.message.reply_text(msg, parse_mode="Markdown")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💬 MESAJ HANDLER'LARI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Metin mesajı handler — doğal sohbet."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    text = update.message.text.strip()
    if not text:
        return

    user_name = user.first_name or user.username or ""
    result = await asyncio.to_thread(
        conversation_mgr.handle_text_message, user.id, text, user_name
    )

    # ── SCENARIO_APPROVAL: Metin tabanlı onay ──
    if result.get("action") == "approve":
        session = conversation_mgr.get_session(user.id)
        session.state = ConversationState.PRODUCING
        await update.message.reply_text(
            "🚀 **Üretim başlıyor!**\n"
            "Her adımda bildirim alacaksın.",
            parse_mode="Markdown",
        )
        task = asyncio.create_task(
            _run_production(update.effective_message, user.id)
        )
        task.add_done_callback(_handle_task_exception)
        return

    # ── PHOTO_CONFIRMATION: Sonraki fotoğrafı göster ──
    if result.get("action") == "show_next_photo":
        next_photo = result.get("_next_photo")
        if next_photo:
            await _send_photo_for_confirmation(
                update.effective_message, user.id, next_photo
            )
            return

    # ── Normal yanıt ──
    if result.get("reply"):
        # GPT'den gelen dinamik yanıtlar Markdown özel karakter içerebilir
        # parse_mode=None ile gönder (parse hatasını önle)
        try:
            await update.message.reply_text(result["reply"], parse_mode="Markdown")
        except Exception:
            log.warning("Markdown parse hatası — parse_mode=None ile tekrar deneniyor")
            await update.message.reply_text(result["reply"])

    # ── Tüm bilgiler toplandı: URL scrape mi yoksa araştırma mı? ──
    if result.get("needs_url_scrape"):
        await _run_url_scrape(update, context)
    elif result.get("ready_for_research"):
        await _run_research_and_scenario(update, context)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fotoğraf handler — ürün görseli alır ve ImgBB'ye yükler."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    user_name = user.first_name or user.username or ""

    # PHOTO_CONFIRMATION state'inde fotoğraf geldiyse — kullanıcı kendi fotoğrafını gönderiyor
    session = conversation_mgr.get_session(user.id)
    if session.state == ConversationState.PHOTO_CONFIRMATION:
        # Teyit akışını kır — kullanıcının kendi fotoğrafını kullan
        pass  # Devam et, aşağıda handle_photo ile işlenecek

    # En yüksek çözünürlüklü fotoğrafı al
    photo = update.message.photo[-1]

    try:
        # Telegram'dan dosyayı indir
        file = await photo.get_file()
        file_bytes = await file.download_as_bytearray()

        # ImgBB'ye yükle
        await update.message.reply_text("📤 Fotoğraf yükleniyor...", parse_mode="Markdown")
        upload_result = await asyncio.to_thread(
            imgbb_svc.upload_image_bytes, bytes(file_bytes), "product_ecom"
        )
        photo_url = upload_result["url"]

    except Exception:
        log.error("Fotoğraf yükleme hatası", exc_info=True)
        await update.message.reply_text(
            "⚠️ Fotoğraf yüklenirken bir hata oluştu. Tekrar dene.",
            parse_mode="Markdown",
        )
        return

    # ConversationManager'a bildir
    result = conversation_mgr.handle_photo(user.id, photo_url, user_name)
    await update.message.reply_text(result["reply"], parse_mode="Markdown")

    # Tüm bilgiler toplandıysa araştırmaya geç
    if result.get("ready_for_research"):
        await _run_research_and_scenario(update, context)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dosya olarak gönderilen görselleri yakalar."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    doc = update.message.document
    if not doc.mime_type or not doc.mime_type.startswith("image/"):
        await update.message.reply_text(
            "📎 Sadece görsel dosyalar kabul ediliyor (JPEG, PNG, WebP).",
            parse_mode="Markdown",
        )
        return

    user_name = user.first_name or user.username or ""

    try:
        file = await doc.get_file()
        file_bytes = await file.download_as_bytearray()

        await update.message.reply_text("📤 Görsel yükleniyor...", parse_mode="Markdown")
        upload_result = await asyncio.to_thread(
            imgbb_svc.upload_image_bytes, bytes(file_bytes), "product_ecom_doc"
        )
        photo_url = upload_result["url"]

    except Exception:
        log.error("Dosya gorsel yükleme hatası", exc_info=True)
        await update.message.reply_text(
            "⚠️ Görsel yüklenirken hata oluştu. Tekrar dene.",
            parse_mode="Markdown",
        )
        return

    result = conversation_mgr.handle_photo(user.id, photo_url, user_name)
    await update.message.reply_text(result["reply"], parse_mode="Markdown")

    if result.get("ready_for_research"):
        await _run_research_and_scenario(update, context)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📸 URL'DEN FOTOĞRAF ÇEKME + TEYİT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _run_url_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """URL'den ürün fotoğraflarını çeker ve teyit akışını başlatır."""
    user = update.effective_user
    session = conversation_mgr.get_session(user.id)
    product_url = session.collected_data.get("product_url")

    if not product_url:
        log.error("URL scrape istendi ama product_url boş!")
        await update.effective_message.reply_text(
            "⚠️ URL bulunamadı. Lütfen ürün sayfasının linkini paylaş.",
            parse_mode="Markdown",
        )
        return

    await update.effective_message.reply_text(
        f"🔍 Ürün fotoğrafı aranıyor...\n`{product_url[:60]}{'...' if len(product_url) > 60 else ''}`",
        parse_mode="Markdown",
    )

    try:
        images = await asyncio.to_thread(
            web_scraper_svc.scrape_product_images, product_url, 5
        )
    except Exception:
        log.error("URL scrape hatası", exc_info=True)
        images = []

    if not images:
        # Fotoğraf bulunamadı
        await update.effective_message.reply_text(
            "😓 Bu sayfada uygun ürün fotoğrafı bulamadım.\n\n"
            "Şu seçeneklerin var:\n"
            "• Doğrudan **ürün fotoğrafı gönder** 📤\n"
            "• **Fotoğrafsız devam et** yaz — text-to-video ile çalışırız",
            parse_mode="Markdown",
        )
        # State'i CHATTING'de bırak — kullanıcı fotoğraf gönderebilir veya devamını söyleyebilir
        return

    # Fotoğraflar bulundu — teyit akışını başlat
    conversation_mgr.start_photo_confirmation(user.id, images)

    # İlk fotoğrafı göster
    first_img = images[0]
    await _send_photo_for_confirmation(
        update.effective_message, user.id, first_img,
        total=len(images), current=1,
    )


async def _send_photo_for_confirmation(
    message, user_id: int, image: dict,
    total: int | None = None, current: int | None = None,
):
    """Fotoğrafı inline butonlarla birlikte Telegram'a gönderir."""
    session = conversation_mgr.get_session(user_id)

    if total is None:
        total = len(session.scraped_images)
    if current is None:
        current = session.current_photo_index + 1

    caption = f"📸 **Fotoğraf {current}/{total}**"
    if image.get("alt"):
        caption += f"\n_{image['alt']}_"

    # Butonlar
    buttons = [
        InlineKeyboardButton("✅ Bu doğru", callback_data="photo_confirm"),
    ]
    if current < total:
        buttons.append(InlineKeyboardButton("➡️ Sonraki", callback_data="photo_next"))
    buttons.append(InlineKeyboardButton("⏭ Fotoğrafsız devam", callback_data="photo_skip"))

    keyboard = InlineKeyboardMarkup([buttons])

    try:
        # Fotoğrafı doğrudan URL ile gönder
        await message.reply_photo(
            photo=image["url"],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
    except Exception:
        log.warning(f"Fotoğraf URL ile gönderilemedi: {image['url'][:60]}", exc_info=True)
        # Fallback: URL'yi metin olarak gönder
        await message.reply_text(
            f"{caption}\n\n🔗 {image['url']}\n\n"
            "_(Fotoğraf doğrudan gösterilemedi, linke tıklayarak görebilirsin)_",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 ARAŞTIRMA + SENARYO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _run_research_and_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Araştırma + senaryo üretimi — ağır iş, arka planda çalışır."""
    user = update.effective_user
    session = conversation_mgr.get_session(user.id)

    # State güncelle
    conversation_mgr.mark_researching(user.id)

    # Video modu bilgisi
    mode_info = "🖼️ image-to-video" if session.has_photo() else "✍️ text-to-video"

    await update.effective_message.reply_text(
        f"🔍 **Marka ve ürün araştırılıyor...**\n"
        f"Mod: {mode_info}\n"
        f"Bu 15-30 saniye sürebilir.",
        parse_mode="Markdown",
    )

    try:
        # Araştırma (Perplexity + GPT Vision)
        research_data = await asyncio.to_thread(
            scenario_engine.research, session.collected_data
        )

        # Senaryo üretimi
        scenario = await asyncio.to_thread(
            scenario_engine.generate_scenario, session.collected_data, research_data
        )
        session.scenario = scenario

        # Senaryo özeti + onay butonları
        summary = ScenarioEngine.format_scenario_summary(scenario)

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Onayla", callback_data="scenario_approve"),
                InlineKeyboardButton("✏️ Düzelt", callback_data="scenario_edit"),
                InlineKeyboardButton("❌ İptal", callback_data="scenario_cancel"),
            ]
        ])

        conversation_mgr.mark_scenario_approval(user.id)

        await update.effective_message.reply_text(
            summary,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

    except Exception:
        log.error("Araştırma/senaryo hatası", exc_info=True)
        session.state = ConversationState.CHATTING
        await update.effective_message.reply_text(
            "⚠️ Senaryo üretiminde bir hata oluştu. Bilgileri düzeltip tekrar deneyelim.\n"
            "Hangi bilgiyi değiştirmek istersin?",
            parse_mode="Markdown",
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔘 INLINE BUTTON HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Senaryo onay/düzelt/iptal + fotoğraf teyit inline butonları."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    if not is_authorized(user.id):
        await query.edit_message_text("⛔ Yetkiniz yok.")
        return

    data = query.data

    # ── FOTOĞRAF TEYİT BUTONLARI ──
    if data.startswith("photo_"):
        result = conversation_mgr.handle_photo_confirmation(user.id, data)

        if data == "photo_confirm":
            # Fotoğraf onaylandı — araştırmaya geç
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(
                result["reply"],
                parse_mode="Markdown",
            )
            if result.get("ready_for_research"):
                # Fake update — araştırma tetiklemek için
                await _run_research_and_scenario_from_callback(query.message, user.id)

        elif data == "photo_next":
            if result.get("show_next_photo") and result.get("next_photo"):
                await query.edit_message_reply_markup(reply_markup=None)
                await _send_photo_for_confirmation(
                    query.message, user.id, result["next_photo"]
                )
            else:
                # Tüm fotoğraflar bitti
                await query.edit_message_reply_markup(reply_markup=None)
                await query.message.reply_text(
                    result["reply"],
                    parse_mode="Markdown",
                )

        elif data == "photo_skip":
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(
                result["reply"],
                parse_mode="Markdown",
            )
            if result.get("ready_for_research"):
                await _run_research_and_scenario_from_callback(query.message, user.id)

        return

    # ── SENARYO BUTONLARI ──
    if data == "scenario_approve":
        result = conversation_mgr.handle_scenario_response(user.id, "approve")

        # Butonları kaldır
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            "🚀 **Üretim başlıyor!**\n"
            "Her adımda bildirim alacaksın.",
            parse_mode="Markdown",
        )

        # Pipeline'ı arka planda çalıştır
        task = asyncio.create_task(
            _run_production(query.message, user.id)
        )
        task.add_done_callback(_handle_task_exception)

    elif data == "scenario_edit":
        result = conversation_mgr.handle_scenario_response(user.id, "edit")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            result.get("reply", "✏️ Ne değiştirmek istiyorsun?"),
            parse_mode="Markdown",
        )

    elif data == "scenario_cancel":
        result = conversation_mgr.handle_scenario_response(user.id, "cancel")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            result.get("reply", "❌ İptal edildi."),
            parse_mode="Markdown",
        )

    else:
        # Bilinmeyen callback data — eski mesaj butonları
        log.warning(f"Bilinmeyen callback data: {data}")
        await query.edit_message_reply_markup(reply_markup=None)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 ARAŞTIRMA (CALLBACK'DEN TETİKLEME)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _run_research_and_scenario_from_callback(message, user_id: int):
    """Callback handler'dan araştırma tetikleme (Update objesi yok)."""
    session = conversation_mgr.get_session(user_id)

    # State güncelle
    conversation_mgr.mark_researching(user_id)

    mode_info = "🖼️ image-to-video" if session.has_photo() else "✍️ text-to-video"

    await message.reply_text(
        f"🔍 **Marka ve ürün araştırılıyor...**\n"
        f"Mod: {mode_info}\n"
        f"Bu 15-30 saniye sürebilir.",
        parse_mode="Markdown",
    )

    try:
        research_data = await asyncio.to_thread(
            scenario_engine.research, session.collected_data
        )
        scenario = await asyncio.to_thread(
            scenario_engine.generate_scenario, session.collected_data, research_data
        )
        session.scenario = scenario

        summary = ScenarioEngine.format_scenario_summary(scenario)

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Onayla", callback_data="scenario_approve"),
                InlineKeyboardButton("✏️ Düzelt", callback_data="scenario_edit"),
                InlineKeyboardButton("❌ İptal", callback_data="scenario_cancel"),
            ]
        ])

        conversation_mgr.mark_scenario_approval(user_id)

        await message.reply_text(
            summary,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

    except Exception:
        log.error("Araştırma/senaryo hatası (callback)", exc_info=True)
        session.state = ConversationState.CHATTING
        await message.reply_text(
            "⚠️ Senaryo üretiminde bir hata oluştu. Bilgileri düzeltip tekrar deneyelim.\n"
            "Hangi bilgiyi değiştirmek istersin?",
            parse_mode="Markdown",
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎬 VIDEO ÜRETİM PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _run_production(message, user_id: int):
    """Pipeline'ı async olarak çalıştır, her adımda bildirim gönder."""
    session = conversation_mgr.get_session(user_id)
    scenario = session.scenario

    if not scenario:
        await message.reply_text("⚠️ Senaryo bulunamadı. /start ile tekrar başla.")
        return

    # Progress callback — her adımda Telegram'a bildirim
    async def progress_callback(step: str, msg: str):
        try:
            await message.reply_text(msg, parse_mode="Markdown")
        except Exception:
            log.error(f"Progress bildirim hatası: {step}", exc_info=True)

    try:
        result = await pipeline.produce(
            scenario=scenario,
            collected_data=session.collected_data,
            progress_callback=progress_callback,
            user_name=session.user_name,
        )

        if result["status"] == "success":
            video_url = result.get("video_url", "")

            # Video'yu Telegram'a gönder (URL ile)
            delivery_msg = (
                f"🎬 **Video Hazır!**\n\n"
                f"📥 **İndir:** {video_url}\n"
            )

            if result.get("cost"):
                cost = result["cost"]
                delivery_msg += f"💰 **Maliyet:** ${cost.get('total_usd', 0):.2f}\n"

            if result.get("notion_page_url"):
                delivery_msg += f"📋 **Log:** {result['notion_page_url']}\n"

            delivery_msg += "\n🔄 Yeni video için /start yaz!"

            await message.reply_text(delivery_msg, parse_mode="Markdown")

            # Video dosyasını doğrudan Telegram'a göndermeyi dene
            # stream=True ile chunk'lı indirme — RAM spike'ı önler
            try:
                import requests as req
                MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB Telegram limiti
                CHUNK_SIZE = 1024 * 1024  # 1MB chunk

                def _download_video_streamed(url: str) -> io.BytesIO | None:
                    """Video'yu stream ile indirir, 50MB'ı aşarsa None döner."""
                    resp = req.get(url, timeout=120, stream=True)
                    resp.raise_for_status()
                    # Content-Length varsa önce boyut kontrolü
                    content_length = resp.headers.get("Content-Length")
                    if content_length and int(content_length) > MAX_VIDEO_SIZE:
                        resp.close()
                        return None
                    buf = io.BytesIO()
                    downloaded = 0
                    for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                        downloaded += len(chunk)
                        if downloaded > MAX_VIDEO_SIZE:
                            resp.close()
                            buf.close()
                            return None
                        buf.write(chunk)
                    buf.seek(0)
                    return buf

                video_io = await asyncio.to_thread(_download_video_streamed, video_url)
                if video_io is not None:
                    video_io.name = "reklam_videosu.mp4"
                    await message.reply_video(
                        video=InputFile(video_io),
                        caption=f"🎬 {session.collected_data.get('brand_name', '')} — "
                                f"{session.collected_data.get('product_name', '')}",
                    )
                    video_io.close()
                else:
                    log.warning("Video 50MB'ı aşıyor — Telegram'a gönderilemedi, URL paylaşıldı")
            except Exception:
                log.warning("Video dosyası Telegram'a gönderilemedi — URL paylaşıldı", exc_info=True)

            # State güncelle
            conversation_mgr.mark_delivered(user_id)

        else:
            error = result.get("error", "Bilinmeyen hata")
            await message.reply_text(
                f"❌ **Üretim başarısız oldu**\n\n"
                f"Hata: {error[:300]}\n\n"
                f"🔄 Tekrar denemek için /start yaz.",
                parse_mode="Markdown",
            )
            session.reset()

    except Exception:
        log.error("Production pipeline çöktü", exc_info=True)
        await message.reply_text(
            "💥 **Kritik hata!** Üretim sırasında beklenmeyen bir hata oluştu.\n"
            "🔄 /start ile tekrar dene.",
            parse_mode="Markdown",
        )
        session.reset()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚠️ GLOBAL HATA HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global hata yakalayıcı — Telegram bot'un çökmesini önler."""
    log.error(f"Telegram handler hatası: {context.error}", exc_info=True)

    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Bir hata oluştu. Lütfen tekrar dene.",
                parse_mode="Markdown",
            )
        except Exception:
            pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 UYGULAMA BAŞLATMA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    """Bot'u başlat ve polling modunda çalıştır."""
    mode = "🏜️ DRY-RUN" if settings.IS_DRY_RUN else "🟢 PRODUCTION"
    log.info(f"🚀 eCom Reklam Otomasyonu v2.0 başlatılıyor... [Mod: {mode}]")
    log.info(f"📊 Model: {settings.OPENAI_MODEL}")
    log.info(f"👤 İzinli kullanıcılar: {settings.ALLOWED_USER_IDS}")

    # Telegram bot oluştur
    app = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Komutlar
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("status", cmd_status))

    # Metin mesajları (komut olmayanlar)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Fotoğraflar
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Dosya olarak gönderilen görseller
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))

    # Inline button callback
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Global hata handler
    app.add_error_handler(error_handler)

    # Session bellek temizleme task'ını başlat
    async def _start_cleanup(app_instance):
        asyncio.create_task(_cleanup_idle_sessions())
    app.post_init = _start_cleanup

    # Polling başlat
    log.info("🤖 Telegram polling başlatılıyor...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
