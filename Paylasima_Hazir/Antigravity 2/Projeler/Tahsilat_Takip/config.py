import os
import sys

# Yolları belirle
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, "_knowledge", "credentials", "master.env")

def load_env():
    """Reads master.env manually and loads variables into os.environ"""
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Uyarı: {CREDENTIALS_FILE} bulunamadı.")
        return

    with open(CREDENTIALS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

load_env()

NOTION_API_TOKEN = os.getenv("NOTION_SOCIAL_TOKEN") or os.getenv("NOTION_API_TOKEN")

# Notion Database ID'leri — Yeni Workspace (Mart 2026+)
YOUTUBE_DB_ID = "5bb95514-0a32-821f-98cc-81605e4a971f"
REELS_DB_ID = "27b95514-0a32-8385-89eb-813222d532a2"
