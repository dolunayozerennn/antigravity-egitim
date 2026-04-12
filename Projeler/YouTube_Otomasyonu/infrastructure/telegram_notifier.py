"""
Telegram Bildirim — Pipeline sonuçlarını Telegram'a gönderir.
P1 (kritik) ve P2 (uyarı) seviye ayrımı uygular.
"""
import requests
from config import settings
from logger import get_logger

log = get_logger("TelegramNotifier")


def notify_success(content: dict, video_url: str = "", youtube_url: str = ""):
    """
    Başarılı pipeline çalışmasını bildirir.
    
    Args:
        content: {title, description, prompt} — üretilen içerik
        video_url: Kie AI CDN video URL'si
        youtube_url: YouTube video URL'si
    """
    title = content.get("title", "N/A")

    lines = [
        "✅ *YouTube Otomasyonu — Başarılı*",
        "",
        f"🎬 *Başlık:* {_escape_md(title)}",
    ]

    if youtube_url:
        lines.append(f"📺 *YouTube:* {youtube_url}")
    if video_url:
        lines.append(f"🔗 *Video:* {video_url[:100]}")

    lines.append(f"\n📝 *Prompt:* _{_escape_md(content.get('prompt', 'N/A')[:150])}..._")

    message = "\n".join(lines)
    _send_telegram(message)


def notify_error(step: str, error_msg: str, topic_info: str = ""):
    """
    P1 Kritik hata bildirimi.
    
    Args:
        step: Hangi adımda hata oluştu (prompt_generation, video_creation, vb.)
        error_msg: Hata mesajı
        topic_info: Konu bilgisi
    """
    lines = [
        "🚨 *YouTube Otomasyonu — HATA (P1)*",
        "",
        f"📍 *Adım:* {_escape_md(step)}",
        f"❌ *Hata:* {_escape_md(str(error_msg)[:300])}",
    ]

    if topic_info:
        lines.append(f"🎯 *Konu:* {_escape_md(topic_info)}")

    message = "\n".join(lines)
    _send_telegram(message)


def _send_telegram(message: str):
    """Telegram mesajı gönderir."""
    if settings.IS_DRY_RUN:
        log.info(f"🧪 DRY-RUN Telegram mesajı:\n{message}")
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_YOUTUBE_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": settings.TELEGRAM_ADMIN_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            log.info("📨 Telegram bildirimi gönderildi.")
        else:
            log.warning(f"⚠️ Telegram gönderilemedi: HTTP {response.status_code}")
    except requests.RequestException as e:
        # Telegram hatası pipeline'ı durdurmamalı
        log.warning(f"⚠️ Telegram bağlantı hatası: {e}")


def _escape_md(text: str) -> str:
    """Markdown V1 özel karakterlerini escape eder.
    
    NOT: parse_mode='Markdown' (V1) kullanıldığı için sadece V1 özel karakterleri escape edilir.
    V2 karakterleri (\\~, \\|, \\., \\!) escape etmek V1'de mesajı BOZAR.
    """
    # MarkdownV1 özel karakterler: _ * ` [
    for char in ['_', '*', '`', '[']:
        text = text.replace(char, f"\\{char}")
    return text
