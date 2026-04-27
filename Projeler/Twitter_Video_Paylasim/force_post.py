from ops_logger import get_ops_logger
from core.tiktok_scraper import TikTokScraper
from core.video_processor import VideoProcessor
from core.x_publisher import XPublisher
import time
import os

ops = get_ops_logger("Twitter_Video_Paylasim", "TestForcePost")

def main():
    ops.info("Starting FORCE POST test")
    scraper = TikTokScraper()
    processor = VideoProcessor()
    publisher = XPublisher()
    
    video_info = scraper.get_latest_video_info()
    if not video_info:
        ops.error("No video info found")
        return
        
    video_id = video_info['id']
    ops.info(f"Downloading video {video_id}")
    downloaded_path = scraper.download_video(video_info['url'], f"test_{video_id}")
    
    if not downloaded_path:
        ops.error("Download failed")
        return
        
    ops.info("Stripping metadata")
    cleaned_path = processor.strip_metadata(downloaded_path)
    if not cleaned_path:
        ops.error("Metadata strip failed")
        return
        
    ops.info("Uploading to X")
    media_id = publisher.upload_video(cleaned_path)
    if not media_id:
        ops.error("Upload to X failed")
        return
        
    ops.info(f"Uploaded with media_id {media_id}. Posting tweet.")
    tweet_text = f"Test Video!\n\nVideo ID: {video_id}"
    tweet_id = publisher.post_tweet(tweet_text, media_id)
    
    if tweet_id:
        ops.info(f"SUCCESS! Tweet ID: {tweet_id}")
    else:
        ops.error("Failed to post tweet")
        
    scraper.clean_tmp_files(downloaded_path)
    if cleaned_path and cleaned_path != downloaded_path:
        scraper.clean_tmp_files(cleaned_path)

if __name__ == "__main__":
    main()
