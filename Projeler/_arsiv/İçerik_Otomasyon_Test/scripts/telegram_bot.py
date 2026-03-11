#!/usr/bin/env python3
"""
İçerik Otomasyon Telegram Botu v4
Ürün reklam videosu üretim pipeline'ı:
  1. NanoBanana Pro → Başlangıç görseli üret
  2. Qwen Image Edit → Küçük düzenlemeler
  3. Sora 2 Pro Storyboard → Video üretimi
"""
import asyncio
import json
import logging
import re
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ── Ayarlar ──────────────────────────────────────────────
# ⚠️ ARŞİV: Bu proje artık aktif değil. Token'lar env variable'dan okunmalıdır.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
KIE_API_KEY = os.environ.get("KIE_API_KEY", "")
KIE_BASE = "https://api.kie.ai/api/v1"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
SEEDANCE_API_KEY = os.environ.get("SEEDANCE_API_KEY", "")
SEEDANCE_BASE_URL = "https://seedanceapi.org/v1"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_debug.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ── Konuşma Hafızası ─────────────────────────────────────
conversations: dict[int, dict] = {}

# ── State'ler ─────────────────────────────────────────────
# waiting_info      → Ürün bilgisi bekleniyor
# generating_image  → NanoBanana ile görsel üretiliyor
# reviewing_image   → Kullanıcı görseli inceliyor
# editing_image     → Qwen ile düzenleme yapılıyor
# collecting_scenes → Storyboard sahne bilgisi toplanıyor
# producing_video   → Sora 2 ile video üretiliyor


# ── Yardımcı: Prompt Üretimi (Şablon Bazlı) ─────────────

def generate_nanobananapro_prompt(product_info: dict) -> str:
    """Ürün bilgisinden İngilizce NanoBanana Pro prompt'u üretir.

    Referans görsel varsa: ürünü %100 koruyup sadece ortamı değiştirir.
    Referans görsel yoksa: sıfırdan ürün görseli üretir.
    """
    product = product_info.get("product", "product")
    brand = product_info.get("brand", "")
    style = product_info.get("style", "modern and professional")
    colors = product_info.get("colors", "")
    extra = product_info.get("extra", "")
    has_reference = bool(product_info.get("reference_image_url"))

    if has_reference:
        # ── Referans görsel VAR → Ürünü koru, sadece ortamı değiştir ──
        prompt_parts = [
            f"Place this exact ErDoor exterior door ({product}) in a luxurious exterior architectural setting",
            f"DO NOT change the {product} itself — keep every detail, shape, color, texture, and branding exactly as shown in the reference image",
            f"only change the background and environment around the {product}",
            f"{style} aesthetic environment, showing the exterior facade of a premium building or villa entrance",
        ]

        if brand:
            prompt_parts.append(f"the product belongs to {brand} brand")

        prompt_parts.extend([
            "natural cinematic sunlight illuminating the exterior",
            "beautiful landscaping or elegant architectural elements in the background",
            "shallow depth of field with soft bokeh",
            f"the {product} must remain the absolute focal point and be identical to the original",
            "4K resolution",
            "high detail",
            "exterior architectural photography",
            "NO text, NO watermark, NO logo, NO typography, completely clean and blank surface",
        ])
    else:
        # ── Referans görsel YOK → Sıfırdan ürün görseli üret ──
        prompt_parts = [
            f"Professional exterior architectural photography of an ErDoor {product}",
            "installed seamlessly on the entrance of a luxury modern villa",
        ]

        if brand:
            prompt_parts.append(f"for {brand} brand")

        prompt_parts.append(f"{style} aesthetic")

        if colors:
            prompt_parts.append(f"color palette: {colors}")

        prompt_parts.extend([
            "natural cinematic sunlight creating gentle dynamic shadows on the facade",
            "elegant exterior environment with subtle greenery and stone textures",
            "shallow depth of field",
            "4K resolution",
            "high detail",
            "premium exterior door commercial shot",
            "NO text, NO watermark, NO logo, NO typography, completely clean and blank surface",
        ])

    if extra:
        prompt_parts.append(extra)

    return ", ".join(prompt_parts) + "."


def generate_qwen_edit_prompt(edit_request: str) -> str:
    """Kullanıcının Türkçe düzenleme talebini İngilizce prompt'a çevirir.

    Basit anahtar kelime eşleştirmesi ile çeviri yapar.
    Karmaşık talepler için orijinal metni de prompt'a ekler.
    """
    # Yaygın Türkçe → İngilizce düzenleme terimleri
    tr_en_map = {
        "arka plan": "background",
        "arkaplan": "background",
        "renk": "color",
        "rengini": "color of the product to",
        "kırmızı": "red",
        "mavi": "blue",
        "yeşil": "green",
        "beyaz": "white",
        "siyah": "black",
        "sarı": "yellow",
        "turuncu": "orange",
        "mor": "purple",
        "pembe": "pink",
        "gri": "gray",
        "değiştir": "change",
        "ekle": "add",
        "kaldır": "remove",
        "sil": "remove",
        "parlak": "bright",
        "mat": "matte",
        "metin": "text",
        "yazı": "text",
        "logo": "logo",
        "gölge": "shadow",
        "ışık": "lighting",
    }

    # Basit çeviri denemesi
    translated = edit_request.lower()
    for tr_word, en_word in tr_en_map.items():
        translated = translated.replace(tr_word, en_word)

    return f"Edit the product image: {translated}. Keep the main subject intact, match lighting and shadows."


