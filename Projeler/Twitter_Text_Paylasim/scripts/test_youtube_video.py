"""One-shot YouTube thread testi (v3).

Verilen video ID'siyle uçtan uca pipeline'ı çalıştırır:
  - ÖNCE Notion 'Yayınlandı' DB'sinde aynı video_id varsa script_text kullan.
  - Yoksa RSS+transcript-api fallback.
  - tweet_writer.write_for_youtube_video() ile thread + standalone üret
  - --dry flag verilirse Typefully push atlanır (sadece konsola yazdırır)

Kullanım:
  python scripts/test_youtube_video.py q3Dp4AQYb-I --dry
  python scripts/test_youtube_video.py q3Dp4AQYb-I        # gerçek draft basar
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
from core.notion_scripts import get_published_youtube_videos


def main():
    setup_logging()
    if len(sys.argv) < 2:
        print("Kullanım: python scripts/test_youtube_video.py <video_id> [--dry]")
        sys.exit(1)
    video_id = sys.argv[1]
    dry_run = "--dry" in sys.argv
    print(f"=== Test başladı: {video_id} (dry={dry_run}) ===")

    watcher = YoutubeWatcher()
    writer = TweetWriter()
    publisher = TypefullyDraftPublisher()
    notion = NotionLogger()

    # 1) Notion script ara
    transcript = ""
    source = "rss"
    title = ""
    notion_videos = get_published_youtube_videos(limit=20)
    for nv in notion_videos:
        if nv.get("video_id") == video_id:
            script = (nv.get("script_text") or "").strip()
            if len(script) >= 200:
                transcript = script
                source = "notion"
                title = nv.get("title", "")
                print(f"Notion script bulundu: {len(transcript)} char — {title[:80]}")
            break

    # 2) Fallback: transcript-api
    if not transcript:
        transcript = watcher.fetch_transcript(video_id)
        if not transcript:
            print("HATA: ne Notion ne transcript bulundu, çıkılıyor.")
            sys.exit(1)
        print(f"Transcript (RSS fallback): {len(transcript)} karakter")

    # Video meta
    if not title:
        videos = watcher.fetch_recent_videos(limit=20)
        title = next((v["title"] for v in videos if v["video_id"] == video_id), f"Video {video_id}")
    url = f"https://www.youtube.com/watch?v={video_id}"

    video_data = {"title": title, "url": url, "transcript": transcript, "source": source}
    print(f"Title: {title}")

    print("\nLLM'e gönderiliyor (thread + standalone adayları)...")
    result = writer.write_for_youtube_video(video_data)
    print(f"Skor: {result.get('score')}")
    print(f"Thread tweets: {len(result.get('thread_tweets') or [])}")
    print(f"Standalones:   {len(result.get('standalone_tweets') or [])}")
    if result.get("skip_reason"):
        print(f"Skip: {result['skip_reason']}")

    score = int(result.get("score") or 0)

    thread = result.get("thread_tweets") or []
    standalones = result.get("standalone_tweets") or []
    if thread:
        print("\n--- THREAD (önizleme) ---")
        for i, t in enumerate(thread, 1):
            print(f"[{i}/{len(thread)}] ({len(t)} char)\n{t}\n")
    if standalones:
        print("\n--- STANDALONES ---")
        for i, st in enumerate(standalones, 1):
            print(f"[{i}] ({len(st)} char)\n{st}\n")

    if dry_run:
        print("\n[DRY-RUN] Typefully push atlanıyor.")
        wait_all_loggers()
        return

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
