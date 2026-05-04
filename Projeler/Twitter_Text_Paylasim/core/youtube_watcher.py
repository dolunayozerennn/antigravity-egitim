"""YouTube Channel Watcher.

Akış (v3):
  1. ÖNCE Notion 'Dolunay Reels & YouTube' DB'sinden Status=Yayınlandı + icon=youtube_logo
     videoların script body'sini çek. Script otomatik altyazıdan çok daha temiz
     (Dolunay'ın videoyu çekmeden yazdığı script).
  2. Notion'da uygun script yoksa veya çok kısaysa (<200 karakter), RSS + transcript-api
     fallback'una düş.
  3. Dedup için (video_url veya page_url) main.py'de NotionLogger kullanılır.

Not: YOUTUBE_CHANNEL_ID UC ile başlayan kanal ID olmalı (handle değil).
"""

import re

import requests
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

_yt_api = YouTubeTranscriptApi()

from ops_logger import get_ops_logger
from config import settings
from core.notion_scripts import get_published_youtube_videos

ops = get_ops_logger("Twitter_Text_Paylasim", "YoutubeWatcher")

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
MIN_SCRIPT_CHARS = 200


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
        """En son işlenenden sonraki yeni videoyu döner. Yoksa boş dict.

        v3 davranışı:
          - Önce Notion 'Yayınlandı' YouTube videolarına bak; en yeni olan, last_processed_id
            ile uyuşmuyorsa script_text'i transcript olarak kullan.
          - Notion'da yoksa veya script çok kısaysa RSS fallback.
        """
        # 1) Notion-first
        try:
            notion_videos = get_published_youtube_videos(limit=5)
        except Exception as e:
            ops.warning(f"Notion script çekme hatası, RSS'e düşülüyor: {e}")
            notion_videos = []

        for nv in notion_videos:
            vid = nv.get("video_id") or ""
            if vid and vid == last_processed_id:
                continue
            script = (nv.get("script_text") or "").strip()
            if len(script) >= MIN_SCRIPT_CHARS:
                ops.info(f"Notion script bulundu: {nv.get('title','?')[:80]} ({len(script)} char)")
                return {
                    "video_id": vid,
                    "title": nv.get("title", ""),
                    "url": nv.get("video_url") or nv.get("page_url", ""),
                    "page_url": nv.get("page_url", ""),
                    "transcript": script,
                    "source": "notion",
                }
            else:
                ops.info(f"Notion script kısa/boş, fallback'a düşülüyor: {nv.get('title','?')[:60]}")

        # 2) RSS fallback
        videos = self.fetch_recent_videos(limit=5)
        if not videos:
            return {}
        latest = videos[0]
        if latest["video_id"] == last_processed_id:
            ops.info("Yeni video yok", f"En son: {latest['video_id']}")
            return {}
        transcript = self.fetch_transcript(latest["video_id"])
        if not transcript:
            ops.warning(f"Transkript boş, video atlanıyor: {latest['video_id']}")
            return {}
        latest["transcript"] = transcript
        latest["source"] = "rss"
        return latest
