#!/usr/bin/env python3
"""
Blog Generator Pipeline — Step 3: Write Blog
1. Reads annotated frames data from annotate_v3.py (annotations_v3.json)
2. Uses Gemini 2.5 Flash to generate a high-quality blog article
3. Saves the output to blog_draft.md
"""
import json
import os
import sys
import requests

# ─── Config ───
def get_gemini_api_key():
    master_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "_knowledge", "credentials", "master.env"))
    if not os.path.exists(master_env_path):
        return None
    with open(master_env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                return line.strip().split("=", 1)[1]
    return None

GEMINI_API_KEY = get_gemini_api_key()
if not GEMINI_API_KEY:
    print("HATA: GEMINI_API_KEY master.env dosyasında bulunamadı!")
    sys.exit(1)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

VIDEO_DIR = sys.argv[1] if len(sys.argv) > 1 else "./Projeler/Blog_Yazici/typeless5"
OUTPUT_DIR = VIDEO_DIR
ANNOTATIONS_JSON = os.path.join(VIDEO_DIR, "annotated_v3", "annotations_v3.json")

SCRIPT_TEXT = """
Sekreterinizi kovabilirsiniz.
Avukatların en büyük derdi: çözüldü.
Sayfalarca sözleşmeleri artık 4 kat daha hızlı düzenleyebilirsin.
Çünkü en çok zaman alan şey 'yazmak' değil… aynı şeyi tekrar tekrar düzeltmek.
Değiştirmek istediğim alanı seçiyorum ve komutu veriyorum.
"Bunu daha kısa yaz"
"Karşılıklı yükümlülük yap"
"Başlıkları kalın yap"
CLOSING: hemen denemen için yoruma LİNK yaz gönderiyim.
"""

def generate_blog(annotations_data, script_text):
    """Gemini 2.5 Flash ile blog taslağı üret"""
    print(f"\n{'='*50}")
    print(f"ADIM 2/3: Blog Yazımı (Gemini 2.5 Flash)")
    
    # Adım listesini oluştur (annotate_v3'ten gelen verileri kullanarak)
    steps_description = "\n".join([
        f"Adım {a['step']}: {a['title']}\n  Görsel açıklama: {a['caption']}"
        for a in annotations_data
    ])
    
    prompt = f"""Sen site.com'nin kurucusu KULLANICI_ADI_BURAYA'in blog yazılarını yazan bir teknoloji blog yazarısın. KULLANICI_ADI_BURAYA, yapay zeka araçlarını tanıtan Türkiye'nin en büyük Instagram sayfalarından birini yönetiyor.

Aşağıda bir Instagram Reels videosunun scripti ve ekran görüntülerinin adım adım analizi var. Bunlardan profesyonel bir blog yazısı yaz.

## Instagram Script (Orijinal)
{script_text}

## Ekran Görüntüsü Adımları
{steps_description}

## Blog Yazısı Kuralları
1. SEO uyumlu başlık olsun (H1)
2. Blog girişinde aracı tanıt ve neden önemli olduğunu açıkla
3. "Adım adım rehber" formatı kullan — her adımda H2 başlığı
4. Her adımda "[Görsel X]" şeklinde görsel referansı ver — bu görseller sonra otomatik yerleştirilecek
5. Ses tonu: samimi, bilgili, heyecanlı ama profesyonel (AI tarafından yazıldığı belli olmasın)
6. Typeless'ın ne olduğunu, kimlere hitap ettiğini detaylıca anlat
7. Paragraflar kısa olsun (2-3 cümle max)
8. Blog sonunda "Sonuç" bölümü ekle
9. 1000-1500 kelime arası
10. Türkçe yaz
11. Meta description öner (160 karakter)
12. 5-7 adet SEO keyword öner

SADECE blog yazısını ver, başka bir şey ekleme. Markdown formatında yaz."""

    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4000
        }
    }
    
    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        blog_text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # Token kullanımı
        usage = result.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)
        
        print(f"  Tokens — Input: {input_tokens}, Output: {output_tokens}")
        print(f"  Maliyet — ~${input_tokens * 0.30 / 1_000_000 + output_tokens * 2.50 / 1_000_000:.4f}")
        print(f"  Blog uzunluğu: {len(blog_text)} karakter, ~{len(blog_text.split())} kelime")
        
        return blog_text, usage
    
    except Exception as e:
        print(f"  ❌ Gemini hatası: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text[:500]}")
        return None, {}

def save_output(blog_text, output_dir):
    """Blog'u kaydet"""
    print(f"\n{'='*50}")
    print(f"ADIM 3/3: Çıktı Kaydediliyor")
    
    blog_path = os.path.join(output_dir, "blog_draft.md")
    with open(blog_path, "w", encoding="utf-8") as f:
        f.write(blog_text)
    print(f"  Blog draft: {blog_path}")
    
    return blog_path

def main():
    if not os.path.exists(ANNOTATIONS_JSON):
        print(f"❌ HATA: Annotation JSON dosyası bulunamadı ({ANNOTATIONS_JSON}). Lütfen önce annotate_v3.py'yi çalıştırın.")
        sys.exit(1)
        
    with open(ANNOTATIONS_JSON, "r", encoding="utf-8") as f:
        annotations_data = json.load(f)
    print(f"Adım 1/3: {len(annotations_data)} adım annotation verisi yüklendi.")
    
    blog_text, usage = generate_blog(annotations_data, SCRIPT_TEXT)
    
    if blog_text:
        blog_path = save_output(blog_text, OUTPUT_DIR)
        
        print(f"\n{'='*50}")
        print(f"✅ PIPELINE TAMAMLANDI: Blog Metni Hazır")
        print(f"  Kaydedildi: {blog_path}")
    else:
        print("❌ Blog üretilemedi!")

if __name__ == "__main__":
    main()

