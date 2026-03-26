import logging
import time
import schedule

from core.tiktok_scraper import TikTokScraper
from core.video_processor import VideoProcessor
from core.x_publisher import XPublisher
from core.notion_logger import NotionLogger

def job():
    logging.info("==============================================")
    logging.info("Starting Daily TikTok -> X (Twitter) Workflow")
    logging.info("==============================================")
    
    try:
        # Initialize Core Modules
        scraper = TikTokScraper()
        processor = VideoProcessor()
        publisher = XPublisher()
        logger_db = NotionLogger()

        # Step 1: Check Latest Video
        latest_video = scraper.get_latest_video_info()
        if not latest_video:
            logging.info("Workflow Stop: Could not fetch latest video.")
            return

        video_id = latest_video["id"]
        video_url = latest_video["url"]
        
        # Step 2: Duplication Check
        if logger_db.is_video_posted(video_id):
            logging.info(f"Workflow Stop: Video {video_id} has already been posted previously. Exiting early.")
            return
            
        logging.info(f"New video found! Video ID: {video_id} will be processed now.")
        
        # Step 3: Download Video
        downloaded_path = scraper.download_video(video_url, output_id=f"tiktok_{video_id}")
        if not downloaded_path:
            logging.error("Workflow Stop: Video download failed.")
            return

        try:
            # Step 4: Metadata Strip
            cleaned_path = processor.strip_metadata(downloaded_path)
            if not cleaned_path:
                logging.error("Workflow Stop: Metadata stripping failed.")
                return
            
            # Step 5: Format Caption
            final_caption = processor.refine_caption(latest_video.get("title", ""))
            logging.info(f"Final Caption prepared: '{final_caption}'")
            
            # Step 6: X API Video Upload
            media_id = publisher.upload_video(cleaned_path)
            if not media_id:
                logging.error("Workflow Stop: X Video upload failed.")
                return
            
            # Step 7: Create Tweet
            tweet_id = publisher.post_tweet(text=final_caption, media_id=media_id)
            if not tweet_id:
                logging.error("Workflow Stop: X Tweet posting failed.")
                return
            
            # Step 8: Log Success
            twitter_url = f"https://x.com/dolunayozeren/status/{tweet_id}"
            logger_db.log_video(
                video_id=video_id, 
                platform="X (Twitter)", 
                status="Success",
                tiktok_url=video_url,
                twitter_url=twitter_url
            )
            
            logging.info("Workflow Complete: Video successfully posted to X!")
            
        finally:
            # Step 9: Cleanup
            scraper.clean_tmp_files(downloaded_path)
            # Ensure cleaned path variable exists conceptually even if exception was thrown prior
            if 'cleaned_path' in locals():
                scraper.clean_tmp_files(cleaned_path)
    
    except Exception as e:
        logging.error(f"FATAL ERROR in job: {e}", exc_info=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.info("Twitter_Paylasim service started. Entering idle schedule mode.")
    logging.info("Ensure the TZ env variable is set to 'Europe/Istanbul' on Railway for accurate timings.")
    
    # Run at specific Turkey hours (11, 14, 17). 
    # If the docker container has TZ=Europe/Istanbul, this maps perfectly.
    schedule.every().day.at("11:00").do(job)
    schedule.every().day.at("14:00").do(job)
    schedule.every().day.at("17:00").do(job)
    
    # You can uncomment this to test immediately upon start:
    # logging.info("Executing immediate initial run...")
    # job()
    
    while True:
        schedule.run_pending()
        time.sleep(60)
