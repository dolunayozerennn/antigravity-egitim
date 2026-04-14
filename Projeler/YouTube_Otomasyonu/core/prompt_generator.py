"""
Prompt Üretici V2 — Viral Video Prompt Mühendisliği.

N8N referans sisteminden öğrenilen formül:
1. Sabit senaryo havuzu (kanıtlanmış viral konseptler)
2. Kamera tipi bazlı kategoriler (bodycam, ring cam, home cam, CCTV)
3. Aksiyon odaklı promptlar (sinematografi jargonu yerine)
4. İngilizce prompt, Türkçe video-içi konuşma
5. Random rotasyon (aynı senaryoyu tekrar etme)
"""
import json
import random
import asyncio
import logging
import threading
from openai import OpenAI
from config import settings

log = logging.getLogger("PromptGenerator")

# ────────────────────────────────────────
# 📋 VİRAL SENARYO HAVUZU
# ────────────────────────────────────────
# Her senaryo kanıtlanmış izlenme potansiyeline sahip.
# Kamera tipi + aksiyon + kaotik twist = viral formül.

SCENARIO_POOLS = {
    "bodycam": {
        "camera_directive": "bodycam footage, POV perspective, shaky handheld feel, real-time action",
        "scenarios": [
            "Firefighter rescuing a kitten stuck on a rooftop during a storm — rain pouring, wind howling, careful climb and gentle grab to safety",
            "Dog grabbing a huge piece of steak from a BBQ party and running away while everyone chases it through the backyard — knocking over lawn chairs, sliding on wet grass",
            "Cat snatching a giant fish from an outdoor fish market and sprinting through the crowd — the fish vendor trips over a bucket trying to catch it",
            "Dog sitting in the driver seat of a parked car, accidentally honks the horn — a crowd gathers, the dog looks at everyone and barks happily",
            "Cat sitting in a shopping cart rolling downhill in a parking lot — meowing loudly, people diving out of the way, cart crashes into a bush",
            "Monkey at a street market grabbing fruit from every stall while the vendor chases it — the monkey keeps eating while running",
            "Goose chasing a jogger through a park — the jogger tries to hide behind a tree but the goose circles around",
        ],
    },
    "ring_camera": {
        "camera_directive": "ring doorbell camera angle, wide-angle fixed position, front porch view, daylight",
        "scenarios": [
            "Man sleeping on his porch with a huge friendly dog licking his face — he wakes up startled and the dog wags its tail excitedly",
            "Giant friendly tortoise slowly walking onto the porch and eating flowers from the pot — the cat watches from the window in disbelief",
            "Raccoon family walking onto the porch in a perfect line — the baby raccoon trips and rolls, the mom raccoon picks it up",
            "Delivery man places a package, then a parrot on the porch starts talking to him — the delivery man has a full conversation with the parrot",
            "Bear wandering onto the porch, spots a cat in the window — the cat hisses, the bear gets startled and waddles away quickly",
            "Farm porch — an eagle swoops down near the porch, when suddenly a rooster charges at it and the eagle flies away confused",
            "Stray cat brings a gift (a leaf) to the doorstep every morning — time-lapse of leaf pile growing over days",
        ],
    },
    "home_camera": {
        "camera_directive": "home security camera footage, indoor wide angle, slightly elevated, static position",
        "scenarios": [
            "Golden retriever carefully carrying a sleeping kitten in its mouth from the living room to its dog bed — gently places it down and curls around it",
            "Person with their dog and cat — big mess of torn pillows on the floor — the cat is meowing and pointing at the dog, the dog looks guilty, and the owner is listening to the cat like a judge",
            "Cat discovering a robot vacuum for the first time — cautiously approaches, it moves, cat leaps three feet in the air, then rides on top of it around the house",
            "Dog learning to open the fridge — opens it, grabs a whole chicken, closes it perfectly, walks away casually",
            "Dinner table with lots of people — cat jumps from a shelf onto the table and lands perfectly in an empty plate — sits there like royalty while everyone stares",
            "Wedding ceremony — couple about to exchange rings — ring bearer dog runs in with the ring box, slides across the floor, and delivers it perfectly",
            "Cat knocking a glass off the table in slow motion — owner tries to dive and catch it — catches it but knocks over three other things in the process",
        ],
    },
}

