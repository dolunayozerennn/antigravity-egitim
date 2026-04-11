"""
eCom Reklam Otomasyonu — Telegram Bot Entry Point
====================================================
Seedance 2.0 ile profesyonel ürün reklam videoları üreten
Telegram bot. Doğal sohbet ile bilgi toplar, senaryo üretir,
video üretim pipeline'ını çalıştırır.

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
        ConversationState.RESEARCHING: "🔍 Araştırma",
        ConversationState.SCENARIO_APPROVAL: "📋 Senaryo onayı",
        ConversationState.PRODUCING: "🎬 Video üretimi",
        ConversationState.DELIVERED: "✅ Teslim edildi",
    }
    status_text = state_labels.get(session.state, "❓ Bilinmiyor")

    msg = f"📊 **Durum:** {status_text}\n"
    if session.state == ConversationState.CHATTING:
        missing = session.get_missing_fields()
        if missing:
            msg += f"📋 Eksik bilgiler: {', '.join(missing)}\n"
        if session.collected_data.get("product_image"):
            msg += "📸 Ürün fotoğrafı: ✅\n"
        else:
            msg += "📸 Ürün fotoğrafı: ❌\n"

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
    result = conversation_mgr.handle_text_message(user.id, text, user_name)

    await update.message.reply_text(result["reply"], parse_mode="Markdown")

    # Tüm bilgiler toplandı → araştırma ve senaryo üretimine geç
    if result["ready_for_research"]:
        await _run_research_and_scenario(update, context)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fotoğraf handler — ürün görseli alır ve ImgBB'ye yükler."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    user_name = user.first_name or user.username or ""

    # En yüksek çözünürlüklü fotoğrafı al
    photo = update.message.photo[-1]

    try:
        # Telegram'dan dosyayı indir
        file = await photo.get_file()
        file_bytes = await file.download_as_bytearray()

        # ImgBB'ye yükle
        await update.message.reply_text("📤 Fotoğraf yükleniyor...", parse_mode="Markdown")
        upload_result = imgbb_svc.upload_image_bytes(bytes(file_bytes), name="product_ecom")
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
    if result["ready_for_research"]:
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
        upload_result = imgbb_svc.upload_image_bytes(bytes(file_bytes), name="product_ecom_doc")
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

    if result["ready_for_research"]:
        await _run_research_and_scenario(update, context)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 ARAŞTIRMA + SENARYO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _run_research_and_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Araştırma + senaryo üretimi — ağır iş, arka planda çalışır."""
    user = update.effective_user
    session = conversation_mgr.get_session(user.id)

    # State güncelle
    conversation_mgr.mark_researching(user.id)

    await update.effective_message.reply_text(
        "🔍 **Marka ve ürün araştırılıyor...**\n"
        "Bu 15-30 saniye sürebilir.",
        parse_mode="Markdown",
    )

    try:
        # Araştırma (Perplexity + GPT-5 Vision)
        research_data = scenario_engine.research(session.collected_data)

        # Senaryo üretimi
        scenario = scenario_engine.generate_scenario(session.collected_data, research_data)
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
    """Senaryo onay/düzelt/iptal inline butonları."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    if not is_authorized(user.id):
        await query.edit_message_text("⛔ Yetkiniz yok.")
        return

    data = query.data

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
        asyncio.create_task(
            _run_production(query.message, user.id)
        )

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
            try:
                import requests as req
                video_resp = req.get(video_url, timeout=120)
                if video_resp.status_code == 200 and len(video_resp.content) < 50 * 1024 * 1024:
                    video_io = io.BytesIO(video_resp.content)
                    video_io.name = "reklam_videosu.mp4"
                    await message.reply_video(
                        video=InputFile(video_io),
                        caption=f"🎬 {session.collected_data.get('brand_name', '')} — "
                                f"{session.collected_data.get('product_name', '')}",
                    )
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
    log.info(f"🚀 eCom Reklam Otomasyonu başlatılıyor... [Mod: {mode}]")
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

    # Polling başlat
    log.info("🤖 Telegram polling başlatılıyor...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
