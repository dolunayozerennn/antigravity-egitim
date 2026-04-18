---
description: Emlak Arazi Drone Çekim — TKGM parseli üzerinden AI drone video üretimi (lokal pipeline)
---

# /drone-cekim

> Emlak arazisi için drone perspektifli tanıtım videosu üretir.
> Pipeline: TKGM Parsel → Uydu Görseli → 5 AI Frame → 4-5 AI Video → Final Montaj

> [!IMPORTANT]
> **VENV KURALI:** Bu projedeki TÜM Python komutları `.venv` ile çalışır.
> Her komutu `cd ~/Desktop/Antigravity/Projeler/Emlak_Arazi_Drone_Çekim && source .venv/bin/activate &&` ile başlat.
> FFmpeg de `.venv` içindeki `static_ffmpeg` paketinden gelir (video_assembler.py otomatik ekler).

---

## 🎯 Tetikleyici

Kullanıcı aşağıdakilerden birini sağlar:

| Format | Örnek |
|--------|-------|
| **TKGM URL** | `https://parselsorgu.tkgm.gov.tr/#ara/idari/149762/7881/11/1772300198196` |
| **İl/İlçe/Mahalle/Ada/Parsel** | `Antalya Alanya Kestel 2216 13` |
| **Mod belirtimi (opsiyonel)** | `arsa` (mimari proje) veya `tarla` (tarımsal arazi) |

> Mod belirtilmezse → TKGM nitelik verisine bak: "TARLA" ise tarla modu, diğerleri arsa modu.

---

## ⚙️ Ön Koşullar (Adım 0)

// turbo
```bash
cd ~/Desktop/Antigravity/Projeler/Emlak_Arazi_Drone_Çekim && source .venv/bin/activate && \
  python3 -c "
import sys
errors = []

# 1. Check Python packages
for pkg in ['requests', 'dotenv', 'PIL', 'google.generativeai']:
    try:
        __import__(pkg)
    except ImportError:
        errors.append(f'MISSING: {pkg}')

# 2. Check .env
import os
from pathlib import Path
env_path = Path('.env')
if not env_path.exists():
    errors.append('.env dosyası YOK — master.env den oluşturulmalı')
else:
    from dotenv import load_dotenv
    load_dotenv()
    for key in ['GOOGLE_MAPS_API_KEY', 'KIE_AI_API_KEY', 'IMGBB_API_KEY', 'GEMINI_API_KEY']:
        val = os.getenv(key, '')
        if not val or val.startswith('your_'):
            errors.append(f'ENV EKSİK: {key}')

# 3. Check ffmpeg
import shutil
if not shutil.which('ffmpeg'):
    errors.append('ffmpeg YÜKLENMEMİŞ — brew install ffmpeg')

if errors:
    print('❌ ÖN KOŞUL HATALARI:')
    for e in errors:
        print(f'  - {e}')
    sys.exit(1)
else:
    print('✅ Tüm ön koşullar sağlandı.')
"
```

### Ön koşul başarısız olursa:

1. **Paket eksik** → `cd ~/Desktop/Antigravity/Projeler/Emlak_Arazi_Drone_Çekim && pip install -r requirements.txt`
2. **.env yok** → `view_file` ile `_knowledge/credentials/master.env` oku → gerekli 4 anahtarı çek → `.env` oluştur:
   ```
   GOOGLE_MAPS_API_KEY=...
   KIE_AI_API_KEY=...
   IMGBB_API_KEY=...
   GEMINI_API_KEY=...
   ```
3. **ffmpeg yok** → `brew install ffmpeg`

> ⛔ Ön koşullar sağlanmadan ASLA bir sonraki adıma geçme.

---

## 📡 Adım 1 — Parsel Verisi Çek (~5 saniye)

```bash
cd ~/Desktop/Antigravity/Projeler/Emlak_Arazi_Drone_Çekim && \
python3 -c "
import json, sys
sys.path.insert(0, '.')
from src.data_fetcher import TKGMDataFetcher

# --- KULLANICI GİRDİSİ BURAYA ---
# URL modunda:
result = TKGMDataFetcher.parse_from_url('TKGM_URL_BURAYA')
# VEYA koordinat modunda:
# result = TKGMDataFetcher.parse_parcel_info('İL', 'İLÇE', 'MAHALLE', 'ADA', 'PARSEL')

if result:
    print(json.dumps(result, indent=2, ensure_ascii=False))
else:
    print('❌ Parsel verisi alınamadı!')
    sys.exit(1)
"
```

### Çıktı kontrolü:
- ✅ `alan` > 0
- ✅ `geometri` → `coordinates` listesi dolu
- ✅ `nitelik` alanı okunabilir

