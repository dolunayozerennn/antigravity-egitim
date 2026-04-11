"""
Prompt Üretici — GPT-4.1 ile Seedance 2.0'a optimize edilmiş prompt üretir.
Seedance Skill Guide'daki 6 adımlı formülü (ÖZNE + AKSİYON + ORTAM + KAMERA + STİL + KISITLAMALAR) uygular.
"""
import json
from openai import OpenAI
from config import settings
from logger import get_logger

log = get_logger("PromptGenerator")

SYSTEM_PROMPT = """You are an expert AI video prompt engineer specializing in Seedance 2.0 model. Your task is to generate prompts for short-form vertical video content (YouTube Shorts / TikTok / Reels).

IMPORTANT RULES:
1. Every prompt MUST describe a bodycam POV (first-person perspective) video. The viewer should feel like they are WEARING the camera.
2. Follow this exact formula for every prompt:
   [SUBJECT] + [ACTION] + [ENVIRONMENT] + [CAMERA] + [LIGHTING/STYLE] + [CONSTRAINTS]

3. Prompt length: 60-100 words. Not too short, not too long.
4. Use STRONG, specific verbs (not "moves" but "surges", "strides", "tumbles").
5. ONE primary action per shot — don't overload with multiple simultaneous actions.
6. Always include lighting description — it has the HIGHEST impact on video quality.
7. Always end with constraints: duration, artifacts to avoid, motion stability.
8. Camera is ALWAYS bodycam/first-person POV — describe what the wearer SEES and DOES.
9. Include audio cues when relevant (metallic clinks, wind, alarms, breathing).

OUTPUT FORMAT (strict JSON):
{
  "title": "Short, exciting YouTube Shorts title (max 60 chars, English)",
  "description": "1-3 sentences summarizing the video for YouTube description (English)",
  "prompt": "The detailed Seedance 2.0 video generation prompt (English, 60-100 words)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}

NEVER output anything outside this JSON structure."""


def generate_prompt(topic: dict) -> dict:
    """
    Verilen konu için Seedance 2.0'a optimize edilmiş prompt üretir.
    
    Args:
        topic: pick_topic()'dan dönen konu objesi
        
    Returns:
        dict: {title, description, prompt, tags}
    """
    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: Mock prompt üretiliyor...")
        return {
            "title": f"[DRY-RUN] {topic['title_hint']}",
            "description": f"Test video about {topic['category']}",
            "prompt": f"Bodycam POV footage of {topic['description'][:100]}. "
                      f"Dramatic lighting, immersive first-person view, 10 seconds.",
            "tags": ["space", "bodycam", "shorts", "ai", "test"]
        }

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    user_message = f"""Generate a unique, creative bodycam POV video prompt for this topic:

TOPIC CATEGORY: {topic['category']}
TOPIC DESCRIPTION: {topic['description']}
STYLE HINTS: {', '.join(topic.get('style_hints', []))}
CHANNEL NICHE: {topic.get('channel_niche', 'Space & Sci-Fi Bodycam')}

Remember:
- Bodycam/first-person POV is MANDATORY
- Include specific audio cues (breathing, machinery, alarms, wind, etc.)
- Use strong action verbs
- Include precise lighting description
- Target duration: {settings.VIDEO_DURATION} seconds
- Aspect ratio: {settings.VIDEO_ASPECT_RATIO} (vertical/portrait)
- Make it feel IMMERSIVE — the viewer IS the person in the video"""

    log.info(f"🤖 GPT-4.1'e prompt üretim isteği gönderiliyor... (konu: {topic['category']})")

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.9,
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)

        # Zorunlu alanları doğrula
        required_fields = ["title", "description", "prompt", "tags"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"GPT yanıtında '{field}' alanı eksik: {raw}")

        log.info(f"✅ Prompt üretildi: \"{result['title'][:50]}...\"")
        log.info(f"   Prompt uzunluğu: {len(result['prompt'].split())} kelime")

        return result

    except json.JSONDecodeError as e:
        log.error(f"❌ GPT yanıtı JSON parse edilemedi: {e}", exc_info=True)
        raise
    except Exception as e:
        log.error(f"❌ Prompt üretimi başarısız: {e}", exc_info=True)
        raise
