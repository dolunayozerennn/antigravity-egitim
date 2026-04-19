from __future__ import annotations

"""
Prompt Generator V3 — "Pets Got Talent" Tam Otonom Pipeline.

Creative Engine'den seed alır → GPT-4.1 ile senaryo yazar →
Sora/Seedance-optimize basit prompt'a dönüştürür.

Dinamik klip sayısı ve süre: GPT hikayenin yapısına göre karar verir.
Ses her zaman açık, konuşma/diyalog asla yok.
"""
import json
import asyncio
import logging
import threading
from openai import OpenAI
from config import settings
from core.creative_engine import (
    generate_creative_seed,
    SCENARIO_WRITER_SYSTEM,
    PROMPT_SIMPLIFIER_SYSTEM,
    YOUTUBE_METADATA_SYSTEM,
)

log = logging.getLogger("PromptGenerator")

# ── OpenAI Client Singleton (TCP bağlantı yeniden kullanımı) ──
_openai_client: OpenAI | None = None
_openai_lock = threading.Lock()


def _get_openai_client() -> OpenAI:
    """OpenAI client singleton — her çağrıda yeni bağlantı açmaz."""
    global _openai_client
    if _openai_client is None:
        with _openai_lock:
            if _openai_client is None:  # Double-check locking
                _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


async def _call_gpt(system_prompt: str, user_message: str, temperature: float = 0.95) -> dict:
    """GPT-4.1'i çağır ve JSON yanıtı parse et."""
    try:
        client = _get_openai_client()
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        return json.loads(raw)
    except json.JSONDecodeError as e:
        log.error(f"❌ GPT yanıtı JSON parse edilemedi: {e}", exc_info=True)
        raise
    except Exception as e:
        log.error(f"❌ GPT çağrısı başarısız: {e}", exc_info=True)
        raise


async def generate_prompts(config: dict) -> dict:
    """
    Tam otonom video prompt pipeline'ı.

    Akış:
      1. Creative Engine → seed (hayvan + yetenek + sahne)
      2. GPT → senaryo (kaç klip, kaç saniye, ne oluyor)
      3. GPT → her sahne için Seedance-optimize basit prompt
      4. GPT → YouTube metadata (title, description, tags)
      5. Safety sanitizer → son güvenlik kontrolü

    Args:
        config: {
            "used_combos": ["animal|talent", ...],  # tekrar önleme
        }

    Returns:
        dict: {
            "scenes": [{"scene_number": 1, "prompt": "...", "duration": 10}, ...],
            "youtube_title": "...",
            "youtube_description": "...",
            "tags": [...],
            "scenario_summary": "...",
            "combo_key": "animal|talent",
            "total_duration": 25,
        }
    """
    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: Mock promptlar üretiliyor...")
        return _dry_run_output()

    used_combos = config.get("used_combos", [])

    # ── ADIM 1: Yaratıcı Seed Seç ──
    seed = generate_creative_seed(used_combos)
    log.info(f"🎲 Seed: {seed['animal']} × {seed['talent']}")

    # ── ADIM 2: GPT Senaryo Yaz ──
    log.info("🤖 GPT-4.1'e senaryo yazdırılıyor...")
    scenario = await _generate_scenario(seed)
    log.info(
        f"📋 Senaryo hazır: {scenario.get('clip_count', 1)} klip, "
        f"{scenario.get('total_duration', 10)}s"
    )

    # ── ADIM 3: Her Sahne İçin Seedance-Optimize Prompt ──
    scenes = scenario.get("scenes", [])
    simplified_scenes = []

    for scene in scenes:
        log.info(f"✂️ Sahne {scene['scene_number']}/{len(scenes)} simplify ediliyor...")
        simplified = await _simplify_prompt(scene, seed)
        simplified_scenes.append({
            "scene_number": scene["scene_number"],
            "prompt": simplified["prompt"],
            "duration": scene.get("duration", 10),
        })
        word_count = len(simplified["prompt"].split())
        log.info(f"   → {word_count} kelime: {simplified['prompt'][:80]}...")

    # ── ADIM 4: YouTube Metadata ──
    log.info("📺 YouTube metadata üretiliyor...")
    metadata = await _generate_metadata(scenario, seed)

    # ── ADIM 5: Safety Sanitizer ──
    from core.prompt_sanitizer import sanitize_prompt
    for scene in simplified_scenes:
        original = scene["prompt"]
        sanitized, changes = sanitize_prompt(original)
        if changes:
            scene["prompt"] = sanitized
            log.info(f"   🛡️ Sahne {scene['scene_number']} sanitize edildi: {len(changes)} değişiklik")

    # ── Sonuç Birleştir ──
    result = {
        "scenes": simplified_scenes,
        "youtube_title": metadata.get("youtube_title", "Pets Got Talent"),
        "youtube_description": metadata.get("youtube_description", ""),
        "tags": metadata.get("tags", ["Pets Got Talent", "Shorts"]),
        "scenario_summary": scenario.get("scenario_summary", ""),
        "combo_key": seed["combo_key"],
        "total_duration": scenario.get("total_duration", sum(s["duration"] for s in simplified_scenes)),
        "animal": seed["animal"],
        "talent": seed["talent"],
        "category": seed["category"],
    }

    log.info(f"✅ Pipeline tamamlandı: \"{result['youtube_title']}\"")
    log.info(f"   {len(simplified_scenes)} sahne, toplam {result['total_duration']}s")

    return result


