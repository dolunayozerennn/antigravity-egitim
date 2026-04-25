import logging
import time
import schedule

import config  # Load environment variables first

from core.tiktok_scraper import TikTokScraper
from core.video_processor import VideoProcessor
from core.content_filter import ContentFilter
from core.linkedin_publisher import LinkedInPublisher
from core.notion_logger import NotionLogger
from ops_logger import get_ops_logger, wait_all_loggers

ops = get_ops_logger("LinkedIn_Video_Paylasim", "Pipeline")


def _process_and_post_video(video, reason, scraper, processor, content_filter, publisher, logger_db):
    """Tek bir videoyu indir → FFmpeg → upload → post et. Başarılıysa True döner."""
    video_id = video["id"]
    video_url = video["url"]
    video_title = video.get("title", "")

    # Step 3: Download Video (1080p)
    downloaded_path = scraper.download_video(video_url, output_id=f"linkedin_{video_id}")
    if not downloaded_path:
        ops.error("Video İndirme Başarısız", message=f"Video {video_id} indirilemedi")
        logger_db.log_video(
            video_id=video_id, status="Failed", tiktok_url=video_url,
            filter_decision="Approved", filter_reason=f"Download failed. Filter reason: {reason}"
        )
        return False

    try:
        # Step 4: Metadata Strip + 1080p Ensure
        cleaned_path = processor.strip_metadata(downloaded_path)
        if not cleaned_path:
            ops.error("FFmpeg İşleme Başarısız", message=f"Video {video_id} metadata strip hatası")
            logger_db.log_video(
                video_id=video_id, status="Failed", tiktok_url=video_url,
                filter_decision="Approved", filter_reason=f"FFmpeg processing failed. Filter reason: {reason}"
            )
            return False

        # Step 5: Adapt Caption for LinkedIn (LLM)
        linkedin_caption = content_filter.adapt_caption_for_linkedin(video_title)
        ops.info("Caption Üretildi", f"'{linkedin_caption[:80]}...'")

        # Step 6: Upload Video to LinkedIn
        video_urn = publisher.upload_video(cleaned_path)
        if not video_urn:
            ops.error("LinkedIn Upload Başarısız", message=f"Video {video_id} yüklenemedi")
            logger_db.log_video(
                video_id=video_id, status="Failed", tiktok_url=video_url,
                filter_decision="Approved", filter_reason=f"LinkedIn upload failed. Filter reason: {reason}",
                adapted_caption=linkedin_caption
            )
            return False

        # Step 7: Create LinkedIn Post
        post_urn = publisher.create_post(text=linkedin_caption, video_urn=video_urn)
        if not post_urn:
            ops.error("LinkedIn Post Başarısız", message=f"Video {video_id} post oluşturulamadı")
            logger_db.log_video(
                video_id=video_id, status="Failed", tiktok_url=video_url,
                filter_decision="Approved", filter_reason=f"Post creation failed. Filter reason: {reason}",
                adapted_caption=linkedin_caption
            )
            return False

        # Step 8: Log Success
        linkedin_url = f"https://www.linkedin.com/feed/update/{post_urn}/"
        logger_db.log_video(
            video_id=video_id, status="Success", tiktok_url=video_url,
            linkedin_url=linkedin_url, filter_decision="Approved",
            filter_reason=reason, adapted_caption=linkedin_caption
        )
        ops.success("Workflow Tamamlandı", f"Video başarıyla paylaşıldı — {linkedin_url}")
        return True

    finally:
        # Cleanup temp files
        scraper.clean_tmp_files(downloaded_path)
        if 'cleaned_path' in locals() and cleaned_path:
            scraper.clean_tmp_files(cleaned_path)


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
        recent_videos = scraper.get_recent_videos(count=20)
        if not recent_videos:
            ops.warning("Workflow Durdu", "TikTok'tan video çekilemedi")
            return

        ops.info("Video Listesi", f"{len(recent_videos)} video kontrol ediliyor")

        # Step 2: Loop through videos — find first suitable, unprocessed one
        rejected_candidates = []  # Fallback için: filter reddederse en uygununu seç

        for idx, video in enumerate(recent_videos, 1):
            video_id = video["id"]
            video_url = video["url"]
            video_title = video.get("title", "")

            # 2a: Duplication Check (already posted OR filtered)
            if logger_db.is_video_posted(video_id):
                ops.info("Atlandı", f"[{idx}/{len(recent_videos)}] {video_id} — zaten işlenmiş")
                continue

            ops.info("Yeni Video Bulundu", f"[{idx}/{len(recent_videos)}] ID: {video_id} — {video_title[:60]}...")

            # 2b: LLM Content Filter
            filter_result = content_filter.evaluate_content(video_title)
            decision = filter_result["decision"]
            reason = filter_result["reason"]
            confidence = filter_result["confidence"]

            ops.info("Filter Sonucu", f"{decision} (güven: {confidence:.2f}) — {reason[:80]}")

            if decision == "REJECT":
                # Reddedilen videoyu fallback listesine ekle
                rejected_candidates.append({
                    "video": video, "confidence": confidence, "reason": reason
                })
                logger_db.log_video(
                    video_id=video_id,
                    status="Filtered",
                    tiktok_url=video_url,
                    filter_decision="Rejected",
                    filter_reason=reason
                )
                ops.info("Video Reddedildi", f"Content filter: {reason[:100]}")
                continue

            # Filter geçti — bu videoyu işle
            result = _process_and_post_video(video, reason, scraper, processor, content_filter, publisher, logger_db)
            if result:
                return  # SUCCESS — exit after first successful post

        # ── FALLBACK: Tüm videolar reddedildiyse, en düşük güvenli reddedileni ZORLA kabul et ──
        if rejected_candidates:
            best = min(rejected_candidates, key=lambda x: x["confidence"])
            ops.warning(
                "Fallback Aktivasyon",
                f"Tüm {len(rejected_candidates)} video filtrelendi — en düşük güvenli reddedileni kabul ediyorum: {best['video']['id']} (güven: {best['confidence']:.2f})"
            )
            result = _process_and_post_video(
                best["video"], f"FALLBACK — orijinal ret: {best['reason'][:80]}",
                scraper, processor, content_filter, publisher, logger_db
            )
            if result:
                return

        # If we reach here, all videos were either already processed or processing failed
        ops.info("Workflow Tamamlandı", "Uygun yeni video bulunamadı — tümü zaten işlenmiş veya işleme başarısız")

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
        wait_all_loggers()