# Kullanıcı spesifik konu istediğinde kullanılacak fallback
CUSTOM_TOPIC_SYSTEM = """You are an expert at creating VIRAL short-form video prompts.

VIRAL PROMPT FORMULA (MANDATORY):
1. Start with a specific camera type: bodycam, ring camera, home camera, CCTV, smartphone footage, dash cam
2. Describe a SPECIFIC event happening — not a vague concept
3. Include a surprising twist or unexpected moment
4. Keep the prompt BRIEF AND SIMPLE. Less is more. Focus ONLY on the primary action.
5. Characters should DO things — action verbs, not descriptions. Do not add complex background details.

⚠️ CONTENT SAFETY RULES (CRITICAL — FOLLOW OR VIDEO WILL BE REJECTED BY AI MODEL):
- NEVER use words: "steal", "theft", "crime", "arrest", "gun", "weapon", "violence", "blood", "attack", "kill", "destroy", "fight", "drugs"
- NEVER show children in dangerous situations (near crocodiles, heights, cars, electricity)
- NEVER show police/cop chases, car theft, or criminal activity
- REPLACE "stealing" with "grabbing" or "snatching playfully"
- REPLACE "chased by police" with "chased by the owner" or "chased by everyone"
- Keep all scenarios WHOLESOME, FAMILY-FRIENDLY, and PLAYFUL
- Focus on animal humor, wholesome surprises, and funny reactions
- If the user requests something potentially dangerous, make it safe: e.g., "dog steals meat" → "dog grabs steak from BBQ and runs away"

ANTI-PATTERNS (NEVER DO):
❌ Overly detailed environmental descriptions (e.g., "Golden hour lighting bouncing off the green leaves while the wind blows gently") — THIS KILLS THE MODEL
❌ "Cinematic establishing shot of a beautiful landscape" — boring
❌ "Dolly in on a character contemplating life" — no action

GOOD EXAMPLES (SHORT AND PUNCHY):
✅ "Bodycam: Golden retriever grabs a steak from BBQ and sprints away. People chasing. Dog slides under trampoline."
✅ "Ring camera: Raccoon walks on porch, starts eating from cat bowl. Cat watches from window."
✅ "Home camera: Dog slides across dance floor into wedding cake. Everyone gasps."

LANGUAGE RULE:
- The prompt itself MUST be in English

OUTPUT FORMAT (STRICT JSON):
{
  "scenes": [
    {
      "scene_number": 1,
      "prompt": "Short, simple, action-focused viral video prompt (15-40 words, English)",
      "duration": 10
    }
  ],
  "youtube_title": "Short, exciting title (max 60 chars, English)",
  "youtube_description": "1-3 sentences summarizing the event (English)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}"""

# Senaryo havuzundan üretirken kullanılan system prompt
POOL_SYSTEM = """You are an expert at expanding short video scenarios into effective AI video generation prompts.

YOUR JOB:
Take the given scenario and camera type, and write a SHORT, PUNCHY, and DIRECT video generation prompt. 
Extensive testing shows that short and simple prompts generate much better video results than overly detailed paragraphs.

RULES:
1. Keep the original scenario's story beats — don't change the plot.
2. Focus ONLY on the primary action and the subjects. DO NOT add complex background details or excessive adjectives.
3. Keep the prompt BRIEF (15-30 words max).
4. Do not use technical cinematographic jargon unless it's the requested camera angle.
5. End with: "smooth motion, {duration} seconds".
6. If humans speak, add: "Spoken dialogue must be in English. No other languages."

⚠️ CONTENT SAFETY (CRITICAL):
- NEVER use: "steal", "theft", "crime", "police", "cop", "arrest", "gun", "weapon", "violence", "blood", "attack", "kill", "destroy"
- Use SAFE alternatives: "grab" instead of "steal", "chase" instead of "pursue", "surprise" instead of "scare"
- Keep everything WHOLESOME and FAMILY-FRIENDLY
- No children in danger, no criminal activity, no weapons

CAMERA STYLE MUST MATCH:
- bodycam: shaky, POV, forward-facing, first-person perspective
- ring_camera: wide-angle, static, elevated, doorbell height
- home_camera: indoor security cam, slightly elevated, wide static frame

OUTPUT FORMAT (STRICT JSON):
{
  "scenes": [
    {
      "scene_number": 1,
      "prompt": "Short, simple, action-focused prompt (15-30 words max)",
      "duration": 10
    }
  ],
  "youtube_title": "Short, exciting title (max 60 chars, English)",
  "youtube_description": "1-3 sentences for YouTube (English)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}"""


# ── Kullanılan senaryo geçmişi (tekrar önleme) ──
_used_scenarios: list[str] = []
_MAX_HISTORY = 10
_scenario_lock = threading.Lock()  # Thread safety — concurrent_updates(True) koruması


def _pick_random_scenario() -> tuple[str, str, str]:
    """
    Senaryo havuzundan rastgele bir senaryo seçer.
    Tekrar etmemeye çalışır. Thread-safe.

    Returns:
        (camera_type, camera_directive, scenario_text)
    """
    global _used_scenarios

    with _scenario_lock:
        # Tüm senaryoları düzleştir
        all_options = []
        for cam_type, data in SCENARIO_POOLS.items():
            for scenario in data["scenarios"]:
                if scenario not in _used_scenarios:
                    all_options.append((cam_type, data["camera_directive"], scenario))

        # Tümü kullanıldıysa geçmişi sıfırla
        if not all_options:
            _used_scenarios.clear()
            for cam_type, data in SCENARIO_POOLS.items():
                for scenario in data["scenarios"]:
                    all_options.append((cam_type, data["camera_directive"], scenario))

        choice = random.choice(all_options)
        _used_scenarios.append(choice[2])

        # Geçmiş çok büyürse kırp
        if len(_used_scenarios) > _MAX_HISTORY:
            _used_scenarios = _used_scenarios[-_MAX_HISTORY:]

    return choice


