> ⚠️ **ÖNEMLİ BİLGİLENDİRME**  
> Bu proje, eğitim ve örnekleme amacıyla hazırlanmış olan bir **taslak (template)** projedir. Doğrudan tıklayıp "çalıştır" (plug-and-play) mantığıyla tasarlanmamıştır. Kendi sisteminize entegre etmeden önce:
> - Kimlik bilgilerinizi (API anahtarları, token'lar, email adresleri) tanımlamanız
> - Dosya yollarını (file paths) ve bağlantıları kendi ortamınıza göre güncellemeniz
> - Senaryoyu kendi hedeflerinize göre özelleştirmeniz beklenmektedir.
> Lütfen bu kodları inceleyerek ve kendi senaryonuza uyarlayarak geliştirin.

# 🎨 Reels Kapak — Otomatik AI Kapak Üretim Sistemi

> **⚠️ TASLAK PROJE:** Bu proje, bir AI otomasyon sisteminin iskelet yapısını göstermek amacıyla paylaşılmıştır. Tam çalışır durumda değildir — kendi markanıza ve iş süreçlerinize göre uyarlamanız ve tamamlamanız beklenmektedir. API anahtarlarınızı, Notion veritabanınızı ve referans görsellerinizi eklemeniz gerekir.

**Versiyon:** v3 — Multi-theme (3 tema × 2 varyasyon)

---

## Açıklama

YouTube ve Instagram Reels videoları için **AI destekli otomatik kapak görseli üretim pipeline'ı**. Notion veritabanından "çekildi" durumundaki videoları alır, Kie AI ile birden fazla tema ve varyasyonda kapak üretir, Google Drive'a yükler ve Notion'da revizyon paneli oluşturur.

### Temel Özellikler

- **Multi-Theme Generation** — Her video için 3 farklı tema × 2 varyasyon = 6 kapak
- **Autonomous Agent** — Kie AI API ile tam otonom kapak üretimi
- **Revision Engine** — Notion üzerinden revizyon talepleri ile yeniden üretim
- **Google Drive Entegrasyonu** — Kapaklar otomatik olarak ilgili Drive klasörüne yüklenir
- **Batch Processing** — Birden fazla video için toplu kapak üretimi
- **Railway Cron** — Periyodik otomatik çalışma (3 saatte bir kontrol)

## 🔄 Pipeline Akışı

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  1. Notion    │ →  │  2. Kie AI    │ →  │  3. Google Drive  │ →  │  4. Notion        │
│  (Video Bul)  │    │  (Kapak Üret) │    │  (Yükle)          │    │  (Revizyon Panel) │
└──────────────┘    └──────────────┘    └──────────────────┘    └──────────────────┘
```

## 📁 Dosya Yapısı

```
Reels_Kapak/
├── main.py                    # Ana pipeline — video bul → kapak üret → yükle
├── worker.py                  # Railway worker (cron modunda çalışır)
├── autonomous_cover_agent.py  # Kie AI ile otonom kapak üretimi
├── multi_theme_gen.py         # 3 tema × 2 varyasyon üretim motoru
├── batch_cover_run.py         # Toplu kapak üretimi
├── composition_engine.py      # Görsel kompozisyon motoru
├── image_service.py           # Görsel işleme servisi
├── notion_service.py          # Notion API — video çekme, revizyon paneli
├── drive_service.py           # Google Drive — kapak yükleme
├── google_auth.py             # Google OAuth authentication
├── revision_engine.py         # Revizyon talep işleme motoru
├── revision_cron_worker.py    # Revizyon cron worker
├── requirements.txt           # Python bağımlılıkları
├── railway.json               # Railway deploy konfigürasyonu
└── Instruction.md             # Stil kılavuzu ve kullanım talimatları
```

## ⚙️ Environment Variables

| Variable | Zorunlu | Açıklama |
|----------|---------|----------|
| `KIE_API_KEY` | ✅ | Kie AI API anahtarı |
| `NOTION_TOKEN` | ✅ | Notion API anahtarı |
| `NOTION_DATABASE_ID` | ✅ | Video veritabanı ID |
| `GOOGLE_DRIVE_CREDENTIALS_JSON` | ✅ | Google Drive SA JSON |
| `REFERENCE_PHOTO_URL` | ✅ | Referans kişi fotoğrafı URL |

## 🏗️ Deployment

- **Platform:** Railway (Native Cron Job)
- **Servis 1 (Ana Kapak Üretimi):** `python worker.py` (Günde 3 kere)
- **Servis 2 (Revizyon Kontrolü):** `python revision_cron_worker.py` (Günde 5 kere)
- **Restart Policy:** `NEVER`

## 📋 Versiyon Geçmişi

- **v1:** Tek tema, 3 varyasyon
- **v2:** Autonomous agent + Drive entegrasyonu
- **v3 (Güncel):** Multi-theme (3 tema × 2 varyasyon), revision engine, batch processing

---

*Antigravity ile oluşturulmuş taslak projedir.*
