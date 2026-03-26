import logging
import yt_dlp
import os

from config import settings

class TikTokScraper:
    def __init__(self):
        self.username = settings.TIKTOK_USERNAME
        self.profile_url = f"https://www.tiktok.com/@{self.username}"
        self.download_dir = "/tmp/linkedin_paylasim"
        os.makedirs(self.download_dir, exist_ok=True)

    def get_latest_video_info(self):
        """
        Fetches the latest video's metadata from the assigned TikTok profile.
        Returns a dict: {'id': '...', 'title': '...', 'url': '...', 'ext': 'mp4'} or None.
        """
        ydl_opts = {
            'extract_flat': True,
            'playlistend': 1,
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                result = ydl.extract_info(self.profile_url, download=False)
                if 'entries' in result and len(result['entries']) > 0:
                    latest = result['entries'][0]
                    video_id = latest.get('id')
                    title = latest.get('title', '')
                    url = latest.get('url', f"https://www.tiktok.com/@{self.username}/video/{video_id}")

                    logging.info(f"Found latest video ID: {video_id} - Title snippet: {title[:50]}...")
                    return {
                        "id": video_id,
                        "title": title,
                        "url": url
                    }
                else:
                    logging.warning(f"No videos found on profile: {self.profile_url}")
                    return None
            except Exception as e:
                logging.error(f"Error extracting profile info for {self.profile_url}: {e}", exc_info=True)
                return None

    def download_video(self, video_url: str, output_id: str) -> str:
        """
        Downloads a single TikTok video in 1080p quality and returns the path to the downloaded MP4 file.
        """
        output_template = os.path.join(self.download_dir, f"{output_id}.%(ext)s")
        ydl_opts = {
            # Prefer 1080p video + best audio, fallback to best available
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'restrictfilenames': True,
            'merge_output_format': 'mp4',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([video_url])
                expected_file = os.path.join(self.download_dir, f"{output_id}.mp4")
                if os.path.exists(expected_file):
                    # Verify resolution
                    file_size_mb = os.path.getsize(expected_file) / (1024 * 1024)
                    logging.info(f"Successfully downloaded TikTok video to {expected_file} ({file_size_mb:.1f} MB)")
                    return expected_file
                else:
                    logging.error(f"Download completed but file not found at {expected_file}")
                    return None
            except Exception as e:
                logging.error(f"Error downloading TikTok video {video_url}: {e}", exc_info=True)
                return None

    def clean_tmp_files(self, filepath: str):
        """
        Cleans up the downloaded file.
        """
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                logging.info(f"Cleaned up temporary file: {filepath}")
            except Exception as e:
                logging.error(f"Failed to clean up file {filepath}: {e}", exc_info=True)