### Kullanıcıya rapor et:
```
📍 Parsel: {ilceAd}/{mahalleAd} Ada:{adaNo} Parsel:{parselNo}
📐 Alan: {alan} m² | Nitelik: {nitelik}
🗺️ Koordinat merkezi: {lat}, {lon}
🎬 Önerilen mod: {arsa/tarla} (nitelik bazlı)

Devam edeyim mi?
```

> ⛔ Kullanıcı onaylamadan Adım 2'ye geçme.

---

## 🛰️ Adım 2 — Uydu Görseli Oluştur (~10 saniye)

```bash
cd ~/Desktop/Antigravity/Projeler/Emlak_Arazi_Drone_Çekim && \
python3 -c "
import sys, json
sys.path.insert(0, '.')
from src.config import generate_job_id
from src.map_generator import MapGenerator

job_id = 'JOB_ID_BURAYA'  # Adım 1'den al veya yeni üret
geometry = GEOMETRY_JSON_BURAYA  # Adım 1'in çıktısından kopyala
area_m2 = ALAN_BURAYA             # Adım 1'in çıktısından

# Temiz uydu (neon çizgisiz)
clean = MapGenerator.generate_satellite_image(job_id, geometry, draw_polygon=False, target_area=area_m2)
# Çizimli uydu (polygon sınırları ile)
drawn = MapGenerator.generate_satellite_image(job_id, geometry, draw_polygon=True, target_area=area_m2)

print(f'Temiz uydu: {clean}')
print(f'Çizimli uydu: {drawn}')
"
```

### Çıktı kontrolü:
- `view_file` ile her iki uydu görselini aç → kullanıcıya göster
- ✅ Parsel merkeze yakın görünüyor
- ✅ Çizimli versiyonda polygon doğru konumda
- ❌ Eğer görsel yeşil mock ise → Google Maps API key kontrol et

### Kullanıcıya göster:
- Temiz uydu görseli
- Çizimli uydu görseli
- "Uydu görselleri uygun mu? Frame üretimine geçeyim mi?"

> ⛔ Kullanıcı onaylamadan Adım 3'e geçme.

---

## 🖼️ Adım 3 — Frame Üretimi (Frame başına ~60-120 saniye)

> Bu adım SERİ yapılır (her frame bir öncekine bağlı).
> Her frame sonrası kullanıcıya gösterilir ve onay alınır.

### Kullanılacak değişkenler (önceki adımlardan):
```python
job_id = "..."        # Adım 2'den
area_m2 = ...         # Adım 1'den
geometry = {...}      # Adım 1'den
```

### ⚠️ MOD SEÇİMİ BURADA ETKİLİ:

**ARSA MODU** için frame sırası:
1. Frame 1 → 45° Drone perspektifi (uydudan dönüşüm)
2. Frame 2 → Neon sınır çizgileri
3. Frame 3 → m² metni (Pillow — deterministik)
4. Frame 4 → Mimari proje vizualizasyonu
5. Frame 5 → Göz hizası proje görünümü

