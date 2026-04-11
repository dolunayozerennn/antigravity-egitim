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
            "Firefighter rescuing someone in a massive flood — water rising, debris floating, desperate grab and pull to safety",
            "Dog stealing a huge piece of meat from a grocery store and being chased by a security guard through the aisles — knocking things over, sliding on the floor",
            "Cat stealing a giant fish from an outdoor fish market and being chased by a cop — an old man trips and falls trying to catch the cat",
            "Dog getting pulled over for driving a car — the dog looks at the officer, then floors it and drives off at high speed",
            "Cat getting pulled over for driving a car — the cat meows at the officer, then hits the gas and speeds away",
            "Kid driving a car getting pulled over — the kid says something rude then floors it and runs from the cop",
            "Police officer chasing a monkey through a busy street market — the monkey keeps grabbing food from stalls while running",
        ],
    },
    "ring_camera": {
        "camera_directive": "ring doorbell camera angle, wide-angle fixed position, front porch view, daylight",
        "scenarios": [
            "Man sleeping on his porch with a huge black bear sniffing him — he wakes up startled and the bear runs away scared",
            "Kid feeding a crocodile at the front door — the mom comes running at the last second and grabs the kid inside",
            "Baby being approached by a crocodile on the porch — a cat jumps in and hisses at the crocodile, scaring it off, then the mom grabs the baby",
            "Kid feeding a lion a steak on the porch — the lion calmly eats while the kid pets it",
            "Bear charging towards a baby on the porch — then a cat jumps in the way, hisses aggressively, and the bear backs off",
            "Farm porch — an eagle swoops down at a cat, when suddenly a goat charges in and scares off the eagle",
            "Monkey screaming and holding onto the door — there's a tornado in the background and the monkey tries to hold on but gets pulled away",
        ],
    },
    "home_camera": {
        "camera_directive": "home security camera footage, indoor wide angle, slightly elevated, static position",
        "scenarios": [
            "Baby in a onesie curiously climbing up to a high open window — a dog comes from behind, grabs the baby by the clothes and pulls it back to safety — mom comes rushing in",
            "Person with their dog and cat — big mess on the floor — the cat is meowing and pointing at the dog, the dog looks guilty, and the owner is listening to the cat like a judge",
            "Man on the toilet when suddenly a wild animal smashes through the bathroom window and runs around inside — total chaos",
            "Kid playing near an electrical outlet — dog comes over and pulls the kid away just in time — parents rush in afterward",
            "Dinner table with lots of people — cat jumps from a balcony onto the chandelier and swings from it — chandelier crashes onto the table",
            "Wedding ceremony — couple about to cut a massive cake — dog jumps up and bites the entire cake — everyone freaks out",
            "Cat knocking a glass off the table in slow motion — owner tries to dive and catch it — fails spectacularly and knocks over everything else",
        ],
    },
}

# Kullanıcı spesifik konu istediğinde kullanılacak fallback
CUSTOM_TOPIC_SYSTEM = """You are an expert at creating VIRAL short-form video prompts.

VIRAL PROMPT FORMULA (MANDATORY):
1. Start with a specific camera type: bodycam, ring camera, home camera, CCTV, smartphone footage, dash cam
2. Describe a SPECIFIC event happening — not a vague concept
3. Include a chaotic twist or unexpected moment
4. Make the viewer think "WHAT HAPPENS NEXT?"
5. Characters should DO things — action verbs, not descriptions

ANTI-PATTERNS (NEVER DO):
❌ "Cinematic establishing shot of a beautiful landscape" — boring
❌ "Dolly in on a character contemplating life" — no action
❌ "Golden hour rim light illuminates the scene" — technical jargon
❌ Generic "a cat does something cute" — too vague

GOOD EXAMPLES:
✅ "Bodycam footage: officer approaches a parked car. A golden retriever is in the driver's seat. The dog puts the car in drive and speeds off"
✅ "Ring camera: a bear charges at a baby on the porch. Out of nowhere, the family cat leaps in, hisses, and the bear backs off"
✅ "Home camera: wedding cake ceremony. Everyone is watching. The dog leaps onto the table and destroys the entire cake"

LANGUAGE RULE:
- The prompt itself MUST be in English
- If the video involves people speaking, add this directive at the end:
  "All spoken dialogue must be in Turkish. Use natural, everyday Istanbul Turkish with short, emotionally engaging lines."

OUTPUT FORMAT (STRICT JSON):
{
  "scenes": [
    {
      "scene_number": 1,
      "prompt": "Detailed viral video prompt (40-100 words, English, action-focused)",
      "duration": 10
    }
  ],
  "youtube_title": "Short, exciting title (max 60 chars, English)",
  "youtube_description": "1-3 sentences summarizing the event (English)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}"""

# Senaryo havuzundan üretirken kullanılan system prompt
POOL_SYSTEM = """You are an expert at expanding short video scenarios into detailed AI video generation prompts.

YOUR JOB:
Take the given scenario and camera type, and write a rich, detailed video generation prompt.

RULES:
1. Keep the original scenario's story beats — don't change the plot
2. ADD vivid physical details: character appearance, environment, textures, weather
3. ADD action choreography: timing, speed, reactions, expressions
4. ADD audio cues: footsteps, crashes, animal sounds, ambient noise
5. KEEP it 40-100 words — detailed but not bloated
6. End with: "smooth motion, natural physics, {duration} seconds"
7. If humans speak in the video, add: "All spoken dialogue must be in Turkish. Use natural, everyday Istanbul Turkish."

CAMERA STYLE MUST MATCH:
- bodycam: shaky, POV, forward-facing, first-person perspective
- ring_camera: wide-angle, static, elevated, doorbell height
- home_camera: indoor security cam, slightly elevated, wide static frame

OUTPUT FORMAT (STRICT JSON):
{
  "scenes": [
    {
      "scene_number": 1,
      "prompt": "Detailed AI video generation prompt",
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


def _pick_random_scenario() -> tuple[str, str, str]:
    """
    Senaryo havuzundan rastgele bir senaryo seçer.
    Tekrar etmemeye çalışır.

    Returns:
        (camera_type, camera_directive, scenario_text)
    """
    global _used_scenarios

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


async def _call_gpt(system_prompt: str, user_message: str, config: dict) -> dict:
    """GPT-4.1'i çağır ve yanıtı parse et."""
    log.info("🤖 GPT-4.1'e prompt üretim isteği gönderiliyor...")

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
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

        return result

    except json.JSONDecodeError as e:
        log.error(f"❌ GPT yanıtı JSON parse edilemedi: {e}", exc_info=True)
        raise
    except Exception as e:
        log.error(f"❌ Prompt üretimi başarısız: {e}", exc_info=True)
        raise
