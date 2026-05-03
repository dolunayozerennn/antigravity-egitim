"""Drive klasöründen master video seç + indir (Service Account, readonly)."""

import os
import re
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("LinkedIn_Video_Paylasim", "DriveDownloader")

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}


class DriveDownloader:
    def __init__(self):
        creds = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_SA_JSON_PATH,
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )
        self.service = build("drive", "v3", credentials=creds, cache_discovery=False)
        self.tmp_dir = Path("/tmp/linkedin_paylasim")
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def extract_folder_id(url: str) -> str:
        if not url:
            return ""
        m = re.search(r"/folders/([a-zA-Z0-9_-]+)", url)
        return m.group(1) if m else ""

    def list_videos(self, folder_id: str) -> list:
        files = self._list_folder(folder_id)
        videos = [f for f in files if not _is_folder(f) and _is_video(f["name"])]
        for sf in [f for f in files if _is_folder(f)]:
            sub_files = self._list_folder(sf["id"])
            videos.extend([f for f in sub_files if not _is_folder(f) and _is_video(f["name"])])
        return videos

    def _list_folder(self, folder_id: str) -> list:
        try:
            res = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="files(id, name, mimeType, size)",
                pageSize=200,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute()
            return res.get("files", [])
        except Exception as e:
            ops.error(f"Drive list hatası ({folder_id[:12]}…): {e}", exception=e)
            return []

    def select_video(self, videos: list) -> dict:
        for pattern in settings.VIDEO_PATTERN_PRIORITY:
            matches = [v for v in videos if pattern in v["name"].lower()]
            if not matches:
                continue
            best = max(matches, key=lambda v: int(v.get("size", 0) or 0))
            ops.info(f"Pattern '{pattern}' eşleşti: {best['name']} ({int(best.get('size', 0) or 0)/1024/1024:.1f} MB)")
            return best
        return None

    def download_file(self, file_id: str, output_name: str) -> str:
        safe_name = re.sub(r"[^\w.\-]+", "_", output_name)[:120]
        target = self.tmp_dir / safe_name
        if target.exists():
            target.unlink()
        try:
            request = self.service.files().get_media(fileId=file_id, supportsAllDrives=True)
            with open(target, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request, chunksize=8 * 1024 * 1024)
                done = False
                last_log = -1
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        pct = int(status.progress() * 100)
                        if pct >= last_log + 10:
                            ops.info(f"Drive indirme: {pct}%")
                            last_log = pct
            ops.info(f"İndirme tamam: {target} ({target.stat().st_size/1024/1024:.1f} MB)")
            return str(target)
        except Exception as e:
            ops.error(f"Drive indirme hatası: {e}", exception=e)
            if target.exists():
                target.unlink()
            return ""

    def cleanup(self, path: str):
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                ops.warning(f"Temp dosya silinemedi {path}: {e}")


def _is_folder(f: dict) -> bool:
    return f.get("mimeType") == "application/vnd.google-apps.folder"


def _is_video(name: str) -> bool:
    return os.path.splitext(name)[1].lower() in VIDEO_EXTS
