"""Twitter_Text_Paylasim — config & env."""

import sys

from env_loader import get_env


class Config:
    def __init__(self):
        self.ENV = (get_env("ENV") or "development").lower()
        self.IS_DRY_RUN = self.ENV == "development" or get_env("DRY_RUN") == "1"

        # Typefully (X publisher proxy, draft mode)
        self.TYPEFULLY_API_KEY = self._require("TYPEFULLY_API_KEY")
        self.TYPEFULLY_SOCIAL_SET_ID = int(self._require("TYPEFULLY_SOCIAL_SET_ID"))

        # LLM provider: anthropic (default v3.1) veya openai
        self.LLM_PROVIDER = (get_env("LLM_PROVIDER") or "anthropic").lower()

        # Anthropic Claude (varsayılan writer)
        self.ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY") or ""

        # OpenAI (image prompt + opsiyonel writer fallback)
        self.OPENAI_API_KEY = self._require("OPENAI_API_KEY")

        # v3.1: writer modeli Claude Opus 4.7. OpenAI'a düşülürse gpt-4o.
        if self.LLM_PROVIDER == "anthropic":
            if not self.ANTHROPIC_API_KEY:
                raise EnvironmentError("CRITICAL STARTUP FAILURE: LLM_PROVIDER=anthropic ama ANTHROPIC_API_KEY yok")
            self.WRITER_MODEL = get_env("WRITER_MODEL") or "claude-opus-4-7"
        else:
            self.WRITER_MODEL = get_env("WRITER_MODEL") or "gpt-4o"

        # Perplexity (AI haberleri)
        self.PERPLEXITY_API_KEY = self._require("PERPLEXITY_API_KEY")
        self.PERPLEXITY_BASE_URL = get_env("PERPLEXITY_BASE_URL") or "https://api.perplexity.ai"

        # GitHub (repo discovery)
        self.GITHUB_TOKEN = self._require("GITHUB_TOKEN")

        # Kie AI (görsel üretim — AI Use Case serisi)
        self.KIE_API_KEY = self._require("KIE_API_KEY")

        # YouTube (kanal RSS + transcript)
        # Channel ID veya handle (@dolunayozeren). Handle verilirse RSS feed'e
        # çevirmek için YouTube Data API gerekecek; pratikte kullanıcı UC ID'sini
        # verir. Şimdilik UC ID bekliyoruz.
        self.YOUTUBE_CHANNEL_ID = get_env("YOUTUBE_CHANNEL_ID")

        # Notion
        self.NOTION_TOKEN = self._require("NOTION_SOCIAL_TOKEN")
        self.NOTION_X_DB_ID = get_env("NOTION_X_DB_ID")  # ilk koşuştan önce doldurulacak
        self.NOTION_DB_REELS_KAPAK = get_env("NOTION_DB_REELS_KAPAK")  # YouTube script kaynağı

        # Kalite eşiği — v3: 8 (prompt'lar sıkılaştığı için)
        self.QUALITY_THRESHOLD = int(get_env("QUALITY_THRESHOLD") or 8)

        # Dedup penceresi (gün)
        self.DEDUP_DAYS = int(get_env("DEDUP_DAYS") or 30)

    def _require(self, key: str) -> str:
        val = get_env(key)
        if not val:
            raise EnvironmentError(f"CRITICAL STARTUP FAILURE: {key} bulunamadı")
        return val


try:
    settings = Config()
except EnvironmentError as e:
    print(f"BOOT ERROR: {e}")
    sys.exit(1)
