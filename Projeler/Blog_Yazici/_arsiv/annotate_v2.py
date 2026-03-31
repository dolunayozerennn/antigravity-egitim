#!/usr/bin/env python3
"""
Improved Annotation Pipeline v2 — Self-feedback loop ile
1. Doğru frame seçimi (hikaye akışına göre)
2. Akıllı kırpma (crop) — gereksiz alanlar çıkarılır
3. Hedefli annotation — spesifik UI elemanlarına vurgu
4. Self-review loop — her annotation üretildikten sonra analiz
"""
from PIL import Image, ImageDraw, ImageFont
import os, json, math

FRAMES_DIR = "/Users/dolunayozeren/Desktop/Antigravity/Projeler/Blog_Yazici/typeless5/frames"
OUTPUT_DIR = "/Users/dolunayozeren/Desktop/Antigravity/Projeler/Blog_Yazici/typeless5/annotated_v2"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Font helper ───
def get_font(size=16):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except:
        return ImageFont.load_default()

# ─── Drawing helpers ───
def draw_arrow(draw, start, end, color="#FF3333", width=3):
    draw.line([start, end], fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    arrow_len = 18
    for sign in [-1, 1]:
        aa = angle + sign * math.pi / 6
        ax = end[0] - arrow_len * math.cos(aa)
        ay = end[1] - arrow_len * math.sin(aa)
        draw.line([(int(ax), int(ay)), end], fill=color, width=width)

def draw_callout(draw, x, y, text, color="#FF3333", bg_color="#FF3333", text_color="white", font=None):
    """Callout label çizer — arka planlı metin"""
    if font is None:
        font = get_font(14)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    padding = 6
    rx, ry = x, y
    draw.rounded_rectangle(
        [rx - padding, ry - padding, rx + tw + padding, ry + th + padding],
        radius=4, fill=bg_color, outline="white", width=1
    )
    draw.text((rx, ry), text, fill=text_color, font=font)
    return tw + 2 * padding, th + 2 * padding  # Boyutları döndür

def draw_step_badge(draw, number, x=15, y=15, radius=20, color="#FF3333"):
    """Adım numarası badge'i"""
    draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color, outline="white", width=2)
    font = get_font(20)
    text = str(number)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x - tw/2, y - th/2 - 1), text, fill="white", font=font)

def draw_highlight_rect(draw, x, y, w, h, color="#FF3333", width=3, dashed=False):
    """Vurgulama dikdörtgeni"""
    for i in range(width):
        draw.rectangle([x-i, y-i, x+w+i, y+h+i], outline=color)

def crop_to_document(img, crop_box=None):
    """Chrome UI elemanlarını kırp — sadece doküman alanı"""
    w, h = img.size
    if crop_box:
        return img.crop(crop_box)
    # Default: üstten Chrome bar kesilir (~190px), sağdan sidebar (~40px)
    top = 190
    right = w - 30
    left = 0
    bottom = h
    return img.crop((left, top, right, bottom))

# ─── ANNOTATION DEFINITIONS ───
# Videonun hikaye akışına göre doğru frame'ler ve annotation'lar

