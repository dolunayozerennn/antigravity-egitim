#!/usr/bin/env python3
"""
Supplement Buddy — Telegram Bot
================================
Fotoğraf gönder → Gemini Vision ile analiz → Notion'a logla
Metin gönder → Gemini Chat ile yanıtla

7/24 Railway'de çalışır (polling mode).
"""

import asyncio
import io
import traceback

from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import settings
from logger import get_logger
from core.gemini_analyzer import analyze_image_bytes, chat_with_gemini
from infrastructure.notion_service import NotionLogger

log = get_logger("supplement_bot")

# ── Notion Service ──
notion = NotionLogger(
    token=settings.NOTION_TOKEN,
    database_id=settings.NOTION_DB_ID,
)

# ────────────────────────────────────────
# 🤖 COMMAND HANDLERS
# ────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot başlangıç mesajı."""
    user = update.effective_user
    if settings.ALLOWED_USER_IDS and user.id not in settings.ALLOWED_USER_IDS:
        await update.message.reply_text("⛔ Bu botu kullanma yetkiniz yok.")
        return

    welcome = (
        "👋 Merhaba! Ben **Supplement Buddy**.\n\n"
        "📸 Bana bir supplement/vitamin fotoğrafı gönder, "
        "içindeki tüm bilgileri çıkarayım ve Notion'a kaydedeyim.\n\n"
        "💬 Supplement hakkında soru sormak istersen, yaz yeter!\n\n"
        "📋 **Komutlar:**\n"
        "/start — Bu mesajı göster\n"
        "/help — Yardım\n"
        "/durum — Bot durumu"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yardım mesajı."""
    user = update.effective_user
    if settings.ALLOWED_USER_IDS and user.id not in settings.ALLOWED_USER_IDS:
        await update.message.reply_text("⛔ Bu botu kullanma yetkiniz yok.")
        return

    help_text = (
        "**📸 Fotoğraf Analizi:**\n"
        "Bir supplement/vitamin etiketi fotoğrafı gönder.\n"
        "Birden fazla fotoğrafı aynı anda gönderebilirsin.\n"
        "Bot analiz edip Notion'a kaydeder.\n\n"
        "**💬 Sohbet:**\n"
        "Herhangi bir metin yaz, ben yanıtlarım.\n"
        "Supplement/vitamin soruları için özelleştirilmiş yanıt veririm.\n\n"
        "**📂 Loglar:**\n"
        "Tüm analizler otomatik olarak Notion'daki "
        "Supplement Analiz Logları database'ine kaydedilir."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def cmd_durum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot durum kontrolü."""
    user = update.effective_user
    if settings.ALLOWED_USER_IDS and user.id not in settings.ALLOWED_USER_IDS:
        await update.message.reply_text("⛔ Bu botu kullanma yetkiniz yok.")
        return

    status = (
        "✅ **Bot Durumu: Aktif**\n\n"
        f"🤖 Model: `{settings.GEMINI_MODEL}`\n"
        "🗄️ Notion DB: `[Bağlandı - Gizli]`\n"
        f"🌍 Ortam: `{settings.ENV}`"
    )
    await update.message.reply_text(status, parse_mode="Markdown")


# ────────────────────────────────────────
# 📸 FOTOĞRAF İŞLEME
# ────────────────────────────────────────

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gelen fotoğrafı Gemini ile analiz et ve Notion'a kaydet."""
    user = update.effective_user
    log.info(f"Fotoğraf alındı: user={user.id} ({user.first_name})")

    # Yetki kontrolü (yapılandırılmışsa)
    if settings.ALLOWED_USER_IDS and user.id not in settings.ALLOWED_USER_IDS:
        await update.message.reply_text("⛔ Bu botu kullanma yetkiniz yok.")
        return

    # Bekleme mesajı
    waiting_msg = await update.message.reply_text(
        "🔬 Fotoğraf analiz ediliyor... Lütfen bekle (~15 saniye)"
    )

    try:
        # En yüksek çözünürlüklü fotoğrafı al
        photo = update.message.photo[-1]  # Son eleman = en büyük
        file = await photo.get_file()

        # Fotoğrafı indir
        bio = io.BytesIO()
        await file.download_to_memory(bio)
        image_bytes = bio.getvalue()

        log.info(f"İndirilen boyut: {len(image_bytes)} bytes")

        # ── Gemini Analiz ──
        result = analyze_image_bytes(
            image_bytes=image_bytes,
            mime_type="image/jpeg",
            model_name=settings.GEMINI_MODEL,
            api_key=settings.GEMINI_API_KEY,
        )

        success = result["success"]
        parsed = result.get("parsed") or {}

        # ── Notion'a Kaydet ──
        notion_url = None
        if not settings.IS_DRY_RUN:
            notion_url = notion.log_analysis(
                analysis_result=result,
                model=settings.GEMINI_MODEL,
                success=success,
            )
        else:
            log.info("DRY_RUN modu — Notion'a yazma atlanıyor")

        # ── Kullanıcıya Yanıt Oluştur ──
        reply = _format_analysis_reply(parsed, success, notion_url)

        await waiting_msg.edit_text(reply, parse_mode="Markdown")

    except Exception:
        log.error("Fotoğraf analiz hatası", exc_info=True)
        await waiting_msg.edit_text(
            "❌ Analiz sırasında bir hata oluştu. Lütfen tekrar dene."
        )


async def handle_document_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dosya olarak gönderilen fotoğrafları da yakala."""
    doc = update.message.document
    if not doc or not doc.mime_type or not doc.mime_type.startswith("image/"):
        # Fotoğraf değilse chat'e yönlendir
        await handle_text(update, context)
        return

    user = update.effective_user
    log.info(f"Dosya-fotoğraf alındı: user={user.id} mime={doc.mime_type}")

    if settings.ALLOWED_USER_IDS and user.id not in settings.ALLOWED_USER_IDS:
        await update.message.reply_text("⛔ Bu botu kullanma yetkiniz yok.")
        return

    waiting_msg = await update.message.reply_text(
        "🔬 Fotoğraf analiz ediliyor... Lütfen bekle (~15 saniye)"
    )

    try:
        file = await doc.get_file()
        bio = io.BytesIO()
        await file.download_to_memory(bio)
        image_bytes = bio.getvalue()

        result = analyze_image_bytes(
            image_bytes=image_bytes,
            mime_type=doc.mime_type,
            model_name=settings.GEMINI_MODEL,
            api_key=settings.GEMINI_API_KEY,
        )

        success = result["success"]
        parsed = result.get("parsed") or {}

        notion_url = None
        if not settings.IS_DRY_RUN:
            notion_url = notion.log_analysis(
                analysis_result=result,
                model=settings.GEMINI_MODEL,
                success=success,
            )

        reply = _format_analysis_reply(parsed, success, notion_url)
        await waiting_msg.edit_text(reply, parse_mode="Markdown")

    except Exception:
        log.error("Dosya-fotoğraf analiz hatası", exc_info=True)
        await waiting_msg.edit_text(
            "❌ Analiz sırasında bir hata oluştu. Lütfen tekrar dene."
        )


# ────────────────────────────────────────
# 💬 SOHBET (CHAT)
# ────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Metin mesajlarını Gemini Chat ile yanıtla."""
    user = update.effective_user
    message_text = update.message.text

    if settings.ALLOWED_USER_IDS and user.id not in settings.ALLOWED_USER_IDS:
        await update.message.reply_text("⛔ Bu botu kullanma yetkiniz yok.")
        return

    log.info(f"Chat mesajı: user={user.id} msg={message_text[:50]}...")

    try:
        reply = chat_with_gemini(
            message=message_text,
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL,
        )
        # Telegram markdown limit: 4096 char
        if len(reply) > 4000:
            reply = reply[:4000] + "..."

        await update.message.reply_text(reply)

    except Exception:
        log.error("Chat hatası", exc_info=True)
        await update.message.reply_text(
            "❌ Yanıt oluşturulurken bir hata oluştu. Lütfen tekrar dene."
        )


# ────────────────────────────────────────
# 📝 YARDIMCI FONKSİYONLAR
# ────────────────────────────────────────

def _format_analysis_reply(parsed: dict, success: bool, notion_url: str | None) -> str:
    """Analiz sonucunu kullanıcıya gösterilecek Telegram mesajına dönüştür."""
    if not success or not parsed:
        return (
            "⚠️ Fotoğraftan yeterli bilgi çıkarılamadı.\n"
            "Lütfen daha net bir etiket fotoğrafı gönder."
        )

    urun = parsed.get("urun_bilgisi", {})
    icerik = parsed.get("icerik_tablosu", [])
    kullanim = parsed.get("kullanim_onerisi", {})

    lines = []
    lines.append(f"✅ *{urun.get('urun_adi', 'Ürün')}*")
    if urun.get("marka"):
        lines.append(f"🏷️ Marka: {urun['marka']}")
    if urun.get("urun_turu"):
        lines.append(f"💊 Tür: {urun['urun_turu']}")

    lines.append(f"\n📊 *İçerik Tablosu ({len(icerik)} madde):*")

    # İlk 10 maddeyi göster
    for item in icerik[:10]:
        madde = item.get("madde_adi", "")
        miktar = item.get("miktar", "")
        birim = item.get("birim", "")
        brd = item.get("brd_yuzde", "")
        miktar_str = f"{miktar} {birim}".strip() if birim else str(miktar)
        brd_str = f" ({brd})" if brd else ""
        lines.append(f"  • {madde}: {miktar_str}{brd_str}")

    if len(icerik) > 10:
        lines.append(f"  _...ve {len(icerik) - 10} madde daha_")

    if kullanim.get("onerilen_kullanim"):
        lines.append(f"\n💡 *Kullanım:* {kullanim['onerilen_kullanim']}")

    if notion_url:
        lines.append("\n✅ Notion'a kaydedildi.")
    else:
        lines.append("\n⚠️ _Notion'a kayıt başarısız oldu_")

    return "\n".join(lines)


# ────────────────────────────────────────
# 🚀 MAIN
# ────────────────────────────────────────

async def post_init(application):
    """Bot başlatıldığında komut listesini ayarla."""
    commands = [
        BotCommand("start", "Bot hakkında bilgi"),
        BotCommand("help", "Yardım"),
        BotCommand("durum", "Bot durumu"),
    ]
    await application.bot.set_my_commands(commands)
    bot_info = await application.bot.get_me()
    log.info(f"Bot başlatıldı: @{bot_info.username} (ID: {bot_info.id})")


def main():
    """Bot entrypoint — polling mode ile 7/24 çalışır."""
    log.info(f"Supplement Buddy başlatılıyor... ENV={settings.ENV}")

    if not settings.ALLOWED_USER_IDS:
        log.warning("⚠️ DİKKAT: ALLOWED_USER_IDS boş! Bot HERKESE AÇIK durumda çalışıyor.")
        log.warning("⚠️ DİKKAT: Kötü niyetli kullanım Gemini kotanızı ve Notion veritabanınızı doldurabilir!")

    app = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Komutlar
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("durum", cmd_durum))

    # Fotoğraf (sıkıştırılmış)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Dosya olarak gönderilen fotoğraflar
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document_photo))

    # Metin mesajları (chat)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    log.info("Polling başlatıldı — 7/24 aktif")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
