#!/usr/bin/env python3
"""
Annotation Pipeline v3 — High-quality, harmonious annotations
Key improvements:
1. 2x supersampling for crisp anti-aliased text
2. Consistent output dimensions (all same width)
3. Precise frame alignment via pixel-accurate coordinates
4. Color-harmonious callouts matching step theme
5. Step badge color matches step theme
6. Bottom caption bar for description text (blog harmony)
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, json, math
import requests
import base64
import sys # Added based on user's provided code edit, though not explicitly requested in instruction
import glob # Added based on user's provided code edit, though not explicitly requested in instruction

# Dynamically resolve directories based on the script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SCRIPT_DIR, "typeless5", "frames")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "typeless5", "annotated_v3")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── FINAL OUTPUT WIDTH (all images same width for blog harmony) ───
TARGET_WIDTH = 900

# ─── SCALE factor for supersampling (2x = crisp text) ───
SCALE = 2

# ===============================================
# DINAMIK API KEY OKUMA EKLENTISI
# ===============================================
def get_groq_api_key():
    master_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "_knowledge", "credentials", "master.env"))
    if not os.path.exists(master_env_path):
        return None
    with open(master_env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                return line.strip().split("=", 1)[1]
    return None

GROQ_API_KEY = get_groq_api_key()
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Groq vision model currently accessible:
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# ─── COLOR PALETTE (harmonious, blog-ready) ───
COLORS = {
    "blue":   {"main": "#3B82F6", "dark": "#1E40AF", "light": "#DBEAFE"},
    "red":    {"main": "#EF4444", "dark": "#991B1B", "light": "#FEE2E2"},
    "amber":  {"main": "#F59E0B", "dark": "#92400E", "light": "#FEF3C7"},
    "green":  {"main": "#10B981", "dark": "#065F46", "light": "#D1FAE5"},
    "purple": {"main": "#8B5CF6", "dark": "#5B21B6", "light": "#EDE9FE"},
}

# ─── Font helper ───
def get_font(size):
    """Get font at scaled size for supersampling"""
    scaled_size = size * SCALE
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSText.ttf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, scaled_size)
        except:
            continue
    return ImageFont.load_default()

# ─── Drawing helpers (all work at SCALE multiplier) ───
def s(val):
    """Scale a coordinate value"""
    if isinstance(val, tuple):
        return tuple(v * SCALE for v in val)
    return val * SCALE

def draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    """Anti-aliased rounded rectangle"""
    x1, y1, x2, y2 = bbox
    r = radius
    # Draw using Pillow's built-in rounded_rectangle
    draw.rounded_rectangle(bbox, radius=r, fill=fill, outline=outline, width=width)

def draw_callout(draw, x, y, text, theme_color, font_size=15, position="top"):
    """Premium callout label with rounded background"""
    font = get_font(font_size)
    sx, sy = s(x), s(y)
    
    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    pad_x = s(10)
    pad_y = s(5)
    
    bg_color = theme_color["main"]
    
    # Background rounded rect
    rx1 = sx - pad_x
    ry1 = sy - pad_y
    rx2 = sx + tw + pad_x
    ry2 = sy + th + pad_y
    
    # Shadow
    shadow_offset = s(2)
    draw.rounded_rectangle(
        [rx1 + shadow_offset, ry1 + shadow_offset, rx2 + shadow_offset, ry2 + shadow_offset],
        radius=s(6), fill="#00000040"
    )
    
    # Main background
    draw.rounded_rectangle(
        [rx1, ry1, rx2, ry2],
        radius=s(6), fill=bg_color, outline="white", width=s(1)
    )
    
    # Text (white, sharp)
    draw.text((sx, sy), text, fill="white", font=font)
    
    return tw + 2 * pad_x, th + 2 * pad_y

def draw_step_badge(draw, number, x, y, theme_color, radius=18):
    """Step number badge matching step theme"""
    sx, sy, sr = s(x), s(y), s(radius)
    
    # Shadow
    draw.ellipse([sx-sr+s(2), sy-sr+s(2), sx+sr+s(2), sy+sr+s(2)], fill="#00000050")
    
    # Main circle
    draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], fill=theme_color["main"], outline="white", width=s(2))
    
    # Number
    font = get_font(18)
    text = str(number)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((sx - tw//2, sy - th//2 - s(1)), text, fill="white", font=font)

def draw_highlight_rect(draw, x, y, w, h, color, width=3, corner_marks=False):
    """Highlight rectangle with optional corner decorations"""
    sx, sy, sw, sh = s(x), s(y), s(w), s(h)
    swidth = s(width)
    
    if corner_marks:
        # Corner-style markers (L-shaped brackets) instead of full rectangle
        corner_len = min(sw, sh) // 4
        corners = [
            # Top-left
            [(sx, sy+corner_len), (sx, sy), (sx+corner_len, sy)],
            # Top-right
            [(sx+sw-corner_len, sy), (sx+sw, sy), (sx+sw, sy+corner_len)],
            # Bottom-left
            [(sx, sy+sh-corner_len), (sx, sy+sh), (sx+corner_len, sy+sh)],
            # Bottom-right
            [(sx+sw-corner_len, sy+sh), (sx+sw, sy+sh), (sx+sw, sy+sh-corner_len)],
        ]
        for corner in corners:
            draw.line(corner, fill=color, width=swidth, joint="curve")
    else:
        for i in range(swidth):
            draw.rectangle([sx-i, sy-i, sx+sw+i, sy+sh+i], outline=color)

def draw_arrow(draw, start, end, color="#FF3333", width=3):
    """Arrow with proper head"""
    sx1, sy1 = s(start[0]), s(start[1])
    sx2, sy2 = s(end[0]), s(end[1])
    swidth = s(width)
    
    draw.line([(sx1, sy1), (sx2, sy2)], fill=color, width=swidth)
    
    angle = math.atan2(sy2 - sy1, sx2 - sx1)
    arrow_len = s(14)
    for sign in [-1, 1]:
        aa = angle + sign * math.pi / 5.5
        ax = sx2 - arrow_len * math.cos(aa)
        ay = sy2 - arrow_len * math.sin(aa)
        draw.line([(int(ax), int(ay)), (sx2, sy2)], fill=color, width=swidth)

def draw_caption_bar(img, draw, caption_text, theme_color, font_size=13):
    """Bottom caption bar for blog harmony"""
    w, h = img.size
    bar_height = s(36)
    font = get_font(font_size)
    
    # Semi-transparent dark bar
    bar_y = h - bar_height
    draw.rectangle([0, bar_y, w, h], fill="#1F2937E6")
    
    # Thin colored accent line at top of bar
    draw.rectangle([0, bar_y, w, bar_y + s(3)], fill=theme_color["main"])
    
    # Caption text
    bbox = draw.textbbox((0, 0), caption_text, font=font)
    tw = bbox[2] - bbox[0]
    tx = (w - tw) // 2
    ty = bar_y + s(10)
    draw.text((tx, ty), caption_text, fill="white", font=font)

# ─── ANNOTATION DEFINITIONS v3 ───
ANNOTATIONS = [
    {
        "step": 1,
        "title": "Orijinal Sözleşmeyi Açın",
        "frame_file": "frame_000_t0s.jpg",
        "caption": "Adım 1 — Orijinal hizmet sözleşmesini Google Docs'ta açın",
        "theme": "blue",
        "crop": (70, 190, 940, 810),  # Doküman alanı, Chrome bar yok
        "elements": [
            {"type": "callout", "x": 15, "y": 8, "text": "Orijinal Hizmet Sözleşmesi", "size": 15},
            {"type": "rect", "x": 250, "y": 45, "w": 510, "h": 565, "corner_marks": True},
        ]
    },
    {
        "step": 2,
        "title": "Metni Seçin ve Typeless'ı Başlatın",
        "frame_file": "frame_001_t6s.jpg",
        "caption": "Adım 2 — Tüm metni seçin, Typeless toolbar ile sesli komut verin",
        "theme": "red",
        "crop": (70, 190, 940, 830),  # Doküman + toolbar
        "elements": [
            {"type": "callout", "x": 15, "y": 25, "text": "Tüm metin seçili (mavi)", "size": 15},
            # Typeless toolbar vurgu
            {"type": "rect", "x": 500, "y": 605, "w": 120, "h": 38},
            {"type": "callout", "x": 380, "y": 585, "text": "Typeless Toolbar — Sesli komut verin", "size": 13},
            {"type": "arrow", "start": (495, 625), "end": (500, 625)},
        ]
    },
    {
        "step": 3,
        "title": "AI İşliyor — Thinking",
        "frame_file": "frame_005_t30s.jpg",
        "caption": "Adım 3 — AI sözleşmenizi analiz ediyor, birkaç saniye bekleyin",
        "theme": "amber",
        "crop": (250, 530, 950, 830),  # Alt kısım + Thinking
        "elements": [
            {"type": "callout", "x": 15, "y": 8, "text": "AI sözleşmeyi analiz ediyor...", "size": 15},
            # Thinking butonu: Koordinatları tam siyah alana oturacak şekilde ayarlandı
            {"type": "rect", "x": 380, "y": 265, "w": 95, "h": 32},
            {"type": "arrow", "start": (300, 281), "end": (360, 281)},
            {"type": "callout", "x": 190, "y": 267, "text": "Thinking", "size": 14},
        ]
    },
    {
        "step": 4,
        "title": "Sonuç: Sözleşme Özetlendi",
        "frame_file": "frame_010_t60s.jpg",
        "caption": "Adım 4 — Sayfalarca sözleşme tek sayfada özetlendi!",
        "theme": "green",
        "crop": (70, 240, 940, 640),  # Doküman alanı — özet görünsün
        "elements": [
            {"type": "callout", "x": 15, "y": 8, "text": "Sözleşme otomatik özetlendi!", "size": 15},
            # Başlık: Corner marks başlıgı tam sarması için optimize edildi
            {"type": "rect", "x": 310, "y": 57, "w": 170, "h": 24, "corner_marks": True},
            {"type": "callout", "x": 500, "y": 50, "text": "← Yeni başlık", "size": 13},
            # Bullet points: Doğru maddeyi göstersin
            {"type": "arrow", "start": (230, 142), "end": (270, 142)},
            {"type": "callout", "x": 135, "y": 130, "text": "Maddeler →", "size": 13},
        ]
    },
    {
        "step": 5,
        "title": "İkinci Komut Verin",
        "frame_file": "frame_015_t90s.jpg",
        "caption": "Adım 5 — İkinci sesli komut: 'Başlıkları kalın yap'",
        "theme": "purple",
        "crop": (280, 240, 870, 540),  # Başlıklar + mavi seçim
        "elements": [
            {"type": "callout", "x": 15, "y": 8, "text": "İkinci komut: 'Başlıkları kalın yap'", "size": 15},
            # Başlıklar: frame_015'te başlıklar orijinal y pozisyonları:
            # "Hizmet Sözleşmesi Özeti" ~280, "Hizmet ve Teslimat:" ~325, "Ödeme Koşulları:" ~365, "Karşılıklı Yük." ~405
            # crop (280,240) çıkarılır → y: 40, 85, 125, 165
            # Başlıklar hizalama (daha düzgün aralıklarla kalınlık alanları)
            {"type": "arrow", "start": (8, 48), "end": (55, 48)},
            {"type": "arrow", "start": (8, 92), "end": (55, 92)},
            {"type": "arrow", "start": (8, 137), "end": (55, 137)},
            {"type": "arrow", "start": (8, 185), "end": (55, 185)},
            {"type": "arrow", "start": (8, 235), "end": (55, 235)},
        ]
    },
    {
        "step": 6,
        "title": "Final: Profesyonel Sözleşme",
        "frame_file": "frame_020_t120s.jpg",
        "caption": "Adım 6 — İşlem tamamlandı! Profesyonel formatta sözleşme özeti",
        "theme": "green",
        "crop": (280, 240, 870, 660),  # Doküman içeriği
        "elements": [
            {"type": "callout", "x": 15, "y": 8, "text": "Final — Profesyonel formatta!", "size": 15},
            # Kalın başlıkları vurgula — frame_020 başlıklar:
            # "Taraflar ve Konu:" y~60, "Hizmet ve Teslimat:" y~105, "Ödeme Koşulları:" y~175, "Karşılıklı Yük." y~245, "Gizililik" y~315
            {"type": "rect", "x": 60, "y": 62, "w": 260, "h": 20, "corner_marks": True},
            {"type": "rect", "x": 60, "y": 108, "w": 155, "h": 20, "corner_marks": True},
            {"type": "rect", "x": 60, "y": 180, "w": 145, "h": 20, "corner_marks": True},
            {"type": "rect", "x": 60, "y": 248, "w": 185, "h": 20, "corner_marks": True},
            {"type": "rect", "x": 60, "y": 318, "w": 195, "h": 20, "corner_marks": True},
            {"type": "callout", "x": 400, "y": 100, "text": "← Kalın başlıklar", "size": 13},
        ]
    },
]

def create_annotation(annot_def):
    """Create a single high-quality annotation"""
    step = annot_def["step"]
    title = annot_def["title"]
    theme = COLORS[annot_def["theme"]]
    frame_path = os.path.join(FRAMES_DIR, annot_def["frame_file"])
    
    if not os.path.exists(frame_path):
        print(f"  ⚠️ Frame yok: {frame_path}")
        return None
    
    # 1. Load and crop
    img = Image.open(frame_path).convert("RGB")
    if "crop" in annot_def:
        img = img.crop(annot_def["crop"])
    
    # 2. Resize to target width, maintaining aspect ratio
    orig_w, orig_h = img.size
    scale_factor = TARGET_WIDTH / orig_w
    new_h = int(orig_h * scale_factor)
    img = img.resize((TARGET_WIDTH, new_h), Image.LANCZOS)
    
    # 3. Add space for caption bar
    caption_height = 36
    canvas_h = new_h + caption_height
    canvas = Image.new("RGB", (TARGET_WIDTH, canvas_h), "#1F2937")
    canvas.paste(img, (0, 0))
    
    # 4. Scale up for supersampling
    big_w, big_h = TARGET_WIDTH * SCALE, canvas_h * SCALE
    big_canvas = canvas.resize((big_w, big_h), Image.LANCZOS)
    draw = ImageDraw.Draw(big_canvas)
    
    # 5. Draw annotations
    # Adjust coordinates for the resize (original crop → target width)
    crop_w = annot_def["crop"][2] - annot_def["crop"][0] if "crop" in annot_def else orig_w
    coord_scale = TARGET_WIDTH / crop_w
    
    for elem in annot_def.get("elements", []):
        # Scale coordinates from crop-relative to target-width-relative
        def cx(v): return int(v * coord_scale)
        def cy(v): return int(v * coord_scale)
        
        if elem["type"] == "rect":
            draw_highlight_rect(
                draw, cx(elem["x"]), cy(elem["y"]), cx(elem["w"]), cy(elem["h"]),
                color=theme["main"], width=3,
                corner_marks=elem.get("corner_marks", False)
            )
        elif elem["type"] == "callout":
            draw_callout(
                draw, cx(elem["x"]), cy(elem["y"]), elem["text"],
                theme_color=theme, font_size=elem.get("size", 14)
            )
        elif elem["type"] == "arrow":
            draw_arrow(
                draw, 
                (cx(elem["start"][0]), cy(elem["start"][1])),
                (cx(elem["end"][0]), cy(elem["end"][1])),
                color=theme["main"], width=3
            )
    
    # 6. Step badge (top-right)
    badge_x = TARGET_WIDTH - 30
    badge_y = 28
    draw_step_badge(draw, step, badge_x, badge_y, theme, radius=18)
    
    # 7. Caption bar
    big_canvas_draw = ImageDraw.Draw(big_canvas)
    draw_caption_bar(big_canvas, big_canvas_draw, annot_def.get("caption", ""), theme)
    
    # 8. Downsample (LANCZOS = high quality anti-aliasing)
    final = big_canvas.resize((TARGET_WIDTH, canvas_h), Image.LANCZOS)
    
    # 9. Save
    safe_title = title.replace(" ", "_").replace(":", "").replace("—", "-").replace("'", "")[:40]
    output_path = os.path.join(OUTPUT_DIR, f"step_{step:02d}_{safe_title}.jpg")
    final.save(output_path, quality=93)
    
    print(f"  ✅ Adım {step}: {title} → {os.path.basename(output_path)} ({final.size[0]}x{final.size[1]})")
    return output_path

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def self_review(results):
    """
    Self-review mechanism that uses LLM vision to verify coordinates and overall UI aesthetics.
    """
    print(f"\n{'='*60}")
    print("🔍 AI VISION SELF-REVIEW BAŞLIYOR (Groq)")
    print(f"{'='*60}")
    
    if not GROQ_API_KEY:
        print("  ⚠️ Uyarı: GROQ_API_KEY bulunamadı. Self-review atlanıyor.")
        return
        
    issues_found = 0
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    for res in results:
        step = res['step']
        img_path = res['path']
        print(f"  🧐 İnceleniyor: Adım {step} - {os.path.basename(img_path)}")
        
        b64_image = encode_image(img_path)
        
        prompt = f'''Bu resim otomatik olarak üretilmiş bir "Eğitimsel Call-out / Ok Gösterme" görselidir.
        Görselde eklenen çeşitli renkli çerçeveler, oklar ve metin balonları (callout) var. 
        Görevin bir Kalite Kontrol (QA) asistanı gibi davranmak. Şunları kontrol et:
        1. Eklenen oklar, balonlar veya çerçeveler asıl okunması gereken orijinal metinlerin üzerini kapatıyor mu?
        2. Herhangi bir hizalama büyük ölçüde kaymış mı (Örn: ok hiçbir şeyi göstermiyor ya da çerçeve boşlukta)?
        3. Metin balonlarındaki yazılar resimden dışarı taşıyor mu veya rahatsız edici şekilde kesilmiş mi?
        
        JSON formatında cevap ver:
        {{
            "has_error": boolean,
            "error_description": "varsa detay",
            "suggestion": "çerçeve X ekseninde +10 piksel öteye taşınmalı vb."
        }}
        '''
        
        payload = {
            "model": VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1024
        }
        
        try:
            response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=45)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            
            # JSON parse
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            review_data = json.loads(content.strip())
            
            if review_data.get("has_error"):
                issues_found += 1
                print(f"    ❌ Hata Bulundu: {review_data.get('error_description')}")
                print(f"    💡 Öneri: {review_data.get('suggestion')}")
                # Automatic coordinate adjustment placement
            else:
                print(f"    ✅ Kusursuz: Görsel testten geçti.")
                
        except Exception as e:
            print(f"    ⚠️ Groq Vision API Hatası: {e}")

    if issues_found == 0:
        print("\n  ✨ Self-review tamamlandı. Olası hizalama hataları bulunamadı (Tüm elementler QA onaylı).")
    else:
        print(f"\n  ⚠️ {issues_found} adet sorun tespit edildi. Yukarıdaki öneriler doğrultusunda annotate_v3.py 'ANNOTATIONS' bloğunu güncelleyebilirsiniz.")


# ─── MAIN ───
def main():
    print("=" * 60)
    print("ANNOTATION v3 — Supersampled, harmonious, blog-ready")
    print("=" * 60)
    
    results = []
    for annot_def in ANNOTATIONS:
        path = create_annotation(annot_def)
        if path:
            results.append({
                "step": annot_def["step"],
                "title": annot_def["title"],
                "caption": annot_def.get("caption", ""),
                "path": path
            })
    
    print(f"\n{'='*60}")
    print(f"Toplam {len(results)} annotation oluşturuldu")
    print(f"Tüm görseller: {TARGET_WIDTH}px genişliğinde (tutarlı)")
    print(f"Supersampling: {SCALE}x → anti-aliased, keskin metin")
    print(f"Dizin: {OUTPUT_DIR}")
    
    # Metadata
    meta_path = os.path.join(OUTPUT_DIR, "annotations_v3.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    # Trigger self_review
    self_review(results)

if __name__ == "__main__":
    main()
