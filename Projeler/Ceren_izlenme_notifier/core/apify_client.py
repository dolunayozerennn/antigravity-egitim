from apify_client import ApifyClient
from apify_client._errors import ApifyApiError
from datetime import datetime, timedelta, timezone
from logger import get_logger
from config import settings
import time
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)

def call_apify_actor(actor_id, run_input):
    """
    Apify actor çağrısını yapar. Biten limitlere karşı sırayla key dener.
    Başarılı olursa (client, run_result) döner.
    """
    last_error = None
    
    for _ in range(3): # En fazla 3 genel deneme
        for key in settings.APIFY_KEYS:
            try:
                client = ApifyClient(key)
                logger.info(f"Apify Actor çağrılıyor: {actor_id} (Token: {key[:6]}...)")
                run = client.actor(actor_id).call(run_input=run_input)
                return client, run
            except ApifyApiError as e:
                err_msg = str(e).lower()
                if "monthly usage" in err_msg or "hard limit exceeded" in err_msg or "rate limit" in err_msg:
                    logger.warning(f"Apify limiti doldu (Token {key[:6]}...), diğer key'e geçiliyor... ({e})")
                    last_error = e
                    continue
                else:
                    logger.error(f"Apify API hatası! (Token {key[:6]}...): {e}", exc_info=True)
                    last_error = e
                    continue
            except Exception as e:
                logger.error(f"Beklenmeyen Apify hatası! (Token {key[:6]}...): {e}", exc_info=True)
                last_error = e
                continue
                
        time.sleep(5)
    
    raise last_error or Exception(f"Tüm try/catch denemeleri tükendi! ({len(settings.APIFY_KEYS)} key)")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_items_with_retry(client, dataset_id):
    """Network drop ihtimaline karşı dataset'i retry mekanizmasıyla çeker."""
    logger.debug(f"Dataset {dataset_id} için veriler çekiliyor (retry aktif)...")
    return list(client.dataset(dataset_id).iterate_items())

def is_within_7_days(date_str):
    """
    Checks if a given ISO8601 date string or timestamp is within the last 7 days.
    """
    if not date_str:
        return False
        
    try:
        if isinstance(date_str, (int, float)):
            # Handle standard unix timestamp (seconds). Sometimes scrapers return milliseconds.
            if date_str > 1e11:  # ms
                date_str = date_str / 1000
            dt = datetime.fromtimestamp(date_str, tz=timezone.utc)
        else:
            # Handle ISO string like "2024-03-01T12:00:00.000Z"
            # Replacing Z with +00:00 for python 3.10-, or use fromisoformat
            date_str = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(date_str)
            
        now = datetime.now(timezone.utc)
        margin = timedelta(days=7)
        return now - dt <= margin
    except Exception as e:
        logger.warning(f"Tarih ayristirma hatasi: {date_str} - {e}")
        return False

def get_instagram_data():
    """
    Instagram'dan profil bazli son gonderileri ceker ve filtrelenmis videoları listeler.
    Reels icin baraj: 200K > izlenme
    """
    logger.info("Instagram verileri çekiliyor...")
    videos = []
    try:
        post_run_input = {
            "usernames": ["dolunay_ozeren"],
            "resultsLimit": 20
        }
        
        client, run = call_apify_actor(settings.APIFY_INSTAGRAM_ACTOR, post_run_input)
        
        items = fetch_items_with_retry(client, run["defaultDatasetId"])
        for item in items:
            # Profil scraper kullanıldığında postlar latestPosts içinde gelebilir, 
            # ya da direkt item post olabilir.
            posts = item.get("latestPosts", [item]) if "latestPosts" in item else [item]
            for post in posts:
                # Instagram API'den gelen ISO tarih
                dt = post.get("timestamp") or post.get("postedAt")
                if not is_within_7_days(dt):
                    continue
                    
                is_video = post.get("type") == "Video" or post.get("videoViewCount") is not None
                
                if is_video:
                    views = post.get("videoViewCount") or post.get("viewCount") or 0
                    if isinstance(views, str):
                        try:
                            views = int(views.replace(",", ""))
                        except ValueError:
                            views = 0
                            
                    if views >= 200000:
                        videos.append({
                            "platform": "Instagram Reels",
                            "url": post.get("url"),
                            "views": int(views),
                            "date": dt
                        })
                    
    except Exception as e:
        logger.error(f"Instagram scrapinge hatasi: {e}", exc_info=True)
        return [], str(e)
        
    return videos, None

