"""Pre-flight diagnose: 3 Apify actor + Gmail OAuth + Notion DB schema."""
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_apify():
    section("APIFY ACTORS")
    from apify_client import ApifyClient
    from config import settings

    actors = [
        ("Instagram", settings.APIFY_INSTAGRAM_ACTOR, {"usernames": [settings.IG_USERNAME], "resultsLimit": 3}),
        ("TikTok", settings.APIFY_TIKTOK_ACTOR, {"profiles": [settings.TIKTOK_USERNAME], "resultsPerPage": 3, "downloadVideo": False}),
        ("YouTube", settings.APIFY_YOUTUBE_ACTOR, {"searchKeywords": settings.YOUTUBE_SEARCH_QUERY, "maxResults": 3, "maxResultStreams": 0}),
    ]

    if not settings.APIFY_KEYS:
        print("[FAIL] No APIFY_API_KEY_x found")
        return

    key = settings.APIFY_KEYS[0]
    client = ApifyClient(key)

    for name, actor_id, payload in actors:
        print(f"\n--- {name}  actor={actor_id} ---")
        try:
            run = client.actor(actor_id).call(run_input=payload)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            print(f"[OK] returned {len(items)} items")
            if items:
                sample = items[0]
                preview_keys = ["url", "webVideoUrl", "videoUrl", "timestamp", "createTimeISO", "date",
                                "uploadDate", "videoViewCount", "playCount", "viewCount", "channelName",
                                "isShorts", "type", "latestPosts"]
                preview = {k: sample.get(k) for k in preview_keys if k in sample}
                if "latestPosts" in preview and isinstance(preview["latestPosts"], list):
                    preview["latestPosts"] = f"<{len(preview['latestPosts'])} posts>"
                print(json.dumps(preview, ensure_ascii=False, indent=2, default=str)[:1500])
        except Exception as e:
            print(f"[FAIL] {type(e).__name__}: {e}")


def check_notion():
    section("NOTION STATE DB")
    import requests
    token = os.environ.get("NOTION_SOCIAL_TOKEN") or os.environ.get("NOTION_API_TOKEN")
    db_id = os.environ.get("NOTION_DB_NOTIFIED_VIDEOS")
    if not token or not db_id:
        print(f"[SKIP] token={'set' if token else 'missing'}, db_id={'set' if db_id else 'missing'}")
        return
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}
    try:
        r = requests.get(f"https://api.notion.com/v1/databases/{db_id}", headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        props = data.get("properties", {})
        print(f"[OK] DB title: {data.get('title', [{}])[0].get('plain_text', '?')}")
        print("Properties:")
        for name, meta in props.items():
            print(f"  - {name!r}  type={meta.get('type')}")
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")


def check_gmail():
    section("GMAIL OAUTH")
    try:
        from config import settings
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        path = settings.OAUTH_TOKEN_PATH
        if not path or not os.path.exists(path):
            print(f"[FAIL] OAuth token file not found: {path}")
            return
        creds = Credentials.from_authorized_user_file(
            path, ["https://www.googleapis.com/auth/gmail.modify"]
        )
        print(f"[INFO] valid={creds.valid}  expired={creds.expired}  has_refresh={bool(creds.refresh_token)}")
        if not creds.valid and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("[OK] refresh succeeded")
            except Exception as e:
                print(f"[FAIL] refresh raised: {type(e).__name__}: {e}")
                return
        elif not creds.valid:
            print("[FAIL] no refresh token, token expired/invalid")
            return
        print("[OK] Gmail credentials usable")
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        traceback.print_exc()


def main():
    print("Ceren Notifier — DIAGNOSE")
    print(f"ENV={os.environ.get('ENV', 'development')}  DRY_RUN={os.environ.get('DRY_RUN', '0')}")
    check_apify()
    check_notion()
    check_gmail()
    print("\n" + "=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()
