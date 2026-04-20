from __future__ import annotations

"""
Creative Engine — "Pets Got Talent" Yaratıcı Senaryo Motoru.

3 Katmanlı Sistem:
  Katman 1: Hayvan + Yetenek + Sahne seed havuzu (1400+ kombinasyon)
  Katman 2: GPT-4o ile absürt ama çekilebilir senaryo üretimi
  Katman 3: Sora/Seedance-optimize basit prompt'a dönüştürme

Her gün benzersiz, yaratıcı, eğlenceli hayvan videoları üretir.
"""
import random
import logging

log = logging.getLogger("CreativeEngine")

# ────────────────────────────────────────
# 🐾 KATMAN 1: SEED HAVUZLARI
# ────────────────────────────────────────

TALENT_CATEGORIES = {
    "music": {
        "label": "Musical Talents",
        "talents": [
            "playing piano", "drumming on pots and pans", "singing opera",
            "playing guitar", "conducting an orchestra", "beatboxing",
            "playing violin", "DJ mixing on turntables", "playing harmonica",
            "playing drums", "playing xylophone with chopsticks",
        ],
    },
    "sports": {
        "label": "Athletic Feats",
        "talents": [
            "skateboarding", "surfing", "doing gymnastics on a balance beam",
            "bowling a perfect strike", "slam dunking a basketball",
            "figure skating", "weightlifting tiny dumbbells",
            "doing a high jump over a stick", "playing table tennis",
            "doing yoga poses", "running hurdles over shoes",
            "synchronized swimming in a kiddie pool",
        ],
    },
    "cooking": {
        "label": "Culinary Arts",
        "talents": [
            "flipping pancakes", "making sushi rolls", "decorating a cake",
            "chopping vegetables like a chef", "tossing pizza dough",
            "barbecuing on a tiny grill", "making latte art",
            "whisking eggs at lightning speed", "frosting cupcakes",
            "making a fruit salad with precision",
        ],
    },
    "art": {
        "label": "Creative Arts",
        "talents": [
            "painting on canvas with paws", "sculpting clay",
            "doing magic tricks", "juggling balls",
            "breakdancing", "doing calligraphy with a brush",
            "making balloon animals", "doing puppetry",
            "pottery on a spinning wheel", "origami folding",
        ],
    },
    "intellectual": {
        "label": "Brain Power",
        "talents": [
            "solving a Rubik's cube", "playing chess",
            "doing math on a chalkboard", "reading a newspaper",
            "typing on a laptop keyboard", "giving a presentation",
            "assembling a puzzle", "playing Jenga carefully",
            "writing on a whiteboard", "sorting colored blocks",
        ],
    },
    "extreme": {
        "label": "Extreme & Absurd",
        "talents": [
            "tightrope walking on a clothesline",
            "balancing on a rolling ball",
            "escaping from a cardboard box like Houdini",
            "parkour across living room furniture",
            "bungee jumping off a couch cushion",
            "limbo dancing under a broomstick",
            "rock climbing a bookshelf",
            "trampoline backflips on a bed",
            "unicycle riding",
        ],
    },
    "daily_life": {
        "label": "Everyday Tasks Gone Wrong",
        "talents": [
            "vacuuming the floor with a tiny vacuum",
            "ironing clothes on a mini ironing board",
            "gardening and planting flowers",
            "washing dishes in a sink",
            "driving a toy car through traffic cones",
            "delivering mail from a tiny mailbox",
            "fishing with a tiny fishing rod",
            "building a tower with wooden blocks",
        ],
    },
    "performance": {
        "label": "Stage Performances",
        "talents": [
            "doing stand-up comedy at a microphone",
            "performing ballet in a tutu",
            "doing a fashion runway walk",
            "sword fighting with breadsticks",
            "doing a ventriloquist act with a puppet",
            "hula hooping", "tap dancing on a wooden floor",
            "mime performance behind invisible glass",
            "acrobatic duo act with another animal",
        ],
    },
}

ANIMALS = [
    "golden retriever", "tabby cat", "raccoon", "parrot", "hamster",
    "duck", "baby goat", "red panda", "otter", "penguin",
    "corgi", "hedgehog", "capybara", "ferret", "bunny",
    "miniature pig", "owl", "small monkey", "tortoise",
    "chihuahua", "husky", "persian cat",
    "chameleon", "flamingo", "seal", "beaver",
    "french bulldog", "dachshund", "cockatoo", "guinea pig",
    "shiba inu", "maine coon cat", "beagle", "pomeranian",
]