def get_tiktok_data():
    """
    TikTok'tan son 7 gunku videolari ceker. Baraj: 100K > izlenme
    """
    logger.info("TikTok verileri çekiliyor...")
    videos = []
    try:
        tk_run_input = {
            "profiles": ["dolunayozeren"],
            "resultsPerPage": 20,
            "downloadVideo": False
        }
        client, run = call_apify_actor(settings.APIFY_TIKTOK_ACTOR, tk_run_input)
        
        items = fetch_items_with_retry(client, run["defaultDatasetId"])
        for item in items:
            # Apify TikTok JSON schema: createTimeISO for standard ISO 8601
            dt = item.get("createTimeISO") or item.get("createTime")
            if not is_within_7_days(dt):
                continue
                
            views = item.get("playCount") or 0
            if isinstance(views, str):
                try:
                    views = int(views.replace(",", ""))
                except ValueError:
                    views = 0
                
            if views >= 100000:
                videos.append({
                    "platform": "TikTok",
                    "url": item.get("webVideoUrl") or item.get("videoUrl"),
                    "views": int(views),
                    "date": dt
                })
                
    except Exception as e:
        logger.error(f"TikTok scrapinge hatasi: {e}", exc_info=True)
        return [], str(e)
        
    return videos, None

def get_youtube_data():
    """
    YouTube'dan son 7 gunku videolari ve Shorts iceriklerini ceker. 
    Baraj: Shorts >= 100K, Long-Form >= 10K
    """
    logger.info("YouTube verileri çekiliyor...")
    videos = []
    try:
        yt_run_input = {
            "searchKeywords": "dolunayozeren",
            "maxResults": 25,
            "maxResultStreams": 0
        }
        client, run = call_apify_actor(settings.APIFY_YOUTUBE_ACTOR, yt_run_input)
        
        items = fetch_items_with_retry(client, run["defaultDatasetId"])
        for item in items:
            # JSON format returns full iso format in 'date' field
            dt = item.get("date") or item.get("uploadDate")
            
            if not is_within_7_days(dt):
                continue
                
            # Must be from our channel to be sure
            channel = item.get("channelName", "").lower()
            url_check = (item.get("url") or item.get("videoUrl") or "").lower()
            if "dolunay" not in channel and "dolunay" not in url_check:
                logger.debug(f"Baska kanal videosu atlandi: {channel}")
                continue
                
            views_num = item.get("viewCount") or item.get("views") or 0
            if isinstance(views_num, str):
                try:
                    views_num = int(views_num.replace(",", ""))
                except ValueError:
                    views_num = 0
                    
            url = item.get("url") or item.get("videoUrl") or ""
            is_shorts = item.get("isShorts", False) or "/shorts/" in url
            
            if is_shorts and views_num >= 100000:
                videos.append({
                    "platform": "YouTube Shorts",
                    "url": url,
                    "views": int(views_num),
                    "date": dt
                })
            elif not is_shorts and views_num >= 10000:
                videos.append({
                    "platform": "YouTube Long Video",
                    "url": url,
                    "views": int(views_num),
                    "date": dt
                })

    except Exception as e:
        logger.error(f"YouTube scrapinge hatasi: {e}", exc_info=True)
        return [], str(e)
        
    return videos, None

def fetch_all_social_media():
    videos = []
    errors = []
    
    ig_videos, ig_err = get_instagram_data()
    videos.extend(ig_videos)
    if ig_err:
        errors.append(f"Instagram Hatası: {ig_err}")
        
    tk_videos, tk_err = get_tiktok_data()
    videos.extend(tk_videos)
    if tk_err:
        errors.append(f"TikTok Hatası: {tk_err}")
        
    yt_videos, yt_err = get_youtube_data()
    videos.extend(yt_videos)
    if yt_err:
        errors.append(f"YouTube Hatası: {yt_err}")
        
    return videos, errors
