"""Firecrawl + URLDataExtractor sağlık testi (eski WebScraperService kaldırıldı)."""

import asyncio
import os
import sys

sys.path.append(os.getcwd())

import config
from services.firecrawl_service import FirecrawlService
from services.openai_service import OpenAIService
from core.url_data_extractor import URLDataExtractor

settings = config.settings


async def test():
    fc = FirecrawlService(api_key=settings.FIRECRAWL_API_KEY)
    openai_svc = OpenAIService(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
    extractor = URLDataExtractor(openai_service=openai_svc, firecrawl_service=fc)

    url = "https://www.trendyol.com/the-ordinary/niacinamide-10-zinc-1-30-ml-p-67669559"
    print(f"Scraping: {url}...")

    extracted = await extractor.extract(url)
    print("\n--- EXTRACTED ---")
    print(f"brand     : {extracted.get('brand_name')}")
    print(f"product   : {extracted.get('product_name')}")
    print(f"concept   : {(extracted.get('ad_concept') or '')[:200]}")
    print(f"audience  : {extracted.get('target_audience')}")
    print(f"images    : {len(extracted.get('best_image_urls') or [])}")
    for u in (extracted.get("best_image_urls") or [])[:3]:
        print(f"  - {u}")


if __name__ == "__main__":
    asyncio.run(test())
