import asyncio
import os
import sys

# Yollari ekle
sys.path.append(os.getcwd())

with open('../../_knowledge/credentials/master.env') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            os.environ['OPENAI_API_KEY'] = line.split('=', 1)[1].strip()

from services.web_scraper_service import WebScraperService
from services.openai_service import OpenAIService

async def test():
    scraper = WebScraperService()
    openai_svc = OpenAIService(api_key=os.environ['OPENAI_API_KEY'])
    
    url = "https://www.apple.com/shop/buy-iphone/iphone-15"
    print(f"Scraping: {url}...")
    
    # 1. Scrape
    data = scraper.scrape_product_data(url, max_images=5)
    
    print("\n--- TEXT EXTRACTED ---")
    print(data.get("page_text")[:500] + "...")
    
    images = data.get("images", [])
    print(f"\n--- IMAGES EXTRACTED ({len(images)}) ---")
    for img in images:
        print(img["url"])
        
    if not images:
        print("No images found.")
        return
        
    # 2. Select best
    print("\n--- AI SELECTION ---")
    best_image = openai_svc.select_best_product_image([img["url"] for img in images])
    print(f"Best Image: {best_image}")

asyncio.run(test())
