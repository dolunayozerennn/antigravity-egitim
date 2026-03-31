import os
import sys

# Antigravity V2 Fail-Fast Environment Validation
class Config:
    def __init__(self):
        # 1. Check if ENV is defined (Development or Production)
        self.ENV = os.environ.get("ENV", "development").lower()
        self.IS_DRY_RUN = self.ENV == "development" or os.environ.get("DRY_RUN", "0") == "1"
        
        # 2. Add all your required tokens and keys here.
        # Example: self.NOTION_TOKEN = self._require_env("NOTION_API_TOKEN")
        self.EXAMPLE_TOKEN = self._require_env("EXAMPLE_TOKEN", default="local_placeholder" if self.IS_DRY_RUN else None)
        
    def _require_env(self, key, default=None):
        """Fetches an environment variable, raises error if missing."""
        val = os.environ.get(key, default)
        if not val:
            raise EnvironmentError(f"CRITICAL STARTUP FAILURE: Gerekli ortam değişkeni {key} bulunamadı!")
        return val

# Instantiating the config globally so it fails fast on module load.
try:
    settings = Config()
except EnvironmentError as e:
    # Use a basic print here because logger might not be ready, or generic logging might depend on config.
    print(f"BOOT ERROR: {e}")
    sys.exit(1)
