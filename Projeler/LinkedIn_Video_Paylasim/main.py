import logging
import time
import schedule

from core.tiktok_scraper import TikTokScraper
from core.video_processor import VideoProcessor
from core.content_filter import ContentFilter
from core.linkedin_publisher import LinkedInPublisher
from core.notion_logger import NotionLogger


def job():
    logging.info("==============================================")
    logging.info("Starting Daily TikTok -> LinkedIn Workflow")
    logging.info("==============================================")

    try:
        # Initialize Core Modules
        scraper = TikTokScraper()
        processor = VideoProcessor()
        content_filter = ContentFilter()
        publisher = LinkedInPublisher()
        logger_db = NotionLogger()

        # Step 1: Check Latest Video
        latest_video = scraper.get_latest_video_info()
        if not latest_video:
            logging.info("Workflow Stop: Could not fetch latest video.")
            return

        video_id = latest_video["id"]
        video_url = latest_video["url"]
        video_title = latest_video.get("title", "")

        # Step 2: Duplication Check (already posted OR filtered)
        if logger_db.is_video_posted(video_id):
            logging.info(f"Workflow Stop: Video {video_id} has already been processed. Exiting early.")
            return

        logging.info(f"New video found! Video ID: {video_id} — Title: {video_title[:60]}...")

        # Step 3: LLM Content Filter
        logging.info("Running LLM content filter...")
        filter_result = content_filter.evaluate_content(video_title)
        decision = filter_result["decision"]
        reason = filter_result["reason"]
        confidence = filter_result["confidence"]

        logging.info(f"Filter Decision: {decision} (confidence: {confidence:.2f}) — {reason}")

        if decision == "REJECT":
            # Log the rejection and stop
            logger_db.log_video(
                video_id=video_id,
                status="Filtered",
                tiktok_url=video_url,
                filter_decision="Rejected",
                filter_reason=reason
            )
            logging.info(f"Workflow Stop: Video {video_id} rejected by content filter. Reason: {reason}")
            return

        # Step 4: Download Video (1080p)
        downloaded_path = scraper.download_video(video_url, output_id=f"linkedin_{video_id}")
        if not downloaded_path:
            logging.error("Workflow Stop: Video download failed.")
            logger_db.log_video(
                video_id=video_id,
                status="Failed",
                tiktok_url=video_url,
                filter_decision="Approved",
                filter_reason=f"Download failed. Filter reason: {reason}"
            )
            return

        try:
            # Step 5: Metadata Strip + 1080p Ensure
            cleaned_path = processor.strip_metadata(downloaded_path)
            if not cleaned_path:
                logging.error("Workflow Stop: Metadata stripping failed.")
                logger_db.log_video(
                    video_id=video_id,
                    status="Failed",
                    tiktok_url=video_url,
                    filter_decision="Approved",
                    filter_reason=f"FFmpeg processing failed. Filter reason: {reason}"
                )
                return

            # Step 6: Adapt Caption for LinkedIn (LLM)
            logging.info("Adapting caption for LinkedIn...")
            linkedin_caption = content_filter.adapt_caption_for_linkedin(video_title)
            logging.info(f"LinkedIn Caption: '{linkedin_caption[:100]}...'")

            # Step 7: Upload Video to LinkedIn
            video_urn = publisher.upload_video(cleaned_path)
            if not video_urn:
                logging.error("Workflow Stop: LinkedIn video upload failed.")
                logger_db.log_video(
                    video_id=video_id,
                    status="Failed",
                    tiktok_url=video_url,
                    filter_decision="Approved",
                    filter_reason=f"LinkedIn upload failed. Filter reason: {reason}",
                    adapted_caption=linkedin_caption
                )
                return

            # Step 8: Create LinkedIn Post
            post_urn = publisher.create_post(text=linkedin_caption, video_urn=video_urn)
            if not post_urn:
                logging.error("Workflow Stop: LinkedIn post creation failed.")
                logger_db.log_video(
                    video_id=video_id,
                    status="Failed",
                    tiktok_url=video_url,
                    filter_decision="Approved",
                    filter_reason=f"Post creation failed. Filter reason: {reason}",
                    adapted_caption=linkedin_caption
                )
                return

            # Step 9: Log Success
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

            logging.info("==============================================")
            logging.info(f"Workflow Complete: Video successfully posted to LinkedIn!")
            logging.info(f"LinkedIn URL: {linkedin_url}")
            logging.info("==============================================")

        finally:
            # Step 10: Cleanup
            scraper.clean_tmp_files(downloaded_path)
            if 'cleaned_path' in locals() and cleaned_path:
                scraper.clean_tmp_files(cleaned_path)

    except Exception as e:
        logging.error(f"FATAL ERROR in job: {e}", exc_info=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    import os
    mode = os.environ.get("RUN_MODE", "cron").lower()

    if mode == "schedule":
        # Lokal geliştirme veya sürekli çalışan mod
        logging.info("LinkedIn_Video_Paylasim started in SCHEDULE mode (local dev).")
        logging.info("Ensure the TZ env variable is set to 'Europe/Istanbul' on Railway for accurate timings.")
        schedule.every().day.at("13:00").do(job)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        # Railway Cron modu: container açılır, job çalışır, container kapanır.
        logging.info("LinkedIn_Video_Paylasim started in CRON mode. Running job once and exiting.")
        job()
        logging.info("Job finished. Container will now exit.")
