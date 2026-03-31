"""
🎨 Multi-Theme Cover Generator
================================
Her video için 3 farklı tema × 2 varyasyon = 6 kapak üretir.
Toplam: 2 video × 6 = 12 kapak.
"""
import os
import sys
import json
import time

# Ensure /tmp working dir modules are found
sys.path.insert(0, ".")

# Patch OAUTH_DIR for Google Drive access
import google_auth
google_auth.OAUTH_DIR = "../../_knowledge/credentials/oauth"

os.chdir(".")

from google import genai
from google.genai import types
from autonomous_cover_agent import (
    upload_to_imgbb,
    generate_cover_with_nanobanana,
    evaluate_image_with_vision,
)
from drive_service import upload_cover_to_drive
import requests

# ── Config ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

DRIVE_URL = "https://drive.google.com/drive/folders/1zy5nhR8w0Nyc8LT_QT9b-9CPqbUBkGts"
CUTOUT_IMG = "./cutout_temp.png"

# ── Videos ──
VIDEOS = [
    {
        "name": "AI Tools Top 5",
        "script": """Bugüne kadar 100'ün üzerinde yapay zeka kullandım. İşte gerçekten işe yarayan 5 tanesi Pixelcut AI. Fotoğrafların kalitesini 10 kat arttırıyor. Grok tamamen sansürsüz. Diğer yapay zekaların yapamadığı pis işleri yapabiliyor. Claude, tarif ettiğim şeyi kod olarak yazabiliyor. Yazılımcı gibi bir şey. RunwaymL Hollywood bundan korkuyor çünkü gerçekçi videolar oluşturabiliyor. Elevenlabs, sesimi klonluyor ve seslendirme yapabiliyor.""",
    },
    {
        "name": "Viral Spider Icecream",
        "script": """Böyle mide bulandırıcı videolar yapıp nasıl milyonlarca izlenirsin Hemen gösteriyorum. Öncelikle 2 tane görsel oluşturman gerekiyor. ChatGPT den simsiyah bir dondurma ve simsiyah bir örümcek çizmesini istedim. Daha sonra klingai.com isimli siteye gittim. Bu arada site ücretsiz. Görsellerimi ekledim ve dondurmayı örümceğe dönüştür yazdım. Bu arada siteyi ve detayları almak için yorumlara dondurma yaz. Ve işte sonuç.""",
    },
]