STAGE_SETTINGS = [
    "on a brightly lit talent show stage with a cheering crowd",
    "in a living room while the owner watches in shock",
    "at a park with other animals sitting in the audience",
    "in a kitchen with dramatic overhead lighting",
    "on a rooftop terrace during golden hour",
    "in a pet store, other animals staring through glass walls",
    "at a backyard party with fairy lights",
    "in a fancy restaurant dining room",
    "on a street corner busking for treats",
    "in a gymnasium with bleachers full of stuffed animals",
    "in a recording studio with professional equipment",
    "at a circus tent center ring",
    "in a cozy library with bookshelves",
    "at a beach boardwalk with ocean in the background",
    "in a garage workshop",
    "in a classroom with a chalkboard behind",
]

# Punchline / twist şablonları — GPT bunları ilham olarak kullanacak
TWIST_TEMPLATES = [
    "everything goes perfectly... until one hilarious mishap at the end",
    "the animal nails it on the first try and looks smugly at the camera",
    "another animal in the background is completely unimpressed",
    "the animal gets distracted mid-performance by something silly",
    "the audience reaction is the funniest part",
    "the animal finishes, takes a dramatic bow, and walks away like a boss",
    "the animal fails spectacularly but somehow still wins the crowd over",
    "a second animal tries to copy and fails hilariously",
    "the animal accidentally does something even more impressive",
    "the performance ends with an unexpected plot twist",
]


def generate_creative_seed(used_combos: list[str] | None = None) -> dict:
    """
    Benzersiz bir hayvan + yetenek + sahne kombinasyonu üretir.

    Args:
        used_combos: Daha önce kullanılmış "animal|talent" string'leri

    Returns:
        dict: {animal, talent, category, setting, twist, combo_key}
    """
    if used_combos is None:
        used_combos = []

    # Tüm olası kombinasyonları oluştur
    all_combos = []
    for cat_key, cat_data in TALENT_CATEGORIES.items():
        for talent in cat_data["talents"]:
            for animal in ANIMALS:
                combo_key = f"{animal}|{talent}"
                if combo_key not in used_combos:
                    all_combos.append({
                        "animal": animal,
                        "talent": talent,
                        "category": cat_key,
                        "category_label": cat_data["label"],
                        "combo_key": combo_key,
                    })

    # Tüm kombinasyonlar tükendiyse (pratikte imkansız) geçmişi sıfırla
    if not all_combos:
        log.warning("⚠️ Tüm kombinasyonlar kullanılmış — geçmiş sıfırlanıyor")
        all_combos = []
        for cat_key, cat_data in TALENT_CATEGORIES.items():
            for talent in cat_data["talents"]:
                for animal in ANIMALS:
                    all_combos.append({
                        "animal": animal,
                        "talent": talent,
                        "category": cat_key,
                        "category_label": cat_data["label"],
                        "combo_key": f"{animal}|{talent}",
                    })

    chosen = random.choice(all_combos)
    chosen["setting"] = random.choice(STAGE_SETTINGS)
    chosen["twist"] = random.choice(TWIST_TEMPLATES)

    log.info(
        f"🎲 Seed seçildi: {chosen['animal']} × {chosen['talent']} "
        f"[{chosen['category_label']}] @ {chosen['setting'][:40]}..."
    )

    return chosen


# ────────────────────────────────────────
# 🤖 KATMAN 2: GPT SENARYO ÜRETİCİ — System Prompt
# ────────────────────────────────────────

SCENARIO_WRITER_SYSTEM = """You are the head writer for "Pets Got Talent" — a viral YouTube Shorts channel featuring absurd animal talent shows.

YOUR JOB: Given an animal, a talent, a setting, and a twist direction, create a SHORT but hilarious scenario.

## CREATIVE RULES:
1. The scenario must be VISUALLY ABSURD but something an AI video model can actually generate.
2. Include a clear BEGINNING → ACTION → PUNCHLINE structure.
3. Think like a viral TikTok creator: what makes someone stop scrolling and watch twice?
4. Keep it WHOLESOME — no violence, no danger, no distress.
5. The ANIMAL is always the STAR PERFORMER.
6. NO spoken dialogue, NO text overlays, NO narration. The humor is 100% VISUAL.
7. Sound effects and ambient sounds are fine (cheering, music, crashes, animal sounds).

## WHAT MAKES A GREAT SCENARIO:
✅ Clear physical action that's easy to visualize
✅ An unexpected twist or punchline moment
✅ Absurd but somehow believable — "I can totally see a cat doing this"
✅ Universal humor — funny regardless of language or culture

## ANTI-PATTERNS (NEVER DO):
❌ Vague descriptions ("a beautiful moment unfolds")
❌ Complex multi-character plots (keep it focused on ONE animal)
❌ Anything requiring reading text on screen
❌ Boring "animal sits there looking cute" — NEEDS ACTION
❌ Dangerous situations (heights, fire, water danger, cars)

## CLIP STRUCTURE DECISION:
You must decide how many video clips this scenario needs and how long each should be.

GUIDELINES:
- **1 clip (8-15 seconds):** Simple, single-action scenarios. Most scenarios should be ONE clip.
  Examples: "Cat flips pancake, it lands on its head" = 1 clip, 10 seconds
- **2 clips (8-12 seconds each):** Only if there's a clear SETUP → PAYOFF that needs a scene change.
  Examples: "Dog practices piano alone → performs on stage for audience" = 2 clips
- **3 clips (8-10 seconds each):** Only for stories with clear beginning/middle/end AND each part needs a DIFFERENT visual.
  Examples: "Raccoon sees cooking show → tries to cook → kitchen is a mess but food is perfect" = 3 clips

IMPORTANT: Do NOT create multiple clips just to pad the video. If the story works in one continuous shot, USE ONE CLIP.

## OUTPUT FORMAT (STRICT JSON):
{
  "scenario_summary": "One sentence describing the whole scenario",
  "scenes": [
    {
      "scene_number": 1,
      "description": "What happens in this scene (2-3 sentences, detailed enough for the viewer to picture it)",
      "duration": 10
    }
  ],
  "total_duration": 10,
  "clip_count": 1,
  "why_this_clip_count": "Brief explanation of why you chose this number of clips"
}"""


