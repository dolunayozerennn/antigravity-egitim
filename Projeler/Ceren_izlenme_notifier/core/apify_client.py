from apify_client import ApifyClient
from apify_client._errors import ApifyApiError
from datetime import datetime, timedelta, timezone
from logger import get_logger
from config import settings
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)


class ApifyExhaustedError(Exception):
    """Tüm Apify key'leri tükendi (rate/quota limit)."""


def call_apify_actor(actor_id, run_input):
    """Sıralı key dene; rate/quota hatasında diğerine geç. Ağ hatasında raise et."""
    last_quota_err = None
    for key in settings.APIFY_KEYS:
        masked = f"{key[:6]}...{key[-4:]}"
        try:
            client = ApifyClient(key)
            logger.info(f"Apify call: actor={actor_id} token={masked}")
            run = client.actor(actor_id).call(run_input=run_input)
            return client, run
        except ApifyApiError as e:
            err_msg = str(e).lower()
            if any(x in err_msg for x in ["monthly usage", "hard limit", "rate limit", "quota"]):
                logger.warning(f"Apify quota dolu (token={masked}, actor={actor_id}): {e}")
                last_quota_err = e
                continue
            # Quota dışı API hatası (404 actor not found, 400 bad input, vs.) — retry'a değmez
            raise RuntimeError(f"Apify API error (actor={actor_id}, token={masked}): {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected Apify error (actor={actor_id}, token={masked}): {e}") from e

    raise ApifyExhaustedError(
        f"Tüm {len(settings.APIFY_KEYS)} Apify key'i quota'da; son hata: {last_quota_err}"
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_items_with_retry(client, dataset_id):
    logger.debug(f"Dataset {dataset_id} çekiliyor (retry aktif)")
    return list(client.dataset(dataset_id).iterate_items())


def is_within_lookback(date_str):
    if not date_str:
        return False
    try:
        if isinstance(date_str, (int, float)):
            ts = date_str / 1000 if date_str > 1e11 else date_str
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - dt <= timedelta(days=settings.LOOKBACK_DAYS)
    except Exception as e:
        logger.warning(f"Tarih parse hatası ({date_str!r}): {e}")
        return False


def _coerce_int(val):
    if isinstance(val, str):
        try:
            return int(val.replace(",", ""))
        except ValueError:
            return 0
    if isinstance(val, (int, float)):
        return int(val)
    return 0


def _platform_error(platform, stage, actor_id, exc):
    return {
        "platform": platform,
        "stage": stage,
        "actor_id": actor_id,
        "error": f"{type(exc).__name__}: {exc}",
    }


def get_instagram_data():
    actor = settings.APIFY_INSTAGRAM_ACTOR
    logger.info("Instagram verileri çekiliyor")
    videos = []
    skipped_no_date = 0
    try:
        client, run = call_apify_actor(actor, {
            "usernames": [settings.IG_USERNAME],
            "resultsLimit": 20,
        })
    except Exception as e:
        return [], _platform_error("Instagram", "actor_call", actor, e)

    try:
        items = fetch_items_with_retry(client, run["defaultDatasetId"])
    except Exception as e:
        return [], _platform_error("Instagram", "fetch", actor, e)

    try:
        for item in items:
            posts = item.get("latestPosts", [item]) if "latestPosts" in item else [item]
            for post in posts:
                dt = post.get("timestamp") or post.get("postedAt")
                if not dt:
                    skipped_no_date += 1
                    continue
                if not is_within_lookback(dt):
                    continue
                is_video = post.get("type") == "Video" or post.get("videoViewCount") is not None
                if not is_video:
                    continue
                views = _coerce_int(post.get("videoViewCount") or post.get("viewCount") or 0)
                if views >= settings.IG_VIEW_THRESHOLD:
                    videos.append({
                        "platform": "Instagram Reels",
                        "url": post.get("url"),
                        "views": views,
                        "date": dt,
                    })
    except Exception as e:
        return videos, _platform_error("Instagram", "parse", actor, e)

    if skipped_no_date:
        logger.warning(f"Instagram: {skipped_no_date} item tarih olmadığı için atlandı")
    return videos, None


def get_tiktok_data():
    actor = settings.APIFY_TIKTOK_ACTOR
    logger.info("TikTok verileri çekiliyor")
    videos = []
    skipped_no_date = 0
    try:
        client, run = call_apify_actor(actor, {
            "profiles": [settings.TIKTOK_USERNAME],
            "resultsPerPage": 20,
            "downloadVideo": False,
        })
    except Exception as e:
        return [], _platform_error("TikTok", "actor_call", actor, e)

    try:
        items = fetch_items_with_retry(client, run["defaultDatasetId"])
    except Exception as e:
        return [], _platform_error("TikTok", "fetch", actor, e)

    try:
        for item in items:
            dt = item.get("createTimeISO") or item.get("createTime")
            if not dt:
                skipped_no_date += 1
                continue
            if not is_within_lookback(dt):
                continue
            views = _coerce_int(item.get("playCount") or 0)
            if views >= settings.TIKTOK_VIEW_THRESHOLD:
                videos.append({
                    "platform": "TikTok",
                    "url": item.get("webVideoUrl") or item.get("videoUrl"),
                    "views": views,
                    "date": dt,
                })
    except Exception as e:
        return videos, _platform_error("TikTok", "parse", actor, e)

    if skipped_no_date:
        logger.warning(f"TikTok: {skipped_no_date} item tarih olmadığı için atlandı")
    return videos, None


def _channel_match(item):
    channel = (item.get("channelName") or "").lower()
    url = (item.get("url") or item.get("videoUrl") or "").lower()
    return any(k in channel or k in url for k in settings.YOUTUBE_CHANNEL_KEYWORDS)


def get_youtube_data():
    actor = settings.APIFY_YOUTUBE_ACTOR
    logger.info("YouTube verileri çekiliyor")
    videos = []
    skipped_no_date = 0
    try:
        client, run = call_apify_actor(actor, {
            "searchKeywords": settings.YOUTUBE_SEARCH_QUERY,
            "maxResults": 25,
            "maxResultStreams": 0,
        })
    except Exception as e:
        return [], _platform_error("YouTube", "actor_call", actor, e)

    try:
        items = fetch_items_with_retry(client, run["defaultDatasetId"])
    except Exception as e:
        return [], _platform_error("YouTube", "fetch", actor, e)

    try:
        for item in items:
            dt = item.get("date") or item.get("uploadDate")
            if not dt:
                skipped_no_date += 1
                continue
            if not is_within_lookback(dt):
                continue
            if not _channel_match(item):
                logger.debug(f"YouTube: başka kanal atlandı ({item.get('channelName')})")
                continue

            views = _coerce_int(item.get("viewCount") or item.get("views") or 0)
            url = item.get("url") or item.get("videoUrl") or ""
            is_shorts = bool(item.get("isShorts")) or "/shorts/" in url

            if is_shorts and views >= settings.YT_SHORTS_THRESHOLD:
                videos.append({"platform": "YouTube Shorts", "url": url, "views": views, "date": dt})
            elif not is_shorts and views >= settings.YT_LONG_THRESHOLD:
                videos.append({"platform": "YouTube Long Video", "url": url, "views": views, "date": dt})
    except Exception as e:
        return videos, _platform_error("YouTube", "parse", actor, e)

    if skipped_no_date:
        logger.warning(f"YouTube: {skipped_no_date} item tarih olmadığı için atlandı")
    return videos, None


def fetch_all_social_media():
    """Tüm platformları çek. Returns: (videos, errors_list[dict])."""
    videos = []
    errors = []

    for fn in (get_instagram_data, get_tiktok_data, get_youtube_data):
        v, err = fn()
        videos.extend(v)
        if err:
            errors.append(err)

    return videos, errors