**TARLA MODU** için frame sırası:
1. Frame 2 → 45° Drone + Neon (tek seferde — `generate_farm_video.py` yaklaşımı)
2. Frame 1 → Neon temizleme (Frame 2'den — arka plan tutarlılığı)
3. Frame 3 → m² metni (Pillow — deterministik)
4. Frame 4 → Aktif tarla vizualizasyonu
5. Frame 5 → Zemin seviyesi tarla görünümü

---

### Frame 1 (veya 2 → 1 tarla modunda)

```bash
cd ~/Desktop/Antigravity/Projeler/Emlak_Arazi_Drone_Çekim && \
python3 -c "
import sys
sys.path.insert(0, '.')
from src.image_generator import ImageGenerator
from src.image_uploader import ImageUploader

job_id = 'JOB_ID'
satellite_url = 'UYDU_URL'  # Önce upload et: ImageUploader.upload('uydu_dosya_yolu')

# Upload satellite first
satellite_url = ImageUploader.upload('UYDU_DOSYA_YOLU')
print(f'Uydu URL: {satellite_url}')

# ARSA MODU:
frame_1 = ImageGenerator.generate_frame_1(job_id, satellite_url)
# TARLA MODU: generate_farm_video.py'deki yaklaşımı kullan

print(f'Frame 1: {frame_1}')
"
```

### Her frame sonrası ZORUNLU kontrol:
1. `view_file` ile frame'i aç → kullanıcıya göster
2. Kullanıcıya sor: "Frame kalitesi yeterli mi? Devam mı, tekrar mı?"
3. **Kalite düşükse** → aynı frame'i tekrar üret (max 3 deneme)
4. **3 denemede de düşükse** → kullanıcıya bildir, prompt değişikliği öner

> Sonraki her frame için aynı döngüyü uygula:
> Frame üret → Upload → Göster → Onay → Sonraki frame

### Frame 3 (Pillow — HER ZAMAN)
Frame 3 her iki modda da Pillow ile üretilir (deterministik):
```python
frame_3 = ImageGenerator.generate_frame_3_fallback_pillow(job_id, frame_2_local_path, area_m2)
```
Bu frame'de kullanıcı onayı opsiyonel (çıktı deterministik).

---

## 🎬 Adım 4 — Video Üretimi (~15-45 dakika)

> Tüm frame'ler onaylandıktan sonra.
> Videolar PARALEL başlatılır, poll edilir.

### Video başlatma:
```bash
cd ~/Desktop/Antigravity/Projeler/Emlak_Arazi_Drone_Çekim && \
python3 << 'SCRIPT'
import sys
sys.path.insert(0, '.')
from src.video_generator import VideoGenerator

# --- FRAME URL'LERİ (önceki adımlardan) ---
frame_1_url = "..."
frame_2_url = "..."
frame_3_url = "..."
frame_4_url = "..."
frame_5_url = "..."

# --- ARSA MODU VIDEO PROMPTLARl ---
v1_prompt = "A cinematic drone shot. Bright cyan/blue glowing boundary lines appear outlining the parcel borders. Smooth cinematic motion. Vertical format 9:16."
v2_prompt = "A drone shot. Camera zooms in slightly. Large bold 3D text gradually materializes floating above parcel. Vertical format 9:16."
v3_prompt = "Text fades, empty land transforms. A modern architectural project gradually rises cinematic time-lapse. Vertical format 9:16."
v4_prompt = "Camera smoothly descends and rotates to arrive at an eye-level street view. Smooth drone downward flight. Vertical format 9:16."

# --- TARLA MODU VIDEO PROMPTLARl ---
# v1_prompt = "A premium cinematic drone shot flying smoothly forward. Camera gently tilts from 90 to 45 degrees. No rotation, no spin."
# v2_prompt = "Slow cinematic push-in at 45-degree angle. Glowing cyan boundary lines fade in outlining the field."
# v3_prompt = "Premium cinematic tracking shot. Large 3D typography fades in floating above field."
# v4_prompt = "Breathtaking time-lapse. Bare field transforms into cultivated agricultural paradise with crop rows and tractor."
# v5_prompt = "Ground-level slow-motion between crop rows. Red tractor working in background. Pastoral elegance."

# Paralel başlat
task_v1 = VideoGenerator.start_video_generation(frame_1_url, frame_2_url, v1_prompt)
task_v2 = VideoGenerator.start_video_generation(frame_2_url, frame_3_url, v2_prompt)
task_v3 = VideoGenerator.start_video_generation(frame_3_url, frame_4_url, v3_prompt)
task_v4 = VideoGenerator.start_video_generation(frame_4_url, frame_5_url, v4_prompt)

import json
tasks = {
    1: {"task_id": task_v1, "output_filename": "JOB_ID_video_1.mp4"} if task_v1 else None,
    2: {"task_id": task_v2, "output_filename": "JOB_ID_video_2.mp4"} if task_v2 else None,
    3: {"task_id": task_v3, "output_filename": "JOB_ID_video_3.mp4"} if task_v3 else None,
    4: {"task_id": task_v4, "output_filename": "JOB_ID_video_4.mp4"} if task_v4 else None,
}
tasks = {k: v for k, v in tasks.items() if v}
print(f"✅ {len(tasks)} video görevi başlatıldı:")
for k, v in tasks.items():
    print(f"  Video {k}: Task ID = {v['task_id']}")
print(json.dumps(tasks))
SCRIPT
```

### Video polling (ayrı komut — uzun sürer):
```bash
cd ~/Desktop/Antigravity/Projeler/Emlak_Arazi_Drone_Çekim && \
python3 << 'SCRIPT'
import sys, json
sys.path.insert(0, '.')
from src.video_generator import VideoGenerator

# --- ÖNCEKİ ADIMDAN TASKS JSON'I YAPIŞTIR ---
tasks = TASKS_JSON_BURAYA

print("⏳ Video polling başlıyor (max 45 dakika)...")
results = VideoGenerator.poll_multiple_videos(tasks)

print(f"\n✅ {len(results)}/{len(tasks)} video tamamlandı:")
for part, path in sorted(results.items()):
    print(f"  Video {part}: {path}")
SCRIPT
```

### Kullanıcıya rapor:
```
🎬 Video Durumu:
  Video 1: ✅/❌ {path veya hata}
  Video 2: ✅/❌ {path veya hata}
  Video 3: ✅/❌ {path veya hata}
  Video 4: ✅/❌ {path veya hata}

Birleştirmeye geçeyim mi?
```

> ⛔ En az 3/4 video başarılı olmalı. 2 veya altı → kullanıcıya bildir.

---

## 🎞️ Adım 5 — Video Birleştirme (~30 saniye)

```bash
cd ~/Desktop/Antigravity/Projeler/Emlak_Arazi_Drone_Çekim && \
python3 -c "
import sys
sys.path.insert(0, '.')
from src.video_assembler import VideoAssembler

job_id = 'JOB_ID'
videos = [
    'VIDEO_1_PATH',
    'VIDEO_2_PATH',
    'VIDEO_3_PATH',
    'VIDEO_4_PATH',
]

final = VideoAssembler.assemble_videos(job_id, videos)
if final:
    print(f'✅ Final video: {final}')
else:
    print('❌ Birleştirme başarısız!')
"
```

### Çıktı:
- Final video yolu: `output/{job_id}_final_video.mp4`
- `view_file` ile video'yu kontrol et (ilk frame görüntüsü)

---

## 📊 Adım 6 — Teslimat Raporu

Kullanıcıya şu bilgileri sun:

```
═══════════════════════════════════════════
🏗️ DRONE ÇEKİM PİPELINE TAMAMLANDI
═══════════════════════════════════════════
📍 Parsel: {il}/{ilçe}/{mahalle} Ada:{ada} Parsel:{parsel}
📐 Alan: {alan} m² | Nitelik: {nitelik}
🎬 Mod: {Arsa/Tarla}
═══════════════════════════════════════════

🖼️ Üretilen Frame'ler:
  Frame 1 (45° Drone)     : {frame_1_url}
  Frame 2 (Neon Sınırlar) : {frame_2_url}
  Frame 3 (m² Metni)      : {frame_3_url}
  Frame 4 (Proje/Tarla)   : {frame_4_url}
  Frame 5 (Göz Hizası)    : {frame_5_url}

🎬 Üretilen Videolar:
  Video 1: {video_1_path}
  Video 2: {video_2_path}
  Video 3: {video_3_path}
  Video 4: {video_4_path}

📦 Final Video: output/{job_id}_final_video.mp4
═══════════════════════════════════════════
```

---

## 🚨 Hata Senaryoları ve Kurtarma

| Hata | Çözüm |
|------|--------|
| TKGM API timeout/500 | Mock fallback otomatik devreye girer (data_fetcher.py). Geometri varsa devam et, yoksa kullanıcıya bildir |
| Google Maps API key hatalı | Yeşil mock uydu üretilir. **DURMA** — kullanıcıya bildir, key kontrol et |
| Kie AI frame üretimi başarısız | Max 3 retry. 3'te de başarısız → kullanıcıya bildir, prompt değişikliği öner |
| Kie AI credit bitti | Hata mesajını raporla. Pipeline durdur |
| Veo 3.1 video timeout (45 dk) | Kullanıcıya bildir. Tamamlanan videolarla devam et |
| Veo 3.1 task failed (successFlag=2/3) | O video atlanır. En az 3/4 video ile birleştirmeye devam et |
| FFmpeg birleştirme hatası | Codec uyumsuzluğu olabilir. Her video'yu ayrı standardize et |
| ImgBB/Catbox upload fail | Catbox→ImgBB fallback zaten var. İkisi de çökerse → kullanıcıya bildir |

---

## 📋 Kontrol Listesi (Her çalıştırmada)

- [ ] Ön koşullar sağlandı
- [ ] Parsel verisi alındı — kullanıcı onayladı
- [ ] Uydu görseli üretildi — kullanıcı onayladı
- [ ] Frame 1 üretildi — kullanıcı onayladı
- [ ] Frame 2 üretildi — kullanıcı onayladı
- [ ] Frame 3 üretildi (Pillow)
- [ ] Frame 4 üretildi — kullanıcı onayladı
- [ ] Frame 5 üretildi — kullanıcı onayladı
- [ ] Tüm videolar paralel başlatıldı
- [ ] Video polling tamamlandı (en az 3/4 başarılı)
- [ ] Final video birleştirildi
- [ ] Teslimat raporu sunuldu

---

## 📁 Dosya Referansları

| Dosya | Yol |
|-------|-----|
| Proje kökü | `Projeler/Emlak_Arazi_Drone_Çekim/` |
| Ana pipeline (arsa) | `main.py` |
| Tarla pipeline | `generate_farm_video.py` |
| TKGM data fetcher | `src/data_fetcher.py` |
| Harita üretici | `src/map_generator.py` |
| Frame üretici | `src/image_generator.py` |
| Video üretici | `src/video_generator.py` |
| Video birleştirici | `src/video_assembler.py` |
| Görsel analizci | `src/visual_analyzer.py` |
| Görsel upload | `src/image_uploader.py` |
| Prompt şablonları | `PROMPTS.md` |
| API referansı | `API_REFERENCE.md` |
| Prompt iterasyon logları | `optimized_prompts_log.json` |
