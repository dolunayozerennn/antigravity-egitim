#!/usr/bin/env python3
"""
YouTube Otomasyonu V2 — Chat-Based Telegram Bot
================================================
Kullanıcı Telegram'dan sohbet eder → Bot bilgileri toplar →
Otonom olarak video üretir → YouTube'a yükler → Bildirim gönderir.

7/24 Railway'de çalışır (polling mode).
Antigravity V2 Enterprise standardında.
"""
import os
import sys
import io
import time
import asyncio
import logging
import traceback

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(__file__))

from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import Conflict, NetworkError, TimedOut

from config import settings
from logger import get_logger
from core.conversation_manager import ConversationManager
from core.prompt_generator import generate_prompts
from infrastructure.kie_client import KieClient
from infrastructure.replicate_merger import merge_videos
from infrastructure.video_downloader import download_video, cleanup_video
from infrastructure.youtube_uploader import upload_to_youtube
from infrastructure.notion_logger import NotionTracker

log = get_logger("YouTubeBot")

# ── Servisler ──
conversation = ConversationManager()
kie = KieClient()


# ────────────────────────────────────────
# 🔒 YETKİ KONTROLÜ
# ────────────────────────────────────────

def _is_authorized(user_id: int) -> bool:
    """Admin kullanıcı mı kontrol eder."""
    return user_id in settings.ALLOWED_USER_IDS


