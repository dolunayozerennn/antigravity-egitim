import os
import sys
import shutil

from env_loader import get_env, get_sa_json_path


class Config:
    def __init__(self):
        self.ENV = (os.environ.get("ENV") or get_env("ENV") or "development").lower()
        self.IS_DRY_RUN = self.ENV == "development" or os.environ.get("DRY_RUN", "0") == "1"

        if not shutil.which("ffmpeg"):
            raise EnvironmentError("CRITICAL STARTUP FAILURE: ffmpeg binary bulunamadı! nixpacks.toml doğru yapılandırılmalı.")

        self.LINKEDIN_ACCESS_TOKEN = self._require("LINKEDIN_ACCESS_TOKEN")
        self.LINKEDIN_PERSON_URN = self._require("LINKEDIN_PERSON_URN")

        self.GROQ_API_KEY = self._require("GROQ_API_KEY")
        self.GROQ_BASE_URL = get_env("GROQ_BASE_URL") or "https://api.groq.com/openai/v1"
        self.GROQ_MODEL = get_env("GROQ_MODEL") or "llama-3.3-70b-versatile"

        self.NOTION_TOKEN = self._require("NOTION_SOCIAL_TOKEN")
        self.NOTION_DB_REELS = self._require("NOTION_DB_REELS_KAPAK")
        self.NOTION_LINKEDIN_DB_ID = self._require("NOTION_LINKEDIN_DB_ID")

        self.GOOGLE_SA_JSON_PATH = get_sa_json_path()
        if not self.GOOGLE_SA_JSON_PATH:
            raise EnvironmentError(
                "CRITICAL STARTUP FAILURE: Google Service Account JSON bulunamadı! "
                "Railway: GOOGLE_SERVICE_ACCOUNT_JSON env var (base64). "
                "Lokal: _knowledge/credentials/google-service-account.json"
            )

        self.VIDEO_PATTERN_PRIORITY = [
            p.strip().lower() for p in
            (get_env("VIDEO_PATTERN_PRIORITY") or "tiktok,insta").split(",")
            if p.strip()
        ]

        self.MAX_VIDEO_BYTES = int(get_env("MAX_VIDEO_BYTES") or (5 * 1024 * 1024 * 1024))
        thr = get_env("REENCODE_OVER_BYTES")
        self.REENCODE_OVER_BYTES = int(thr) if thr else None

    def _require(self, key: str) -> str:
        val = get_env(key)
        if not val:
            raise EnvironmentError(f"CRITICAL STARTUP FAILURE: Gerekli ortam değişkeni {key} bulunamadı!")
        return val


try:
    settings = Config()
except EnvironmentError as e:
    print(f"BOOT ERROR: {e}")
    sys.exit(1)
