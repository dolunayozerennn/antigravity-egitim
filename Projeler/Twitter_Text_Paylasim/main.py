"""Twitter_Text_Paylasim — orkestratör.

3 cron job, weekday'a göre seçilir. Railway tek bir cron servisi olarak deploy
edilir; cronSchedule = '0 6 * * *' (her sabah 09:00 TR). main.py weekday +
yeni-içerik-var-mı bayraklarına göre uygun job'ı çağırır.

Pazartesi: LinkedIn'de AI haberleri postu var (Twitter_Text dokunmuyor)
Salı:     GitHub repo job
Perşembe: LinkedIn'de AI tip postu var (Twitter_Text dokunmuyor)
Cuma:     Perplexity AI haber job (X için ayrı açı)
Her gün:  YouTube watcher — yeni video varsa thread+adaylar üretir
"""

import os
from datetime import datetime, timezone

from logger import setup_logging
from ops_logger import get_ops_logger, wait_all_loggers
from config import settings
from core.tweet_writer import TweetWriter
from core.typefully_publisher import TypefullyDraftPublisher, TypefullyDraftError
from core.notion_logger import NotionLogger
from core.github_discoverer import GithubDiscoverer
from core.youtube_watcher import YoutubeWatcher
from core.perplexity_researcher import PerplexityResearcher

ops = get_ops_logger("Twitter_Text_Paylasim", "Pipeline")


def _push_or_skip(notion: NotionLogger, publisher: TypefullyDraftPublisher,
                  source: str, source_url: str, result: dict) -> bool:
    """Tweet writer çıktısını eşik kontrolüne sokar, draft veya atlandı logu."""
    score = int(result.get("score") or 0)
    skip_reason = result.get("skip_reason") or ""

    if score < settings.QUALITY_THRESHOLD:
        ops.info(f"Atlandı (skor {score})", skip_reason[:200])
        notion.log_skipped(
            source=source, source_url=source_url, score=score,
            skip_reason=skip_reason or f"Skor {score} < eşik {settings.QUALITY_THRESHOLD}",
            title=f"{source} skor {score}",
        )
        return False

    # Eşik geçti — Typefully'ye draft at
    try:
        if "thread_tweets" in result and result.get("thread_tweets"):
            # YouTube thread + standalone'lar
            thread = result["thread_tweets"]
            standalones = result.get("standalone_tweets") or []
            # 1 thread draft
            tdraft = publisher.create_thread_draft(thread)
            notion.log_draft(
                source=source, source_url=source_url, score=score,
                tweet_text=thread[0] if thread else "",
                thread_tweets=thread,
                draft_url=tdraft.get("share_url", ""),
                title=f"{source} thread (skor {score})",
            )
            # Her standalone tweet ayrı draft
            for st in standalones:
                if not st or len(st) < 30:
                    continue
                sdraft = publisher.create_single_draft(st)
                notion.log_draft(
                    source=source, source_url=source_url, score=score,
                    tweet_text=st, draft_url=sdraft.get("share_url", ""),
                    title=f"{source} standalone (skor {score})",
                )
            ops.success(f"{source}: 1 thread + {len(standalones)} standalone draft oluşturuldu")
        else:
            tweet = result.get("tweet_text", "")
            if not tweet or len(tweet) < 20:
                ops.warning(f"{source}: tweet metni boş, atlanıyor")
                return False
            draft = publisher.create_single_draft(tweet)
            notion.log_draft(
                source=source, source_url=source_url, score=score,
                tweet_text=tweet, draft_url=draft.get("share_url", ""),
                title=f"{source} (skor {score})",
            )
            ops.success(f"{source}: draft oluşturuldu (skor {score})")
        return True
    except TypefullyDraftError as e:
        ops.error(f"{source} Typefully error", message=str(e))
        notion.log_failed(source=source, source_url=source_url, error=str(e))
        return False


def run_github_job():
    ops.info("Job başladı", "GitHub repo discovery")
    notion = NotionLogger()
    writer = TweetWriter()
    publisher = TypefullyDraftPublisher()
    discoverer = GithubDiscoverer()

    candidates = discoverer.discover_candidates(max_candidates=8)
    if not candidates:
        ops.warning("GitHub: aday repo bulunamadı")
        return

    posted = 0
    for repo in candidates:
        if posted >= 1:  # Haftada 1 repo postu
            break
        if notion.is_already_processed(repo["url"]):
            ops.info("Zaten işlenmiş repo, atlanıyor", repo["full_name"])
            continue
        result = writer.write_for_github_repo(repo)
        ok = _push_or_skip(notion, publisher, "GitHub", repo["url"], result)
        if ok:
            posted += 1
    ops.info("GitHub job bitti", f"{posted} draft oluşturuldu")


def run_perplexity_job():
    ops.info("Job başladı", "Perplexity AI haber")
    notion = NotionLogger()
    writer = TweetWriter()
    publisher = TypefullyDraftPublisher()
    researcher = PerplexityResearcher()

    news = researcher.research_x_news()
    if not news:
        ops.warning("Perplexity: haber gelmedi")
        return
    result = writer.write_for_ai_news(news)
    _push_or_skip(notion, publisher, "Perplexity", "", result)


def run_youtube_job():
    ops.info("Job başladı", "YouTube yeni video kontrolü")
    notion = NotionLogger()
    writer = TweetWriter()
    publisher = TypefullyDraftPublisher()
    watcher = YoutubeWatcher()

    last_id = notion.get_last_youtube_video_id()
    video = watcher.get_new_video(last_processed_id=last_id)
    if not video:
        ops.info("YouTube: yeni video yok, çıkılıyor")
        return

    if notion.is_already_processed(video["url"]):
        ops.info("Video zaten işlenmiş, atlanıyor")
        return

    result = writer.write_for_youtube_video(video)
    _push_or_skip(notion, publisher, "YouTube", video["url"], result)


JOB_FOR_WEEKDAY = {
    1: run_github_job,       # Salı
    4: run_perplexity_job,   # Cuma
}


def main():
    setup_logging()
    mode = (os.environ.get("RUN_MODE") or "cron").lower()
    today = datetime.now(timezone.utc).weekday()
    ops.info("Başlatıldı", f"mode={mode}, weekday={today}, threshold={settings.QUALITY_THRESHOLD}")

    if mode == "github":
        run_github_job()
    elif mode == "perplexity":
        run_perplexity_job()
    elif mode == "youtube":
        run_youtube_job()
    else:
        # Cron (default): YouTube her gün, GitHub salı, Perplexity cuma
        try:
            run_youtube_job()
        except Exception as e:
            ops.error("YouTube job exception", exception=e)
        special_job = JOB_FOR_WEEKDAY.get(today)
        if special_job:
            try:
                special_job()
            except Exception as e:
                ops.error(f"Weekday {today} job exception", exception=e)

    ops.info("Container kapanıyor")
    wait_all_loggers()


if __name__ == "__main__":
    main()
