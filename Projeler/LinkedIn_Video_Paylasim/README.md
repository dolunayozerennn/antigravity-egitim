# LinkedIn Paylaşım — Notion + Drive → LinkedIn Master Pipeline

Notion'daki "Yayınlandı" videoları, Google Drive'daki master kalitedeki dosyalardan
LinkedIn'e otomatik paylaşan günlük pipeline.

## Özellikler

- **Master Kalite:** Drive'daki orijinal master `.mp4` dosyası kullanılır — TikTok kompresyonu yok, watermark yok
- **Sıfır Kayıp:** FFmpeg sadece kayıpsız faststart remux yapar (`-c copy`); reencode yok
- **Akıllı Caption:** Groq LLM, sayfa script'inden tek cümlelik LinkedIn caption üretir (max 280 char, hashtag yok, CTA yok, **spesifik ürün adı yok** — jenerik kategori + tavsiye dili)
- **Notion Dedup:** Aynı video iki kez paylaşılmaz; logger DB sorgu yapar
- **Günlük 1 Paylaşım:** Cron `0 10 * * *` (UTC) = 13:00 TR

## Akış

1. Notion `Dolunay Reels & YouTube` DB → `Status = "Yayınlandı"` videoları çek (Paylaşım Tarihi DESC)
2. Logger DB'de zaten paylaşılmamış ilk video
3. `Drive` property'sindeki klasörü Service Account ile aç
4. Klasördeki dosyalardan pattern öncelikli seç: `tiktok` > `insta` (env: `VIDEO_PATTERN_PRIORITY`)
5. Drive'dan indir → kayıpsız faststart remux
6. Notion sayfa body'sinden Groq ile tek cümle caption üret
7. LinkedIn Videos API (chunked upload) + Posts API
8. Logger DB'ye `page_id` ile kayıt at

## Mimari

```
main.py → Pipeline orchestration
├── core/notion_video_selector.py → Notion DB sorgu + Drive URL parse
├── core/drive_downloader.py      → Service Account ile klasör listele + dosya indir
├── core/video_processor.py       → Faststart remux (kayıpsız); >REENCODE_OVER_BYTES ise compress
├── core/content_filter.py        → CaptionGenerator (Groq, tek cümle)
├── core/linkedin_publisher.py    → LinkedIn Videos API + Posts API (chunked)
└── core/notion_logger.py         → Logger DB (dedup birincil anahtar: page_id)
```

## Environment Variables

| Variable | Açıklama |
|----------|----------|
| `LINKEDIN_ACCESS_TOKEN` | OAuth2 Bearer Token |
| `LINKEDIN_PERSON_URN` | `urn:li:person:XXXXX` |
| `GROQ_API_KEY` | Groq API key |
| `GROQ_MODEL` | (opsiyonel) default `llama-3.3-70b-versatile` |
| `NOTION_SOCIAL_TOKEN` | Notion integration token |
| `NOTION_DB_REELS_KAPAK` | Kaynak DB ("Dolunay Reels & YouTube") |
| `NOTION_LINKEDIN_DB_ID` | Logger DB |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | (Railway) base64 encoded SA JSON; lokal: `_knowledge/credentials/google-service-account.json` |
| `VIDEO_PATTERN_PRIORITY` | (opsiyonel) Virgüllü liste, default `tiktok,insta` |
| `MAX_VIDEO_BYTES` | (opsiyonel) Üzerini skip et, default 5GB (LinkedIn limit) |
| `REENCODE_OVER_BYTES` | (opsiyonel) Bunun üzerinde compress yap; default OFF |

## Çalıştırma

```bash
ENV=development python main.py    # lokal DRY-RUN
RUN_MODE=cron python main.py      # Railway cron
```

## Deploy

Railway servis: `linkedin-video-cron` (auto-deploy KAPALI; `serviceInstanceDeployV2` mutation
ile manuel commit deploy gerekli — bkz. `_knowledge/deploy-registry.md`).
