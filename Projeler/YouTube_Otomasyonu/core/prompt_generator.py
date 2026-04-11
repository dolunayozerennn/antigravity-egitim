"""
Prompt Üretici V2 — GPT-4.1 ile model-spesifik video prompt üretimi.
Seedance 2.0 ve Veo 3.1 için ayrı optimizasyon kuralları uygular.
Çoklu sahne desteği: karakter tutarlılığı ve continuity phrase'ler.
"""
import json
import asyncio
import logging
from openai import OpenAI
from config import settings

log = logging.getLogger("PromptGenerator")

SEEDANCE_SYSTEM = """You are an expert video prompt engineer for Seedance 2.0 model (ByteDance).

SEEDANCE-SPECIFIC RULES:
1. Prompts should be 60-120 words. Detailed but not bloated.
2. Use strong camera directions: dolly in, orbit left, crane up, tracking shot, steadicam follow.
3. Include precise lighting: "golden hour rim light", "neon-lit fog", "harsh overhead fluorescent".
4. Describe ONE primary action per clip — don't overload.
5. Use strong verbs: "surges", "tumbles", "emerges", "strides" (not "moves" or "goes").
6. Always mention audio cues if audio is enabled: "footsteps echo", "wind howls", "metallic clank".
7. End with constraints: "smooth motion, no sudden cuts, cinematic 24fps feel, {duration} seconds".
8. Seedance resolution is 720p — optimize for medium detail, strong composition.

OUTPUT FORMAT (STRICT JSON):
{
  "scenes": [
    {
      "scene_number": 1,
      "prompt": "Detailed video generation prompt (60-120 words, English)",
      "duration": 10
    }
  ],
  "youtube_title": "Short, exciting title (max 60 chars, English)",
  "youtube_description": "1-3 sentences for YouTube description (English)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}

For multi-scene videos: maintain character consistency across scenes using "Same character as Scene 1" continuity phrases."""

VEO_SYSTEM = """You are an expert video prompt engineer for Veo 3.1 model (Google DeepMind).

VEO-SPECIFIC RULES:
1. Veo excels at cinematic, film-quality output. Write prompts like a cinematographer's brief.
2. Prompts should be 40-80 words. Veo responds better to concise, high-level direction.
3. Emphasize mood and atmosphere: "melancholic twilight", "vibrant carnival energy", "tense silence".
4. Veo handles human faces exceptionally well — feel free to include close-ups.
5. Audio is auto-synced in Veo — describe sounds naturally within the scene.
6. Focus on natural physics: "hair blows gently", "rain drops ripple in puddle".
7. Do NOT use specific camera model names — use descriptive motions instead.
8. Veo is 1080p native — take advantage of detail.

OUTPUT FORMAT (STRICT JSON):
{
  "scenes": [
    {
      "scene_number": 1,
      "prompt": "Cinematic video prompt (40-80 words, English)",
      "duration": 8
    }
  ],
  "youtube_title": "Short, exciting title (max 60 chars, English)",
  "youtube_description": "1-3 sentences for YouTube description (English)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}

For multi-scene: maintain character continuity."""


async def generate_prompts(config: dict) -> dict:
    """
    Conversation config'inden video üretim promptları üretir.

    Args:
        config: conversation_manager'dan gelen config
            - topic: Video konusu
            - model: "seedance-2" veya "veo3.1"
            - clip_count: Kaç sahne
            - orientation: "portrait" veya "landscape"
            - audio: Ses isteniyor mu
            - youtube_title: Varsa kullanıcının istediği başlık
            - youtube_description: Varsa kullanıcının istediği açıklama

    Returns:
        dict: {
            "scenes": [{"scene_number": 1, "prompt": "...", "duration": 10}],
            "youtube_title": "...",
            "youtube_description": "...",
            "tags": [...]
        }
    """
    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: Mock promptlar üretiliyor...")
        scenes = []
        for i in range(config.get("clip_count", 1)):
            scenes.append({
                "scene_number": i + 1,
                "prompt": f"[DRY-RUN] Scene {i+1}: {config.get('topic', 'Test topic')}. "
                          f"Cinematic lighting, dramatic composition, 10 seconds.",
                "duration": 10
            })
        return {
            "scenes": scenes,
            "youtube_title": f"[DRY-RUN] {config.get('topic', 'Test')}",
            "youtube_description": f"Test video about {config.get('topic', 'test')}",
            "tags": ["ai", "shorts", "test", "generated", "cinematic"]
        }

    model = config.get("model", settings.DEFAULT_MODEL)
    system_prompt = SEEDANCE_SYSTEM if model == "seedance-2" else VEO_SYSTEM

    aspect = "9:16 (vertical/portrait)" if config.get("orientation", "portrait") == "portrait" else "16:9 (horizontal/landscape)"

    user_message = f"""Generate video prompt(s) for this concept:

TOPIC: {config.get('topic', 'Creative video')}
NUMBER OF SCENES: {config.get('clip_count', 1)}
ASPECT RATIO: {aspect}
AUDIO: {'Yes — include audio cue descriptions' if config.get('audio', True) else 'No audio'}
TARGET DURATION PER SCENE: {config.get('duration', settings.DEFAULT_DURATION)} seconds

{f'PREFERRED TITLE: {config["youtube_title"]}' if config.get('youtube_title') else 'Generate a catchy English title.'}
{f'PREFERRED DESCRIPTION: {config["youtube_description"]}' if config.get('youtube_description') else 'Generate a brief English description.'}

Make each scene visually distinct but narratively connected if multiple scenes."""

    log.info(f"🤖 GPT-4.1'e prompt üretim isteği gönderiliyor... (model: {model}, scenes: {config.get('clip_count', 1)})")

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.9,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)

        # Zorunlu alan doğrulama
        if "scenes" not in result or not result["scenes"]:
            raise ValueError(f"GPT yanıtında 'scenes' alanı eksik veya boş: {raw}")

        for field_name in ["youtube_title", "youtube_description", "tags"]:
            if field_name not in result:
                raise ValueError(f"GPT yanıtında '{field_name}' alanı eksik: {raw}")

        log.info(f"✅ {len(result['scenes'])} sahne promptu üretildi: \"{result['youtube_title'][:50]}...\"")
        for scene in result["scenes"]:
            word_count = len(scene["prompt"].split())
            log.info(f"   Sahne {scene['scene_number']}: {word_count} kelime, {scene.get('duration', '?')}s")

        return result

    except json.JSONDecodeError as e:
        log.error(f"❌ GPT yanıtı JSON parse edilemedi: {e}", exc_info=True)
        raise
    except Exception as e:
        log.error(f"❌ Prompt üretimi başarısız: {e}", exc_info=True)
        raise
