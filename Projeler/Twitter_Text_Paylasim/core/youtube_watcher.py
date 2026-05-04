"""YouTube Channel Watcher.

Akış:
  1. Kanal RSS feed'inden son 5 video listesi (public, auth gerekmez)
  2. Notion'dan en son işlenen video ID'sini al
  3. Yeni video varsa transkript çek (youtube-transcript-api, TR/EN otomatik)
  4. Transkript + meta tweet_writer'a verilir

Not: YOUTUBE_CHANNEL_ID UC ile başlayan kanal ID olmalı (handle değil).
Handle'dan ID çevirme YouTube Data API gerektirir; şimdilik kullanıcı UC ID'sini verir.
"""

import re

import requests
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

_yt_api = YouTubeTranscriptApi()

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "YoutubeWatcher")

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


class YoutubeWatcher:
    def __init__(self):
        self.channel_id = settings.YOUTUBE_CHANNEL_ID

    def fetch_recent_videos(self, limit: int = 5) -> list[dict]:
        """RSS'ten son N videoyu döner: [{video_id, title, url, published}, ...]"""
        if not self.channel_id:
            ops.warning("YOUTUBE_CHANNEL_ID set değil")
            return []
        url = RSS_URL.format(channel_id=self.channel_id)
        try:
            feed = feedparser.parse(url)
            videos = []
            for entry in feed.entries[:limit]:
                # entry.yt_videoid veya entry.id'den parse
                vid = getattr(entry, "yt_videoid", None)
                if not vid and hasattr(entry, "id"):
                    m = re.search(r"video:([^/]+)", entry.id)
                    vid = m.group(1) if m else ""
                if not vid:
                    continue
                videos.append({
                    "video_id": vid,
                    "title": getattr(entry, "title", ""),
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "published": getattr(entry, "published", ""),
                })
            return videos
        except Exception as e:
            ops.error("RSS parse hatası", exception=e)
            return []

    def fetch_transcript(self, video_id: str) -> str:
        """Transkript metnini birleştirilmiş string olarak döner.
        youtube-transcript-api v1.x: önce TR, sonra EN, otomatik altyazı dahil.
        """
        try:
            fetched = _yt_api.fetch(video_id, languages=["tr", "en"])
            text = " ".join(s.text for s in fetched if s.text)
            return text
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            ops.warning(f"Transkript yok ({video_id}): {e}")
            return ""
        except Exception as e:
            ops.error(f"Transkript çekme hatası ({video_id})", exception=e)
            return ""

    def get_new_video(self, last_processed_id: str = "") -> dict:
        """En son işlenenden sonraki yeni videoyu döner. Yoksa boş dict."""
        videos = self.fetch_recent_videos(limit=5)
        if not videos:
            return {}
        # RSS reverse-chronological — en yeni ilk
        latest = videos[0]
        if latest["video_id"] == last_processed_id:
            ops.info("Yeni video yok", f"En son: {latest['video_id']}")
            return {}
        # Transkripti çek
        transcript = self.fetch_transcript(latest["video_id"])
        if not transcript:
            ops.warning(f"Transkript boş, video atlanıyor: {latest['video_id']}")
            return {}
        latest["transcript"] = transcript
        return latest
