import requests
from ops_logger import get_ops_logger
ops = get_ops_logger("Twitter_Video_Paylasim", "NotionLogger")
from config import settings

class NotionLogger:
    def __init__(self):
        self.token = settings.NOTION_TOKEN
        self.db_id = settings.NOTION_TWITTER_DB_ID
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    def is_video_posted(self, video_id: str) -> bool:
        """
        Check if the given video_id has already been posted successfully to X (Twitter).
        Uses platform filter to avoid confusion with LinkedIn entries sharing the same DB.
        """
        try:
            url = f"https://api.notion.com/v1/databases/{self.db_id}/query"
            payload = {
                "filter": {
                    "and": [
                        {
                            "property": "Video ID",
                            "title": {
                                "equals": video_id
                            }
                        },
                        {
                            "property": "Status",
                            "select": {
                                "equals": "Success"
                            }
                        },
                        {
                            "property": "Platform",
                            "select": {
                                "equals": "X (Twitter)"
                            }
                        }
                    ]
                }
            }
            resp = requests.post(url, headers=self.headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return len(data.get("results", [])) > 0
        except Exception as e:
            ops.error(f"Error checking Notion for video_id {video_id}: {e}", exception=e)
            # Fail-OPEN: API hatasında paylaşmayı dene.
            # En kötü ihtimalle duplicate tweet olur ama hiç paylaşmamaktan iyidir.
            return False

    def log_video(self, video_id: str, platform: str, status: str, tiktok_url: str, twitter_url: str):
        """
        Logs a video attempt or success to the Notion database.
        """
        if settings.IS_DRY_RUN:
            ops.info(f"[DRY-RUN] Would log to Notion -> ID: {video_id}, Status: {status}")
            return True

        from datetime import datetime
        now_iso = datetime.utcnow().isoformat() + "Z"

        try:
            url = "https://api.notion.com/v1/pages"
            payload = {
                "parent": {"database_id": self.db_id},
                "properties": {
                    "Video ID": {
                        "title": [
                            {"text": {"content": video_id}}
                        ]
                    },
                    "Platform": {
                        "select": {"name": platform}
                    },
                    "Status": {
                        "select": {"name": status}
                    },
                    "TikTok URL": {
                        "url": tiktok_url if tiktok_url else "https://www.tiktok.com"
                    },
                    "Twitter URL": {
                        "url": twitter_url if twitter_url else "https://x.com"
                    },
                    "Paylaşım Tarihi": {
                        "date": {"start": now_iso}
                    }
                }
            }
            resp = requests.post(url, headers=self.headers, json=payload, timeout=10)
            resp.raise_for_status()
            ops.info(f"Successfully logged Video ID {video_id} to Notion with status {status}.")
            return True
        except Exception as e:
            ops.error(f"Error logging video {video_id} to Notion: {e}", exception=e)
            return False
