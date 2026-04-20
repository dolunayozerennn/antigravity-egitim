"""
eCom Reklam Otomasyonu — Telegram Bot Entry Point
====================================================
Seedance 2.0 ile profesyonel ürün reklam videoları üreten
Telegram bot. SIFIR insan müdahalesi, MİNİMUM soru sorar.
Sadece ürün linki verilir, pipeline otomatik işler.

v3.0 — Deterministik, URL-tabanlı tam otomasyon
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
from services.firecrawl_service import FirecrawlService
from services.chat_logger import chat_tracker

# ── Core Logic ──
from core.conversation_manager import ConversationManager, ConversationState
from core.scenario_engine import ScenarioEngine
from core.production_pipeline import ProductionPipeline
from core.url_data_extractor import URLDataExtractor

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
firecrawl_svc = FirecrawlService(api_key=getattr(settings, "FIRECRAWL_API_KEY", ""))

# Core modüller — DI ile servisler enjekte edilir
conversation_mgr = ConversationManager(openai_service=openai_svc)
url_extractor = URLDataExtractor(openai_service=openai_svc, firecrawl_service=firecrawl_svc)
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

                    # PRODUCING ve RESEARCHING/URL_PROCESSING korunur
                    if state_name in ("PRODUCING", "RESEARCHING", "URL_PROCESSING"):
                        if idle_seconds > 7200:
                            to_delete.append(uid)
                        continue

                    # IDLE/DELIVERED → 10 dakika sonra temizle
                    if state_name in ("IDLE", "DELIVERED") and idle_seconds > 600:
                        to_delete.append(uid)
                    # SCENARIO_APPROVAL → 30 dakika sonra temizle
                    elif state_name in ("SCENARIO_APPROVAL") and idle_seconds > 1800:
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
    await chat_tracker.log_interaction(str(user.id), "/start", reply)


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
        ConversationState.URL_PROCESSING: "🔗 URL inceleniyor",
        ConversationState.RESEARCHING: "🔍 Araştırma & Senaryo",
        ConversationState.SCENARIO_APPROVAL: "📋 Senaryo onayı",
        ConversationState.PRODUCING: "🎬 Video üretimi",
        ConversationState.DELIVERED: "✅ Teslim edildi",
    }
    status_text = state_labels.get(session.state, "❓ Bilinmiyor")

    msg = f"📊 **Durum:** {status_text}\n"

    mode = "🏜️ DRY-RUN" if settings.IS_DRY_RUN else "🟢 PRODUCTION"
    msg += f"\n⚙️ **Mod:** {mode}"

    await update.message.reply_text(msg, parse_mode="Markdown")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💬 MESAJ HANDLER'LARI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Metin mesajı handler — ana giriş noktası (URL bekler)."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    text = update.message.text.strip()
    if not text:
        return

    user_name = user.first_name or user.username or ""
    
    # URL veya aksiyon algılama
    result = await conversation_mgr.handle_text_message(user.id, text, user_name)

    # SCENARIO_APPROVAL: Metin tabanlı onay/iptal
    if result.get("action") == "approve":
        reply_msg = "🚀 **Üretim başlıyor!**\nHer adımda bildirim alacaksın."
        await update.message.reply_text(reply_msg, parse_mode="Markdown")
        await chat_tracker.log_interaction(str(user.id), text, reply_msg)
        task = asyncio.create_task(
            _run_production(update.effective_message, user.id)
        )
        task.add_done_callback(_handle_task_exception)
        return
    elif result.get("action") == "cancel":
        await update.message.reply_text(result["reply"], parse_mode="Markdown")
        await chat_tracker.log_interaction(str(user.id), text, result["reply"])
        return

    # Normal yanıt
    if result.get("reply"):
        try:
            await update.message.reply_text(result["reply"], parse_mode="Markdown")
        except Exception:
            log.warning("Markdown parse hatası — parse_mode=None ile tekrar deneniyor")
            await update.message.reply_text(result["reply"])
            
        await chat_tracker.log_interaction(str(user.id), text, result["reply"])

    # Buton yanıtı
    if result.get("buttons"):
        try:
            btn_data = result["buttons"]
            keyboard_rows = []
            options = btn_data.get("options", [])
            choice_key = btn_data.get("choice_key", "unknown")
            question = btn_data.get("question", "Lütfen seçiminizi yapın:")
            
            for opt in options:
                val = opt.get('value', 'unkn')
                label = opt.get('label', 'Seçenek')
                cb_data = f"pref:{choice_key}:{val}"
                # Telegram callback_data limit extends to 64 bytes - ensuring it fits
                if len(cb_data.encode('utf-8')) > 64:
                    cb_data = cb_data[:64]
                keyboard_rows.append([InlineKeyboardButton(label, callback_data=cb_data)])
            
            if btn_data.get("allow_freetext"):
                cb_data = f"pref:{choice_key}:__freetext__"
                if len(cb_data.encode('utf-8')) > 64:
                    cb_data = cb_data[:64]
                keyboard_rows.append([InlineKeyboardButton("✍️ Kendi cevabımı yazacağım", callback_data=cb_data)])
            
            markup = InlineKeyboardMarkup(keyboard_rows)
            try:
                await update.message.reply_text(question, reply_markup=markup, parse_mode="Markdown")
            except Exception:
                await update.message.reply_text(question, reply_markup=markup)
                
            await chat_tracker.log_interaction(str(user.id), "[Sistem - Buton Gösterildi]", question)
        except Exception as e:
            log.error(f"Buton yanıtı oluşturulurken hata: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Seçenekler gösterilirken bir hata oluştu, lütfen manuel yazın.")

    # Eğer URL bulunduysa Pipeline'ı başlat
    if result.get("has_url") and result.get("url"):
        task = asyncio.create_task(
            _process_url_and_scenario(update.effective_message, user.id, result["url"])
        )
        task.add_done_callback(_handle_task_exception)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 Pipeline 1: URL ÇIKARMA + SENARYO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _process_url_and_scenario(message, user_id: int, url: str):
    """Arka planda veri çıkarma, araştırma ve senaryo üretimini yürütür."""
    session = conversation_mgr.get_session(user_id)

    try:
        # Adım 1: URL'den Veri Çıkarma
        extracted_data = await url_extractor.extract(url)
        session.set_extracted_data(extracted_data)

        # Adım 2: Araştırma
        conversation_mgr.mark_researching(user_id)
        await message.reply_text(
            f"🔍 **Görsel ve metin analizleri tamam!**\nMarka araştırması ve senaryo kurgulanıyor...\nBu 15-30 saniye sürebilir.",
            parse_mode="Markdown"
        )

        research_data = await asyncio.to_thread(
            scenario_engine.research, session.collected_data
        )

        # Adım 3: Senaryo Üretimi
        scenario = await asyncio.to_thread(
            scenario_engine.generate_scenario, session.collected_data, research_data, session.preferences
        )
        session.scenario = scenario

        # Senaryo Özeti + Onay
        summary = ScenarioEngine.format_scenario_summary(scenario)
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Onayla", callback_data="scenario_approve"),
                InlineKeyboardButton("❌ İptal", callback_data="scenario_cancel"),
            ]
        ])

        conversation_mgr.mark_scenario_approval(user_id)

        await message.reply_text(
            summary,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

    except Exception as e:
        log.error(f"URL işleme/senaryo hatası: {e}", exc_info=True)
        session.state = ConversationState.IDLE
        
        error_reply = (
            f"⚠️ Ürün bilgisi çıkarılamadı veya senaryo üretilemedi.\n\n"
            f"Hata detayı: {str(e)[:200]}\n\n"
            f"Lütfen bağlantıyı kontrol et ve tekrar dene."
        )
        await message.reply_text(error_reply, parse_mode=None)
        await chat_tracker.log_interaction(str(user_id), "[Sistem - Fallback URL Hatası]", error_reply)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔘 INLINE BUTTON HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Senaryo onay/iptal inline butonları."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    if not is_authorized(user.id):
        await query.edit_message_text("⛔ Yetkiniz yok.")
        return

    data = query.data

    if data == "scenario_approve":
        result = conversation_mgr.handle_scenario_response(user.id, "approve")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            "🚀 **Üretim başlıyor!**\n"
            "Her adımda bildirim alacaksın.",
            parse_mode="Markdown",
        )
        task = asyncio.create_task(
            _run_production(query.message, user.id)
        )
        task.add_done_callback(_handle_task_exception)

    elif data == "scenario_cancel":
        result = conversation_mgr.handle_scenario_response(user.id, "cancel")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            result.get("reply", "❌ İptal edildi."),
            parse_mode="Markdown",
        )
    elif data.startswith("pref:"):
        parts = data.split(":", 2)  # pref:choice_key:value
        choice_key = parts[1]
        choice_value = parts[2] if len(parts) > 2 else ""

        session = conversation_mgr.get_session(user.id)
        
        if choice_value == "__freetext__":
            # Serbest metin modu
            session.pending_choice_key = choice_key
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("✍️ Lütfen tercihini metin olarak yazarak bana gönder:")
        else:
            # Butondan seçildi
            await query.edit_message_reply_markup(reply_markup=None)
            
            result = await conversation_mgr.handle_preference_set(user.id, choice_key, choice_value)
            
            if result.get("reply"):
                try:
                    await query.message.reply_text(result["reply"], parse_mode="Markdown")
                except Exception:
                    await query.message.reply_text(result["reply"], parse_mode=None)

            if result.get("buttons"):
                btn_data = result["buttons"]
                keyboard_rows = []
                for opt in btn_data["options"]:
                    cb_data = f"pref:{btn_data['choice_key']}:{opt['value']}"
                    if len(cb_data.encode('utf-8')) > 64:
                        cb_data = cb_data[:64]
                    keyboard_rows.append([InlineKeyboardButton(opt["label"], callback_data=cb_data)])
                
                if btn_data.get("allow_freetext"):
                    cb_data = f"pref:{btn_data['choice_key']}:__freetext__"
                    if len(cb_data.encode('utf-8')) > 64:
                        cb_data = cb_data[:64]
                    keyboard_rows.append([InlineKeyboardButton("✍️ Kendi cevabımı yazacağım", callback_data=cb_data)])
                
                markup = InlineKeyboardMarkup(keyboard_rows)
                try:
                    await query.message.reply_text(btn_data["question"], reply_markup=markup, parse_mode="Markdown")
                except Exception:
                    await query.message.reply_text(btn_data["question"], reply_markup=markup)
            # Eğer URL algılandıysa (Agent text handle sonrası pipeline başlatmak isterse)
            if result.get("has_url") and result.get("url"):
                task = asyncio.create_task(
                    _process_url_and_scenario(query.message, user.id, result["url"])
                )
                task.add_done_callback(_handle_task_exception)

    else:
        log.warning(f"Bilinmeyen callback data: {data}")
        await query.edit_message_reply_markup(reply_markup=None)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎬 Pipeline 2: VIDEO ÜRETİMİ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _run_production(message, user_id: int):
    """Deterministik üretim pipeline'ını arka planda yürütür."""
    session = conversation_mgr.get_session(user_id)
    scenario = session.scenario

    if not scenario:
        await message.reply_text("⚠️ Senaryo bulunamadı. /start ile tekrar başla.")
        return

    async def progress_callback(step: str, msg: str):
        try:
            await message.reply_text(msg, parse_mode="Markdown")
        except Exception:
            # Markdown parse hatası — düz metin ile tekrar dene
            try:
                await message.reply_text(msg, parse_mode=None)
            except Exception:
                log.error(f"Progress bildirim hatası: {step}", exc_info=True)

    try:
        result = await pipeline.produce(
            scenario=scenario,
            collected_data=session.collected_data,
            progress_callback=progress_callback,
            user_name=session.user_name,
            preferences=session.preferences,
        )

        if result["status"] == "success":
            video_url = result.get("video_url", "")

            delivery_msg = (
                f"🎬 **Video Hazır!**\n\n"
                f"📥 **İndir:** {video_url}\n"
            )

            if result.get("cost"):
                cost = result["cost"]
                delivery_msg += f"💰 **Maliyet:** ${cost.get('total_usd', 0):.2f}\n"

            if result.get("notion_page_url"):
                delivery_msg += f"📋 **Log:** {result['notion_page_url']}\n"

            delivery_msg += "\n🔄 Yeni video için ürün linki gönderebilir veya /start yazabilirsin!"

            await message.reply_text(delivery_msg, parse_mode="Markdown")
            await chat_tracker.log_interaction(str(user_id), "[Sistem - Üretim Tamamlandı]", delivery_msg)

            # Native Telegram Video Upload (Fallbacks to URL)
            try:
                import requests as req
                MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB Telegram limit
                CHUNK_SIZE = 1024 * 1024  # 1MB chunk

                def _download_video_streamed(url: str) -> io.BytesIO | None:
                    resp = req.get(url, timeout=120, stream=True)
                    resp.raise_for_status()
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

            conversation_mgr.mark_delivered(user_id)

        else:
            error = result.get("error", "Bilinmeyen hata")
            error_msg = f"❌ Üretim başarısız oldu\n\nHata: {error[:300]}\n\n🔄 Tekrar link göndererek yeniden deneyebilirsin."
            await message.reply_text(error_msg, parse_mode=None)
            await chat_tracker.log_interaction(str(user_id), "[Sistem - Hata]", error_msg)
            session.reset()

    except Exception:
        log.error("Production pipeline çöktü", exc_info=True)
        await message.reply_text(
            "💥 Kritik hata! Üretim sırasında beklenmeyen bir hata oluştu.\n"
            "🔄 Linki kontrol edip tekrar dene.",
            parse_mode=None,
        )
        session.reset()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚠️ GLOBAL HATA HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_CRASHED_WITH_CONFLICT = False

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global hata yakalayıcı — Telegram bot'un çökmesini önler."""
    log.error(f"Telegram handler hatası: {context.error}", exc_info=True)

    try:
        if "Conflict" in str(context.error) or "getUpdates" in str(context.error):
            global _CRASHED_WITH_CONFLICT
            _CRASHED_WITH_CONFLICT = True
            log.warning("🔄 Conflict algılandı! Process SIGTERM gönderilerek yeniden başlatılacak...")
            import os
            import signal
            import asyncio
            # run_polling'in sonsuza kadar beklemesini önlemek için 1 sn sonra graceful kill
            asyncio.get_running_loop().call_later(1.0, lambda: os.kill(os.getpid(), signal.SIGTERM))
    except Exception as check_exc:
        log.error(f"Conflict kontrolü sırasında hata: {check_exc}")

    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Bir hata oluştu. Lütfen tekrar dene.",
                parse_mode="Markdown",
            )
        except Exception as fallback_exc:
            log.error(f"Kullanıcıya mesaj gönderilemedi: {fallback_exc}", exc_info=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 UYGULAMA BAŞLATMA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    """Bot'u başlat ve polling modunda çalıştır."""
    global _CRASHED_WITH_CONFLICT
    _CRASHED_WITH_CONFLICT = False

    mode = "🏜️ DRY-RUN" if settings.IS_DRY_RUN else "🟢 PRODUCTION"
    log.info(f"🚀 eCom Reklam Otomasyonu v3.0 başlatılıyor... [Mod: {mode}]")
    log.info(f"📊 Model: {settings.OPENAI_MODEL}")
    log.info(f"👤 İzinli kullanıcılar: {settings.ALLOWED_USER_IDS}")

    app = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("status", cmd_status))

    # Tek mesaj dinleyicisi: Linkleri algılar
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Inline button callback
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Global hata handler
    app.add_error_handler(error_handler)

    # Post-init: webhook temizle + session cleanup başlat
    async def _post_init(app_instance):
        # Conflict hatasını önle: eski webhook/polling session'ını temizle
        try:
            await app_instance.bot.delete_webhook(drop_pending_updates=True)
            log.info("✅ Webhook temizlendi, polling için hazır")
        except Exception as e:
            log.warning(f"Webhook silme uyarısı (devam ediliyor): {e}")

        # Session bellek temizleme task'ı
        asyncio.create_task(_cleanup_idle_sessions())

    app.post_init = _post_init

    log.info("🤖 Telegram polling başlatılıyor...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        poll_interval=1.0,
        timeout=30,
    )
    
    if _CRASHED_WITH_CONFLICT:
        raise RuntimeError("Bot durduruldu çünkü Conflict (409) hatası alındı!")


if __name__ == "__main__":
    import time as _startup_time

    MAX_RESTARTS = 10
    restart_count = 0

    while restart_count < MAX_RESTARTS:
        try:
            main()
            break  # Normal çıkış — restart gerekmez
        except SystemExit:
            break  # Bilerek kapatıldı
        except KeyboardInterrupt:
            log.info("Bot kullanıcı tarafından durduruldu")
            break
        except Exception as e:
            restart_count += 1
            log.error(
                f"💥 Bot çöktü (restart {restart_count}/{MAX_RESTARTS}): {e}",
                exc_info=True,
            )
            if restart_count < MAX_RESTARTS:
                wait = min(5 * restart_count, 30)
                log.info(f"🔄 {wait} saniye sonra yeniden başlatılıyor...")
                _startup_time.sleep(wait)
            else:
                log.error("❌ Maksimum restart sayısına ulaşıldı, bot durduruluyor")
                sys.exit(1)
