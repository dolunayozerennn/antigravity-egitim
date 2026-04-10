import os
import sys
import shutil
import logging

logger = logging.getLogger("Config")

# Antigravity V2 Fail-Fast Environment Validation
class Config:
    def __init__(self):
        # 1. Check if ENV is defined (Development or Production)
        self.ENV = os.environ.get("ENV", "development").lower()
        self.IS_DRY_RUN = self.ENV == "development" or os.environ.get("DRY_RUN", "0") == "1"
        
        # 2. COVER_TYPE — which platform to generate covers for
        self.COVER_TYPE = os.environ.get("COVER_TYPE", "")
        # COVER_TYPE can also be passed via CLI arg, so don't fail here if empty
        
        # 3. Required API tokens — PRODUCTION'da yoksa boot crash
        _dev_default = "dev_placeholder" if self.IS_DRY_RUN else None
        
        self.NOTION_SOCIAL_TOKEN = self._require_env("NOTION_SOCIAL_TOKEN", default=_dev_default)
        self.KIE_API_KEY = self._require_env("KIE_API_KEY", default=_dev_default)
        self.GEMINI_API_KEY = self._require_env("GEMINI_API_KEY", default=_dev_default)
        self.IMGBB_API_KEY = self._require_env("IMGBB_API_KEY", default=_dev_default)
        
        # 4. Google Drive — Railway'de JSON env var olarak gelir, lokal'de dosyadan okunur
        self.GOOGLE_OUTREACH_TOKEN_JSON = os.environ.get("GOOGLE_OUTREACH_TOKEN_JSON", "")
        if not self.GOOGLE_OUTREACH_TOKEN_JSON and not self.IS_DRY_RUN:
            # Railway'de zorunlu, lokal'de dosyadan okunuyor
            logger.warning("GOOGLE_OUTREACH_TOKEN_JSON env var not set — Drive uploads will use local OAuth token file")
        
        # 5. Notion Database IDs (have defaults from master.env)
        self.NOTION_DB_REELS_KAPAK = os.environ.get("NOTION_DB_REELS_KAPAK", "")
        self.NOTION_DB_YOUTUBE_ISBIRLIKLERI = os.environ.get("NOTION_DB_YOUTUBE_ISBIRLIKLERI", "")
        
        logger.info(f"Config loaded: ENV={self.ENV}, DRY_RUN={self.IS_DRY_RUN}, COVER_TYPE={self.COVER_TYPE or '(CLI/env)'}")
        
    def _require_env(self, key, default=None):
        """Fetches an environment variable, raises error if missing."""
        val = os.environ.get(key, default)
        if not val:
            raise EnvironmentError(f"CRITICAL STARTUP FAILURE: Gerekli ortam değişkeni {key} bulunamadı!")
        return val

    def _check_system_deps(self, binaries: list):
        """Verifies that required system binaries exist in PATH. Fails fast if missing."""
        for binary in binaries:
            if not shutil.which(binary):
                raise EnvironmentError(
                    f"CRITICAL STARTUP FAILURE: Sistem bağımlılığı '{binary}' bulunamadı! "
                    f"nixpacks.toml dosyasına nixPkgs = [\"{binary}\"] eklenmeli."
                )

# Instantiating the config globally so it fails fast on module load.
try:
    settings = Config()
except EnvironmentError as e:
    # Use a basic print here because logger might not be ready, or generic logging might depend on config.
    print(f"BOOT ERROR: {e}")
    sys.exit(1)
