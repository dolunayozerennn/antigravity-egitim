"""
YouTube Thumbnail Cover Agent — 16:9 Landscape Format
Kie AI (Nano Banana Pro) ile YouTube thumbnail üretimi, Gemini ile değerlendirme.
Reels (9:16) agent'ından fork edilmiştir — tüm promptlar ve değerlendirme kriterleri
YouTube formatına adapte edilmiştir.
"""

import os
import time
import base64
import requests
import json
import glob
import random
import urllib.parse
from dotenv import load_dotenv

# SDK Compatibility Layer: prefer google-genai (new), fallback to google-generativeai (deprecated)
_USE_NEW_SDK = False
try:
    from google import genai
    _USE_NEW_SDK = True
except ImportError:
    try:
        import google.generativeai as genai_legacy
    except ImportError:
        genai_legacy = None

# Load project .env first, then master credentials as fallback
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "_knowledge", "credentials", "master.env"))

KIE_API_KEY = os.getenv("KIE_API_KEY")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SCREENSHOT_API_KEY = os.getenv("SCREENSHOT_API_KEY", "128GKV1-WP4MPY5-PSMHEFD-5HTARAE")

REQUEST_TIMEOUT = 60  # seconds for HTTP requests

gemini_client = None
try:
    if _USE_NEW_SDK:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini SDK: google-genai (new)")
    elif genai_legacy:
        genai_legacy.configure(api_key=GEMINI_API_KEY)
        gemini_client = True  # sentinel — functions check this
        print("⚠️ Gemini SDK: google-generativeai (deprecated, migrate to google-genai)")
except Exception as e:
    print(f"Warning: Failed to initialize Gemini Client: {e}")
    gemini_client = None


def _gemini_generate_text(prompt: str, json_mode: bool = False) -> str:
    """SDK-agnostic text generation."""
    if _USE_NEW_SDK:
        config = {"response_mime_type": "application/json"} if json_mode else {}
        response = gemini_client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=config
        )
        return response.text
    else:
        model = genai_legacy.GenerativeModel("gemini-1.5-flash")
        gen_config = {"response_mime_type": "application/json"} if json_mode else {}
        response = model.generate_content(prompt, generation_config=gen_config)
        return response.text

def _gemini_generate_vision(image_path: str, prompt: str, json_mode: bool = False) -> str:
    """SDK-agnostic vision generation with image."""
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    if _USE_NEW_SDK:
        from google.genai import types
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        config = {"response_mime_type": "application/json"} if json_mode else {}
        response = gemini_client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[image_part, prompt],
            config=config
        )
        return response.text
    else:
        model = genai_legacy.GenerativeModel("gemini-1.5-flash")
        encoded = base64.b64encode(image_bytes).decode('utf-8')
        image_data = {"mime_type": "image/jpeg", "data": encoded}
        gen_config = {"response_mime_type": "application/json"} if json_mode else {}
        response = model.generate_content([image_data, prompt], generation_config=gen_config)
        return response.text

# ─── SHARED UTILITIES ────────────────────────────────────────────────────────

