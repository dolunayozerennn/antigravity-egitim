import os
import sys
from dotenv import load_dotenv

# Load env before imports
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "_knowledge", "credentials", "master.env"))
os.environ["COVER_TYPE"] = "reels"

from core.logger import get_logger
from core import drive_service
original_count = drive_service.count_existing_covers

def mock_count(drive_url):
    print(f"Mocking cover count for drive url: {drive_url}")
    return 0

drive_service.count_existing_covers = mock_count

import core.notion_service
original_get_ready = core.notion_service.get_ready_videos

def mock_get_ready(cover_type):
    videos = original_get_ready(cover_type)
    filtered = [v for v in videos if v["name"] == "Atoms"]
    return filtered

core.notion_service.get_ready_videos = mock_get_ready

from main import process_reels

if __name__ == "__main__":
    logger = get_logger("Otonom_Kapak_Atoms", level="INFO")
    logger.info("Running reels pipeline specifically for Atoms.")
    process_reels(logger)
