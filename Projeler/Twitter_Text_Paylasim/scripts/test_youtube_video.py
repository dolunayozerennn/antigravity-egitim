"""One-shot YouTube thread testi.

Verilen video ID'siyle uçtan uca pipeline'ı çalıştırır:
  - Transkript çek
  - tweet_writer.write_for_youtube_video() ile thread + standalone üret
  - Eşik geçerse Typefully'ye gerçek draft + Notion log

Kullanım:
  python scripts/test_youtube_video.py q3Dp4AQYb-I
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from logger import setup_logging
from ops_logger import wait_all_loggers
from core.youtube_watcher import YoutubeWatcher
from core.tweet_writer import TweetWriter
from core.typefully_publisher import TypefullyDraftPublisher
from core.notion_logger import NotionLogger


def main():
    setup_logging()
    if len(sys.argv) < 2:
        print("Kullanım: python scripts/test_youtube_video.py <video_id>")
        sys.exit(1)
    video_id = sys.argv[1]
    print(f"=== Test başladı: {video_id} ===")

    watcher = YoutubeWatcher()
    writer = TweetWriter()
    publisher = TypefullyDraftPublisher()
    notion = NotionLogger()

    transcript = watcher.fetch_transcript(video_id)
    if not transcript:
        print("HATA: transkript boş, çıkılıyor.")
        sys.exit(1)
    print(f"Transcript: {len(transcript)} karakter")

    # Video meta — başlığı RSS'ten çekelim ya da generic verelim
    videos = watcher.fetch_recent_videos(limit=20)
    title = next((v["title"] for v in videos if v["video_id"] == video_id), f"Video {video_id}")
    url = f"https://www.youtube.com/watch?v={video_id}"

    video_data = {"title": title, "url": url, "transcript": transcript}
    print(f"Title: {title}")

    print("\nLLM'e gönderiliyor (thread + standalone adayları)...")
    result = writer.write_for_youtube_video(video_data)
    print(f"Skor: {result.get('score')}")
    print(f"Thread tweets: {len(result.get('thread_tweets') or [])}")
    print(f"Standalones:   {len(result.get('standalone_tweets') or [])}")
    if result.get("skip_reason"):
        print(f"Skip: {result['skip_reason']}")

    score = int(result.get("score") or 0)
    if score < 7:
        print("Eşik altı — atlandı, Typefully'ye gönderilmiyor.")
        notion.log_skipped(
            source="YouTube", source_url=url, score=score,
            skip_reason=result.get("skip_reason") or "Eşik altı",
            title=title,
        )
        wait_all_loggers()
        return

    # Thread draft
    thread = result.get("thread_tweets") or []
    if thread:
        print("\nThread draft oluşturuluyor...")
        td = publisher.create_thread_draft(thread)
        print(f"  → Draft URL: {td.get('share_url')}")
        notion.log_draft(
            source="YouTube", source_url=url, score=score,
            tweet_text=thread[0], thread_tweets=thread,
            draft_url=td.get("share_url", ""),
            title=f"YouTube thread: {title[:80]}",
        )

    # Standalone'lar
    standalones = result.get("standalone_tweets") or []
    for i, st in enumerate(standalones, 1):
        if not st or len(st) < 30:
            continue
        print(f"\nStandalone {i}/{len(standalones)} draft oluşturuluyor...")
        sd = publisher.create_single_draft(st)
        print(f"  → Draft URL: {sd.get('share_url')}")
        notion.log_draft(
            source="YouTube", source_url=url, score=score,
            tweet_text=st, draft_url=sd.get("share_url", ""),
            title=f"YouTube standalone {i}: {title[:60]}",
        )

    print("\n=== Test tamam ===")
    wait_all_loggers()


if __name__ == "__main__":
    main()
