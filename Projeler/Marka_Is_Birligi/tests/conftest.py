import os
import sys
from pathlib import Path

# Repo root'u sys.path'e ekle ki `from src...` import'ları çalışsın.
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

# notion_service modül-seviyesinde token kontrolü yapmıyor (fonksiyonlarda),
# ama yine de import'a güvenli env stub'ları sağla.
os.environ.setdefault("NOTION_SOCIAL_TOKEN", "test-token")
os.environ.setdefault("NOTION_DB_BRAND_REACHOUT", "test-db")
os.environ.setdefault("NOTION_DB_BRAND_LOGS", "test-logs")
