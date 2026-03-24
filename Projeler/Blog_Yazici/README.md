# 📝 Blog Yazıcı — Reels-to-Blog Otomasyon Sistemi

> **Proje Konumu:** `Antigravity/Projeler/Blog_Yazici/`  
> **Durum:** 🟢 Multi-Video Pipeline hazır  
> **Son Güncelleme:** 2026-03-22

---

## 🎯 Amaç

Instagram Reels için çekilen ekran kayıtlarını otomatik olarak adım adım rehber (step-by-step guide) formatında SEO-uyumlu blog yazılarına dönüştürmek.

**Pipeline:**
```
Notion "Yayınlandı" Videoları
  → Video Seçimi (notion_video_selector.py — Confidence Score)
  → Script Çekme (script_extractor.py — Notion Caption)
  → Drive İndirme (drive_downloader.py — Service Account, 50MB chunk)
  → Frame Çıkarma (extract_frames.py — OpenCV, her 6s)
  → Vision LLM Analiz (vision_analyzer.py — Groq Llama 4 Scout)
  → Dinamik Annotation (annotate_v3.py — 2x supersampling, auto-highlight)
  → Self-Review ve Auto-Fix (Groq Vision)
  → Blog Metni Üretimi (generate_blog.py — Gemini 2.5 Pro)
  → Yayına Hazır Blog Yazısı
```

---

## 📁 Dosya Yapısı

```
Blog_Yazici/
├── README.md                     ← Bu dosya
├── run_pipeline.py               ← 🎛️ Ana orkestratör (klasik + Notion modu)
├── notion_video_selector.py      ← Notion'dan video seçimi + confidence scoring
├── drive_downloader.py           ← Drive'dan ekran kaydı indirme (SA ile)
├── script_extractor.py           ← Notion caption → script.txt
├── extract_frames.py             ← Adım 1: Video → Frame çıkarma (OpenCV)
├── vision_analyzer.py            ← Adım 2: Frame analizi (Groq Llama 4 Scout)
├── annotate_v3.py                ← Adım 3: Annotation (dinamik + hardcoded mod)
├── generate_blog.py              ← Adım 4: Blog metni üretimi (Gemini 2.5 Pro)
├── video_assessment_report.json  ← Notion video değerlendirme raporu
├── processed_videos.json         ← İşlenmiş video takibi
├── env/                          ← Python sanal ortam
│
└── typeless5/                    ← Pilot video verileri: "Typeless 5"
    ├── frames/
    │   ├── frame_000_t0s.jpg ... frame_020_t120s.jpg
    │   ├── frames_metadata.json
    │   └── vision_analysis.json
    ├── annotated_v3/
    │   ├── step_01_*.jpg ... step_06_*.jpg
    │   └── annotations_v3.json
    ├── script.txt
    └── blog_draft.md
```

---

## 🔧 Kullanım

### Yeni Mod: Notion → Drive → Pipeline (Otomatik)

```bash
cd Projeler/Blog_Yazici

# En yüksek puanlı videoyu otomatik seç ve işle:
python3 run_pipeline.py --from-notion

# Belirli bir videoyu seç:
python3 run_pipeline.py --from-notion --video-name "Skywork"

# Özel eşik ve indirme limiti:
python3 run_pipeline.py --from-notion --threshold 50 --max-downloads 3
```

### Klasik Mod: Lokal Dosya/Klasör

```bash
# Belirli bir video dosyası veya klasör ile:
python3 run_pipeline.py typeless5

# Pipeline sırasıyla şu adımları işletir:
# 1. extract_frames.py  → Frame çıkarma
# 2. vision_analyzer.py → Groq ile frame analizi
# 3. annotate_v3.py     → Annotation (dinamik/hardcoded)
# 4. generate_blog.py   → Gemini 2.5 Pro ile blog üretimi
```

---

## 🔑 API Anahtarları

| Servis | Kaynak | Kullanım |
|--------|--------|----------|
| Notion | `master.env` → `NOTION_SOCIAL_TOKEN` | Video listesi çekme |
| Groq | `master.env` → `GROQ_API_KEY` | Vision analizi + Self-Review |
| Gemini | `master.env` → `GEMINI_API_KEY` | Blog metni üretimi |
| Drive SA | `google-service-account.json` | Ekran kaydı indirme |

---

## ✅ Tamamlananlar

- [x] Frame çıkarma pipeline'ı (extract_frames.py)
- [x] Vision analizi (vision_analyzer.py — Groq Llama 4 Scout)
- [x] Blog metni üretimi (generate_blog.py — Gemini 2.5 Pro)
- [x] Pilot blog metni üretildi ve beğenildi
- [x] Annotation v3: 2x supersampling, 900px tutarlı boyut, tematik renkler, caption bar
- [x] Self-Review Sistemi (Groq Vision ile auto-fix, max 2 iterasyon)
- [x] Pipeline Entegrasyonu (run_pipeline.py orkestrasyon)
- [x] API Keyler merkezi depoya taşındı (dinamik okuma)
- [x] **Notion Entegrasyonu** — `--from-notion` flag ile otomatik video seçimi
- [x] **Drive İndirme** — Service Account ile ekran kayıtlarını streaming indirme
- [x] **Dinamik Annotation** — vision_analysis.json'dan otomatik adım oluşturma
- [x] **Script Extractor** — Notion caption'dan script.txt oluşturma
- [x] **Hardcoded script kaldırıldı** — Tüm scriptler dinamik yüklenir

---

## ⏳ Yapılması Gerekenler

### Öncelik 1: Blog Yayın Mekanizması
- Dolunay_AI_Website'e blog altyapısı kur (MDX entegrasyonu)

### Öncelik 2: Kalite İyileştirmeleri
- Multi-video merge (tek video yerine tüm ekran kayıtlarını birleştir)
- Notion'a blog durumu geri yazma (status update)

---

## 📊 Pilot Sonuçlar (Typeless 5)

| Metrik | Değer |
|--------|-------|
| Video süresi | ~2 dakika |
| Frame sayısı | 21 |
| Annotation adımları | 6 |
| Vision maliyet | ~$0.01 |
| Blog maliyet | ~$0.005 |
| **Toplam maliyet** | **~$0.02** |

---

## 📝 Değişiklik Geçmişi

| Tarih | Değişiklik |
|-------|-----------|
| 2026-03-21 | Proje oluşturuldu, pilot video işlendi |
| 2026-03-21 | Annotation v3 + Self-Review mekanizması |
| 2026-03-21 | run_pipeline.py orkestrasyonu eklendi |
| 2026-03-22 | Refaktör: env/ taşıma, API key merkezi okuma |
| 2026-03-22 | Hardcoded script kaldırıldı → dinamik script.txt |
| 2026-03-22 | Gemini 2.5 Flash → Gemini 2.5 Pro yükseltme |
| 2026-03-22 | notion_video_selector.py: Notion → confidence scoring |
| 2026-03-22 | **Multi-Video Pipeline v2.0:** drive_downloader.py, script_extractor.py, dinamik annotation modu, --from-notion flag |
