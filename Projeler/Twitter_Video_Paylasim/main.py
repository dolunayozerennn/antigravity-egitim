import logging
import os
import time

import schedule

import config  # boot-time validation
from core.notion_video_selector import NotionVideoSelector
from core.drive_downloader import DriveDownloader
from core.video_processor import VideoProcessor
from core.content_filter import CaptionGenerator, SuitabilityFilter
from core.typefully_publisher import TypefullyPublisher, TypefullyError, TypefullyRateLimited
from core.notion_logger import NotionLogger
from ops_logger import get_ops_logger, wait_all_loggers

ops = get_ops_logger("Twitter_Video_Paylasim", "Pipeline")


def _process_one(page, selector, drive, processor, captioner, publisher, logger_db, body_text: str = "") -> bool:
    page_id = page["page_id"]
    short_id = page_id.replace("-", "")[:8]
    name = page["name"]
    drive_url = page["drive_url"]

    ops.info("Video İşleniyor", f"[{short_id}] {name[:60]}")

    folder_id = DriveDownloader.extract_folder_id(drive_url)
    if not folder_id:
        msg = "Drive URL'sinde klasör ID yok"
        ops.warning("Drive Hatası", msg)
        logger_db.log_video(page_id=page_id, status="Failed", source_url=page.get("notion_url", ""), note=msg)
        return False

    videos = drive.list_videos(folder_id)
    if not videos:
        msg = f"Drive klasörü ({folder_id[:12]}…) erişilemez veya boş"
        ops.warning("Drive Hatası", msg)
        logger_db.log_video(page_id=page_id, status="Failed", source_url=page.get("notion_url", ""), note=msg)
        return False

    chosen = drive.select_video(videos)
    if not chosen:
        msg = f"Klasörde {config.settings.VIDEO_PATTERN_PRIORITY} pattern'ine uyan dosya yok"
        ops.warning("Dosya Seçim Hatası", msg)
        logger_db.log_video(page_id=page_id, status="Failed", source_url=page.get("notion_url", ""), note=msg)
        return False

    file_size = int(chosen.get("size", 0) or 0)
    if file_size > config.settings.MAX_VIDEO_BYTES:
        msg = f"Dosya çok büyük ({file_size/(1024**2):.0f}MB) — X (Twitter) limiti aşıldı"
        ops.warning("Boyut Limiti", msg)
        logger_db.log_video(page_id=page_id, status="Failed", source_url=page.get("notion_url", ""), note=msg)
        return False

    downloaded = drive.download_file(chosen["id"], output_name=f"tw_{short_id}_{chosen['name']}")
    if not downloaded:
        logger_db.log_video(page_id=page_id, status="Failed", source_url=page.get("notion_url", ""), note="Drive indirme başarısız")
        return False

    prepared_path = ""
    try:
        prepared_path = processor.prepare_for_upload(downloaded)
        if not prepared_path:
            logger_db.log_video(page_id=page_id, status="Failed", source_url=page.get("notion_url", ""), note="Video processor başarısız")
            return False

        if not body_text:
            body_text = selector.get_page_body_text(page_id)
        caption = captioner.generate(page, body_text)
        ops.info("Caption", f"'{caption[:140]}'")

        media_id = publisher.upload_video(prepared_path)
        if not media_id:
            logger_db.log_video(page_id=page_id, status="Failed", source_url=page.get("notion_url", ""), adapted_caption=caption, note="X video upload başarısız")
            return False

        twitter_url = publisher.post_tweet(text=caption, media_id=media_id)
        if not twitter_url:
            logger_db.log_video(page_id=page_id, status="Failed", source_url=page.get("notion_url", ""), adapted_caption=caption, note="Tweet oluşturulamadı")
            return False
        logger_db.log_video(
            page_id=page_id,
            status="Success",
            source_url=page.get("notion_url", ""),
            twitter_url=twitter_url,
            adapted_caption=caption,
            note=f"Drive file: {chosen['name']}",
        )
        ops.success("Workflow Tamamlandı", f"Yayınlandı → {twitter_url}")
        return True

    finally:
        drive.cleanup(downloaded)
        if prepared_path and prepared_path != downloaded:
            drive.cleanup(prepared_path)


def job():
    ops.info("Workflow Başladı", "Notion → Drive → X (Twitter) (master kalite)")
    try:
        selector = NotionVideoSelector()
        drive = DriveDownloader()
        processor = VideoProcessor()
        captioner = CaptionGenerator()
        suitability = SuitabilityFilter()
        publisher = TypefullyPublisher()
        logger_db = NotionLogger()

        pages = selector.query_published()
        if not pages:
            ops.warning("Workflow Durdu", "'Yayınlandı' video yok")
            return

        for raw in pages:
            page = NotionVideoSelector.parse_page(raw)
            if not page["drive_url"]:
                ops.info("Atlandı", f"{page['name'][:40]} — Drive linki yok")
                continue
            if logger_db.is_video_posted(page["page_id"]):
                ops.info("Atlandı", f"{page['name'][:40]} — zaten işlenmiş")
                continue
            if page.get("is_youtube"):
                ops.info("Filtrelendi", f"{page['name'][:40]} — YouTube videosu (X için uygun değil)")
                logger_db.log_video(
                    page_id=page["page_id"],
                    status="Filtered",
                    source_url=page.get("notion_url", ""),
                    note="YouTube videosu — X'te short-form olarak paylaşılmıyor",
                )
                continue
            body_text = selector.get_page_body_text(page["page_id"])
            ok, reason = suitability.is_suitable(page, body_text)
            if not ok:
                ops.info("Filtrelendi", f"{page['name'][:40]} — {reason}")
                logger_db.log_video(
                    page_id=page["page_id"],
                    status="Filtered",
                    source_url=page.get("notion_url", ""),
                    note=f"X için uygun değil: {reason}",
                )
                continue
            if _process_one(page, selector, drive, processor, captioner, publisher, logger_db, body_text):
                return

        ops.info("Workflow Tamamlandı", "Yeni paylaşılacak video kalmadı")
    except TypefullyRateLimited as e:
        ops.warning("Rate Limit — Workflow Durdu", f"Typefully: {e}. Sonraki cron'da denenecek.")
    except TypefullyError as e:
        ops.error("Typefully Upstream Hatası — Workflow Durdu", message=str(e)[:500])
    except Exception as e:
        ops.error("FATAL ERROR", exception=e, message=str(e)[:500])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    mode = os.environ.get("RUN_MODE", "cron").lower()
    if mode == "schedule":
        ops.info("Başlatıldı", "SCHEDULE mode (local dev) — Her gün 11:00, 14:00, 17:00")
        schedule.every().day.at("11:00").do(job)
        schedule.every().day.at("14:00").do(job)
        schedule.every().day.at("17:00").do(job)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        ops.info("Başlatıldı", "CRON mode — tek çalışma")
        job()
        ops.info("Job Bitti", "Container kapanıyor")
        wait_all_loggers()