# ────────────────────────────────────────
# 🤖 COMMAND HANDLERS
# ────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot başlangıç mesajı."""
    if not _is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Bu botu kullanma yetkiniz yok.")
        return

    welcome = (
        "👋 Merhaba! Ben **YouTube Video Üretim Botu**.\n\n"
        "🎬 Bana ne tür bir video istediğini anlat, "
        "ben sana sorular soracağım ve üretimi başlatacağım.\n\n"
        "💡 **Örnek:** \"Uzayda yüzen astronot videosu istiyorum\"\n\n"
        "🎤 Yazabilir veya **sesli mesaj** da gönderebilirsin!\n\n"
        "📋 **Komutlar:**\n"
        "/start — Bu mesajı göster\n"
        "/yeni — Yeni video talebi başlat\n"
        "/durum — Bot durumu\n"
        "/modeller — Kullanılabilir video modelleri"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def cmd_yeni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Konuşma durumunu sıfırla — yeni video talebi."""
    if not _is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Bu botu kullanma yetkiniz yok.")
        return

    conversation.reset_state(update.effective_user.id)
    await update.message.reply_text(
        "🔄 Yeni konuşma başlatıldı!\n\n"
        "Ne tür bir video üretmek istersin? 🎬"
    )


async def cmd_durum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot durum kontrolü."""
    if not _is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Bu botu kullanma yetkiniz yok.")
        return

    state = conversation.get_state(update.effective_user.id)
    pipeline_status = "🔄 Pipeline çalışıyor..." if state.pipeline_running else "✅ Hazır"

    status = (
        f"✅ **Bot Durumu: Aktif**\n\n"
        f"⚙️ Pipeline: {pipeline_status}\n"
        f"🤖 Default Model: `{settings.DEFAULT_MODEL}`\n"
        f"📺 YouTube Upload: `{'Aktif' if settings.YOUTUBE_ENABLED else 'Devre Dışı'}`\n"
        f"📋 Notion Log: `{'Aktif' if settings.NOTION_ENABLED else 'Devre Dışı'}`\n"
        f"🌍 Ortam: `{settings.ENV}`"
    )
    await update.message.reply_text(status, parse_mode="Markdown")


async def cmd_modeller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanılabilir model bilgisi."""
    if not _is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Bu botu kullanma yetkiniz yok.")
        return

    models_text = (
        "🎬 **Kullanılabilir Video Modelleri:**\n\n"
        "1️⃣ **Seedance 2.0** — Uygun Fiyatlı 💰\n"
        "   • ByteDance altyapısı\n"
        "   • Kamera kontrolü, native ses\n"
        "   • 720p, 4-15 saniye\n"
        "   • ⚡ Daha hızlı üretim\n\n"
        "2️⃣ **Veo 3.1** — Premium Kalite 💎\n"
        "   • Google DeepMind\n"
        "   • 1080p sinematik kalite\n"
        "   • İnsan yüzlerinde üstün\n"
        "   • 💰 ~4x daha pahalı\n\n"
        "Video talebinde model tercihini belirtebilirsin,\n"
        "yoksa ben öneriyorum! 🤖"
    )
    await update.message.reply_text(models_text, parse_mode="Markdown")


# ────────────────────────────────────────
# 💬 MESAJ İŞLEME
# ────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Metin mesajlarını conversation_manager'a yönlendirir."""
    user = update.effective_user
    if not _is_authorized(user.id):
        await update.message.reply_text("⛔ Bu botu kullanma yetkiniz yok.")
        return

    text = update.message.text
    log.info(f"💬 Mesaj alındı: user={user.id} msg={text[:50]}...")

    result = await conversation.process_message(user.id, text)

    action = result.get("action", "chat")
    reply = result.get("reply", "🤖 Bir hata oluştu.")
    config = result.get("config")

    # Yanıtı gönder
    await update.message.reply_text(reply, parse_mode="Markdown")

    # Pipeline tetikleme
    if action == "start_pipeline" and config:
        await _run_pipeline(update, context, config)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sesli mesajları Whisper ile transkript edip işler."""
    user = update.effective_user
    if not _is_authorized(user.id):
        await update.message.reply_text("⛔ Bu botu kullanma yetkiniz yok.")
        return

    log.info(f"🎤 Sesli mesaj alındı: user={user.id}")
    waiting_msg = await update.message.reply_text("🎤 Sesli mesajın transkript ediliyor...")

    try:
        voice = update.message.voice
        file = await voice.get_file()
        bio = io.BytesIO()
        await file.download_to_memory(bio)
        audio_bytes = bio.getvalue()

        result = await conversation.process_voice_transcription(user.id, audio_bytes)

        action = result.get("action", "chat")
        reply = result.get("reply", "🤖 Bir hata oluştu.")
        config = result.get("config")

        await waiting_msg.edit_text(reply, parse_mode="Markdown")

        if action == "start_pipeline" and config:
            await _run_pipeline(update, context, config)

    except Exception:
        log.error("Sesli mesaj işleme hatası", exc_info=True)
        await waiting_msg.edit_text("❌ Sesli mesaj işlenemedi. Lütfen tekrar dene.")


# ────────────────────────────────────────
# ⚙️ PIPELINE ORKESTRATÖRÜ
# ────────────────────────────────────────

async def _run_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE, config: dict):
    """Video üretim pipeline'ını çalıştırır."""
    user = update.effective_user
    state = conversation.get_state(user.id)
    state.pipeline_running = True

    tracker = NotionTracker()
    video_paths = []
    start_time = time.time()

    try:
        # ── ADIM 1: Notion Entry ──
        tracker.create_entry(config, trigger="telegram")

        # ── ADIM 2: Prompt Üret ──
        status_msg = await update.message.reply_text("📋 Prompt(lar) yazılıyor...")

        prompt_data = await generate_prompts(config)
        tracker.update_with_prompts(prompt_data)

        scenes = prompt_data.get("scenes", [])
        model = config.get("model", settings.DEFAULT_MODEL)
        clip_count = len(scenes)

        await status_msg.edit_text(
            f"✅ {clip_count} sahne promptu hazır!\n"
            f"🎬 Video üretimi başlıyor ({model})..."
        )

        # ── ADIM 3: Video Üret ──
        tracker.update_status("Video Üretiliyor")

        if clip_count == 1:
            # Tek klip
            video_url = await kie.create_video(
                model=model,
                prompt=scenes[0]["prompt"],
                orientation=config.get("orientation", "portrait"),
                duration=scenes[0].get("duration", settings.DEFAULT_DURATION),
                audio=config.get("audio", True),
                resolution=settings.DEFAULT_RESOLUTION,
            )
            video_urls = [video_url]
        else:
            # Çoklu klip
            video_urls = await kie.create_videos_batch(
                model=model,
                scenes=scenes,
                orientation=config.get("orientation", "portrait"),
                audio=config.get("audio", True),
                resolution=settings.DEFAULT_RESOLUTION,
            )

        tracker.update_with_video(video_urls[0])
        await status_msg.edit_text(f"✅ {len(video_urls)} video hazır!")

        # ── ADIM 4: Birleştirme (gerekliyse) ──
        final_video_url = video_urls[0]

        if len(video_urls) > 1:
            await status_msg.edit_text("🎞️ Videolar birleştiriliyor...")
            tracker.update_status("Birleştiriliyor")
            final_video_url = await merge_videos(video_urls, keep_audio=config.get("audio", True))

        # ── ADIM 5: Video İndir ──
        await status_msg.edit_text("📥 Video indiriliyor...")
        video_path = download_video(final_video_url)
        video_paths.append(video_path)

        # ── ADIM 6: YouTube Upload ──
        is_shorts = clip_count == 1
        youtube_url = ""

        if settings.YOUTUBE_ENABLED:
            await status_msg.edit_text("📺 YouTube'a yükleniyor...")
            tracker.update_status("Yükleniyor")
            youtube_url = await upload_to_youtube(video_path, prompt_data, is_shorts=is_shorts)
            if youtube_url:
                tracker.update_with_youtube(youtube_url)

        # ── ADIM 7: Tamamlandı ──
        elapsed = time.time() - start_time

        success_lines = [
            f"✅ **Video üretimi tamamlandı!** ({elapsed:.0f}s)\n",
            f"🎬 *{prompt_data.get('youtube_title', 'Video')}*",
        ]
        if youtube_url:
            success_lines.append(f"📺 YouTube: {youtube_url}")
        if final_video_url and final_video_url.startswith("http"):
            success_lines.append(f"🔗 Video: {final_video_url[:80]}...")
        success_lines.append(f"\n📊 Model: {model} | Sahneler: {clip_count}")

        await status_msg.edit_text("\n".join(success_lines), parse_mode="Markdown")

        if not youtube_url:
            tracker.update_with_youtube("")
            tracker.update_status("✅ Tamamlandı")

        log.info(f"✅ Pipeline tamamlandı! ({elapsed:.1f}s)")

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        log.error(f"❌ Pipeline HATASI ({elapsed:.1f}s): {error_msg}", exc_info=True)

        # Kullanıcıya bildir
        try:
            await update.message.reply_text(
                f"❌ **Video üretimi başarısız oldu.**\n\n"
                f"Hata: `{error_msg[:200]}`\n\n"
                f"/yeni komutuyla tekrar deneyebilirsin.",
                parse_mode="Markdown"
            )
        except Exception:
            pass

        # Notion'a hata kaydı
        tracker.update_with_error(error_msg)

    finally:
        # State sıfırla
        state.pipeline_running = False
        conversation.reset_state(user.id)

        # Temp dosyaları temizle
        for vp in video_paths:
            cleanup_video(vp)


# ────────────────────────────────────────
# 🚨 HATA YÖNETİMİ
# ────────────────────────────────────────

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global hata yakalayıcı — bilinen hataları bastırır."""
    error = context.error

    # Bilinen ve güvenle göz ardı edilebilen hatalar
    if isinstance(error, Conflict):
        log.warning("⚠️ Telegram Conflict — muhtemelen birden fazla bot instance çalışıyor.")
        return
    if isinstance(error, (NetworkError, TimedOut)):
        log.warning(f"⚠️ Telegram ağ hatası: {error}")
        return

    log.error(f"🚨 Beklenmeyen hata: {error}", exc_info=True)


# ────────────────────────────────────────
# 🚀 MAIN
# ────────────────────────────────────────

async def post_init(application):
    """Bot başlatıldığında komut listesini ayarla."""
    commands = [
        BotCommand("start", "Bot hakkında bilgi"),
        BotCommand("yeni", "Yeni video talebi başlat"),
        BotCommand("durum", "Bot durumu"),
        BotCommand("modeller", "Video modelleri"),
    ]
    await application.bot.set_my_commands(commands)
    bot_info = await application.bot.get_me()
    log.info(f"🚀 YouTube Bot V2 başlatıldı: @{bot_info.username} (ID: {bot_info.id})")


def main():
    """Bot entrypoint — polling mode ile 7/24 çalışır."""
    mode = "DRY-RUN" if settings.IS_DRY_RUN else "PRODUCTION"
    log.info(f"🚀 YouTube Otomasyonu V2 başlatılıyor... (Mod: {mode})")
    log.info(f"   Default Model: {settings.DEFAULT_MODEL}")
    log.info(f"   YouTube Upload: {'Aktif' if settings.YOUTUBE_ENABLED else 'Devre Dışı'}")
    log.info(f"   Notion Log: {'Aktif' if settings.NOTION_ENABLED else 'Devre Dışı'}")

    app = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_YOUTUBE_BOT_TOKEN)
        .post_init(post_init)
        .concurrent_updates(True)
        .build()
    )

    # Komutlar
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("yeni", cmd_yeni))
    app.add_handler(CommandHandler("durum", cmd_durum))
    app.add_handler(CommandHandler("modeller", cmd_modeller))

    # Sesli mesaj
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Metin mesajları
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Hata yakalayıcı
    app.add_error_handler(error_handler)

    log.info("📡 Polling başlatıldı — 7/24 aktif")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        stop_signals=None,  # Railway uyumluluğu
    )


if __name__ == "__main__":
    main()
