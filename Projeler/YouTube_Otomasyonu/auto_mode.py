"""
Auto Mode — Telegram olmadan otonom video üretimi.
CronJob veya scheduler ile belirli aralıklarla otomatik video üretir.

Kullanım:
  python3 auto_mode.py                    → auto_config.json'dan oku
  python3 auto_mode.py --topic "..."      → tek video üret
  python3 auto_mode.py --dry-run          → gerçek üretim yapmadan test

Entegrasyon:
  main.py'deki Telegram botu "manuel mod" olarak çalışır.
  auto_mode.py "otonom mod" olarak CronJob'dan tetiklenir.
  Her ikisi de AYNI pipeline'ı (prompt → video → merge → upload) kullanır.
"""
import os
import sys
import json
import time
import asyncio
import logging
import argparse
import random

sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from logger import get_logger
from core.prompt_generator import generate_prompts
from infrastructure.kie_client import KieClient
from infrastructure.replicate_merger import merge_videos
from infrastructure.video_downloader import download_video, cleanup_video
from infrastructure.youtube_uploader import upload_to_youtube
from infrastructure.notion_logger import NotionTracker
from infrastructure.telegram_notifier import notify_success, notify_error

log = get_logger("AutoMode")

# ── Auto Config dosyası ──
AUTO_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "auto_config.json")

# ── Varsayılan otonom ayarlar ──
DEFAULT_AUTO_CONFIG = {
    "enabled": False,
    "concept": "Doğa manzaraları ve görsel yolculuk",
    "topics": [
        "Okyanus dalgalarının kıyıya vuruşu, güneş batımında",
        "Kuzey ışıklarının gökyüzünde dans etmesi",
        "Bulutların üzerinde uçak penceresi görüntüsü",
        "Yoğun ormanın içinde sis arasında yürüyüş",
        "Volkanik lavların yavaşça akması, gece çekimi",
        "Yağmur damlalarının yaprak üzerinde ağır çekimde sıçraması",
        "Issız çölde rüzgarla hareket eden kum tepeleri",
        "Derin okyanus altında biyolüminesan canlılar",
        "Uzaydan Dünya'nın gece görünümü, şehir ışıkları",
        "Japon bahçesinde sakura yaprakları dökülüyor",
    ],
    "model": "seedance-2",
    "clip_count": 1,
    "orientation": "portrait",
    "audio": True,
    "is_shorts": True,
    "youtube_upload": False,
    "notify_telegram": True,
}


