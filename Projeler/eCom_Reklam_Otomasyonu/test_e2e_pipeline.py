"""
E2E test harness — Telegram'ı bypass edip pipeline'ı doğrudan çalıştırır.

Kullanım:
    python test_e2e_pipeline.py <kategori> "<url>"

Örnek:
    python test_e2e_pipeline.py skincare "https://www.trendyol.com/the-ordinary/..."

Çıktı: scenario özeti + video_url + notion_page_url + maliyet + süre.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import traceback

import config  # fail-fast env validation
from logger import get_logger

from services.openai_service import OpenAIService
from services.perplexity_service import PerplexityService
from services.imgbb_service import ImgBBService
from services.kie_api import KieAIService
from services.elevenlabs_service import ElevenLabsService
from services.replicate_service import ReplicateService
from services.notion_service import NotionService
from services.firecrawl_service import FirecrawlService

from core.scenario_engine import ScenarioEngine
from core.production_pipeline import ProductionPipeline
from core.url_data_extractor import URLDataExtractor

settings = config.settings
log = get_logger("test_e2e")


def _build_services():
    openai_svc = OpenAIService(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
    perplexity_svc = PerplexityService(api_key=settings.PERPLEXITY_API_KEY, base_url=settings.PERPLEXITY_BASE_URL)
    imgbb_svc = ImgBBService(api_key=settings.IMGBB_API_KEY)
    kie_svc = KieAIService(api_key=settings.KIE_API_KEY, base_url=settings.KIE_BASE_URL)
    elevenlabs_svc = ElevenLabsService(api_key=settings.ELEVENLABS_API_KEY, model_id=settings.ELEVENLABS_MODEL)
    replicate_svc = ReplicateService(api_token=settings.REPLICATE_API_TOKEN)
    notion_svc = NotionService(token=settings.NOTION_TOKEN, database_id=settings.NOTION_DB_ID)
    firecrawl_svc = FirecrawlService(api_key=settings.FIRECRAWL_API_KEY)

    extractor = URLDataExtractor(openai_service=openai_svc, firecrawl_service=firecrawl_svc)
    engine = ScenarioEngine(openai_service=openai_svc, perplexity_service=perplexity_svc)
    pipeline = ProductionPipeline(
        kie_service=kie_svc,
        elevenlabs_service=elevenlabs_svc,
        replicate_service=replicate_svc,
        notion_service=notion_svc,
        imgbb_service=imgbb_svc,
        is_dry_run=False,
    )
    return extractor, engine, pipeline


async def _progress(step: str, msg: str):
    print(f"  ▸ [{step}] {msg}", flush=True)


async def run(category: str, url: str, preferences: dict | None = None):
    preferences = preferences or {"video_format": "9:16", "video_style": "ugc"}

    extractor, engine, pipeline = _build_services()

    t0 = time.time()
    print(f"\n{'='*70}\n  TEST: {category}\n  URL: {url}\n{'='*70}", flush=True)

    # 1) Extract
    print("\n[1/3] Extract — Firecrawl + OpenAI vision", flush=True)
    extracted = await extractor.extract(url)
    print(f"  brand={extracted.get('brand_name')!r}  product={extracted.get('product_name')!r}", flush=True)
    print(f"  concept={(extracted.get('ad_concept') or '')[:120]}", flush=True)
    print(f"  best_image_urls={len(extracted.get('best_image_urls') or [])}", flush=True)

    # 2) Research + scenario
    print("\n[2/3] Research + Scenario", flush=True)
    research = await asyncio.to_thread(engine.research, extracted)
    scenario = await asyncio.to_thread(engine.generate_scenario, extracted, research, preferences)

    print(f"  duration={scenario.get('duration')}s  scenes={len(scenario.get('scenes') or [])}", flush=True)
    print(f"  language={scenario.get('language')}  aspect={scenario.get('aspect_ratio')}", flush=True)
    print(f"  cost={scenario.get('cost')}", flush=True)
    print(f"  prompt[:200]={(scenario.get('prompt') or '')[:200]}", flush=True)
    print(f"  voiceover={scenario.get('voiceover_text')!r}", flush=True)

    # 3) Produce
    print("\n[3/3] Produce — Kie/Replicate/ElevenLabs", flush=True)
    result = await pipeline.produce(
        scenario=scenario,
        collected_data=extracted,
        progress_callback=_progress,
        user_name="e2e-tester",
        preferences=preferences,
    )

    elapsed = time.time() - t0
    print(f"\n{'-'*70}", flush=True)
    print(f"  status      : {result.get('status')}", flush=True)
    print(f"  video_url   : {result.get('video_url')}", flush=True)
    print(f"  raw_video   : {result.get('raw_video_url')}", flush=True)
    print(f"  audio_url   : {result.get('audio_url')}", flush=True)
    print(f"  notion      : {result.get('notion_page_url')}", flush=True)
    print(f"  error       : {result.get('error')}", flush=True)
    print(f"  cost        : {result.get('cost')}", flush=True)
    print(f"  elapsed     : {elapsed:.1f}s", flush=True)
    print(f"{'-'*70}\n", flush=True)

    return {
        "category": category,
        "url": url,
        "extracted": {k: extracted.get(k) for k in ("brand_name", "product_name", "ad_concept", "target_audience")},
        "scenario": {
            "duration": scenario.get("duration"),
            "scenes": len(scenario.get("scenes") or []),
            "prompt": scenario.get("prompt"),
            "voiceover_text": scenario.get("voiceover_text"),
            "cost": scenario.get("cost"),
        },
        "result": result,
        "elapsed_sec": round(elapsed, 1),
    }


async def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    category = sys.argv[1]
    url = sys.argv[2]
    try:
        out = await run(category, url)
        out_path = f"e2e_result_{category}.json"
        with open(out_path, "w") as f:
            json.dump(out, f, indent=2, ensure_ascii=False, default=str)
        print(f"📄 Sonuç kaydedildi: {out_path}", flush=True)
    except Exception:
        print("\n❌ E2E TEST BAŞARISIZ:", flush=True)
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