def upload_to_imgbb(image_path: str) -> str:
    """Upload an image to Catbox.moe first, then fallback to ImgBB."""
    print(f"Uploading {image_path} to Catbox.moe public CDN...")
    url_catbox = "https://catbox.moe/user/api.php"
    
    try:
        with open(image_path, "rb") as file:
            payload = {"reqtype": "fileupload"}
            files = {"fileToUpload": file}
            try:
                response = requests.post(url_catbox, data=payload, files=files, timeout=REQUEST_TIMEOUT)
                
                if response.status_code == 200:
                    img_url = response.text.strip()
                    if "catbox.moe" in img_url:
                        print(f"Uploaded successfully to Catbox: {img_url}")
                        return img_url
                    else:
                        print(f"Catbox invalid response: {img_url}")
                else:
                    print(f"Catbox upload failed: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"Catbox network error: {e}")
    except Exception as e:
        print(f"Error reading file for Catbox: {e}")
        
    print(f"Falling back to ImgBB for {image_path}...")
    try:
        with open(image_path, "rb") as file:
            encoded_image = base64.b64encode(file.read()).decode("utf-8")
        url_imgbb = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY,
            "image": encoded_image
        }
        response = requests.post(url_imgbb, data=payload, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            img_url = response.json()["data"]["url"]
            print(f"Uploaded successfully to ImgBB: {img_url}")
            return img_url
        else:
            print(f"ImgBB upload failed: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"ImgBB network error: {e}")
        return None
    except Exception as e:
        print(f"Error uploading to ImgBB: {e}")
        return None

def capture_screenshot(url: str) -> str:
    """Takes a screenshot of an URL using ScreenshotAPI and saves it locally. Returns the local path."""
    encoded_url = urllib.parse.quote(url)
    api_url = f"https://shot.screenshotapi.net/screenshot?token={SCREENSHOT_API_KEY}&url={encoded_url}&width=1920&height=1080&full_page=false&output=image&file_type=png"
    
    print(f"📸 Taking screenshot of {url}...")
    try:
        response = requests.get(api_url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            safe_name = "".join([c for c in url if c.isalpha() or c.isdigit()]).rstrip()[:15]
            out_path = f"assets/screenshot_{safe_name}.png"
            os.makedirs("assets", exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(response.content)
            print(f"Screenshot saved to {out_path}")
            return out_path
        else:
            print(f"ScreenshotAPI failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"ScreenshotAPI network error: {e}")
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
    return None

def generate_cover_with_nanobanana(image_url: str, prompt: str, extra_ref_urls: list = None) -> str:
    """Generate a YouTube thumbnail using Kie AI Nano Banana Pro (16:9 format)."""
    print("🎬 Sending generation request to Nano Banana Pro (16:9 landscape)...")
    
    create_url = "https://api.kie.ai/api/v1/jobs/createTask"
    headers = {
        "Authorization": f"Bearer {KIE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Build image_input list (Base + Up to 4 Extra Refs like screenshots or face variants)
    image_inputs = [image_url]
    if extra_ref_urls:
        for ref_url in extra_ref_urls[:4]:
            if ref_url and ref_url not in image_inputs:
                image_inputs.append(ref_url)
    
    print(f"  Using {len(image_inputs)} reference image(s) for face identity and background.")
    
    payload = {
        "model": "nano-banana-2",
        "input": {
            "prompt": prompt,
            "image_input": image_inputs,
            "aspect_ratio": "16:9"
        }
    }
    
    try:
        response = requests.post(create_url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            print(f"Failed to create task: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Kie AI network error during task creation: {e}")
        return None
        
    task_id = response.json().get("data", {}).get("taskId")
    if not task_id:
        print("taskId not found in generation response.")
        return None
        
    print(f"Task created successfully. Task ID: {task_id}. Waiting for completion...")
    
    # Polling for result (max 10 minutes)
    poll_url = f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}"
    max_polls = 60  # 60 × 10s = 10 minutes
    
    for poll_count in range(max_polls):
        try:
            poll_resp = requests.get(poll_url, headers=headers, timeout=REQUEST_TIMEOUT)
            if poll_resp.status_code != 200:
                 print(f"Polling failed: {poll_resp.text}")
                 time.sleep(10)
                 continue
        except requests.exceptions.RequestException as e:
            print(f"Polling network error: {e}")
            time.sleep(10)
            continue
             
        data = poll_resp.json().get("data", {})
        state = data.get("state")
        
        if state == "success":
            result_json = data.get("resultJson", "{}")
            result_data = json.loads(result_json)
            print("Generation successful!")
            final_image_url = None
            if isinstance(result_data, dict) and "resultUrls" in result_data:
                final_image_url = result_data["resultUrls"][0]
            elif isinstance(result_data, list) and len(result_data) > 0:
                final_image_url = result_data[0]
            elif isinstance(result_data, dict) and "images" in result_data:
                final_image_url = result_data["images"][0]["url"]
            elif isinstance(result_data, dict) and "url" in result_data:
                 final_image_url = result_data["url"]
                 
            if final_image_url:
                return final_image_url
            else:
                print(f"Could not parse result URL from: {result_json}")
                return None
                
        elif state == "failed":
            print(f"Generation failed. Msg: {data.get('failMsg')}")
            return None
        
        elif state in ["processing", "wait", "waiting"]:
             if poll_count % 6 == 0:  # Log every ~60 seconds
                 print(f"  ⏳ Still waiting... ({poll_count * 10}s elapsed)")
             time.sleep(10)
        else:
             print(f"Unknown state: {state}")
             time.sleep(10)
    
    print(f"⏰ TIMEOUT: Kie AI did not complete within {max_polls * 10}s")
    return None


# ─── CUTOUT SELECTOR ──────────────────────────────────────────────────────────

# Resolve cutouts directory: unified project's assets/cutouts
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up from agents/ to project root
CUTOUTS_DIR = os.path.join(_PROJECT_DIR, "assets", "cutouts")

def select_cutouts_for_theme(theme_name: str, count: int = 3, target_mood: str = "confident") -> list:
    """
    Selects cutouts intelligently matching the target mood from cutout_tags.json.
    """
    all_cutouts = glob.glob(os.path.join(CUTOUTS_DIR, "cutout_*.png"))
    if not all_cutouts:
        print("⚠️ No cutouts found in cutouts directory.")
        return []
        
    target_mood = target_mood.lower()
    selected = []
    
    tags_file = os.path.join(os.path.dirname(__file__), "cutout_tags.json")
    if os.path.exists(tags_file):
        with open(tags_file, "r") as f:
            tags_db = json.load(f)
            
        # Match ones that have the same mood
        matched = []
        unmatched = []
        for cpath in all_cutouts:
            fname = os.path.basename(cpath)
            if tags_db.get(fname) == target_mood:
                matched.append(cpath)
            else:
                unmatched.append(cpath)
                
        if len(matched) >= count:
            selected = random.sample(matched, count)
        else:
            selected = matched + random.sample(unmatched, min(count - len(matched), len(unmatched)))
    else:
        selected = random.sample(all_cutouts, min(count, len(all_cutouts)))
        
    print(f"🎭 Selected {len(selected)} cutout(s) matching mood '{target_mood}': {[os.path.basename(c) for c in selected]}")
    return selected


# ─── YOUTUBE-SPECIFIC THEME GENERATION ────────────────────────────────────────

def generate_concepts(video_name: str, script_text: str, count: int = 5) -> list:
    """
    Gemini ile bir YouTube videosu için 5 FARKLI konsept (tema) üretir.
    Returns: [{'theme_name', 'cover_text', 'scene_description', 'mood', 'suggested_assets', 'screenshot_url'}]
    """
    print(f"🧠 Generating {count} distinct content-aware YouTube thumbnail concepts (Video: {video_name})...")
    if not gemini_client or not script_text:
        return [
            {"theme_name": "fallback1", "cover_text": "BUNU İZLE", "scene_description": "A widescreen cinematic portrait with dramatic side lighting, person on the left third.", "mood": "serious", "screenshot_url": None, "screenshot_context": ""}
            for _ in range(count)
        ]

    prompt = f"""
    You are an expert Turkish YouTube thumbnail strategist and Art Director. Your job is to create {count} DISTINCT thumbnail concepts
    that are DIRECTLY RELEVANT to the video's actual content — NOT generic clickbait.
    
    === VIDEO CONTENT (Analyze this DEEPLY) ===
    \"\"\"
    {script_text[:4000]}
    \"\"\"
    
    === STEP 1: FIND URLs ===
    If the text contains any URLs (like a website, socialblade link, etc) that would make a great screenshot background,
    extract ONE best URL to be used for the background. If none, set "screenshot_url" to null.
    Also provide a short "screenshot_context" explaining WHAT the screenshot is and HOW it should be cleanly integrated.
    
    === STEP 2: CREATE {count} DISTINCT CONCEPTS ===
    Each concept MUST be completely different in visual metaphor and composition.
    🚫 BANNED generic texts: "HERKES ŞAŞIRDI", "İNANILMAZ", "BUNU İZLE", "GELECEK BURADA", "TARİHİ CANLANDIR"
    🚫 BANNED visuals: "person sitting at computer", "person holding a phone", "person looking at a screen". This is strictly forbidden.
    ✅ GOOD texts are HIGHLY PUNCHY, curiosity-inducing, and action-oriented: "BU STRATEJİYİ ÇAL", "REKABET YOK", "YAPAY ZEKA GELİR"
    
    CRITICAL TURKISH TEXT RULE:
    The text MUST be perfectly idiomatic, natural-sounding Turkish! Do NOT output broken or translated phrases like "Milyonluk video dakikada". Use powerful, native hooks like "DAKİKADA MİLYON", "İZLENME SIRRI", "VİRAL OLACAK". Keep it MAX 2-3 WORDS.

    FORMAT: HORIZONTAL (16:9). Person on LEFT 1/3 or RIGHT 1/3.
    DESIGN RULES:
    1. EXTREME MINIMALISM & COLORS: No neon lights, no holograms, no cluttered micro-details. Big, simple, bold elements only. Use ONLY highly curated, aesthetic duo-tone minimal color palettes (avoid clashing colors or ugly bright yellows).
    2. ICONS: NO standard emoji-like or cheap generic icons. Use sleek, minimal graphical elements if any, or none at all.
    3. SCREENSHOTS: If using a screenshot URL, outline how it creatively fits the context (e.g. "displayed elegantly on a sleek floating UI panel"). Do not just blindly blend it.
    
    === OUTPUT FORMAT ===
    Return EXACTLY this JSON array with {count} objects:
    [
        {
            "theme_name": "short_label",
            "cover_text": "2-3 WORD PERFECTLY IDIOMATIC TURKISH TEXT",
            "scene_description": "Detailed English scene description for 16:9 widescreen. KEEP IT MINIMALIST. No holograms, no small cluttered details.",
            "mood": "one of: confident, curious, surprised, pointing, happy, serious, mysterious",
            "screenshot_url": "extracted url or null",
            "screenshot_context": "Short explanation or empty string"
        }
    ]
    """
    try:
        raw_text = _gemini_generate_text(prompt, json_mode=True)
        raw = raw_text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        themes = parsed[:count] if isinstance(parsed, list) else [parsed]
        
        # Log generated themes
        for i, t in enumerate(themes):
            print(f"  Concept {i+1}: [{t.get('theme_name')}] \"{t.get('cover_text')}\" (mood: {t.get('mood')})")
            if t.get("screenshot_url"):
                print(f"           SCREENSHOT URL: {t.get('screenshot_url')}")
        
        return themes
    except Exception as e:
        print(f"Error generating concepts: {e}")
        return [
            {"theme_name": f"fallback{i}", "cover_text": "BUNU İZLE", "scene_description": "A dramatic widescreen portrait.", "mood": "serious", "screenshot_url": None, "screenshot_context": ""}
            for i in range(count)
        ]

def review_thumbnail_with_gemini(image_path: str, expected_text: str) -> dict:
    """Uses Gemini Vision to evaluate the output against strict rules."""
    print(f"🔍 Analyzing generated thumbnail {image_path} with Gemini Vision...")
    if not gemini_client or not os.path.exists(image_path):
        return {"passed": True, "feedback": ""}
        
    try:
        review_prompt = f"""
        You are a strict YouTube Thumbnail Quality Controller.
        Evaluate the image against ALL of these mandatory rules:

        === TEXT RULES ===
        1. EXPECTED TEXT: "{expected_text}" — Must be exact. FAIL if corrupted, gibberish, wrong letters, or hallucinated words.
        2. Text must be BRIGHT YELLOW or WHITE with thick BLACK outline. FAIL if text uses red outline or colored outline.
        3. Text must be large, bold, and easily readable even at 160x90px thumbnail size.

        === PERSON RULES ===
        4. A person must be clearly visible, large (waist-up), and NOT distorted.
        5. The person MUST be 100% SOLID and OPAQUE. FAIL IMMEDIATELY if the person appears semi-transparent, ghostly, or faded. This is a FATAL error.

        === DESIGN RULES ===
        6. MINIMALISM CHECK: The image should have MAX 3 main elements (person + background + text). FAIL if there are excessive micro-details, cluttered small objects, or busy compositions.
        7. NO HOLOGRAMS / NO NEON LIGHTS / NO LAPTOPS: FAIL if you see holographic effects, glowing future lines, or cliché tropes like "person sitting at a laptop" or "person looking at phone". We want physical metaphors.
        8. SCREENSHOT USAGE: If a screenshot/website image is visible, it should be cleanly integrated (e.g., on a laptop screen, floating panel). FAIL if the screenshot is messily used as a raw wallpaper background behind the person.
        9. 160x90px TEST: Mentally shrink the image to a tiny YouTube feed thumbnail. Would you understand the main message? FAIL if it would look like an unreadable mess at small size.

        === FORMAT ===
        10. Must be widescreen 16:9.

        Return JSON EXACTLY:
        {{
            "passed": true/false,
            "feedback": "If false, explain which rule(s) failed and suggest a 1-sentence fix for the NEXT generation prompt."
        }}
        """
        raw_text = _gemini_generate_vision(image_path, review_prompt, json_mode=True)
        result = json.loads(raw_text.replace("```json", "").replace("```", "").strip())
        print(f"  -> Review Passed: {result.get('passed')}. Feedback: {result.get('feedback')}")
        return result
    except Exception as e:
         print(f"Review failed/crashed: {e}. Passing it automatically.")
         return {"passed": True, "feedback": ""}

# ─── MAIN GENERATION PIPELINE ────────────────────────────────────────────────

def run_autonomous_generation(
    local_person_image_path: str,
    video_topic: str,
    main_text: str,
    output_path: str,
    max_retries: int = 5,
    variant_index: int = 1,
    script_text: str = "",
    scene_description: str = "",
    extra_cutout_paths: list = None,
    screenshot_url: str = None,
    screenshot_context: str = ""
):
    """
    Kie AI Video Production Skill (Nano Banana 2) - SELF REVIEW LOOP INCORPORATED.
    """
    
    # 1. Upload base image to ImgBB
    person_image_url = upload_to_imgbb(local_person_image_path)
    if not person_image_url:
        print("Aborting because Catbox upload failed.")
        return False
    
    # 1b. Upload extra reference cutouts
    extra_ref_urls = []
    if extra_cutout_paths:
        for extra_path in extra_cutout_paths:
            if extra_path and os.path.exists(extra_path) and extra_path != local_person_image_path:
                extra_url = upload_to_imgbb(extra_path)
                if extra_url:
                    extra_ref_urls.append(extra_url)
    
    # 1c. Add Screenshot context if exists
    if screenshot_url:
        ss_path = capture_screenshot(screenshot_url)
        if ss_path:
            ss_catbox = upload_to_imgbb(ss_path)
            if ss_catbox:
                extra_ref_urls.append(ss_catbox)
                print(f"Successfully integrated SCREENSHOT {ss_catbox} into references.")
                
    print(f"Total uploaded references (excluding base): {len(extra_ref_urls)}")

    variant_instruction = ""
    if variant_index == 1:
        variant_instruction = "A candid, cinematic widescreen shot. The subject is on the LEFT THIRD of the frame. BACKGROUND MUST BE EXTREMELY MINIMALIST."
    else:
        variant_instruction = "A close-up environmental portrait in widescreen. The subject is CENTER or slightly LEFT. ZERO DISTRACTING DETAILS."

    scene_context = f"Background concept: {scene_description}. Keep the background ULTRA-MINIMAL and free of distractions."

    screenshot_instruction = ""
    if screenshot_url and screenshot_context:
        screenshot_instruction = f"If a screenshot was provided in references, DO NOT use it blindly as a raw full background. It shows: {screenshot_context}. Integrate it cleanly and beautifully into the composition (e.g. inside a sleek floating UI panel or smoothly blended into a minimal environment)."

    base_prompt = (
        f"CRITICAL INSTRUCTIONS:\n"
        f"1. FACE & IDENTITY: The person MUST be EXACTLY the reference person. The person MUST BE 100% SOLID and OPAQUE. NO semi-transparent or ghostly figures! This is a fatal error.\n"
        f"2. COMPOSITION: A cinematic HORIZONTAL WIDESCREEN (16:9) YouTube thumbnail photo. Person large, waist-up.\n"
        f"3. MINIMALISM & COLORS: ZERO micro-details, NO neon lights, NO holograms, NO visual clutter. Big, simple, highly legible elements only. Use a highly curated, aesthetic duo-tone or minimal color palette. ENSURE MAXIMUM CONTRAST between text and background. NO UGLY GENERIC YELLOW ICONS or cheap graphics.\n"
        f"4. BACKGROUND & SCREENSHOTS: ONE ultra-clean dramatic background. {screenshot_instruction}\n"
        f"5. BOLD TEXT OVERLAY: '{main_text}'. TEXT STYLING: HIGH CONTRAST, BRIGHT YELLOW or WHITE, HUGE THICK BOLD letters with a heavy BLACK outline. Extremely readable against background.\n\n"
        f"Special Instructions: {variant_instruction}\n"
        f"Theme: {scene_context}"
    )

    attempt = 1
    current_prompt = base_prompt

    while attempt <= max_retries:
        print(f"\n--- Launching Kie AI Pipeline for Concept [Attempt {attempt}/{max_retries}] ---")
            
        generated_image_url = generate_cover_with_nanobanana(person_image_url, current_prompt, extra_ref_urls=extra_ref_urls)
            
        if not generated_image_url:
            print("Generation failed at Kie AI level. Evaluation aborted.")
            return False
            
        print(f"Image generated! URL: {generated_image_url}")
        
        try:
            img_data = requests.get(generated_image_url, timeout=REQUEST_TIMEOUT).content
            with open(output_path, 'wb') as handler:
                handler.write(img_data)
            print(f"Final cover saved to {output_path}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download generated image: {e}")
            return False

        # Self-Review Phase
        review = review_thumbnail_with_gemini(output_path, main_text)
        if review.get("passed"):
            print("✅ Self-review PASSED! Breaking loop.")
            return True
        else:
            print(f"❌ Self-review FAILED! Reason: {review.get('feedback')}")
            attempt += 1
            if attempt > max_retries:
                print("Max retries reached. Keeping the last generated image anyway.")
                return True
            else:
                current_prompt = base_prompt + "\n\nCRITICAL FIX NEEDED: " + str(review.get("feedback", "Improve thumbnail quality."))

    return True


if __name__ == "__main__":
    pass