def load_auto_config() -> dict:
    """Auto config dosyasını yükler. Yoksa varsayılanı oluşturur."""
    if os.path.exists(AUTO_CONFIG_PATH):
        with open(AUTO_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        log.info(f"📋 Auto config yüklendi: {AUTO_CONFIG_PATH}")
        return config
    else:
        # Varsayılan config dosyasını oluştur
        with open(AUTO_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_AUTO_CONFIG, f, ensure_ascii=False, indent=2)
        log.info(f"📋 Varsayılan auto config oluşturuldu: {AUTO_CONFIG_PATH}")
        return DEFAULT_AUTO_CONFIG.copy()


def pick_topic(config: dict) -> str:
    """Konu havuzundan rastgele konu seçer."""
    topics = config.get("topics", [])
    if not topics:
        return config.get("concept", "AI Generated Video")
    return random.choice(topics)


async def run_auto_pipeline(topic: str = None, dry_run: bool = False):
    """
    Otonom pipeline'ı çalıştırır.

    Args:
        topic: Belirli bir konu (None ise config'den seçilir)
        dry_run: True ise gerçek üretim yapılmaz
    """
    config = load_auto_config()

    if not config.get("enabled") and not topic and not dry_run:
        log.info("⏸️ Auto mode devre dışı (auto_config.json → enabled: false)")
        return

    # Override'lar — settings singleton'ı doğrudan güncelle
    # (os.environ değiştirmek yetersiz: Config zaten boot time'da instantiate olmuş)
    if dry_run:
        # GÜVENLİ: auto_mode.py her zaman ayrı process olarak çalışır (CLI/CronJob)
        # Bu mutation sadece bu process'i etkiler, Telegram bot'a dokunmaz
        settings.IS_DRY_RUN = True
        settings.ENV = "development"

    # Konu seç
    selected_topic = topic or pick_topic(config)
    model = config.get("model", settings.DEFAULT_MODEL)
    clip_count = config.get("clip_count", 1)
    orientation = config.get("orientation", "portrait")
    audio = config.get("audio", True)
    is_shorts = config.get("is_shorts", True)

    log.info(f"🤖 Otonom üretim başlıyor...")
    log.info(f"   Konu: {selected_topic}")
    log.info(f"   Model: {model} | Klip: {clip_count} | Format: {orientation}")

    # Pipeline config'i
    pipeline_config = {
        "topic": selected_topic,
        "model": model,
        "clip_count": clip_count,
        "orientation": orientation,
        "audio": audio,
    }

    tracker = NotionTracker()
    kie = KieClient()
    video_paths = []
    start_time = time.time()

    try:
        # ── 1. Notion ──
        await asyncio.to_thread(tracker.create_entry, pipeline_config, trigger="auto")

        # ── 2. Prompt ──
        log.info("📋 Promptlar üretiliyor...")
        prompt_data = await generate_prompts(pipeline_config)
        await asyncio.to_thread(tracker.update_with_prompts, prompt_data)

        scenes = prompt_data.get("scenes", [])
        actual_clips = len(scenes)
        log.info(f"✅ {actual_clips} sahne promptu hazır")

        # ── 3. Video üret ──
        log.info(f"🎬 Video üretimi başlıyor ({model})...")
        await asyncio.to_thread(tracker.update_status, "Video Üretiliyor")

        if actual_clips == 1:
            video_url = await kie.create_video(
                model=model,
                prompt=scenes[0]["prompt"],
                orientation=orientation,
                duration=scenes[0].get("duration", settings.DEFAULT_DURATION),
                audio=audio,
                resolution=settings.DEFAULT_RESOLUTION,
            )
            video_urls = [video_url]
        else:
            video_urls = await kie.create_videos_batch(
                model=model,
                scenes=scenes,
                orientation=orientation,
                audio=audio,
                resolution=settings.DEFAULT_RESOLUTION,
            )

        await asyncio.to_thread(tracker.update_with_video, video_urls[0])
        log.info(f"✅ {len(video_urls)} video hazır")

        # ── 4. Birleştir ──
        final_video_url = video_urls[0]
        if len(video_urls) > 1:
            log.info("🎞️ Videolar birleştiriliyor...")
            await asyncio.to_thread(tracker.update_status, "Birleştiriliyor")
            final_video_url = await merge_videos(video_urls, keep_audio=audio)

        # ── 5. İndir ──
        video_path = download_video(final_video_url)
        video_paths.append(video_path)

        # ── 6. YouTube upload ──
        youtube_url = ""
        if config.get("youtube_upload") and settings.YOUTUBE_ENABLED:
            log.info("📺 YouTube'a yükleniyor...")
            await asyncio.to_thread(tracker.update_status, "Yükleniyor")
            youtube_url = await upload_to_youtube(video_path, prompt_data, is_shorts=is_shorts)
            if youtube_url:
                await asyncio.to_thread(tracker.update_with_youtube, youtube_url)

        # ── 7. Tamamlandı ──
        elapsed = time.time() - start_time
        log.info(f"✅ Otonom üretim tamamlandı! ({elapsed:.0f}s)")

        if not youtube_url:
            await asyncio.to_thread(tracker.update_with_youtube, "")
            await asyncio.to_thread(tracker.update_status, "✅ Tamamlandı")

        # Telegram bildirimi
        if config.get("notify_telegram"):
            content = {
                "title": prompt_data.get("youtube_title", ""),
                "description": prompt_data.get("youtube_description", ""),
                "prompt": scenes[0].get("prompt", "") if scenes else "",
            }
            await asyncio.to_thread(notify_success, content, video_url=final_video_url, youtube_url=youtube_url)

        return {
            "success": True,
            "topic": selected_topic,
            "video_url": final_video_url,
            "youtube_url": youtube_url,
            "elapsed": elapsed,
        }

    except Exception as e:
        elapsed = time.time() - start_time
        log.error(f"❌ Otonom üretim HATASI ({elapsed:.1f}s): {e}", exc_info=True)
        await asyncio.to_thread(tracker.update_with_error, str(e))

        if config.get("notify_telegram"):
            await asyncio.to_thread(notify_error, "auto_pipeline", str(e), topic_info=selected_topic)

        return {"success": False, "error": str(e)}

    finally:
        for vp in video_paths:
            cleanup_video(vp)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="YouTube Otomasyon V2 — Otonom Mod")
    parser.add_argument("--topic", type=str, help="Belirli bir konu ile üret")
    parser.add_argument("--dry-run", action="store_true", help="Gerçek üretim yapma")
    parser.add_argument("--init-config", action="store_true", help="Varsayılan config oluştur")
    args = parser.parse_args()

    if args.init_config:
        load_auto_config()
        print(f"✅ Config dosyası oluşturuldu: {AUTO_CONFIG_PATH}")
        print("   Düzenleyip 'enabled: true' yap ve CronJob olarak çalıştır.")
        return

    result = asyncio.run(run_auto_pipeline(topic=args.topic, dry_run=args.dry_run))
    if result and result.get("success"):
        log.info("🎉 Otonom üretim başarıyla tamamlandı!")
    elif result:
        log.error(f"💥 Otonom üretim başarısız: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
