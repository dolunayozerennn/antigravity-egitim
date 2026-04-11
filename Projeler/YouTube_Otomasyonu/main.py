"""
YouTube Otomasyonu — Ana Orkestratör
Tüm pipeline adımlarını sırayla çalıştırır:
1. Konu seç
2. Prompt üret (GPT-4.1)
3. Video üret (Seedance 2.0)
4. Videoyu indir
5. YouTube'a yükle
6. Telegram bildirimi
7. Notion'a kaydet

Antigravity V2 Enterprise standardında.
"""
import time
import sys
import os

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from logger import get_logger
from core.topic_picker import pick_topic
from core.prompt_generator import generate_prompt
from infrastructure.seedance_client import create_video
from infrastructure.video_downloader import download_video, cleanup_video
from infrastructure.youtube_uploader import upload_to_youtube
from infrastructure.telegram_notifier import notify_success, notify_error
from infrastructure.notion_logger import NotionPageTracker

log = get_logger("Main")


def main():
    start_time = time.time()
    mode = "DRY-RUN" if settings.IS_DRY_RUN else "PRODUCTION"
    log.info(f"🚀 YouTube Otomasyonu başlatılıyor... (Mod: {mode})")
    log.info(f"   Video Model: {settings.VIDEO_MODEL}")
    log.info(f"   Süre: {settings.VIDEO_DURATION}s | Audio: {settings.GENERATE_AUDIO}")
    log.info(f"   Aspect Ratio: {settings.VIDEO_ASPECT_RATIO} | Resolution: {settings.VIDEO_RESOLUTION}")

    # Notion tracker — pipeline boyunca durumu günceller
    tracker = NotionPageTracker()
    video_path = None
    topic = None

    try:
        # ── ADIM 1: Konu Seç ──
        log.info("=" * 50)
        log.info("📚 ADIM 1/7: Konu seçiliyor...")
        topic = pick_topic()
        tracker.create_entry(topic)

        # ── ADIM 2: Prompt Üret ──
        log.info("=" * 50)
        log.info("🤖 ADIM 2/7: Prompt üretiliyor (GPT-4.1)...")
        content = generate_prompt(topic)
        tracker.update_with_content(content)
        log.info(f"   Başlık: {content['title']}")
        log.info(f"   Prompt: {content['prompt'][:100]}...")

        # ── ADIM 3: Video Üret ──
        log.info("=" * 50)
        log.info("🎬 ADIM 3/7: Video üretiliyor (Seedance 2.0)...")
        tracker.update_status("Video Üretiliyor")
        video_url = create_video(content["prompt"])
        tracker.update_with_video(video_url)

        # ── ADIM 4: Videoyu İndir ──
        log.info("=" * 50)
        log.info("📥 ADIM 4/7: Video indiriliyor...")
        video_path = download_video(video_url)

        # ── ADIM 5: YouTube'a Yükle ──
        log.info("=" * 50)
        log.info("📺 ADIM 5/7: YouTube'a yükleniyor...")
        youtube_url = upload_to_youtube(video_path, content)
        if youtube_url:
            tracker.update_with_youtube(youtube_url)

        # ── ADIM 6: Telegram Bildirimi ──
        log.info("=" * 50)
        log.info("📨 ADIM 6/7: Telegram bildirimi gönderiliyor...")
        notify_success(content, video_url=video_url, youtube_url=youtube_url)

        # ── ADIM 7: Tamamlandı ──
        elapsed = time.time() - start_time
        log.info("=" * 50)
        log.info(f"✅ ADIM 7/7: Pipeline tamamlandı! ({elapsed:.1f} saniye)")
        log.info(f"   Başlık: {content['title']}")
        if youtube_url:
            log.info(f"   YouTube: {youtube_url}")
        log.info(f"   Video: {video_url[:80]}...")

    except Exception as e:
        elapsed = time.time() - start_time
        log.error(f"❌ Pipeline HATASI ({elapsed:.1f}s): {e}", exc_info=True)

        # Hata bildirimi
        topic_info = topic.get("title_hint", "Bilinmiyor") if topic else "Konu seçilemedi"
        notify_error(
            step="pipeline",
            error_msg=str(e),
            topic_info=topic_info
        )

        # Notion'a hata kaydı
        tracker.update_with_error(str(e))

        raise

    finally:
        # Geçici video dosyasını temizle
        if video_path:
            cleanup_video(video_path)


if __name__ == "__main__":
    main()
