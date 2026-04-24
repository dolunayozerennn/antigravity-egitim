"""
Merkezi konfigürasyon — env okuma, Apify fail-over, Notion bağlantı bilgileri.
"""
from __future__ import annotations

import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("web_satis")

# ---------------------------------------------------------------------------
# ENV dosyasından oku  (master.env → lokal geliştirme)
# ---------------------------------------------------------------------------
MASTER_ENV_PATH = os.path.expanduser(
    "~/Desktop/Antigravity/_knowledge/credentials/master.env"
)


def _load_env(path: str) -> dict[str, str]:
    """master.env'den key=value satırlarını parse et."""
    env = {}
    if not os.path.exists(path):
        logger.warning("master.env bulunamadı: %s", path)
        return env
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip().strip("\"'")
    return env


_env = _load_env(MASTER_ENV_PATH)


def get(key: str, default: str | None = None) -> str | None:
    """Önce os.environ, sonra master.env'den oku."""
    return os.environ.get(key) or _env.get(key) or default


# ---------------------------------------------------------------------------
# Apify — fail-over destekli
# ---------------------------------------------------------------------------
APIFY_API_KEY_1 = get("APIFY_API_KEY_1")
APIFY_API_KEY_2 = get("APIFY_API_KEY_2")

if not APIFY_API_KEY_1:
    raise EnvironmentError("APIFY_API_KEY_1 eksik! master.env kontrol et.")

# ---------------------------------------------------------------------------
# Notion
# ---------------------------------------------------------------------------
NOTION_TOKEN = get("NOTION_API_TOKEN")
if not NOTION_TOKEN:
    raise EnvironmentError("NOTION_API_TOKEN eksik! master.env kontrol et.")

# Notion kokpit sayfası (Website Satış Otomasyonu)
NOTION_COCKPIT_PAGE_ID = "34995514-0a32-80b5-82c5-ca93633b15a4"

# Lead Onay DB ID — ilk çalıştırmada oluşturulacak ve buraya set edilecek
NOTION_LEAD_DB_ID: str | None = get("NOTION_LEAD_DB_ID")

# ---------------------------------------------------------------------------
# Apify Google Maps Scraper Actor ID
# ---------------------------------------------------------------------------
APIFY_ACTOR_ID = "nwua9Gu5YrADL7ZDj"

# ---------------------------------------------------------------------------
# Scoring eşikleri
# ---------------------------------------------------------------------------
SCORE_THRESHOLD_MIN = 50       # altı otomatik elenir
SCORE_THRESHOLD_HIGH = 70      # üstü yüksek öncelik

# ---------------------------------------------------------------------------
# Supabase (ANA Logger — Gölge Modu)
# ---------------------------------------------------------------------------
SUPABASE_URL = get("SUPABASE_URL")
SUPABASE_KEY = get("SUPABASE_ANON_KEY")
# Yoksa logger disabled modda çalışır — ana akışı etkilemez

# ---------------------------------------------------------------------------
# Günlük limitler
# ---------------------------------------------------------------------------
MAX_PLACES_PER_SEARCH = 5      # MVP test limiti (prodda 200-300)
