import os
import sys

class Config:
    def __init__(self):
        self.ENV = os.environ.get("ENV", "development").lower()
        self.IS_DRY_RUN = self.ENV == "development" or os.environ.get("DRY_RUN", "0") == "1"
        
        self.APIFY_API_KEY = self._require_env("APIFY_API_KEY")
        
        # When running in Railway or locally, determine where the token is.
        default_token_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "_knowledge", "credentials", "oauth", "gmail-dolunay-ai-token.json"
        ))
        
        self.OAUTH_TOKEN_PATH = os.environ.get("OAUTH_TOKEN_PATH", default_token_path)

        if not os.path.exists(self.OAUTH_TOKEN_PATH):
            # Fallback path if deployed or different layout
            fallback = os.path.join(os.path.dirname(__file__), "..", "..", "..", "_knowledge", "credentials", "oauth", "gmail-dolunay-ai-token.json")
            if os.path.exists(fallback):
                self.OAUTH_TOKEN_PATH = fallback

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
