import os
import sys
import logging


def _int_env(key, default):
    raw = os.environ.get(key)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        raise EnvironmentError(f"Env {key} must be integer, got: {raw!r}")


def _csv_env(key, default):
    raw = os.environ.get(key)
    if not raw:
        return default
    return [x.strip() for x in raw.split(",") if x.strip()]


class Config:
    def __init__(self):
        self.ENV = os.environ.get("ENV", "development").lower()
        self.IS_DRY_RUN = self.ENV == "development" or os.environ.get("DRY_RUN", "0") == "1"

        # ── Apify keys ────────────────────────────────────────────────
        self.APIFY_KEYS = []
        for i in range(1, 10):
            val = os.environ.get(f"APIFY_API_KEY_{i}")
            if val:
                self.APIFY_KEYS.append(val)
        old_val = os.environ.get("APIFY_API_KEY")
        if old_val and old_val not in self.APIFY_KEYS:
            self.APIFY_KEYS.append(old_val)
        if not self.APIFY_KEYS:
            raise EnvironmentError("CRITICAL: en az bir APIFY_API_KEY_x gerekli")

        # ── Apify actor IDs ───────────────────────────────────────────
        self.APIFY_INSTAGRAM_ACTOR = os.environ.get("APIFY_INSTAGRAM_ACTOR", "apify/instagram-profile-scraper")
        self.APIFY_TIKTOK_ACTOR = os.environ.get("APIFY_TIKTOK_ACTOR", "0FXVyOXXEmdGcV88a")
        self.APIFY_YOUTUBE_ACTOR = os.environ.get("APIFY_YOUTUBE_ACTOR", "h7sDV53CddomktSi5")

        # ── Hedef profiller ───────────────────────────────────────────
        self.IG_USERNAME = os.environ.get("IG_USERNAME", "dolunay_ozeren")
        self.TIKTOK_USERNAME = os.environ.get("TIKTOK_USERNAME", "dolunayozeren")
        self.YOUTUBE_SEARCH_QUERY = os.environ.get("YOUTUBE_SEARCH_QUERY", "dolunayozeren")
        self.YOUTUBE_CHANNEL_KEYWORDS = [
            k.lower() for k in _csv_env("YOUTUBE_CHANNEL_KEYWORDS", ["dolunayozeren", "dolunay özeren", "dolunay ozeren"])
        ]

        # ── İzlenme barajları ─────────────────────────────────────────
        self.IG_VIEW_THRESHOLD = _int_env("IG_VIEW_THRESHOLD", 200_000)
        self.TIKTOK_VIEW_THRESHOLD = _int_env("TIKTOK_VIEW_THRESHOLD", 100_000)
        self.YT_SHORTS_THRESHOLD = _int_env("YT_SHORTS_THRESHOLD", 100_000)
        self.YT_LONG_THRESHOLD = _int_env("YT_LONG_THRESHOLD", 10_000)
        self.LOOKBACK_DAYS = _int_env("LOOKBACK_DAYS", 7)

        # ── Mail alıcıları ────────────────────────────────────────────
        self.REPORT_TO = os.environ.get("REPORT_TO", "ceren@dolunay.ai")
        self.REPORT_FROM = os.environ.get("REPORT_FROM", "Dolunay Özeren <dolunay@dolunay.ai>")
        self.TECH_ERROR_TO = os.environ.get("TECH_ERROR_TO", "ozerendolunay@gmail.com")

        # ── LLM ───────────────────────────────────────────────────────
        self.GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

        # ── Gmail OAuth ───────────────────────────────────────────────
        # Production: GMAIL_OAUTH_JSON env'i şart. Lokal: dosya yolu fallback'i.
        oauth_json = os.environ.get("GMAIL_OAUTH_JSON")
        if oauth_json:
            import tempfile
            fd, path = tempfile.mkstemp(suffix=".json")
            with os.fdopen(fd, "w") as f:
                f.write(oauth_json)
            self.OAUTH_TOKEN_PATH = path
        else:
            default_token_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__), "..", "..", "_knowledge", "credentials", "oauth", "gmail-dolunay-ai-token.json"
            ))
            self.OAUTH_TOKEN_PATH = os.environ.get("OAUTH_TOKEN_PATH", default_token_path)
            if not os.path.exists(self.OAUTH_TOKEN_PATH):
                fallback = os.path.join(
                    os.path.dirname(__file__), "..", "..", "..", "_knowledge", "credentials", "oauth", "gmail-dolunay-ai-token.json"
                )
                if os.path.exists(fallback):
                    self.OAUTH_TOKEN_PATH = fallback

            if self.ENV == "production" and not os.path.exists(self.OAUTH_TOKEN_PATH):
                raise EnvironmentError(
                    "CRITICAL: Production ortamında GMAIL_OAUTH_JSON env'i set edilmemiş "
                    f"ve OAUTH_TOKEN_PATH ({self.OAUTH_TOKEN_PATH}) de yok"
                )


try:
    settings = Config()
except EnvironmentError as e:
    logging.basicConfig(level=logging.ERROR)
    logging.error(f"BOOT ERROR: {e}")
    sys.exit(1)