# ────────────────────────────────────────
# ✂️ KATMAN 3: PROMPT SİMPLİFİYER — System Prompt
# ────────────────────────────────────────

PROMPT_SIMPLIFIER_SYSTEM = """You are a Seedance 2.0 video prompt specialist. Your ONE job: convert a detailed scene description into a SHORT, SIMPLE video generation prompt.

## CRITICAL RULES:
1. OUTPUT MUST BE 15-30 WORDS MAXIMUM. No exceptions.
2. Focus ONLY on the primary subject and action. Drop all background detail.
3. Use SIMPLE, DIRECT language. No poetic descriptions.
4. Start with the subject: "A [animal] [action]..."
5. Include ONE key visual detail (setting, prop, or reaction).
6. End with a strict realism style hint (e.g., 'photorealistic, raw camera footage', 'shot on smartphone'). NEVER mention the video duration in the prompt.
7. NEVER include dialogue or spoken words. Audio should only be ambient sounds, music, or sound effects.
8. NEVER use these words: steal, theft, crime, arrest, gun, weapon, violence, blood, attack, kill, fight, drugs, police, cop
9. NEVER use words like '3d render, animation, pixar, cartoon, illustration'. The output MUST look like REAL, amateur or professional camera footage.

## GOOD EXAMPLES:
✅ "A raccoon in a tiny chef hat flips a pancake in a kitchen. The pancake lands on its head. Photorealistic, raw smartphone footage, natural lighting."
✅ "A corgi rides a skateboard down a sidewalk, jumps a ramp, lands perfectly, tail wagging. Realistic camera footage, high quality."
✅ "A hamster in a top hat pulls a carrot from a miniature hat on stage. Another hamster in the audience gasps. Photorealistic, documentary style."
✅ "A penguin does figure skating spins on a frozen puddle. Stumbles at the end, slides gracefully into a bush. Raw amateur footage, lively."

## BAD EXAMPLES:
❌ "In the warm golden light of a beautiful summer afternoon, a magnificent golden retriever..." — TOO LONG, TOO POETIC
❌ "The cat walks across the room." — TOO VAGUE, NO TALENT, NO TWIST
❌ "A dog says 'hello everyone, welcome to my show'" — NO DIALOGUE ALLOWED

## OUTPUT FORMAT (STRICT JSON):
{
  "prompt": "The simplified 15-30 word prompt",
  "word_count": 22
}"""


# ────────────────────────────────────────
# 📺 YOUTUBE METADATA — System Prompt
# ────────────────────────────────────────

YOUTUBE_METADATA_SYSTEM = """You create YouTube Shorts metadata for "Pets Got Talent" — a viral animal talent show channel.

Given the video scenario, create an engaging title, description, and tags.

RULES:
- Title: MAX 60 characters. Must be catchy, use emoji, and make people CLICK.
- Description: 2-3 fun sentences + channel branding. English only.
- Tags: 8-12 relevant tags for discoverability.
- Everything in ENGLISH (global audience).
- Include "Pets Got Talent" in tags.
- Include #Shorts in tags.

TITLE STYLE EXAMPLES:
✅ "🐶 This Dog Can Actually Play Piano?! 😱"
✅ "🐱 Cat's Magic Trick Goes Wrong 🎩✨"
✅ "🦝 Raccoon Chef Makes Better Food Than Me 🍳"

OUTPUT FORMAT (STRICT JSON):
{
  "youtube_title": "Catchy title with emoji (max 60 chars)",
  "youtube_description": "Fun 2-3 sentence description",
  "tags": ["tag1", "tag2", "tag3", "Pets Got Talent", "Shorts"]
}"""
