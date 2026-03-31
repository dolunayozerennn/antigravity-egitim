import os
import sys

class Config:
    """Antigravity V2 Fail-Fast Environment Validation"""

    def __init__(self):
        self.ENV = os.environ.get("ENV", "development").lower()
        self.IS_DRY_RUN = self.ENV == "development" or os.environ.get("DRY_RUN", "0") == "1"

        # ── Telegram ──
        self.TELEGRAM_BOT_TOKEN = self._require_env("TELEGRAM_BOT_TOKEN")

        # ── Gemini (Vision + Chat) ──
        self.GEMINI_API_KEY = self._require_env("GEMINI_API_KEY")
        self.GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

        # ── Notion ──
        # Database, social integration ile paylaşılmış — önce NOTION_TOKEN, sonra NOTION_SOCIAL_TOKEN dene
        self.NOTION_TOKEN = os.environ.get("NOTION_TOKEN") or self._require_env("NOTION_SOCIAL_TOKEN")
        self.NOTION_DB_ID = self._require_env("NOTION_DB_ID")

        # ── Yetkilendirilmiş kullanıcılar (Telegram ID) ──
        allowed = os.environ.get("ALLOWED_USER_IDS", "")
        self.ALLOWED_USER_IDS = [int(uid.strip()) for uid in allowed.split(",") if uid.strip()] if allowed else []

    def _require_env(self, key, default=None):
        val = os.environ.get(key, default)
        if not val:
            raise EnvironmentError(f"CRITICAL STARTUP FAILURE: Gerekli ortam değişkeni {key} bulunamadı!")
        return val


try:
    settings = Config()
except EnvironmentError as e:
    print(f"BOOT ERROR: {e}")
    sys.exit(1)