async def generate_prompts(config: dict) -> dict:
    """
    Video üretim promptları üretir.

    İki mod:
    1. Pool modu: Kullanıcı genel bir konu istedi veya otonom mod →
       senaryo havuzundan seçim + GPT ile zenginleştirme
    2. Custom modu: Kullanıcı spesifik bir video anlattı →
       GPT'ye direkt viral prompt yazdır

    Args:
        config: conversation_manager'dan gelen config
            - topic: Video konusu
            - model: "seedance-2" veya "veo3.1"
            - clip_count: Kaç sahne
            - orientation: "portrait" veya "landscape"
            - audio: Ses isteniyor mu

    Returns:
        dict: scenes, youtube_title, youtube_description, tags
    """
    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: Mock promptlar üretiliyor...")
        scenes = []
        for i in range(config.get("clip_count", 1)):
            scenes.append({
                "scene_number": i + 1,
                "prompt": f"[DRY-RUN] Scene {i+1}: {config.get('topic', 'Test topic')}. "
                          f"Bodycam footage, action-packed, 10 seconds.",
                "duration": 10
            })
        return {
            "scenes": scenes,
            "youtube_title": f"[DRY-RUN] {config.get('topic', 'Test')}",
            "youtube_description": f"Test video about {config.get('topic', 'test')}",
            "tags": ["ai", "shorts", "test", "generated", "viral"]
        }

    topic = config.get("topic", "")
    use_pool = config.get("use_pool", False)

    # Otonom mod veya genel konu → havuzdan seç
    if use_pool or not topic or _is_generic_topic(topic):
        return await _generate_from_pool(config)
    else:
        return await _generate_custom(config)


def _is_generic_topic(topic: str) -> bool:
    """Konu genel mi yoksa spesifik mi kontrol eder."""
    generic_keywords = [
        "video yap", "bir şey üret", "random", "rastgele",
        "ne olursa", "surprise", "fark etmez", "sen seç",
        "otonom", "otomatik", "auto"
    ]
    topic_lower = topic.lower()
    return any(kw in topic_lower for kw in generic_keywords)


async def _generate_from_pool(config: dict) -> dict:
    """Senaryo havuzundan seçip GPT ile zenginleştirir."""
    cam_type, cam_directive, scenario = _pick_random_scenario()
    duration = config.get("duration", settings.DEFAULT_DURATION)

    log.info(f"🎲 Havuzdan senaryo seçildi: [{cam_type}] {scenario[:60]}...")

    user_message = f"""Expand this scenario into a detailed video generation prompt:

CAMERA TYPE: {cam_type} — {cam_directive}
SCENARIO: {scenario}
DURATION: {duration} seconds
AUDIO: {'Yes — include specific sound effects and ambient audio' if config.get('audio', True) else 'No audio'}

Make it vivid, action-packed, and include specific physical details."""

    return await _call_gpt(POOL_SYSTEM, user_message, config)


async def _generate_custom(config: dict) -> dict:
    """Kullanıcının spesifik konusundan viral prompt üretir."""
    topic = config.get("topic", "Creative video")
    duration = config.get("duration", settings.DEFAULT_DURATION)
    clip_count = config.get("clip_count", 1)
    aspect = "9:16 (vertical)" if config.get("orientation", "portrait") == "portrait" else "16:9 (horizontal)"

    log.info(f"🎬 Custom konu: {topic[:60]}...")

    user_message = f"""Create a VIRAL short-form video prompt for this concept:

TOPIC: {topic}
NUMBER OF SCENES: {clip_count}
ASPECT RATIO: {aspect}
DURATION PER SCENE: {duration} seconds
AUDIO: {'Yes — include specific sound effects' if config.get('audio', True) else 'No audio'}

Remember: Make it ACTION-FOCUSED, not cinematic jargon. Think "what happens next?" engagement.
Pick the most fitting camera type (bodycam, ring camera, home camera, CCTV, smartphone footage, etc.)."""

    return await _call_gpt(CUSTOM_TOPIC_SYSTEM, user_message, config)


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


async def _call_gpt(system_prompt: str, user_message: str, config: dict) -> dict:
    """GPT-4.1'i çağır ve yanıtı parse et."""
    log.info("🤖 GPT-4.1'e prompt üretim isteği gönderiliyor...")

    try:
        client = _get_openai_client()
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.95,
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
            log.info(f"   → {scene['prompt'][:80]}...")

        # Son güvenlik katmanı: üretilen promptları sanitize et
        from core.prompt_sanitizer import sanitize_prompt
        for scene in result.get("scenes", []):
            original = scene.get("prompt", "")
            sanitized, changes = sanitize_prompt(original)
            if changes:
                scene["prompt"] = sanitized
                log.info(f"   🛡️ Sahne {scene.get('scene_number', '?')} sanitize edildi: {len(changes)} değişiklik")

        return result

    except json.JSONDecodeError as e:
        log.error(f"❌ GPT yanıtı JSON parse edilemedi: {e}", exc_info=True)
        raise
    except Exception as e:
        log.error(f"❌ Prompt üretimi başarısız: {e}", exc_info=True)
        raise
