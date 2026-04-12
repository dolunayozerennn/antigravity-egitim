"""
YouTube Otomasyonu V2 — Fail-Fast Config
Chat-based Telegram Bot mimarisi.
Tüm gerekli env variable'ları boot time'da doğrular.
"""
import os
import sys
import logging
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

        # ── Video Üretimi (Kie AI) ──
        self.KIE_API_KEY = self._require_env(
            "KIE_API_KEY",
            default="test-kie-key" if self.IS_DRY_RUN else None
        )
        self.KIE_BASE_URL = os.environ.get("KIE_BASE_URL", "https://api.kie.ai/api/v1")

        # ── Video Birleştirme (Replicate) ──
        self.REPLICATE_API_TOKEN = self._require_env(
            "REPLICATE_API_TOKEN",
            default="test-replicate-token" if self.IS_DRY_RUN else None
        )
        self.REPLICATE_MERGE_VERSION = os.environ.get(
            "REPLICATE_MERGE_VERSION",
            "14273448a57117b5d424410e2e79700ecde6cc7d60bf522a769b9c7cf989eba7"
        )

        # ── Default Üretim Parametreleri ──
        self.DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "seedance-2")  # veya "veo3.1"
        self.DEFAULT_ORIENTATION = os.environ.get("DEFAULT_ORIENTATION", "portrait")  # portrait=9:16, landscape=16:9
        self.DEFAULT_CLIP_COUNT = int(os.environ.get("DEFAULT_CLIP_COUNT", "1"))
        self.DEFAULT_AUDIO = os.environ.get("DEFAULT_AUDIO", "true").lower() == "true"
        self.DEFAULT_DURATION = int(os.environ.get("DEFAULT_DURATION", "10"))
        self.DEFAULT_RESOLUTION = os.environ.get("DEFAULT_RESOLUTION", "720p")

        # ── YouTube Upload ──
        self.YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "")
        self.YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
        self.YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
        self.YOUTUBE_CATEGORY_ID = os.environ.get("YOUTUBE_CATEGORY_ID", "15")  # Pets & Animals
        self.YOUTUBE_PRIVACY = os.environ.get("YOUTUBE_PRIVACY", "public")  # public — videonun izlenmesi gerekiyor
        self.YOUTUBE_ENABLED = os.environ.get("YOUTUBE_ENABLED", "false").lower() == "true"

        # ── Telegram Bot (V2 — Chat-based) ──
        self.TELEGRAM_YOUTUBE_BOT_TOKEN = self._require_env(
            "TELEGRAM_YOUTUBE_BOT_TOKEN",
            default="test-telegram-yt-bot-token" if self.IS_DRY_RUN else None
        )
        self.TELEGRAM_ADMIN_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "1238877494")

        # Notification bot (ayrı — eski pipeline uyumluluğu)
        self.TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", self.TELEGRAM_YOUTUBE_BOT_TOKEN)

        # Access control — sadece admin
        _allowed_raw = os.environ.get("ALLOWED_USER_IDS", "1238877494")
        self.ALLOWED_USER_IDS = [int(uid.strip()) for uid in _allowed_raw.split(",") if uid.strip()]

        # ── Notion ──
        self.NOTION_TOKEN = os.environ.get(
            "NOTION_SOCIAL_TOKEN",
            os.environ.get("NOTION_API_TOKEN", "")
        )
        self.NOTION_DB_ID = os.environ.get("NOTION_DB_YOUTUBE_OTOMASYON", "")
        self.NOTION_ENABLED = bool(self.NOTION_TOKEN and self.NOTION_DB_ID)

        # ── Polling Ayarları (Kie AI video üretimi) ──
        self.POLL_INITIAL_WAIT = int(os.environ.get("POLL_INITIAL_WAIT", "60"))
        self.POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "15"))
        self.POLL_MAX_ATTEMPTS = int(os.environ.get("POLL_MAX_ATTEMPTS", "40"))

        # ── Sistem Bağımlılıkları (Opsiyonel — FFmpeg sadece fallback) ──
        self.FFMPEG_AVAILABLE = bool(shutil.which("ffmpeg"))
        if not self.FFMPEG_AVAILABLE and not self.IS_DRY_RUN:
            logging.getLogger("Config").warning(
                "⚠️ FFmpeg bulunamadı — video birleştirme sadece Replicate ile yapılacak."
            )

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
                    f"nixpacks.toml dosyasına aptPkgs = [\"{binary}\"] eklenmeli."
                )


# Boot time'da config'i oluştur — eksik var ise hemen çök
try:
    settings = Config()
except EnvironmentError as e:
    logging.critical(f"BOOT ERROR: {e}", exc_info=True)
    sys.exit(1)
