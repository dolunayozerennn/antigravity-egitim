"""X (Twitter) paylaşım logu — birincil anahtar Notion page_id."""

import requests
from datetime import datetime, timezone

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Video_Paylasim", "NotionLogger")


class NotionLogger:
    def __init__(self):
        self.token = settings.NOTION_TOKEN
        self.db_id = settings.NOTION_TWITTER_DB_ID
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def is_video_posted(self, page_id: str) -> bool:
        try:
            url = f"https://api.notion.com/v1/databases/{self.db_id}/query"
            payload = {"filter": {"property": "Video ID", "title": {"equals": page_id}}}
            resp = requests.post(url, headers=self.headers, json=payload, timeout=10)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                return False
            for record in results:
                status_prop = record.get("properties", {}).get("Status", {}).get("select")
                status_name = status_prop.get("name", "") if status_prop else ""
                if status_name in ("Success", "Filtered"):
                    return True
            ops.info(f"Video {page_id[:8]}… daha önce Failed — yeniden denenecek")
            return False
        except Exception as e:
            ops.error(f"Notion dedup hatası ({page_id[:8]}…): {e}", exception=e)
            return False

    def log_video(self, page_id, status, source_url="", twitter_url="", adapted_caption="", note=""):
        if settings.IS_DRY_RUN:
            ops.info(f"[DRY-RUN] Notion log → page_id={page_id[:8]}… status={status}")
            return True

        now_iso = datetime.now(timezone.utc).isoformat()
        properties = {
            "Video ID": {"title": [{"text": {"content": page_id}}]},
            "Status": {"select": {"name": status}},
            "Platform": {"select": {"name": "X (Twitter)"}},
            "Paylasim Tarihi": {"date": {"start": now_iso}},
        }
        if source_url:
            properties["TikTok URL"] = {"url": source_url}
        if twitter_url:
            properties["Twitter URL"] = {"url": twitter_url}
        if note:
            properties["Filter Sebebi"] = {"rich_text": [{"text": {"content": note[:2000]}}]}
        if adapted_caption:
            properties["Caption"] = {"rich_text": [{"text": {"content": adapted_caption[:2000]}}]}

        payload = {"parent": {"database_id": self.db_id}, "properties": properties}
        try:
            resp = requests.post("https://api.notion.com/v1/pages", headers=self.headers, json=payload, timeout=10)
            resp.raise_for_status()
            ops.info(f"Notion log yazıldı: {page_id[:8]}… ({status})")
            return True
        except Exception as e:
            ops.error(f"Notion log hatası ({page_id[:8]}…): {e}", exception=e)
            return False
