"""
YouTube Otomasyonu — Fail-Fast Config
Antigravity V2 Starter tabanlı.
Tüm gerekli env variable'ları boot time'da doğrular.
"""
import os
import sys
import shutil


class Config:
    def __init__(self):
        self.ENV = os.environ.get("ENV", "development").lower()
        self.IS_DRY_RUN = self.ENV == "development" or os.environ.get("DRY_RUN", "0") == "1"

        # ── AI Servisleri ──
        self.OPENAI_API_KEY = self._require_env(
            "OPENAI_API_KEY",
            default="sk-test-placeholder" if self.IS_DRY_RUN else None
        )

        # ── Video Üretimi ──
        self.KIE_API_KEY = self._require_env(
            "KIE_API_KEY",
            default="test-kie-key" if self.IS_DRY_RUN else None
        )
        self.KIE_BASE_URL = os.environ.get("KIE_BASE_URL", "https://api.kie.ai/api/v1")

        # ── Seedance 2.0 Parametreleri ──
        self.VIDEO_MODEL = os.environ.get("VIDEO_MODEL", "bytedance/seedance-2")
        self.VIDEO_DURATION = int(os.environ.get("VIDEO_DURATION", "10"))
        self.VIDEO_ASPECT_RATIO = os.environ.get("VIDEO_ASPECT_RATIO", "9:16")
        self.VIDEO_RESOLUTION = os.environ.get("VIDEO_RESOLUTION", "720p")
        self.GENERATE_AUDIO = os.environ.get("GENERATE_AUDIO", "true").lower() == "true"

        # ── YouTube Upload ──
        self.YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "")
        self.YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
        self.YOUTUBE_CATEGORY_ID = os.environ.get("YOUTUBE_CATEGORY_ID", "28")  # Science & Technology
        self.YOUTUBE_PRIVACY = os.environ.get("YOUTUBE_PRIVACY", "public")
        self.YOUTUBE_ENABLED = os.environ.get("YOUTUBE_ENABLED", "false").lower() == "true"

        # ── Telegram ──
        self.TELEGRAM_BOT_TOKEN = self._require_env(
            "TELEGRAM_BOT_TOKEN",
            default="test-telegram-token" if self.IS_DRY_RUN else None
        )
        self.TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "1238877494")

        # ── Notion ──
        self.NOTION_TOKEN = os.environ.get(
            "NOTION_SOCIAL_TOKEN",
            os.environ.get("NOTION_API_TOKEN", "")
        )
        self.NOTION_DB_ID = os.environ.get("NOTION_DB_YOUTUBE_OTOMASYON", "")
        self.NOTION_ENABLED = bool(self.NOTION_TOKEN and self.NOTION_DB_ID)

        # ── Polling Ayarları ──
        self.POLL_INITIAL_WAIT = int(os.environ.get("POLL_INITIAL_WAIT", "90"))
        self.POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "15"))
        self.POLL_MAX_ATTEMPTS = int(os.environ.get("POLL_MAX_ATTEMPTS", "40"))

        # ── Sistem Bağımlılıkları ──
        # ffmpeg şu an gerekli değil ama ileride gerekebilir
        # self._check_system_deps(["ffmpeg"])

    def _require_env(self, key, default=None):
        """Gerekli env variable'ı al, yoksa çök."""
        val = os.environ.get(key, default)
        if not val:
            raise EnvironmentError(
                f"CRITICAL STARTUP FAILURE: Gerekli ortam değişkeni '{key}' bulunamadı!"
            )
        return val

    def _check_system_deps(self, binaries: list):
        """Sistem bağımlılığı kontrolü."""
        for binary in binaries:
            if not shutil.which(binary):
                raise EnvironmentError(
                    f"CRITICAL STARTUP FAILURE: Sistem bağımlılığı '{binary}' bulunamadı! "
                    f"nixpacks.toml dosyasına nixPkgs = [\"{binary}\"] eklenmeli."
                )


# Boot time'da config'i oluştur — eksik var ise hemen çök
try:
    settings = Config()
except EnvironmentError as e:
    print(f"BOOT ERROR: {e}")
    sys.exit(1)
