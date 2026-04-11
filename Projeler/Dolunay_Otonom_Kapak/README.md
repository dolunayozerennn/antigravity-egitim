# Dolunay Otonom Kapak Üreticisi (V2)

> Reels (9:16) ve YouTube (16:9) kapak fotoğraflarını otonom olarak üreten birleşik pipeline.
> Kie AI (Nano Banana Pro/2) ile görsel üretim, Gemini Vision ile otomatik değerlendirme ve iterasyon.

## 🏗 Mimari

```
Dolunay_Otonom_Kapak/
├── main.py                    # Orkestratör — COVER_TYPE env ile Reels/YouTube seçimi
├── rourke_style_guide.md      # Görsel stil rehberi (Rourke aesthetic)
├── agents/
│   ├── reels_agent.py         # 9:16 Reels kapak pipeline (3 tema × 2 varyasyon = 6 kapak)
│   ├── youtube_agent.py       # 16:9 YouTube thumbnail pipeline (5 tema × 2 varyasyon = 10 kapak)
│   ├── learnings.md           # Kullanıcı feedback'lerinden öğrenimler
│   └── cutout_tags.json       # Cutout → mood eşleme tablosu
├── core/
│   ├── config.py              # Fail-Fast env doğrulama (boot crash)
│   ├── notion_service.py      # Notion API (video listesi, revizyon paneli)
│   ├── drive_service.py       # Google Drive upload (THUMBNAIL subfolder)
│   ├── google_auth.py         # Merkezi OAuth token yönetimi
│   ├── ops_logger.py          # Notion Operations Logger
│   └── logger.py              # Standart Python logger
├── assets/
│   └── cutouts/               # Kişi cutout fotoğrafları (yüz referansı)
├── outputs/                   # Üretilen kapaklar (geçici, .gitignore)
├── requirements.txt           # Kilitli bağımlılıklar
├── railway.json               # Railway deploy config
└── nixpacks.toml              # Sistem bağımlılıkları (Railway)
```

## 🔄 Pipeline Akışı

1. **Notion Query** → "Çekildi" statüsündeki videoları getir
2. **Tema Üretimi** → Gemini ile 3 (Reels) veya 5 (YouTube) farklı konsept oluştur *(Anti-klişe: Ekrana bakan insan yasaktır, sadece fiziksel güçlü metaforlar üretilir)*
3. **Cutout Seçimi** → Kişi fotoğrafları arasından mood'a göre otomatik seçim
4. **Görsel Üretim** → Kie AI'ya cutout + prompt gönder (9:16 veya 16:9)
5. **Self-Review** → Gemini Vision ile otomatik değerlendirme (metin, safe zone, yüz kimliği ve 'masa başı klişesi' kontrolü)
6. **Iterasyon** → Skor < 8 ise veya görsel klişe ise prompt iyileştirip yeniden üret (max N retry)
7. **Drive Upload** → Onaylanan kapağı Google Drive THUMBNAIL klasörüne yükle
8. **Revizyon Paneli** → Notion sayfasına tema linkli revizyon paneli ekle

## 🚀 Railway Deploy

**2 ayrı CronJob servisi** olarak deploy edilir:

| Servis | COVER_TYPE | Cron Schedule | Açıklama |
|--------|-----------|---------------|----------|
| `dolunay-otonom-kapak-reels` | `reels` | `0 6 * * *` (Günlük TR 09:00) | Reels kapak üretimi |
| `dolunay-otonom-kapak-youtube` | `youtube` | `0 7 * * *` (Günlük TR 10:00) | YouTube thumbnail üretimi |

### Gerekli Environment Variables

| Variable | Açıklama |
|----------|----------|
| `COVER_TYPE` | `reels` veya `youtube` |
| `ENV` | `production` |
| `NOTION_SOCIAL_TOKEN` | Notion API erişimi |
| `NOTION_DB_REELS_KAPAK` | Reels video veritabanı ID |
| `NOTION_DB_YOUTUBE_ISBIRLIKLERI` | YouTube video veritabanı ID |
| `NOTION_DB_OPS_LOG` | Operasyon log veritabanı ID |
| `KIE_API_KEY` | Kie AI görsel üretim |
| `GEMINI_API_KEY` | Google Gemini (metin + vision) |
| `IMGBB_API_KEY` | ImgBB görsel hosting |
| `GOOGLE_OUTREACH_TOKEN_JSON` | Google Drive OAuth token (JSON string) |

## 💻 Lokal Çalıştırma

```bash
# Reels pipeline
python main.py --type reels

# YouTube pipeline
python main.py --type youtube

# Worker modu (sonsuz döngü, opsiyonel)
LOOP=1 python main.py --type reels
```

## 📋 Versiyon Geçmişi

- **V2 (Nisan 2026):** Reels + YouTube tek monolith. CronJob mode. Eski `Dolunay_Reels_Kapak` ve `Dolunay_YouTube_Kapak` projeleri birleştirildi.
- **V1:** Ayrı repolar, Worker mode (pahalı).