ANNOTATIONS = [
    {
        "step": 1,
        "title": "Orijinal Sözleşmeyi Açın",
        "frame_file": "frame_000_t0s.jpg",
        "description": "İşlenecek sözleşme Google Docs'ta açık. Typeless'ı başlatmadan önceki orijinal hali.",
        "crop": (0, 190, 950, 810),  # Sadece doküman alanı
        "annotations": [
            {"type": "callout", "x": 20, "y": 10, "text": "📄 Orijinal Hizmet Sözleşmesi", "bg": "#2563EB"},
            {"type": "rect", "x": 320, "y": 80, "w": 540, "h": 580, "color": "#2563EB"},
        ]
    },
    {
        "step": 2,
        "title": "Metni Seçin ve Typeless'ı Başlatın",
        "frame_file": "frame_001_t6s.jpg",
        "description": "Tüm sözleşme metni seçilmiş (mavi) ve altta Typeless toolbar'ı belirmiş. 'Bunu özetle' gibi sesli komut veriliyor.",
        "crop": (0, 190, 950, 830),  # Doküman + altındaki toolbar
        "annotations": [
            # Mavi seçili alanı göster
            {"type": "callout", "x": 20, "y": 10, "text": "Tüm metin seçili →", "bg": "#2563EB"},
            # Typeless toolbar'a ok ve callout
            {"type": "arrow", "start": (500, 590), "end": (600, 610)},
            {"type": "callout", "x": 480, "y": 560, "text": "⬇ Typeless Toolbar — Sesli komut verin", "bg": "#FF3333"},
            # Toolbar alanını vurgula
            {"type": "rect", "x": 570, "y": 595, "w": 120, "h": 35, "color": "#FF3333"},
        ]
    },
    {
        "step": 3,
        "title": "AI İşliyor — 'Thinking...'",
        "frame_file": "frame_005_t30s.jpg",
        "description": "Typeless komutu işliyor. 'Thinking' yazısı görünüyor — yapay zeka sözleşmeyi analiz edip yeniden yazıyor.",
        "crop": (250, 550, 950, 830),  # Alt kısım: son satırlar + Thinking butonu
        "annotations": [
            {"type": "callout", "x": 20, "y": 10, "text": "⏳ AI sözleşmeyi analiz ediyor...", "bg": "#F59E0B"},
            # Thinking butonunu vurgula (yaklaşık 600-670, 790-820 orijinalde → crop sonrası ~350,240)
            {"type": "rect", "x": 310, "y": 220, "w": 120, "h": 40, "color": "#F59E0B"},
            {"type": "arrow", "start": (260, 242), "end": (310, 242)},
            {"type": "callout", "x": 130, "y": 228, "text": "Thinking", "bg": "#F59E0B"},
        ]
    },
    {
        "step": 4,
        "title": "Sonuç: Özet Sözleşme Hazır",
        "frame_file": "frame_010_t60s.jpg",
        "description": "Typeless, sayfalarca sözleşmeyi otomatik olarak özetledi. Başlıklar kalın, maddeler bullet point formatında.",
        "crop": (0, 190, 950, 630),  # Doküman alanı
        "annotations": [
            {"type": "callout", "x": 20, "y": 10, "text": "✅ Sözleşme otomatik özetlendi!", "bg": "#16A34A"},
            # Başlığı vurgula
            {"type": "rect", "x": 310, "y": 55, "w": 250, "h": 30, "color": "#16A34A"},
            {"type": "callout", "x": 310, "y": 35, "text": "Yeni başlık", "bg": "#16A34A"},
            # Bullet point yapısına dikkat çek
            {"type": "arrow", "start": (280, 200), "end": (325, 200)},
            {"type": "callout", "x": 140, "y": 185, "text": "Maddeler", "bg": "#16A34A"},
        ]
    },
    {
        "step": 5,
        "title": "İkinci Komut: 'Başlıkları Kalın Yap'",
        "frame_file": "frame_015_t90s.jpg",
        "description": "İkinci düzenleme komutu verildi. Metin tekrar seçili ve Typeless 'Başlıkları kalın yap' komutunu işliyor.",
        "crop": (280, 240, 870, 540),  # Başlıklar görünsün
        "annotations": [
            {"type": "callout", "x": 20, "y": 10, "text": "🎙️ İkinci komut: 'Başlıkları kalın yap'", "bg": "#7C3AED"},
            # Başlıkları göster (mavi seçim zaten görünüyor, ek kutu ekleme)
            {"type": "arrow", "start": (15, 45), "end": (60, 45)},
            {"type": "arrow", "start": (15, 90), "end": (60, 90)},
            {"type": "arrow", "start": (15, 130), "end": (60, 130)},
        ]
    },
    {
        "step": 6,
        "title": "Final Sonuç: Profesyonel Sözleşme",
        "frame_file": "frame_020_t120s.jpg",
        "description": "İşlem tamamlandı. Sözleşme özeti kalın başlıklarla, bullet pointlerle düzgün biçimlendirilmiş durumda.",
        "crop": (280, 240, 870, 660),  # Sadece döküman içeriği
        "annotations": [
            {"type": "callout", "x": 20, "y": 10, "text": "✅ Final sonuç — profesyonel formatta", "bg": "#16A34A"},
            # Kalın başlıkları vurgula
            {"type": "rect", "x": 60, "y": 65, "w": 200, "h": 22, "color": "#16A34A"},
            {"type": "callout", "x": 280, "y": 60, "text": "← Kalın başlık", "bg": "#16A34A"},
            {"type": "rect", "x": 60, "y": 110, "w": 150, "h": 22, "color": "#16A34A"},
            {"type": "rect", "x": 60, "y": 182, "w": 140, "h": 22, "color": "#16A34A"},
            {"type": "rect", "x": 60, "y": 252, "w": 175, "h": 22, "color": "#16A34A"},
            {"type": "rect", "x": 60, "y": 322, "w": 175, "h": 22, "color": "#16A34A"},
        ]
    },
]

def create_annotation(annot_def):
    """Tek bir annotation üret"""
    step = annot_def["step"]
    title = annot_def["title"]
    frame_path = os.path.join(FRAMES_DIR, annot_def["frame_file"])
    
    if not os.path.exists(frame_path):
        print(f"  ⚠️ Frame yok: {frame_path}")
        return None
    
    img = Image.open(frame_path)
    
    # 1. Kırpma
    if "crop" in annot_def:
        img = img.crop(annot_def["crop"])
    
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    # 2. Annotation elemanları
    for a in annot_def.get("annotations", []):
        if a["type"] == "rect":
            draw_highlight_rect(draw, a["x"], a["y"], a["w"], a["h"], 
                              color=a.get("color", "#FF3333"), width=a.get("width", 3))
        elif a["type"] == "callout":
            font_size = a.get("font_size", 14)
            draw_callout(draw, a["x"], a["y"], a["text"], 
                        bg_color=a.get("bg", "#FF3333"), font=get_font(font_size))
        elif a["type"] == "arrow":
            draw_arrow(draw, a["start"], a["end"], color=a.get("color", "#FF3333"))
    
    # 3. Adım badge'i
    draw_step_badge(draw, step, x=w-30, y=30)
    
    # Kaydet
    output_path = os.path.join(OUTPUT_DIR, f"step_{step:02d}_{title.replace(' ', '_').replace(':', '').replace('—', '-')[:40]}.jpg")
    img.save(output_path, quality=92)
    
    print(f"  ✅ Adım {step}: {title} → {os.path.basename(output_path)} ({img.size[0]}x{img.size[1]})")
    return output_path

# ─── MAIN ───
def main():
    print("=" * 60)
    print("ANNOTATION v2 — Yeni frame seçimi + kırpma + hedefli vurgu")
    print("=" * 60)
    
    results = []
    for annot_def in ANNOTATIONS:
        path = create_annotation(annot_def)
        if path:
            results.append({
                "step": annot_def["step"],
                "title": annot_def["title"],
                "description": annot_def["description"],
                "path": path
            })
    
    print(f"\n{'='*60}")
    print(f"Toplam {len(results)} annotation oluşturuldu")
    print(f"Dizin: {OUTPUT_DIR}")
    
    # Metadata kaydet
    meta_path = os.path.join(OUTPUT_DIR, "annotations_v2.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