async def _call_openai_json(system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    """OpenAI API çağrısı yaparak JSON çıktısı alır."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 1500,
        "response_format": {"type": "json_object"}
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=60.0)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception as e:
        logger.error(f"OpenAI API hatası: {e}", exc_info=True)
        return None

async def generate_draft_storyboard_with_openai(script: str, product_name: str, n_frames: int) -> list[dict[str, Any]]:
    """
    OpenAI (Pass 1) kullanarak detaylı senaryoyu 
    ilk aşama storyboard scene-duration yapısına böler.
    """
    system_prompt = f"""
    You are an expert commercial video director using the Sora 2 Pro AI model.
    The user wants a {n_frames}-second commercial video for a premium product: "ErDoor exterior {product_name}".
    They provide a Turkish storyboard/script detailing the product features (e.g., durability, luxury, security, weather resistance).

    Your job is to convert their text into a JSON array of "shots" showcasing a high-end ErDoor exterior door (steel or wooden composite) in natural exterior environments like luxury villa entrances or apartment facades.
    
    Rules:
    1. STRICT JSON OUTPUT ONLY: [{{"Scene": "description in English", "duration": float}}]
    2. Sum of 'duration' values MUST exactly equal {n_frames}.
    3. Pacing: Favor dynamic cuts between 3 to 5 seconds. Use mostly 3s or 4s scenes. No scene can be shorter than 3.0s. The FINAL scene MUST be at least 4.0s long.
    4. Exterior Context: Every scene must be set in a premium exterior environment (e.g., natural sunlight, garden pathways, elegant stone facades). Do not place the door inside a standard bedroom or bathroom.
    5. Rigid Physics/Durability: If demonstrating strength, DO NOT prompt the door to bend, twist, or break. Show durability visually via secondary effects (e.g., heavy rain bouncing off the steel, sparks flying without leaving a mark).
    6. CRITICAL AUDIO/VOICEOVER: If the script contains dialogue or voiceover, DO NOT use conversational English. You MUST use strict tags like this: [VOICEOVER: "Türkçe metin"]. E.g., [VOICEOVER: "ErDoor ile güvendesiniz."] IMPORTANT: To prevent audio cutoff in the first scene, ALWAYS start with a moment of silence: [VOICEOVER: "(1 saniye boşluk)... Türkçe metin"]. Keep all voiceover sentences VERY SHORT, CLEAR, and WELL-FORMED (no incomplete words).
    7. DO NOT OPEN THE DOOR AND NO PHYSICAL DESTRUCTION (PHYSICS RED FLAG): To prevent severe physics glitches and geometry failures in AI video models, DO NOT prompt the door to open, get cut, drilled, or violently destroyed. The door MUST remain completely closed and statically intact at all times. Show interactions purely via environmental effects (rain, wind, light), camera moves, and hands touching the handle, but KEEP THE DOOR CLOSED and UNDAMAGED.
    8. VOICEOVER-VISUAL HARMONY: The visual action MUST logically match the meaning of the VoiceOver. For example, if the VoiceOver talks about "Harmony with nature" (Doğayla uyum), the visual MUST show the door in a beautiful natural, sunny, or green setting. If the VoiceOver talks about "Durability" (Dayanıklılık), the visual MUST show it resisting harsh weather, impact, or feeling imposing. Do NOT mismatch these themes.
    9. Ensure the exact phrase "ErDoor exterior door" is prominently used as the subject in every scene description. 
    10. Add "The core physical structure of the ErDoor remains consistent." to the end of every scene instead of forcing it to be perfectly identical.
    """
    
    logger.info(f"🧠 [Pass 1] OpenAI GPT-4o ile draft storyboard üretiliyor... (n_frames: {n_frames})")
    data = await _call_openai_json(system_prompt, f"User script: {script}")
    if not data:
        return []

    # Parse and normalize
    parsed_shots = []
    if "shots" in data and isinstance(data["shots"], list):
        parsed_shots = data["shots"]
    else:
        keys = list(data.keys())
        if keys and isinstance(data[keys[0]], list):
            parsed_shots = data[keys[0]]

    total_dur = sum(s.get("duration", 0) for s in parsed_shots)
    if abs(total_dur - n_frames) > 0.1 and total_dur > 0:
        scale = n_frames / total_dur
        for s in parsed_shots:
            s["duration"] = round(s["duration"] * scale, 2)
    
    return parsed_shots


async def optimize_storyboard_with_openai(draft_shots: list[dict[str, Any]], product_name: str, n_frames: int) -> list[dict[str, Any]]:
    """
    OpenAI (Pass 2) kullanarak draft JSON'u 
    Sora 2 fizikleri ve prompt kurallarına göre denetler ve optimize eder.
    """
    system_prompt = f"""
    You are the Lead Sora 2 Pro Reviewer. Your role is absolute quality control.
    You will receive a drafting JSON array of shots representing a {n_frames}-second premium commercial for "ErDoor exterior {product_name}".
    
    CRITIQUE & REWRITE RULES:
    1. EXTERIOR CONTEXT VIGILANCE:
       - ErDoor produces exterior doors (villa entrances, building facades). Ensure NO scene is optimized to look like a standard indoor bedroom/bathroom door.
       - Ensure natural exterior lighting, elegant facades, or outdoor environments are described.
    2. DURATION HARMONY: 
       - Minimum scene duration is 3.0s. The FINAL scene MUST be at least 4.0s.
       - 3s: Check if it's a single simple action.
       - 4-5s: Check if it's one action + simple camera move.
       - Does a static action take 8s? Red flag. Shorten the duration and create a new shot.
    3. RED FLAG ACTIONS (AVOID THESE):
       - Multi-step physics or impossible physics (bending rigid exterior doors).
       - Close-up hand-object contact (turning knobs).
       - AI PHYSICS RED FLAG (DOOR OPENING & DESTRUCTION): DO NOT allow any scene to show the door opening, being cut, drilled, or broken. Ensure the door remains CLOSED and INTACT at all times. Opening or destroying the door triggers severe physics glitches, dual-hinge openings, and geometry destruction. Remove any "opening" or "destructive" action and replace it with strong camera moves or environmental interaction (e.g., rain, wind) while the door stays firmly closed.
       - Fire or severe destruction on the main product unless it's a natural effect.
       - Showing the back of the door, dirty/cluttered environments, or unappealing angles. Keep contexts luxurious, clean, and majestic.
       - DO NOT include ANY on-screen text, typography, fonts, or overlays. The video must be completely text-free.
       Instead, use creative visualization (e.g., severe weather bouncing off to show strength).
    4. AUDIO & LANGUAGE:
       - 100% of the scene descriptions must be in English.
       - ANY dialogue or voiceover MUST use strictly this bracket format: [VOICEOVER: "Türkçe metin"]. 
       - Keep voiceover sentences VERY SHORT, CLEAR and WELL-FORMED (no incomplete/garbled words).
       - The FIRST scene MUST start with a pause to prevent cutoff: [VOICEOVER: "(1 saniye boşluk)... Türkçe metin"].
    5. VOICEOVER-VISUAL HARMONY: Check the [VOICEOVER: "text"]. The visuals MUST logically match the voiceover. "Doğayla uyum" means natural settings (sunlight, plants). "Dayanıklılık" means strength (resisting rain, wind). Rewrite any scene where the action contradicts the voiceover theme.
    6. EXACT REQUIREMENTS:
       - Every scene MUST contain the phrase "ErDoor exterior door".
       - Every scene MUST end with "The core physical structure of the ErDoor remains consistent."
       - Output STRICTLY JSON formatted as: [{{"Scene": "str", "duration": float}}]
       - The total duration must sum to exactly {n_frames}.
    """
    
    logger.info(f"🧠 [Pass 2] OpenAI GPT-4o ile storyboard optimize ediliyor...")
    data = await _call_openai_json(system_prompt, f"Draft JSON: {json.dumps(draft_shots, ensure_ascii=False)}")
    if not data:
        return draft_shots  # Fallback to draft
        
    # Parse and normalize
    parsed_shots = []
    if "shots" in data and isinstance(data["shots"], list):
        parsed_shots = data["shots"]
    else:
        keys = list(data.keys())
        if keys and isinstance(data[keys[0]], list):
            parsed_shots = data[keys[0]]

    # Ensure valid duration
    if not parsed_shots:
        return draft_shots

    total_dur = sum(s.get("duration", 0) for s in parsed_shots)
    if abs(total_dur - n_frames) > 0.1 and total_dur > 0:
        scale = n_frames / total_dur
        for s in parsed_shots:
            s["duration"] = round(s["duration"] * scale, 2)

    return parsed_shots


async def generate_seedance_prompt_with_openai(script: str, product_name: str, n_frames: int) -> str:
    """
    OpenAI kullanarak kullanıcının senaryosunu Seedance 2.0 için uygun olan
    dinamik sahneli, ses talepli ve yüksek kalitede, İngilizce bir 'cinematic text prompt' haline getirir.
    ErDoor marka dış cephe kapısı konseptini zorunlu tutar.
    
    YENİ: Start frame'e ve Seedance 12s/I2V kuralına uygun yazım.
    """
    system_prompt = f"""
    You are an expert commercial video director writing a prompt for the Seedance 2.0 text-to-video AI model.
    The user wants a {n_frames}-second premium commercial video for: "ErDoor exterior {product_name}".
    They provide a Turkish storyboard/script detailing the product features.

    Your job is to convert their text into the EXACT Master Template format below for Seedance.
    DO NOT output a single paragraph. Output exactly these sections filled with English descriptions.

    Master Template Structure to Output:

    Create a premium {n_frames}-second ErDoor door commercial video from the provided start-frame image.

    Use the provided image as the exact start frame.
    Preserve the same door design, color, material finish, handle shape, and frame proportions throughout the video.

    Scene: [FILL: Describe the premium exterior environment based on the script]
    Mood: [FILL: premium / calm / confident / elegant]
    Lighting: [FILL: soft warm / daylight / dramatic contrast]
    Main message: [FILL: Based on the user script]

    {n_frames}-second flow:
    0-3s: [FILL: establish the door with a smooth cinematic camera move]
    3-7s: [FILL: product interaction or motion in a realistic premium way]
    7-10s: [FILL: close-up detail on edges, texture, craftsmanship]
    10-12s: [FILL: clean hero shot with stable composition]

    Camera: [FILL: smooth commercial movement, readable framing]
    Consistency: keep exact door identity, no deformation, no extra elements, no flicker, no text artifacts. No dirty environments.
    Audio: stereo synchronized audio with premium ambience + realistic foley + Epic cinematic background music accompanied by a highly professional Turkish voiceover
    Style: realistic materials, high prompt adherence, clean composition, premium commercial ad
    
    Output ONLY the text using the exact headers and format above. No JSON, no code block (` ``` `) formatting, no extra explanations.
    """
    
    logger.info(f"🧠 [Pass 1] OpenAI GPT-4o ile Seedance promptu üretiliyor...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"User script: {script}"},
                    ],
                    "temperature": 0.7,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            prompt = data["choices"][0]["message"]["content"].strip()
            return prompt
    except Exception as e:
        logger.error(f"Seedance prompt generation error: {e}", exc_info=True)
        return f"A cinematic {n_frames}-second shot of an elegant ErDoor exterior steel door installed on a luxury villa entrance, natural sunlight, premium architectural photography, 4k."


def generate_sora_input(image_url: str, product_name: str = "product", n_frames: str = "15",
                        aspect_ratio: str = "landscape", custom_shots: list | None = None) -> dict:
    """Sora 2 Pro Storyboard API input formatını oluşturur."""
    nf = float(n_frames)
    durations = [nf / 2, nf / 2] if nf != 25 else [8.33, 8.33, 8.34]

    sora_input: dict = {
        "n_frames": n_frames,
        "aspect_ratio": aspect_ratio,
        "upload_method": "s3",
    }
    
    if custom_shots and len(custom_shots) > 0:
        sora_input["shots"] = custom_shots
    else:
        # Fallback scenes
        sora_input["shots"] = [
            {
                "Scene": f"Cinematic close-up of the exact {product_name} in a professional setting, slowly panning around to reveal details, soft studio lighting, shallow depth of field, commercial product photography. The {product_name} stays identical.",
                "duration": durations[0]
            },
            {
                "Scene": f"Wide shot showing the exact {product_name} in its elegant environment, dynamic camera movement, cinematic lighting, 4K resolution, highly detailed. The {product_name} stays identical.",
                "duration": durations[1]
            }
        ]
        
        if nf == 25:
            sora_input["shots"].append({
                "Scene": f"The exact {product_name} glowing in beautiful light, camera slowly zooming out, fade to professional and elegant aesthetic at the end.",
                "duration": durations[2]
            })

    if image_url:
        sora_input["image_urls"] = [image_url]

    return sora_input


# ── Yardımcı: Markdown Temizleme ────────────────────────

def sanitize_markdown(text: str) -> str:
    """Telegram Markdown parse hatalarını önlemek için düzelt."""
    count_bold = text.count("**")
    if count_bold % 2 != 0:
        idx = text.rfind("**")
        text = text[:idx] + text[idx + 2:]

    parts = text.split("`")
    cleaned_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            underscore_count = 0
            for match in re.finditer(r'(?<!\w)_|_(?!\w)', part):
                underscore_count += 1
            if underscore_count % 2 != 0:
                idx = part.rfind("_")
                part = part[:idx] + part[idx + 1:]
        cleaned_parts.append(part)
    text = "`".join(cleaned_parts)

    count_bt = text.count("`")
    if count_bt % 2 != 0:
        text = text.rstrip("`")
        if text.count("`") % 2 != 0:
            text += "`"

    return text


# ── Yardımcı Fonksiyonlar ────────────────────────────────

def get_conversation(chat_id: int) -> dict:
    """Konuşma hafızasını al veya oluştur."""
    if chat_id not in conversations:
        conversations[chat_id] = {
            "state": "waiting_info",
            "messages": [],              # Konuşma geçmişi
            "product_info": {},
            "image_url": None,           # Üretilen ürün görseli URL'si
            "image_task_id": None,
            "video_task_id": None,
            "edit_count": 0,
        }
    return conversations[chat_id]


async def safe_reply(message, text: str, **kwargs):
    """Markdown hatasına karşı güvenli mesaj gönderimi."""
    try:
        await message.reply_text(
            sanitize_markdown(text), parse_mode="Markdown", **kwargs
        )
    except Exception as e:
        logger.warning(f"Markdown parse hatası, düz metin deneniyor: {e}")
        plain = (
            text.replace("**", "").replace("__", "")
            .replace("_", "").replace("`", "")
        )
        try:
            await message.reply_text(plain, **kwargs)
        except Exception as e2:
            logger.error(f"Mesaj gönderilemedi: {e2}")
            await message.reply_text("Bir hata oluştu, lütfen tekrar deneyin.")


async def safe_edit(message, text: str, **kwargs):
    """Markdown hatasına karşı güvenli mesaj düzenleme."""
    try:
        await message.edit_text(
            sanitize_markdown(text), parse_mode="Markdown", **kwargs
        )
    except Exception:
        plain = (
            text.replace("**", "").replace("__", "")
            .replace("_", "").replace("`", "")
        )
        try:
            await message.edit_text(plain, **kwargs)
        except Exception as e2:
            logger.error(f"Mesaj düzenlenemedi: {e2}")


# ── Görsel Upload (Telegram → Herkese Açık URL) ─────────

async def upload_telegram_photo_to_public(bot, file_id: str) -> str | None:
    """Telegram'dan fotoğrafı indir ve herkese açık URL elde et.

    freeimage.host kullanılır — base64 ile upload,
    doğrudan HTTPS URL döner, cookie koruması yoktur.
    """
    try:
        file = await bot.get_file(file_id)
        file_url = file.file_path
        logger.info(f"Telegram dosya URL: {file_url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(file_url)
            resp.raise_for_status()
            image_bytes = resp.content

        logger.info(f"Fotoğraf indirildi: {len(image_bytes)} bytes")

        # freeimage.host — base64 upload, doğrudan HTTPS URL
        import base64
        b64_image = base64.b64encode(image_bytes).decode()

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://freeimage.host/api/1/upload",
                data={
                    "key": "6d207e02198a847aa98d0a2a901485a5",
                    "action": "upload",
                    "source": b64_image,
                    "format": "json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status_code") == 200:
                public_url = data["image"]["url"]
                logger.info(f"✅ Herkese açık URL (freeimage): {public_url}")
                return public_url

        logger.warning("freeimage.host upload başarısız")
        return file_url

    except Exception as e:
        logger.error(f"Fotoğraf upload hatası: {e}", exc_info=True)
        try:
            file = await bot.get_file(file_id)
            return file.file_path
        except Exception:
            return None


# ── Kie AI API Çağrıları ─────────────────────────────────

async def create_kie_task(model: str, input_data: dict) -> dict | None:
    """Kie AI üzerinde task oluştur."""
    payload = {"model": model, "input": input_data}
    logger.info(
        f"📤 Kie AI'ya gönderilen payload: "
        f"{json.dumps(payload, ensure_ascii=False)[:800]}"
    )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{KIE_BASE}/jobs/createTask",
                headers={
                    "Authorization": f"Bearer {KIE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp_text = response.text
            logger.info(f"📥 Kie AI yanıt ({response.status_code}): {resp_text[:500]}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Kie AI HTTP hatası: {e.response.status_code} - "
            f"{e.response.text[:500]}"
        )
        return {
            "code": e.response.status_code,
            "msg": e.response.text[:500],
            "data": None,
        }
    except Exception as e:
        logger.error(f"Kie AI bağlantı hatası: {e}")
        return None


from typing import Any, Callable, Awaitable

async def poll_kie_result(task_id: str, max_wait: int = 600, callback: Any = None) -> dict | None:
    """Task sonucunu polling ile bekle."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        elapsed = 0
        interval = 10
        while elapsed < max_wait:
            await asyncio.sleep(interval)
            elapsed += interval

            if callback and elapsed % 300 == 0:  # Her 5 dakikada bir (300 saniye) çalıştır
                try:
                    await callback(elapsed)
                except Exception as e:
                    logger.warning(f"Callback hatası: {e}")

            if elapsed % 60 == 0:
                logger.info(f"⏳ Task {task_id} bekleniyor... ({elapsed}s)")
            try:
                response = await client.get(
                    f"{KIE_BASE}/jobs/recordInfo",
                    headers={"Authorization": f"Bearer {KIE_API_KEY}"},
                    params={"taskId": task_id},
                )
                response.raise_for_status()
                data = response.json()
                state = data.get("data", {}).get("state", "")
                logger.info(
                    f"Poll taskId={task_id}: state={state}, elapsed={elapsed}s"
                )

                if state in ("completed", "success", "done"):
                    return data.get("data", {})
                elif state in ("failed", "error", "fail"):
                    logger.error(f"Task failed: {data}")
                    return {"error": True, "details": data}
            except Exception as e:
                logger.warning(f"Poll hatası: {e}")

        return {"error": True, "details": "Timeout"}


def extract_result_url(result: dict) -> str | None:
    """Kie AI sonucundan çıktı URL'ini çıkar."""
    if not result:
        return None

    result_json_str = result.get("resultJson")
    if result_json_str:
        try:
            res_data = json.loads(result_json_str)
            urls = res_data.get("resultUrls", [])
            if urls and len(urls) > 0:
                return urls[0]
        except (json.JSONDecodeError, TypeError):
            pass

    output = result.get("output")
    if output:
        if isinstance(output, str) and output.startswith("http"):
            return output
        elif isinstance(output, dict):
            return (
                output.get("video_url")
                or output.get("image_url")
                or output.get("url")
            )
        elif isinstance(output, list) and len(output) > 0:
            if isinstance(output[0], str):
                return output[0]

    for key in ("video_url", "image_url", "url"):
        val = result.get(key)
        if val:
            return val
    return None


# ── Seedance 2.0 API ──────────────────────────────────────

async def create_seedance_task(prompt: str, image_url: str | None, aspect_ratio: str = "16:9", duration: str = "12") -> str | None:
    """Seedance 2.0 API üzerinden task oluşturur ve Task ID döner.
    Portrait aspect_ratio `9:16`, Landscape `16:9` vb. olmalıdır.
    """
    logger.info(f"📤 Seedance 2.0'a gönderilen prompt (İlk 100): {prompt[:100]}...")
    payload: dict[str, Any] = {
        "model": "seedance-2.0",
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "resolution": "720p",
        "duration": duration,
        "generate_audio": True,
        "fixed_lens": True,
    }
    if image_url:
        payload["image_urls"] = [image_url]
        
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SEEDANCE_BASE_URL}/generate",
                headers={
                    "Authorization": f"Bearer {SEEDANCE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            task_id = data.get("data", {}).get("task_id")
            logger.info(f"📥 Seedance Task Oluşturuldu: {task_id}")
            return task_id
    except Exception as e:
        logger.error(f"Seedance API task oluşturma hatası: {e}", exc_info=True)
        return None


async def poll_seedance_task(task_id: str, max_wait: int = 600) -> str | None:
    """Seedance task sonucunu (Video URL) periyodik olarak bekler."""
    if not task_id:
        return None
        
    async with httpx.AsyncClient(timeout=30.0) as client:
        elapsed = 0
        interval = 10
        while elapsed < max_wait:
            await asyncio.sleep(interval)
            elapsed += interval
            
            if elapsed % 60 == 0:
                logger.info(f"⏳ Seedance Task {task_id} bekleniyor... ({elapsed}s)")
                
            try:
                response = await client.get(
                    f"{SEEDANCE_BASE_URL}/status",
                    headers={"Authorization": f"Bearer {SEEDANCE_API_KEY}"},
                    params={"task_id": task_id},
                )
                response.raise_for_status()
                data = response.json()
                status_data = data.get("data", {})
                status = status_data.get("status")
                
                logger.debug(f"Poll Seedance {task_id}: status={status}, elapsed={elapsed}s")
                
                if status == "SUCCESS":
                    urls = status_data.get("response", [])
                    if urls and len(urls) > 0:
                        return urls[0]
                    return None
                elif status == "FAILED":
                    err = status_data.get("error_message", "Unknown error")
                    logger.error(f"Seedance Task Failed: {err}")
                    return None
            except Exception as e:
                logger.warning(f"Seedance Poll hatası: {e}")

        logger.error("Seedance Time Out")
        return None

# ── İnline Buton Oluşturucular ───────────────────────────

def image_review_keyboard() -> InlineKeyboardMarkup:
    """Görsel inceleme butonları."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Beğendim", callback_data="approve_image"),
            InlineKeyboardButton("🔄 Yeniden Üret", callback_data="regenerate_image"),
        ],
        [
            InlineKeyboardButton(
                "✏️ Küçük Düzenleme", callback_data="edit_image"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def video_settings_keyboard() -> InlineKeyboardMarkup:
    """Video ayarları butonları."""
    keyboard = [
        [
            InlineKeyboardButton("8s (Kısa)", callback_data="duration_8"),
            InlineKeyboardButton("12s", callback_data="duration_12"),
            InlineKeyboardButton("25s (Sora Yalnızca)", callback_data="duration_25"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def aspect_ratio_keyboard() -> InlineKeyboardMarkup:
    """Görsel / Video en-boy oranı butonları."""
    keyboard = [
        [
            InlineKeyboardButton("🖥️ Yatay (16:9)", callback_data="ratio_16:9"),
            InlineKeyboardButton("📱 Dikey (9:16)", callback_data="ratio_9:16"),
            InlineKeyboardButton("⬛ Kare (1:1)", callback_data="ratio_1:1"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ── İçerik Üretim Fonksiyonları ──────────────────────────

async def produce_image(chat_id: int, conv: dict,
                        context: ContextTypes.DEFAULT_TYPE):
    """NanoBanana Pro ile başlangıç görseli üret.

    Referans görsel varsa → image_url ile gönderir (ürünü koruyarak ortam ekler)
    Referans görsel yoksa → sadece prompt ile sıfırdan üretir
    """
    bot = context.bot

    try:
        conv["state"] = "generating_image"
        prompt = generate_nanobananapro_prompt(conv["product_info"])
        logger.info(f"📸 NanoBanana prompt: {prompt[:300]}")

        ref_image = conv["product_info"].get("reference_image_url")

        if ref_image:
            await bot.send_message(
                chat_id,
                f"🎨 Ürün görseliniz profesyonel bir ortama yerleştiriliyor...\n\n"
                f"📸 Model: NanoBanana Pro\n"
                f"🖼️ Referans: Eklendi\n"
                f"📝 Prompt:\n`{prompt[:150]}...`",
                parse_mode="Markdown",
            )
        else:
            await bot.send_message(
                chat_id,
                f"🎨 Görsel sıfırdan üretiliyor...\n\n"
                f"📸 Model: NanoBanana Pro\n"
                f"📝 Prompt:\n`{prompt[:200]}...`",
                parse_mode="Markdown",
            )

        task_params: dict[str, Any] = {
            "prompt": prompt,
            "aspect_ratio": conv.get("image_aspect_ratio", "16:9"),
        }

        if ref_image:
            task_params["image_input"] = [ref_image]
            logger.info(f"📸 Referans görsel eklendi: {ref_image}")

        task_result = await create_kie_task("nano-banana-pro", task_params)

        if task_result is None:
            await bot.send_message(
                chat_id,
                "⚠️ Görsel üretilemedi. API yanıt vermedi. /yeni yazarak tekrar deneyin.",
            )
            conv["state"] = "waiting_info"
            return

        task_data = task_result.get("data") or {}
        task_id = (
            task_data.get("taskId")
            or task_data.get("task_id")
            or task_result.get("taskId")
            or task_result.get("task_id")
        )

        if not task_id:
            await bot.send_message(
                chat_id,
                f"⚠️ Task ID alınamadı.\n{json.dumps(task_result, indent=2)[:500]}",
            )
            conv["state"] = "waiting_info"
            return

        conv["image_task_id"] = task_id
        await bot.send_message(
            chat_id,
            f"✅ Görsel üretimi başlatıldı!\n🆔 Task: `{task_id}`\n\n⏳ Bekleniyor (1-3 dakika)...",
            parse_mode="Markdown",
        )

        result = await poll_kie_result(task_id)

        if result and not result.get("error"):
            output_url = extract_result_url(result)
            if output_url:
                conv["image_url"] = output_url
                conv["state"] = "reviewing_image"

                await bot.send_message(
                    chat_id,
                    f"🖼️ Görseliniz hazır!\n\n🔗 {output_url}\n\n"
                    "Ne yapmak istersiniz?",
                    reply_markup=image_review_keyboard(),
                )
            else:
                await bot.send_message(
                    chat_id,
                    "⚠️ Görsel üretildi ama URL alınamadı. /yeni yazarak tekrar deneyin.",
                )
                conv["state"] = "waiting_info"
        else:
            error_detail = (
                result.get("details", "Bilinmeyen hata") if result else "Zaman aşımı"
            )
            await bot.send_message(
                chat_id,
                f"⚠️ Görsel üretilemedi.\nHata: {str(error_detail)[:300]}\n\n/yeni yazarak tekrar deneyin.",
            )
            conv["state"] = "waiting_info"

    except Exception as e:
        logger.error(f"Görsel üretim hatası: {e}", exc_info=True)
        await bot.send_message(
            chat_id, f"⚠️ Hata: {str(e)[:300]}\n/yeni yazarak tekrar deneyin."
        )
        conv["state"] = "waiting_info"


async def edit_image(chat_id: int, edit_request: str, conv: dict,
                     context: ContextTypes.DEFAULT_TYPE):
    """Qwen Image Edit ile küçük düzenleme yap."""
    bot = context.bot

    try:
        conv["state"] = "editing_image"

        if not conv["image_url"]:
            await bot.send_message(
                chat_id, "⚠️ Düzenlenecek görsel bulunamadı. Önce bir görsel üretin."
            )
            conv["state"] = "waiting_info"
            return

        prompt = generate_qwen_edit_prompt(edit_request)
        logger.info(f"✏️ Qwen edit prompt: {prompt}")

        await bot.send_message(chat_id, f"✏️ Düzenleme yapılıyor...\n📝 `{prompt[:150]}...`", parse_mode="Markdown")

        task_result = await create_kie_task("qwen/image-edit", {
            "prompt": prompt,
            "image_url": conv["image_url"],
            "strength": 0.4,
            "output_format": "png",
        })

        if task_result is None:
            await bot.send_message(chat_id, "⚠️ Düzenleme başlatılamadı.")
            conv["state"] = "reviewing_image"
            return

        task_data = task_result.get("data") or {}
        task_id = (
            task_data.get("taskId")
            or task_data.get("task_id")
            or task_result.get("taskId")
            or task_result.get("task_id")
        )

        if not task_id:
            await bot.send_message(
                chat_id, "⚠️ Task ID alınamadı. Tekrar deneyin."
            )
            conv["state"] = "reviewing_image"
            return

        await bot.send_message(
            chat_id,
            f"✅ Düzenleme başlatıldı!\n🆔 Task: `{task_id}`\n\n⏳ Bekleniyor...",
            parse_mode="Markdown",
        )

        result = await poll_kie_result(task_id)

        if result and not result.get("error"):
            output_url = extract_result_url(result)
            if output_url:
                conv["image_url"] = output_url
                conv["edit_count"] += 1
                conv["state"] = "reviewing_image"

                await bot.send_message(
                    chat_id,
                    f"✅ Düzenleme tamamlandı!\n\n🔗 {output_url}\n\n"
                    "Ne yapmak istersiniz?",
                    reply_markup=image_review_keyboard(),
                )
            else:
                await bot.send_message(
                    chat_id, "⚠️ Düzenleme tamamlandı ama URL alınamadı."
                )
                conv["state"] = "reviewing_image"
        else:
            await bot.send_message(chat_id, "⚠️ Düzenleme başarısız oldu.")
            conv["state"] = "reviewing_image"

    except Exception as e:
        logger.error(f"Düzenleme hatası: {e}", exc_info=True)
        await bot.send_message(chat_id, f"⚠️ Hata: {str(e)[:300]}")
        conv["state"] = "reviewing_image"


async def produce_video(chat_id: int, conv: dict,
                        context: ContextTypes.DEFAULT_TYPE):
    """Sora 2 Pro Storyboard ile video üret."""
    bot = context.bot

    try:
        conv["state"] = "producing_video"

        n_frames = conv.get("video_duration", "15")
        aspect_ratio = conv.get("video_aspect_ratio", "landscape")
        
        raw_script = conv.get("product_info", {}).get("product", "product")
        # Extract a shorter product name just for reference if possible, or use "The Product"
        product_name = conv.get("product_info", {}).get("product", "The Product")
        
        # Sadece ilk 3 kelimeyi alarak temizle (basit bir metod)
        if len(product_name.split()) > 4:
            product_name = "the product"

        # LLM Parse the script! DUAL PASS - Sora 2 Pro Sadece
        draft_shots = await generate_draft_storyboard_with_openai(
            script=raw_script,
            product_name=product_name,
            n_frames=int(n_frames)
        )
        custom_shots = draft_shots
        if len(draft_shots) > 0:
            custom_shots = await optimize_storyboard_with_openai(
                draft_shots=draft_shots,
                product_name=product_name,
                n_frames=int(n_frames)
            )

        sora_input = generate_sora_input(
            image_url=conv["image_url"],
            product_name=product_name,
            n_frames=n_frames,
            aspect_ratio=aspect_ratio,
            custom_shots=custom_shots
        )

        logger.info(f"🎬 Sora input: {json.dumps(sora_input)}")

        await bot.send_message(
            chat_id,
            f"🎬 Sora 2 Pro Video Üretimi başlatılıyor!\n\n"
            f"⏱️ Süre: {n_frames}s\n"
            f"📐 Format: {aspect_ratio}\n"
            f"🖼️ Referans görsel: Eklendi\n\n"
            f"⏳ Bu işlem 3-10 dakika sürebilir.",
        )

        # ŞİMDİLİK SEEDANCE DEVRE DIŞI YEDEĞE ALINDI (Sadece Sora 2 Pro kullanılacak)
        task_result = await create_kie_task("sora-2-pro-storyboard", sora_input)

        sora_task_id = None
        if task_result:
            task_data = task_result.get("data") or {}
            sora_task_id = (
                task_data.get("taskId")
                or task_data.get("task_id")
                or task_result.get("taskId")
                or task_result.get("task_id")
            )

        if not sora_task_id:
            await bot.send_message(
                chat_id, "⚠️ Video motoru başlatılamadı. /yeni yazarak tekrar deneyin."
            )
            conv["state"] = "waiting_info"
            return
            
        conv["sora_task_id"] = sora_task_id

        await bot.send_message(
            chat_id,
            f"✅ Video motoru başarıyla tetiklendi!\n"
            f"🆔 Sora Task: `{sora_task_id}`\n\n"
            f"⏳ Sonuç bekleniyor. Tamamlandığında veya 5 dakikada bir size haber vereceğim."
        )

        async def wait_callback(elapsed_seconds: int):
            minutes = elapsed_seconds // 60
            await bot.send_message(
                chat_id, 
                f"⏳ Video üretimi devam ediyor... ({minutes} dakika geçti)\n"
                f"💡 Bu süreç normaldir."
            )

        async def poll_sora():
            if not sora_task_id:
                return None
            res = await poll_kie_result(sora_task_id, max_wait=3600, callback=wait_callback)
            if res and not res.get("error"):
                return extract_result_url(res)
            return None

        # Sadece Sora'yı bekle
        sora_url = await poll_sora()

        if sora_url:
            msg = "🎉 Videonuz hazır!\n"
            msg += f"\n🎬 Sora 2 Pro Version:\n{sora_url}\n"
            msg += "\nYeni bir video oluşturmak için /yeni yazın."
            await bot.send_message(chat_id, msg)
        else:
            await bot.send_message(
                chat_id,
                "⚠️ Modelden sonuç alınamadı veya zaman aşımı gerçekleşti.\n/yeni yazarak tekrar deneyin."
            )

        conv["state"] = "waiting_info"

    except Exception as e:
        logger.error(f"Video üretim hatası: {e}", exc_info=True)
        await bot.send_message(
            chat_id, f"⚠️ Hata: {str(e)[:300]}\n/yeni yazarak tekrar deneyin."
        )
        conv["state"] = "waiting_info"


# ── Ürün Bilgisi Parse ───────────────────────────────────

async def evaluate_product_info_with_openai(conv: dict) -> dict:
    """OpenAI kullanarak konuşma geçmişinden yeterli ürün bilgisi var mı kontrol eder.
    Hafızadan faydalanarak kullanıcının niyetini anlar ve gereksiz soruları önler.
    
    ERDOOR MARKA ADAPTASYONU:
    Tüm belirsiz veya genel kavramları (ör. "kapı", "çelik kapı", "ahşap kapı"), 
    "ErDoor" markasının "dış cephe, lüks villa girişi veya apartman dış kapısı" vizyonuna zorlar.
    """
    system_prompt = """
    Sen profesyonel bir reklam yönetmeni yapay zeka asistanısın. Görevin, 'ErDoor' isimli premium Türk dış kapı üreticisini temsil eden bir kapı reklamı çekmek için yeterli bilgi olup olmadığını anlamak.
    
    ÖNEMLİ MARKA BİLGİSİ (ERDOOR):
    ErDoor, oda içi standart kapılardan ziyade dış cephe (villa girişi, apartman girişi vs.) çelik ve yüksek kaliteli kompozit ahşap kapılar üretir. Kullanıcı sadece "bir kapı" dese dahi sen bunu her halükarda "An elegant ErDoor exterior steel door for a luxury villa entrance" olarak yorumlamalısın! İç standart oda kapısı konseptini asla kabul etme.
    
    KRİTERLER:
    1. Ürünün kabaca ne olduğu (örn: "kırmızı çelik kapı", "villa kapısı" veya kullanıcı sadece kapı fotoğrafı yükleyip "bunu kullan" vs. dediyse) belli ise "status": "complete" dön. Eksik kalan kısımları (renk, doku vs. yoksa) kendi inisiyatifinle "ErDoor exterior door" konseptine %100 uyacak İngilizce profesyonel bir prompta çevir. Kullanıcıyı detay vermesi için asla darlama.
    2. Yalnızca kullanıcı "merhaba", "reklam çek", "yardım" vs. dediyse ve ortada BİR ÜRÜN (kapı) veya FOTOĞRAF yoksa "status": "incomplete" dön. Bu durumda ona "question" alanından ErDoor dış kapısı için model/tarz sor. Kısa ve motive edici olsun (1 cümleyi geçmesin).
    
    ZORUNLU JSON ÇIKTISI:
    {
      "status": "complete" veya "incomplete",
      "question": "Eğer incomplete ise kullanıcıya sorulacak Türkçe Soru (Değilse boş bırak)",
      "product_info": {
        "product": "Eğer complete ise, ürünün İNGİLİZCE detayı. MUTLAKA 'ErDoor exterior' kelimelerini içersin. Örn: An elegant ErDoor exterior steel door for a luxury villa entrance",
        "brand": "ErDoor",
        "style": "Kullanıcı stil belirttiyse İNGİLİZCE stil, yoksa 'modern, luxurious and professional'"
      }
    }
    """
    
    has_image = bool(conv.get("image_url") or conv.get("product_info", {}).get("reference_image_url"))
    
    user_prompt = f"Kullanıcı Fotoğraf Yükledi Mi?: {'Evet' if has_image else 'Hayır'}\n\nKonuşma Geçmişi:\n"
    for msg in conv.get("messages", []):
        user_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
        
    logger.info("🧠 [Pass 0] OpenAI ErDoor ürün kriteri değerlendirmesi yapıyor...")
    data = await _call_openai_json(system_prompt, user_prompt)
    if not data or "status" not in data:
        return {
            "status": "complete",
            "product_info": {"product": "A luxurious ErDoor exterior steel door", "brand": "ErDoor", "style": "modern and luxurious"}
        }
    return data or {}

def parse_product_info(text: str) -> dict:
    """Kullanıcının mesajından basit kw ile ürün bilgilerini çıkar."""
    info = {"product": text.strip()}
    brand_match = re.search(r'(?:marka|brand)[:\s]+(.+?)(?:,|$)', text, re.IGNORECASE)
    if brand_match:
        info["brand"] = brand_match.group(1).strip()
    if "modern" in text.lower(): info["style"] = "modern and sleek"
    else: info["style"] = "modern and professional"
    return info


# ── Handler'lar ──────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot başlatıldığında hoş geldin mesajı."""
    chat_id = update.effective_chat.id
    conversations.pop(chat_id, None)
    get_conversation(chat_id)

    welcome = (
        "👋 Merhaba! Ben ürün reklam videosu otomasyon asistanınızım.\n\n"
        "📋 **Nasıl Çalışır:**\n\n"
        "1️⃣ Ürününüzü anlatın (ne olduğu, markası, stili)\n"
        "2️⃣ Ben bir ürün görseli üreteyim\n"
        "3️⃣ Beğenirseniz → reklam videosuna dönüştüreyim\n"
        "   Beğenmezseniz → düzenleyeyim veya yeniden üreteyim\n\n"
        "🚀 Hadi başlayalım! Ürününüzü anlatın.\n\n"
        "💡 Bir ürün fotoğrafı da gönderebilirsiniz."
    )
    await safe_reply(update.message, welcome)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📋 **Komutlar:**\n\n"
        "/start — Yeni sohbet başlat\n"
        "/yeni — Sohbeti sıfırla\n"
        "/durum — Mevcut durumu göster\n"
        "/yardim — Bu mesajı göster\n\n"
        "💡 Ürünü anlatın veya fotoğraf gönderin!"
    )
    await safe_reply(update.message, help_text)


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conversations.pop(chat_id, None)
    await update.message.reply_text(
        "🔄 Sohbet sıfırlandı!\n\nÜrününüzü anlatarak başlayın."
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conv = get_conversation(chat_id)

    state_labels = {
        "waiting_info": "📝 Ürün bilgisi bekleniyor",
        "generating_image": "🎨 Görsel üretiliyor",
        "reviewing_image": "🖼️ Görsel inceleniyor",
        "editing_image": "✏️ Düzenleme yapılıyor",
        "collecting_scenes": "🎬 Video ayarları bekleniyor",
        "producing_video": "🎥 Video üretiliyor",
    }

    status = f"📊 **Durum:** {state_labels.get(conv['state'], conv['state'])}\n"

    if conv["product_info"]:
        product = conv["product_info"].get("product", "")
        status += f"📦 Ürün: {product[:100]}\n"

    if conv["image_url"]:
        status += f"🖼️ Görsel: Hazır\n"
        status += f"✏️ Düzenleme sayısı: {conv['edit_count']}\n"

    await safe_reply(update.message, status)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcıdan gelen fotoğrafları işle."""
    chat_id = update.effective_chat.id
    conv = get_conversation(chat_id)

    try:
        await update.effective_chat.send_action("typing")

        photo = update.message.photo[-1]
        public_url = await upload_telegram_photo_to_public(context.bot, photo.file_id)

        if not public_url:
            await update.message.reply_text("⚠️ Görsel yüklenemedi, tekrar deneyin.")
            return

        caption = update.message.caption or ""

        if conv["state"] == "waiting_info":
            # Referans görsel olarak kaydet
            conv["product_info"]["reference_image_url"] = public_url
            conv["messages"].append({"role": "user", "content": f"[Kullanıcı bir Fotoğraf yükledi. Açıklama: '{caption}']"})

            evaluation = await evaluate_product_info_with_openai(conv)

            if evaluation.get("status") == "incomplete":
                question = evaluation.get("question", "Harika bir görsel! Hangi ürün olduğunu biraz tarif edebilir misiniz?")
                conv["messages"].append({"role": "assistant", "content": question})
                await update.message.reply_text(f"🤖 {question}")
            else:
                p_info = evaluation.get("product_info", {})
                conv["product_info"].update(p_info)
                conv["state"] = "collecting_aspect_ratio"
                await update.message.reply_text(
                    f"📸 Görsel ve bilgiler ulaştı!\n"
                    f"📦 Ürün: {conv['product_info'].get('product', caption[:20])}\n\n"
                    f"📐 Görsel ve video için hangi formatı (En-Boy oranını) tercih edersiniz?",
                    parse_mode="Markdown",
                    reply_markup=aspect_ratio_keyboard()
                )

        elif conv["state"] == "reviewing_image":
            # Yeni referans görsel — fotoğrafı doğrudan kullan
            conv["image_url"] = public_url
            await update.message.reply_text(
                "📸 Kendi görseliniz yüklendi!\n\n"
                "Bu görseli video için kullanabilirsiniz.",
                reply_markup=image_review_keyboard(),
            )

        else:
            await update.message.reply_text(
                "📸 Fotoğraf alındı. Ancak şu an farklı bir aşamadayız.\n"
                "Sıfırlamak için /yeni yazabilirsiniz."
            )

    except Exception as e:
        logger.error(f"Fotoğraf hatası: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Fotoğraf işlenirken hata oluştu.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Metin mesajlarını state'e göre işle."""
    chat_id = update.effective_chat.id
    conv = get_conversation(chat_id)
    text = update.message.text.strip()

    if conv["state"] == "waiting_info":
        conv["messages"].append({"role": "user", "content": text})
        await update.effective_chat.send_action("typing")

        evaluation = await evaluate_product_info_with_openai(conv)

        if evaluation.get("status") == "incomplete":
            question = evaluation.get("question", "Hangi ürün için reklam hazırlamak istersiniz?")
            conv["messages"].append({"role": "assistant", "content": question})
            await update.message.reply_text(f"🤖 {question}")
        else:
            p_info = evaluation.get("product_info", {})
            conv["product_info"].update(p_info)
            conv["state"] = "collecting_aspect_ratio"
            await update.message.reply_text(
                f"📦 Bilgiler yeterli, anlaşıldı!\n\n"
                f"**Ürün Detayı:** {conv['product_info'].get('product')}\n"
                f"**Stil:** {conv['product_info'].get('style', 'modern')}\n\n"
                f"📐 Görsel ve video için hangi formatı (En-Boy oranını) tercih edersiniz?",
                parse_mode="Markdown",
                reply_markup=aspect_ratio_keyboard()
            )

    elif conv["state"] == "reviewing_image":
        # Kullanıcı metin yazdıysa düzenleme olarak al
        text_lower = text.lower()

        # Büyük değişiklik anahtar kelimeleri
        big_change_keywords = [
            "yeniden", "baştan", "tamamen", "sıfırdan", "farklı",
            "yeni bir", "bambaşka",
        ]
        is_big_change = any(kw in text_lower for kw in big_change_keywords)

        if is_big_change:
            # Büyük değişiklik → NanoBanana ile yeniden üret
            conv["product_info"].update(parse_product_info(text))
            await update.message.reply_text("🔄 Görsel yeniden üretiliyor...")
            asyncio.create_task(produce_image(chat_id, conv, context))
        else:
            # Küçük düzenleme → Qwen Image Edit
            asyncio.create_task(edit_image(chat_id, text, conv, context))

    elif conv["state"] == "collecting_scenes":
        # Video süresi bekleniyor — ama metin geldiyse yardım et
        await update.message.reply_text(
            "📐 Lütfen yukarıdaki butonlardan video süresini seçin.",
            reply_markup=video_settings_keyboard(),
        )

    elif conv["state"] in ("generating_image", "editing_image", "producing_video"):
        await update.message.reply_text(
            "⏳ İşlem devam ediyor, lütfen bekleyin..."
        )

    else:
        await update.message.reply_text(
            "🤔 Anlamadım. /yeni yazarak baştan başlayabilirsiniz."
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline buton callback'lerini işle."""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    conv = get_conversation(chat_id)

    # ── Görsel İnceleme Butonları ──
    if query.data == "approve_image":
        conv["state"] = "collecting_scenes"
        await safe_edit(
            query.message,
            "✅ Görsel onaylandı!\n\n"
            "🎬 Şimdi video ayarlarına geçelim.\n\n"
            "⏱️ Video süresini seçin:",
            reply_markup=video_settings_keyboard(),
        )

    elif query.data == "regenerate_image":
        await safe_edit(query.message, "🔄 Görsel yeniden üretiliyor...")
        asyncio.create_task(produce_image(chat_id, conv, context))

    elif query.data == "edit_image":
        conv["state"] = "reviewing_image"
        await safe_edit(
            query.message,
            "✏️ Ne değiştirmek istiyorsunuz?\n\n"
            "Örnek:\n"
            "• \"Arka planı mavi yap\"\n"
            "• \"Ürünün rengini kırmızı yap\"\n"
            "• \"Gölgeleri artır\"\n\n"
            "Mesaj olarak yazın:",
        )

    # ── Video Format Butonları (Şimdi Görsel Öncesi Soruluyor) ──
    elif query.data.startswith("ratio_"):
        ratio = query.data.split("_")[1]
        conv["image_aspect_ratio"] = ratio
        conv["video_aspect_ratio"] = ratio

        # Sora için mapping (portrait, landscape, square)
        mapped_ratio = "landscape"
        if ratio == "9:16":
            mapped_ratio = "portrait"
        elif ratio == "1:1":
            mapped_ratio = "square"
        conv["video_aspect_ratio"] = mapped_ratio

        await safe_edit(
            query.message,
            f"📐 Format: **{ratio}** olarak ayarlandı.\n\n"
            f"🎨 Başlangıç görseli (Start Frame) üretiliyor..."
        )

        asyncio.create_task(produce_image(chat_id, conv, context))

    # ── Video Süresi Butonları ──
    elif query.data.startswith("duration_"):
        duration = query.data.split("_")[1]
        conv["video_duration"] = duration
        await safe_edit(
            query.message,
            f"⏱️ Video süresi: **{duration} saniye**\n\n"
            f"🎬 Video üretimi (Çift Motorlu) başlatılıyor..."
        )

        asyncio.create_task(produce_video(chat_id, conv, context))


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Doküman olarak gönderilen görselleri işle."""
    chat_id = update.effective_chat.id
    conv = get_conversation(chat_id)

    doc = update.message.document

    if doc.mime_type and doc.mime_type.startswith("image/"):
        public_url = await upload_telegram_photo_to_public(context.bot, doc.file_id)
        if public_url:
            if conv["state"] == "waiting_info":
                conv["product_info"]["reference_image_url"] = public_url
                caption = update.message.caption or ""
                if caption:
                    conv["product_info"].update(parse_product_info(caption))
                    await update.message.reply_text(
                        "📸 Referans görsel alındı!\n🎨 Görsel üretiliyor..."
                    )
                    asyncio.create_task(produce_image(chat_id, conv, context))
                else:
                    await update.message.reply_text(
                        "📸 Referans görsel alındı!\nŞimdi ürünü kısaca anlatın."
                    )
            elif conv["state"] == "reviewing_image":
                conv["image_url"] = public_url
                await update.message.reply_text(
                    "📸 Görseliniz yüklendi!",
                    reply_markup=image_review_keyboard(),
                )
        else:
            await update.message.reply_text("⚠️ Görsel yüklenemedi.")
    else:
        await update.message.reply_text(
            "📎 Bu dosya türü desteklenmiyor. Lütfen bir görsel gönderin."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hataları logla."""
    logger.error(f"Update caused error: {context.error}", exc_info=context.error)
    if update and update.effective_chat:
        try:
            await context.bot.send_message(
                update.effective_chat.id,
                "⚠️ Bir hata oluştu. /yeni yazarak tekrar deneyin.",
            )
        except Exception:
            pass


# ── Ana Fonksiyon ────────────────────────────────────────

def main():
    print("🤖 Ürün Reklam Videosu Botu v4 başlatılıyor...")
    print(f"   Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("yardim", help_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("yeni", reset_command))
    app.add_handler(CommandHandler("durum", status_command))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)

    print("✅ Bot hazır! Telegram üzerinden mesaj gönderin.")
    print("   Durdurmak için Ctrl+C")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