def generate_three_themes(video_name: str, script_text: str) -> list:
    """Gemini ile bir video scripti için 3 FARKLI yaratıcı tema üretir."""
    prompt = f"""
    You are an expert Turkish social media strategist for short-form videos (Reels/TikTok/Shorts).
    
    IMPORTANT: The video's internal tracking name '{video_name}' is just an identifier—ignore it for text creation.
    
    Here is the actual video script:
    \"\"\"
    {script_text}
    \"\"\"
    
    Task: Based ONLY on the script content, create exactly 3 COMPLETELY DIFFERENT creative theme directions.
    Each theme should have a unique angle, emotion, and visual concept.
    
    For each theme, provide:
    1. **theme_name**: A short internal label (e.g., "shock", "mystery", "power")
    2. **cover_text**: A punchy, 2-4 word Turkish clickbait hook. STRICT RULES:
       - Turkish ONLY. NO English words.
       - NOT the video/tool name.
       - ALL CAPS, max 4 words.
       - Examples: "ANTRENÖRÜNÜ KOV", "AJANSA PARA VERME", "KOMİSYONA SON"
    3. **scene_description**: A creative, cinematic visual scene (in English) that DIRECTLY illustrates the cover_text.
       - AVOID cliché "person at computer" scenes.
       - Use dramatic metaphors, unexpected visuals, movie-poster quality.
       - Must be SPECIFIC and actionable.
       - CRITICAL: The scene MUST be SIMPLE and CLEAN with maximum 2-3 main visual elements.
         These covers will be viewed as tiny ~150px thumbnails on Instagram grid.
         Too many background elements create visual clutter. Think BOLD and SIMPLE, not detailed and complex.
       - GOOD example: man + giant robot shadow on wall (2 elements, clean)
       - BAD example: man surrounded by 7 characters in different costumes (too many elements, cluttered)
    
    The 3 themes MUST be meaningfully different from each other:
    - Theme 1: Focus on SHOCK / PROVOCATIVE angle
    - Theme 2: Focus on CURIOSITY / MYSTERY angle  
    - Theme 3: Focus on EMPOWERMENT / BENEFIT angle
    
    Return EXACTLY this JSON array:
    [
        {{
            "theme_name": "...",
            "cover_text": "...",
            "scene_description": "..."
        }},
        {{
            "theme_name": "...",
            "cover_text": "...",
            "scene_description": "..."
        }},
        {{
            "theme_name": "...",
            "cover_text": "...",
            "scene_description": "..."
        }}
    ]
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        raw = response.text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed[:3]
        return [parsed]
    except Exception as e:
        print(f"Error generating themes: {e}")
        return [
            {"theme_name": "fallback1", "cover_text": "BUNU İZLE", "scene_description": "A dramatic cinematic portrait."},
            {"theme_name": "fallback2", "cover_text": "İNANILMAZ", "scene_description": "A mysterious moody scene."},
            {"theme_name": "fallback3", "cover_text": "HERKES ŞAŞIRDI", "scene_description": "An empowering dynamic shot."},
        ]


def generate_single_cover(person_image_url: str, theme: dict, variant_index: int, video_name: str) -> tuple:
    """Tek bir kapak üretir ve değerlendirir. (image_url, score) döner."""
    
    cover_text = theme["cover_text"]
    scene_desc = theme["scene_description"]
    
    # Variant-specific visual instructions
    if variant_index == 1:
        variant_instruction = (
            "A candid, unposed, in-the-moment cinematic shot. The subject should be engaged in an action "
            "related to the topic. Avoid looking directly "
            "at the camera. Use dramatic, single-source lighting. CLOSE-UP or MEDIUM SHOT (chest/waist up)."
        )
    else:
        variant_instruction = (
            "A mysterious, moody low-angle shot. The environment heavily dictates the lighting "
            "(e.g., inside a car at night, in a dimly lit room, neon-backlit). The face should be partially "
            "in shadow. Shot on 35mm film, highly realistic and authentic. MEDIUM or CLOSE-UP shot."
        )

    prompt = (
        f"A cinematic, highly authentic, and moody vertical photo for a social media cover (Instagram Reels). "
        f"The subject must match the facial identity from the image reference. "
        f"Choose the subject's clothing to match the video topic: for tech/casual/creative topics use streetwear, hoodie, or t-shirt; for business/finance/corporate topics use a smart casual outfit like a dark blazer, turtleneck, or dark button-down shirt; for motivational/luxury topics use a sleek, premium look. The clothing should feel natural and context-appropriate, never generic stock-photo style. "
        f"DO NOT make the subject look like a generic stock photo model. "
        f"The scene MUST visually match this description: {scene_desc}. "
        f"The visual action should directly reinforce the cover text '{cover_text}'. "
        f"The video topic is: '{video_name}'. "
        f"Lighting: Highly dramatic, single-source lighting. Deep shadows. "
        f"Vibe: Candid, unposed, in-the-moment. Shot on 35mm film, grainy, realistic texture. "
        f"Colors: Cinematic grading, cool shadows with warm highlights. "
        f"\n\n"
        f"BACKGROUND SIMPLICITY (CRITICAL — INSTAGRAM GRID RULE): "
        f"The background must be SIMPLE and CLEAN with maximum 2-3 main visual elements total (including the person). "
        f"This cover will be viewed as a tiny ~150px thumbnail on an Instagram profile grid alongside many other covers. "
        f"Too many background elements create visual clutter and make the grid look messy. "
        f"If background elements exist, apply depth-of-field blur/bokeh so the person stays sharp. "
        f"Think BOLD and SIMPLE, not detailed and complex. "
        f"\n\n"
        f"TEXT INSTRUCTIONS (EXTREMELY IMPORTANT): "
        f"The text MUST EXACTLY read: '{cover_text}'. "
        f"The text language is TURKISH. Do NOT include any English words. "
        f"Write the text ONLY ONCE—do NOT repeat or duplicate it. "
        f"Text placement: VERTICAL CENTER or SLIGHTLY BELOW CENTER. "
        f"Text MUST be within Instagram 4:5 safe zone—NOT in the top 15% or bottom 15%. "
        f"Text size: EXTREMELY LARGE — at the scale of a MOVIE POSTER TITLE or BILLBOARD. "
        f"Each line of text must cover 75-80% of the image width. Think BILLBOARD, not book cover. "
        f"The text must be the DOMINANT visual element — readable even at 150px thumbnail size. "
        f"Font: Bold, modern sans-serif, all-caps. High contrast with background. "
        f"\n\nSpecial Instructions: {variant_instruction} "
        f"--cref {person_image_url} --cw 0"
    )

    generated_url = generate_cover_with_nanobanana(person_image_url, prompt)
    if not generated_url:
        return None, 0

    # Load style guide + learnings for evaluation
    with open("rourke_style_guide.md", "r") as f:
        style_guide = f.read()
    learnings = ""
    if os.path.exists("learnings.md"):
        with open("learnings.md", "r") as f:
            learnings = f.read()

    evaluation = evaluate_image_with_vision(generated_url, style_guide, cover_text, learnings)
    score = float(evaluation.get("score", 0))
    print(f"   Score: {score}/10 | Critique: {evaluation.get('critique', '')[:120]}")
    return generated_url, score


def run_multi_theme_pipeline():
    """Ana pipeline: 2 video × 3 tema × 2 varyasyon = 12 kapak."""
    
    # Upload cutout image once
    print("📸 Cutout görseli ImgBB'ye yükleniyor...")
    person_image_url = upload_to_imgbb(CUTOUT_IMG)
    if not person_image_url:
        print("❌ ImgBB yüklemesi başarısız!")
        return
    print(f"✅ Cutout URL: {person_image_url}\n")

    os.makedirs("outputs/multi_theme", exist_ok=True)
    
    results_summary = []

    for video in VIDEOS:
        video_name = video["name"]
        script = video["script"]
        safe_name = video_name.replace(" ", "_").lower()
        
        print(f"\n{'='*60}")
        print(f"🎬 VİDEO: {video_name}")
        print(f"{'='*60}")
        
        # Generate 3 themes
        print("🧠 Gemini'den 3 farklı tema üretiliyor...")
        themes = generate_three_themes(video_name, script)
        
        for t_idx, theme in enumerate(themes, 1):
            theme_name = theme.get("theme_name", f"theme{t_idx}")
            cover_text = theme.get("cover_text", "BUNU İZLE")
            scene_desc = theme.get("scene_description", "")
            
            print(f"\n  📌 Tema {t_idx}/{len(themes)}: {theme_name.upper()}")
            print(f"     Metin: {cover_text}")
            print(f"     Sahne: {scene_desc[:100]}...")
            
            for v_idx in range(1, 3):  # 2 varyasyon
                print(f"\n     🎨 Varyasyon {v_idx}/2 üretiliyor...")
                
                img_url, score = generate_single_cover(
                    person_image_url, theme, v_idx, video_name
                )
                
                if img_url:
                    # Download
                    filename = f"{safe_name}_tema{t_idx}_{theme_name}_v{v_idx}.png"
                    filepath = f"outputs/multi_theme/{filename}"
                    img_data = requests.get(img_url).content
                    with open(filepath, "wb") as f:
                        f.write(img_data)
                    print(f"     💾 Kaydedildi: {filepath}")
                    
                    # Upload to Drive
                    drive_name = f"{video_name} - Tema {t_idx} ({theme_name}) V{v_idx}.png"
                    try:
                        upload_cover_to_drive(filepath, DRIVE_URL, file_name=drive_name)
                        print(f"     ☁️ Drive'a yüklendi: {drive_name}")
                    except Exception as e:
                        print(f"     ⚠️ Drive yükleme hatası: {e}")
                    
                    results_summary.append({
                        "video": video_name,
                        "theme": theme_name,
                        "text": cover_text,
                        "variant": v_idx,
                        "score": score,
                        "file": filename,
                    })
                else:
                    print(f"     ❌ Üretim başarısız (Tema {t_idx}, Var {v_idx})")

    # Summary
    print(f"\n\n{'='*60}")
    print("📊 SONUÇ ÖZETİ")
    print(f"{'='*60}")
    for r in results_summary:
        emoji = "🟢" if r["score"] >= 8 else "🟡" if r["score"] >= 5 else "🔴"
        print(f"  {emoji} {r['video']} | Tema: {r['theme']} | Metin: {r['text']} | V{r['variant']} | Skor: {r['score']}/10 | {r['file']}")
    
    print(f"\n✅ Toplam {len(results_summary)}/12 kapak başarıyla üretildi ve Drive'a yüklendi.")
    print(f"📁 Drive: {DRIVE_URL}")


if __name__ == "__main__":
    run_multi_theme_pipeline()
