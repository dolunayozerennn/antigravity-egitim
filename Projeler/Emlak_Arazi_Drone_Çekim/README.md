# 🏗️ Emlak Arazi Drone Çekim

**Durum:** 🟢 Aktif (lokal)
**Agent:** 🎬 icerik-uretim
**Workflow:** `/drone-cekim`

---

## Açıklama

Emlak arazi ve gayrimenkul projeleri için drone çekim simülasyonu ve görselleştirme sistemi. 
TKGM parsel verisi ile arazi analizi yapar, Google Maps uydu görseli alır, Kie AI ile drone perspektifli 
frame ve video içerikleri üretir, FFmpeg ile final video montajı oluşturur.

### İki Mod
- **Arsa Modu:** Boş arazi → mimari proje vizualizasyonu (villa/apartman)
- **Tarla Modu:** Boş arazi → aktif tarım arazisi vizualizasyonu

## Pipeline Akışı

```
TKGM Parsel → Google Maps Uydu → 5 AI Frame → 4-5 AI Video → FFmpeg Final Video
```

## Kullanılan Servisler

| Servis | Kullanım |
|--------|----------|
| **TKGM API** | Parsel verisi (geometri, alan, nitelik) |
| **Google Maps Static API** | Uydu görseli |
| **Kie AI (Nano Banana Pro)** | AI frame üretimi |
| **Kie AI (Veo 3.1)** | AI video üretimi |
| **ImgBB / Catbox** | Görsel hosting |
| **Gemini** | Görsel kalite analizi |
| **FFmpeg** | Video birleştirme |

## Çalıştırma

```bash
# Workflow ile (önerilen):
# Antigravity'ye "/drone-cekim" de ve TKGM linki ver

# Manuel:
cd ~/Desktop/Antigravity/Projeler/Emlak_Arazi_Drone_Çekim
source .venv/bin/activate
python main.py Antalya Alanya Kestel 2216 13      # Arsa modu
python generate_farm_video.py                       # Tarla modu
```

## Dosya Yapısı

| Dosya | Açıklama |
|-------|----------|
| `main.py` | Ana pipeline (arsa modu — CLI) |
| `generate_farm_video.py` | Tarla modu pipeline |
| `src/config.py` | Konfigürasyon, logger |
| `src/data_fetcher.py` | TKGM API bağlantısı |
| `src/map_generator.py` | Google Maps uydu görseli |
| `src/image_generator.py` | Kie AI frame üretimi |
| `src/image_uploader.py` | ImgBB/Catbox upload |
| `src/video_generator.py` | Veo 3.1 video üretimi |
| `src/video_assembler.py` | FFmpeg video birleştirme |
| `src/visual_analyzer.py` | Gemini kalite analizi |
| `PROMPTS.md` | AI prompt şablonları |
| `API_REFERENCE.md` | TKGM API dokümantasyonu |

## Ortam

- **Deploy:** Yok — sadece lokal
- **Python:** 3.9+ (`.venv/` ile izole)
- **Bağımlılıklar:** `requirements.txt`
