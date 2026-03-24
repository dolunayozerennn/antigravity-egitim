#!/usr/bin/env python3
"""
Vision Analyzer — Groq Llama 4 Scout ile frame analizi
5'erli batch'ler halinde gönderir, her frame için adım açıklaması ve annotation koordinatları alır.
"""
import base64
import json
import os
import sys
import time
import requests

from env_loader import require_env

GROQ_API_KEY = require_env("GROQ_API_KEY")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_IMAGES_PER_REQUEST = 5

def load_script(video_dir):
    """Video klasöründen script.txt oku. Yoksa None döndür."""
    script_path = os.path.join(video_dir, "script.txt")
    if os.path.exists(script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        print(f"  ✅ Script yüklendi: {script_path} ({len(text)} karakter)")
        return text
    else:
        print(f"  ⚠️  UYARI: script.txt bulunamadı ({script_path}). Scriptsiz devam edilecek.")
        print(f"  ℹ️  İpucu: Daha kaliteli analiz için video klasörüne script.txt ekleyin.")
        return None

def encode_image(image_path):
    """Resmi base64'e encode et"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def analyze_batch(frames_batch, batch_idx, total_batches, script_text=None):
    """5'erli batch analizi"""
    print(f"\n--- Batch {batch_idx+1}/{total_batches} ({len(frames_batch)} frame) ---")
    
    # Her frame için image content oluştur
    image_contents = []
    frame_descriptions = []
    
    for frame in frames_batch:
        b64_image = encode_image(frame["filepath"])
        image_contents.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64_image}"
            }
        })
        frame_descriptions.append(f"Frame {frame['index']} (t={frame['timestamp_sec']}s): {frame['filename']}")
    
    frames_list = "\n".join(frame_descriptions)
    
    # Script var/yok durumuna göre prompt oluştur
    if script_text:
        context_intro = f"""Bu {len(frames_batch)} frame bir ekran kaydından alındı. Bu videonun orijinal scripti aşağıda verilmiştir.

Orijinal Instagram script'i:
{script_text}"""
    else:
        context_intro = f"""Bu {len(frames_batch)} frame bir ekran kaydından alındı. Bu video bir yapay zeka aracının ekran kaydını gösteriyor.

⚠️ NOT: Bu video için orijinal script mevcut değil. Ekran görüntülerinden yola çıkarak aracı ve adımları tanımla."""
    
    prompt = f"""{context_intro}

Frame listesi:
{frames_list}

Görevlerin:

1. Her frame'i analiz et ve şunları belirt:
   - Bu frame'de ekranda ne görünüyor? (kısaca açıkla)
   - Frame'ler arasında önemli bir değişiklik var mı?
   - Bu frame blog yazısında kullanılmaya değer mi? (evet/hayır)

2. Blog'a değer frame'ler için:
   - Bu adımın blog'daki başlığı ne olmalı?
   - Ekranda vurgulanması gereken alanın yaklaşık konumu (resmin sol üst köşesi 0,0 kabul edildiğinde yüzdesel x, y, genişlik, yükseklik)
   - Blog'da bu görselin altına yazılacak açıklama

3. Birbirine çok benzeyen (değişmeyen) frame'leri "BENZER" olarak işaretle.

JSON formatında cevap ver. Markdown kullanma:
[
  {{
    "frame_index": 0,
    "timestamp_sec": 0,
    "description": "Ekranda görünen sahne açıklaması",
    "is_blog_worthy": true,
    "similar_to": null,
    "blog_step_title": "Adım başlığı",
    "highlight_area": {{"x_pct": 10, "y_pct": 20, "w_pct": 50, "h_pct": 10}},
    "blog_caption": "Bu görselin altına yazılacak metin"
  }}
]"""

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                *image_contents
            ]
        }
    ]
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})
        
        print(f"  Tokens — Input: {usage.get('prompt_tokens', '?')}, Output: {usage.get('completion_tokens', '?')}")
        print(f"  Maliyet — Input: ${usage.get('prompt_tokens', 0) * 0.11 / 1_000_000:.4f}, Output: ${usage.get('completion_tokens', 0) * 0.34 / 1_000_000:.4f}")
        
        # JSON parse et
        try:
            # Markdown code block temizle
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            parsed = json.loads(content.strip())
            return parsed, usage
        except json.JSONDecodeError:
            print(f"  ⚠️ JSON parse hatası, raw content kaydediliyor")
            return content, usage
    
    except requests.exceptions.RequestException as e:
        print(f"  ❌ API hatası: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text[:500]}")
        return None, {}

def main():
    frames_dir = sys.argv[1] if len(sys.argv) > 1 else "/Users/dolunayozeren/Desktop/Antigravity/Projeler/Blog_Yazici/typeless5/frames"
    
    # Video klasörünü belirle (frames_dir'in parent'ı)
    video_dir = os.path.dirname(frames_dir) if os.path.basename(frames_dir) == "frames" else frames_dir
    
    # Script'i yükle
    script_text = load_script(video_dir)
    
    # Metadata yükle
    meta_path = os.path.join(frames_dir, "frames_metadata.json")
    with open(meta_path, "r") as f:
        metadata = json.load(f)
    
    frames = metadata["extracted_frames"]
    print(f"Toplam {len(frames)} frame analiz edilecek")
    print(f"Model: {MODEL}")
    print(f"Batch boyutu: {MAX_IMAGES_PER_REQUEST}")
    
    all_results = []
    total_input_tokens = 0
    total_output_tokens = 0
    
    # 5'erli batch'ler
    batches = [frames[i:i+MAX_IMAGES_PER_REQUEST] for i in range(0, len(frames), MAX_IMAGES_PER_REQUEST)]
    
    for batch_idx, batch in enumerate(batches):
        result, usage = analyze_batch(batch, batch_idx, len(batches), script_text=script_text)
        
        if result:
            if isinstance(result, list):
                all_results.extend(result)
            else:
                all_results.append({"raw_content": result, "batch_idx": batch_idx})
        
        total_input_tokens += usage.get("prompt_tokens", 0)
        total_output_tokens += usage.get("completion_tokens", 0)
        
        # Rate limit aşmamak için bekle
        if batch_idx < len(batches) - 1:
            print("  ⏳ Rate limit — 3 sn bekleniyor...")
            time.sleep(3)
    
    # Sonuçları kaydet
    output_path = os.path.join(frames_dir, "vision_analysis.json")
    analysis_data = {
        "model": MODEL,
        "total_frames_analyzed": len(frames),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "estimated_cost_usd": round(total_input_tokens * 0.11 / 1_000_000 + total_output_tokens * 0.34 / 1_000_000, 4),
        "results": all_results
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    
    # Blog'a uygun frame'leri filtrele
    blog_worthy = [r for r in all_results if isinstance(r, dict) and r.get("is_blog_worthy")]
    
    print(f"\n{'='*50}")
    print(f"SONUÇ:")
    print(f"  Analiz edilen frame: {len(frames)}")
    print(f"  Blog'a uygun frame: {len(blog_worthy)}")
    print(f"  Toplam token: {total_input_tokens} input + {total_output_tokens} output")
    print(f"  Tahmini maliyet: ${analysis_data['estimated_cost_usd']:.4f}")
    print(f"  Sonuç dosyası: {output_path}")

if __name__ == "__main__":
    main()
