> ⚠️ **ÖNEMLİ BİLGİLENDİRME**  
> Bu proje, eğitim ve örnekleme amacıyla hazırlanmış olan bir **taslak (template)** projedir. Doğrudan tıklayıp "çalıştır" (plug-and-play) mantığıyla tasarlanmamıştır. Kendi sisteminize entegre etmeden önce:
> - Kimlik bilgilerinizi (API anahtarları, token'lar, email adresleri) tanımlamanız
> - Dosya yollarını (file paths) ve bağlantıları kendi ortamınıza göre güncellemeniz
> - Senaryoyu kendi hedeflerinize göre özelleştirmeniz beklenmektedir.
> Lütfen bu kodları inceleyerek ve kendi senaryonuza uyarlayarak geliştirin.

# 📝 Blog Yazıcı — Reels-to-Blog Otomasyon Sistemi

> **⚠️ TASLAK PROJE:** Bu proje, bir AI otomasyon sisteminin iskelet yapısını göstermek amacıyla paylaşılmıştır. Tam çalışır durumda değildir — kendi iş süreçlerinize göre uyarlamanız ve tamamlamanız beklenmektedir. API anahtarlarınızı ve içerik stratejinizi eklemeniz gerekir.

> **Durum:** 🟡 Test aşamasında (Pilot video tamamlandı, annotation iyileştirme ve refaktör devam ediyor)

---

## 🎯 Amaç

Instagram Reels için çekilen ekran kayıtlarını otomatik olarak adım adım rehber (step-by-step guide) formatında SEO-uyumlu blog yazılarına dönüştürmek.

**Pipeline:**
```
Ekran Kaydı (.mov/.mp4)
  → Frame Çıkarma (OpenCV, her 6s)
  → Vision LLM Analiz (Groq Llama 4 Scout)
  → Anlamlı Frame Seçimi
  → Görsel Annotation (Pillow, 2x supersampling)
  → Self-Review ve Otomatik Düzeltme
  → Blog Metni Üretimi (Gemini 2.5 Flash)
  → Yayına Hazır Blog Yazısı
```

---

## 📁 Dosya Yapısı

```
Blog_Yazici/
├── README.md                   ← Bu dosya
├── extract_frames.py           ← Adım 1: Video → Frame çıkarma (OpenCV)
├── vision_analyzer.py          ← Adım 2: Frame analizi (Groq Llama 4 Scout)
├── generate_blog.py            ← Adım 3: Blog metni üretimi (Gemini 2.5 Flash)
├── annotate_v3.py              ← Adım 4: Annotation (2x supersampling, tematik renkler)
├── .venv/                      ← Python sanal ortam (Pillow, opencv-python, requests)
│
└── ornek_video/                ← Pilot video verileri
    ├── frames/                 ← Çıkarılan ham frame'ler
    ├── annotated_v3/           ← Güncel annotation çıktıları
    └── blog_draft.md           ← Üretilen blog metni
```

---

## 🔧 Kullanım

```bash
cd Projeler/Blog_Yazici

# Virtual environment'ı aktif et
source env/bin/activate

# Tüm pipeline'ı tek komutla çalıştır:
python3 run_pipeline.py <video_dosyasi_veya_hedef_klasor>

# Pipeline sırasıyla şu adımları işletir:
# 1. extract_frames.py (Video verildiyse frame çıkarır)
# 2. vision_analyzer.py (Groq ile frame değerlendirmesi yapar)
# 3. annotate_v3.py (Görsel annotasyon ve self-review)
# 4. generate_blog.py (Gemini 2.5 Flash ile blog metni üretimi)
```

---

## 🔑 API Anahtarları

| Servis | Kaynak | Kullanım |
|--------|--------|----------|
| Groq | `_knowledge/credentials/master.env` → `GROQ_API_KEY` | Vision analizi |
| Gemini | `_knowledge/credentials/master.env` → `GEMINI_API_KEY` | Blog metni üretimi |

---

## ✅ Tamamlananlar

- [x] Frame çıkarma pipeline'ı (extract_frames.py)
- [x] Vision analizi (vision_analyzer.py — Groq Llama 4 Scout)
- [x] Blog metni üretimi (generate_blog.py — Gemini 2.5 Flash)
- [x] Annotation v3: 2x supersampling, 900px tutarlı boyut, tematik renkler, caption bar
- [x] Self-Review Sistemi (Groq Vision modeliyle entegre)
- [x] Pipeline Entegrasyonu (`run_pipeline.py` üzerinden tek komutla)

---

## ⏳ Yapılması Gerekenler

### Öncelik 1: Blog Yayın Mekanizması
- Kendi web sitenize blog altyapısı kurun (MDX veya benzeri)

### Öncelik 2: Multi-Video / Notion Entegrasyonu
- Notion veritabanından otomatik video çekme
- Dinamik frame seçimi (video süresine adapte)

---

## 📊 Pilot Sonuçlar

| Metrik | Değer |
|--------|-------|
| Video süresi | ~2 dakika |
| Frame sayısı | 21 |
| Annotation adımları | 6 |
| Vision maliyet | ~$0.01 |
| Blog maliyet | ~$0.005 |
| **Toplam maliyet** | **~$0.02** |

---

*Antigravity ile oluşturulmuş taslak projedir.*
