"""
eCom Reklam Otomasyonu — Fail-Fast Config
==========================================
Boot anında tüm gerekli ENV değişkenlerini doğrular.
Eksik varsa uygulama anında çöker (Railway loglarında görünür).
"""

import os
import sys


class Config:
    def __init__(self):
        # ── Ortam Modu ──
        self.ENV = os.environ.get("ENV", "development").lower()
        self.IS_DRY_RUN = self.ENV == "development" or os.environ.get("DRY_RUN", "0") == "1"

        # ── Telegram ──
        self.TELEGRAM_BOT_TOKEN = self._require_env("TELEGRAM_ECOM_BOT_TOKEN")
        self.ADMIN_CHAT_ID = int(self._require_env("TELEGRAM_ADMIN_CHAT_ID"))
        self.ALLOWED_USER_IDS = [self.ADMIN_CHAT_ID]

        # ── OpenAI (GPT-4.1 Mini — Chat + Vision) ──
        self.OPENAI_API_KEY = self._require_env("OPENAI_API_KEY")
        self.OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

        # ── Perplexity (Marka Araştırması) ──
        self.PERPLEXITY_API_KEY = self._require_env("PERPLEXITY_API_KEY")
        self.PERPLEXITY_BASE_URL = os.environ.get("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")

        # ── ImgBB (Görsel → Public URL) ──
        self.IMGBB_API_KEY = self._require_env("IMGBB_API_KEY")

        # ── Kie AI (Seedance 2.0 + Nano Banana 2) ──
        self.KIE_API_KEY = self._require_env("KIE_API_KEY")
        self.KIE_BASE_URL = os.environ.get("KIE_BASE_URL", "https://api.kie.ai/api/v1/")

        # ── ElevenLabs (Doğrudan API — Türkçe TTS) ──
        self.ELEVENLABS_API_KEY = self._require_env("ELEVENLABS_API_KEY")
        self.ELEVENLABS_MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_v3")

        # ── Replicate (Video + Ses Birleştirme) ──
        self.REPLICATE_API_TOKEN = self._require_env("REPLICATE_API_TOKEN")

        # ── Firecrawl (URL Scraping — birincil) ──
        self.FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

        # ── Notion (Üretim Logları & Chat Hafızası) ──
        self.NOTION_TOKEN = self._require_env("NOTION_SOCIAL_TOKEN")
        self.NOTION_DB_ID = self._require_env("NOTION_DB_ECOM_REKLAM")
        self.NOTION_CHAT_DB_ID = os.environ.get("NOTION_CHAT_DB_ID", "34095514-0a32-81a2-9af3-e06cf9b8c4fd")

    # ── Yardımcılar ──

    def _require_env(self, key):
        """Fetches an environment variable, raises error if missing."""
        val = os.environ.get(key)
        if not val:
            raise EnvironmentError(
                f"CRITICAL STARTUP FAILURE: Gerekli ortam değişkeni '{key}' bulunamadı! "
                f"Railway dashboard → Variables bölümünden ekleyin."
            )
        return val


# ── Global instance — import anında fail-fast ──
try:
    settings = Config()
except EnvironmentError as e:
    print(f"BOOT ERROR: {e}")
    sys.exit(1)
