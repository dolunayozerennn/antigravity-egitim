import logging
import time
import schedule

from core.tiktok_scraper import TikTokScraper
from core.video_processor import VideoProcessor
from core.x_publisher import XPublisher
from core.notion_logger import NotionLogger
from ops_logger import get_ops_logger

ops = get_ops_logger("Twitter_Video_Paylasim", "Pipeline")

def job():
    ops.info("Workflow Başladı", "Daily TikTok → X (Twitter) Video Pipeline")
    
    try:
        # Initialize Core Modules
        scraper = TikTokScraper()
        processor = VideoProcessor()
        publisher = XPublisher()
        logger_db = NotionLogger()

        # Step 1: Check Latest Video
        latest_video = scraper.get_latest_video_info()
        if not latest_video:
            ops.warning("Workflow Durdu", "TikTok'tan son video bilgisi alınamadı")
            return

        video_id = latest_video["id"]
        video_url = latest_video["url"]
        
        # Step 2: Duplication Check
        if logger_db.is_video_posted(video_id):
            ops.info("Duplicate Atlandı", f"Video {video_id} daha önce paylaşılmış")
            return
            
        ops.info("Yeni Video Bulundu", f"Video ID: {video_id} işlenecek")
        
        # Step 3: Download Video
        downloaded_path = scraper.download_video(video_url, output_id=f"tiktok_{video_id}")
        if not downloaded_path:
            ops.error("Video İndirme Başarısız", message="Video indirilemedi")
            return

        try:
            # Step 4: Metadata Strip
            cleaned_path = processor.strip_metadata(downloaded_path)
            if not cleaned_path:
                ops.error("FFmpeg İşleme Başarısız", message="Metadata strip hatası")
                return
            
            # Step 5: Format Caption
            final_caption = processor.refine_caption(latest_video.get("title", ""))
            logging.info(f"Final Caption prepared: '{final_caption}'")
            
            # Step 6: X API Video Upload
            media_id = publisher.upload_video(cleaned_path)
            if not media_id:
                ops.error("X Video Upload Başarısız", message="X API video yüklenemedi")
                return
            
            # Step 7: Create Tweet
            tweet_id = publisher.post_tweet(text=final_caption, media_id=media_id)
            if not tweet_id:
                ops.error("Tweet Gönderme Başarısız", message="X API tweet oluşturulamadı")
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
            
            ops.success("Workflow Tamamlandı", f"Video başarıyla X'e paylaşıldı — {twitter_url}")
            
        finally:
            # Step 9: Cleanup
            scraper.clean_tmp_files(downloaded_path)
            # Ensure cleaned path variable exists conceptually even if exception was thrown prior
            if 'cleaned_path' in locals():
                scraper.clean_tmp_files(cleaned_path)
    
    except Exception as e:
        ops.error("FATAL ERROR", exception=e, message=str(e)[:500])

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    import os
    mode = os.environ.get("RUN_MODE", "cron").lower()
    
    if mode == "schedule":
        # Lokal geliştirme veya sürekli çalışan mod
        ops.info("Başlatıldı", "SCHEDULE mode (local dev) — 11:00, 14:00, 17:00")
        schedule.every().day.at("11:00").do(job)
        schedule.every().day.at("14:00").do(job)
        schedule.every().day.at("17:00").do(job)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        # Railway Cron modu: container açılır, job çalışır, container kapanır.
        ops.info("Başlatıldı", "CRON mode — tek çalışma")
        job()
        ops.info("Job Bitti", "Container kapanıyor")
        ops.wait_for_logs()

