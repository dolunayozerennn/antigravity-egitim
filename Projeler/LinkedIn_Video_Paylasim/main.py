import logging
import time
import schedule

from core.tiktok_scraper import TikTokScraper
from core.video_processor import VideoProcessor
from core.content_filter import ContentFilter
from core.linkedin_publisher import LinkedInPublisher
from core.notion_logger import NotionLogger
from ops_logger import get_ops_logger

ops = get_ops_logger("LinkedIn_Video_Paylasim", "Pipeline")


def job():
    ops.info("Workflow Başladı", "Daily TikTok → LinkedIn Video Pipeline")

    try:
        # Initialize Core Modules
        scraper = TikTokScraper()
        processor = VideoProcessor()
        content_filter = ContentFilter()
        publisher = LinkedInPublisher()
        logger_db = NotionLogger()

        # Step 1: Fetch Recent Videos (last 10)
        recent_videos = scraper.get_recent_videos(count=10)
        if not recent_videos:
            ops.warning("Workflow Durdu", "TikTok'tan video çekilemedi")
            return

        ops.info("Video Listesi", f"{len(recent_videos)} video kontrol ediliyor")

        # Step 2: Loop through videos — find first suitable, unprocessed one
        for idx, video in enumerate(recent_videos, 1):
            video_id = video["id"]
            video_url = video["url"]
            video_title = video.get("title", "")

            # 2a: Duplication Check (already posted OR filtered)
            if logger_db.is_video_posted(video_id):
                logging.info(f"  [{idx}/{len(recent_videos)}] Skipping {video_id} — (Daha önce başarıyla yüklendi VEYA filtreden geçemediği için reddedildi)")
                continue

            ops.info("Yeni Video Bulundu", f"[{idx}/{len(recent_videos)}] ID: {video_id} — {video_title[:60]}...")

            # 2b: LLM Content Filter
            logging.info("  Running LLM content filter...")
            filter_result = content_filter.evaluate_content(video_title)
            decision = filter_result["decision"]
            reason = filter_result["reason"]
            confidence = filter_result["confidence"]

            logging.info(f"  Filter Decision: {decision} (confidence: {confidence:.2f}) — {reason}")

            if decision == "REJECT":
                logger_db.log_video(
                    video_id=video_id,
                    status="Filtered",
                    tiktok_url=video_url,
                    filter_decision="Rejected",
                    filter_reason=reason
                )
                ops.info("Video Reddedildi", f"Content filter: {reason[:100]}")
                continue

            # Step 3: Download Video (1080p)
            downloaded_path = scraper.download_video(video_url, output_id=f"linkedin_{video_id}")
            if not downloaded_path:
                ops.error("Video İndirme Başarısız", message=f"Video {video_id} indirilemedi")
                logger_db.log_video(
                    video_id=video_id,
                    status="Failed",
                    tiktok_url=video_url,
                    filter_decision="Approved",
                    filter_reason=f"Download failed. Filter reason: {reason}"
                )
                continue

            try:
                # Step 4: Metadata Strip + 1080p Ensure
                cleaned_path = processor.strip_metadata(downloaded_path)
                if not cleaned_path:
                    ops.error("FFmpeg İşleme Başarısız", message=f"Video {video_id} metadata strip hatası")
                    logger_db.log_video(
                        video_id=video_id,
                        status="Failed",
                        tiktok_url=video_url,
                        filter_decision="Approved",
                        filter_reason=f"FFmpeg processing failed. Filter reason: {reason}"
                    )
                    continue

                # Step 5: Adapt Caption for LinkedIn (LLM)
                logging.info("  Adapting caption for LinkedIn...")
                linkedin_caption = content_filter.adapt_caption_for_linkedin(video_title)
                logging.info(f"  LinkedIn Caption: '{linkedin_caption[:100]}...'")

                # Step 6: Upload Video to LinkedIn
                video_urn = publisher.upload_video(cleaned_path)
                if not video_urn:
                    ops.error("LinkedIn Upload Başarısız", message=f"Video {video_id} yüklenemedi")
                    logger_db.log_video(
                        video_id=video_id,
                        status="Failed",
                        tiktok_url=video_url,
                        filter_decision="Approved",
                        filter_reason=f"LinkedIn upload failed. Filter reason: {reason}",
                        adapted_caption=linkedin_caption
                    )
                    continue

                # Step 7: Create LinkedIn Post
                post_urn = publisher.create_post(text=linkedin_caption, video_urn=video_urn)
                if not post_urn:
                    ops.error("LinkedIn Post Başarısız", message=f"Video {video_id} post oluşturulamadı")
                    logger_db.log_video(
                        video_id=video_id,
                        status="Failed",
                        tiktok_url=video_url,
                        filter_decision="Approved",
                        filter_reason=f"Post creation failed. Filter reason: {reason}",
                        adapted_caption=linkedin_caption
                    )
                    continue

                # Step 8: Log Success
                linkedin_url = f"https://www.linkedin.com/feed/update/{post_urn}/"
                logger_db.log_video(
                    video_id=video_id,
                    status="Success",
                    tiktok_url=video_url,
                    linkedin_url=linkedin_url,
                    filter_decision="Approved",
                    filter_reason=reason,
                    adapted_caption=linkedin_caption
                )

                ops.success("Workflow Tamamlandı", f"Video başarıyla paylaşıldı — {linkedin_url}")
                return  # SUCCESS — exit after first successful post

            finally:
                # Cleanup temp files for this iteration
                scraper.clean_tmp_files(downloaded_path)
                if 'cleaned_path' in locals() and cleaned_path:
                    scraper.clean_tmp_files(cleaned_path)

        # If we reach here, all videos were either already processed or rejected
        ops.info("Workflow Tamamlandı", "Uygun yeni video bulunamadı — tümü zaten işlenmiş veya reddedilmiş")

    except Exception as e:
        ops.error("FATAL ERROR", exception=e, message=str(e)[:500])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    import os
    mode = os.environ.get("RUN_MODE", "cron").lower()

    if mode == "schedule":
        # Lokal geliştirme veya sürekli çalışan mod
        ops.info("Başlatıldı", "SCHEDULE mode (local dev) — Her gün 13:00")
        schedule.every().day.at("13:00").do(job)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        # Railway Cron modu: container açılır, job çalışır, container kapanır.
        ops.info("Başlatıldı", "CRON mode — tek çalışma")
        job()
        ops.info("Job Bitti", "Container kapanıyor")
        ops.wait_for_logs()
