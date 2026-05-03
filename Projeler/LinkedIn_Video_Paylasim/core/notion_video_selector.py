"""Notion 'Dolunay Reels & YouTube' DB → Yayınlandı + Drive linki olan videolar."""

import requests
from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("LinkedIn_Video_Paylasim", "NotionVideoSelector")


class NotionVideoSelector:
    BASE = "https://api.notion.com/v1"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        self.db_id = settings.NOTION_DB_REELS

    def query_published(self) -> list:
        url = f"{self.BASE}/databases/{self.db_id}/query"
        payload = {
            "filter": {"property": "Status", "select": {"equals": "Yayınlandı"}},
            "sorts": [{"property": "Paylaşım Tarihi", "direction": "descending"}],
            "page_size": 100,
        }
        all_results = []
        while True:
            try:
                resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
                resp.raise_for_status()
            except requests.RequestException as e:
                ops.error(f"Notion query hatası: {e}", exception=e)
                return all_results
            data = resp.json()
            all_results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            payload["start_cursor"] = data["next_cursor"]
        ops.info(f"Notion: {len(all_results)} adet 'Yayınlandı' video bulundu")
        return all_results

    @staticmethod
    def parse_page(page: dict) -> dict:
        props = page.get("properties", {})
        title_parts = props.get("Name", {}).get("title", [])
        name = "".join(t.get("plain_text", "") for t in title_parts).strip()
        drive_url = props.get("Drive", {}).get("url") or ""
        date_obj = props.get("Paylaşım Tarihi", {}).get("date")
        publish_date = date_obj.get("start") if date_obj else None
        cap_parts = props.get("Caption", {}).get("rich_text", [])
        caption = "".join(t.get("plain_text", "") for t in cap_parts).strip()
        return {
            "page_id": page["id"],
            "name": name or "Untitled",
            "drive_url": drive_url,
            "publish_date": publish_date,
            "caption_property": caption,
            "notion_url": page.get("url", ""),
        }

    def get_page_body_text(self, page_id: str) -> str:
        url = f"{self.BASE}/blocks/{page_id}/children?page_size=100"
        all_text = []
        cursor = None
        while True:
            full_url = url + (f"&start_cursor={cursor}" if cursor else "")
            try:
                resp = requests.get(full_url, headers=self.headers, timeout=20)
                resp.raise_for_status()
            except requests.RequestException as e:
                ops.warning(f"Sayfa body okuma hatası ({page_id}): {e}")
                return "\n".join(all_text)
            data = resp.json()
            for block in data.get("results", []):
                btype = block.get("type")
                payload = block.get(btype, {})
                rich = payload.get("rich_text") or payload.get("text") or []
                line = "".join(t.get("plain_text", "") for t in rich).strip()
                if line:
                    all_text.append(line)
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return "\n".join(all_text)