async def _generate_scenario(seed: dict) -> dict:
    """Katman 2: GPT-4.1 ile absürt senaryo üret."""
    user_message = f"""Create a hilarious "Pets Got Talent" scenario:

ANIMAL: {seed['animal']}
TALENT: {seed['talent']} ({seed['category_label']})
SETTING: {seed['setting']}
TWIST DIRECTION: {seed['twist']}

Remember:
- Decide how many clips (1, 2, or 3) based on story structure
- Choose appropriate duration (between 8 to 15 seconds) for each clip
- NO spoken dialogue — this is for a GLOBAL audience
- Audio will include ambient sounds, music, and sound effects only
- Make it ABSURD but VISUALLY CLEAR"""

    result = await _call_gpt(SCENARIO_WRITER_SYSTEM, user_message, temperature=0.95)

    # Doğrulama
    if "scenes" not in result or not result["scenes"]:
        raise ValueError(f"GPT senaryo yanıtında 'scenes' eksik: {result}")

    # Clip süreleri Seedance limitleri içinde mi?
    for scene in result["scenes"]:
        dur = scene.get("duration", 10)
        if dur < 8:
            scene["duration"] = 8
        elif dur > 15:
            scene["duration"] = 15

    return result


async def _simplify_prompt(scene: dict, seed: dict) -> dict:
    """Katman 3: Sahne açıklamasını Seedance-optimize kısa prompt'a çevir."""
    user_message = f"""Simplify this scene into a Seedance 2.0 video prompt:

ANIMAL: {seed['animal']}
SCENE DESCRIPTION: {scene['description']}
DURATION: {scene['duration']} seconds

Output a SHORT prompt (15-30 words max). No dialogue. Include duration hint at the end."""

    result = await _call_gpt(PROMPT_SIMPLIFIER_SYSTEM, user_message, temperature=0.7)

    if "prompt" not in result:
        raise ValueError(f"Simplifier yanıtında 'prompt' eksik: {result}")

    return result


async def _generate_metadata(scenario: dict, seed: dict) -> dict:
    """YouTube title, description, tags üret."""
    user_message = f"""Create YouTube Shorts metadata for this video:

ANIMAL: {seed['animal']}
TALENT: {seed['talent']}
SCENARIO: {scenario.get('scenario_summary', '')}
CLIP COUNT: {scenario.get('clip_count', 1)}
TOTAL DURATION: {scenario.get('total_duration', 10)} seconds"""

    result = await _call_gpt(YOUTUBE_METADATA_SYSTEM, user_message, temperature=0.8)

    # Tags'e sabit olanları ekle
    tags = result.get("tags", [])
    mandatory_tags = ["Pets Got Talent", "Shorts", "ai", "animals", "funny"]
    for tag in mandatory_tags:
        if tag not in tags:
            tags.append(tag)
    result["tags"] = tags

    return result


def _dry_run_output() -> dict:
    """DRY-RUN modunda mock çıktı."""
    return {
        "scenes": [
            {
                "scene_number": 1,
                "prompt": "[DRY-RUN] A corgi in tiny sunglasses rides a skateboard through a park. "
                          "Jumps a ramp, lands perfectly. 10 seconds, smooth motion.",
                "duration": 10,
            }
        ],
        "youtube_title": "[DRY-RUN] 🐶 Corgi Skater Boy 🛹",
        "youtube_description": "This corgi just did what?! Watch this insane skateboard trick!",
        "tags": ["Pets Got Talent", "Shorts", "corgi", "skateboard", "ai"],
        "scenario_summary": "A corgi performs a skateboard trick",
        "combo_key": "corgi|skateboarding",
        "total_duration": 10,
        "animal": "corgi",
        "talent": "skateboarding",
        "category": "sports",
    }
