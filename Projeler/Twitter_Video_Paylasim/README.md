# Twitter Paylaşım — Notion + Drive → X (Twitter) Master Pipeline

Notion'daki "Yayınlandı" videoları, Google Drive'daki master kalitedeki dosyalardan
X (Twitter)'a otomatik paylaşan günde 3 kez çalışan pipeline.

## Özellikler

- **Master Kalite:** Drive'daki orijinal master `.mp4` dosyası kullanılır — TikTok kompresyonu yok, watermark yok
- **Sıfır Kayıp:** FFmpeg sadece kayıpsız faststart remux yapar (`-c copy`); >200MB'da otomatik compress (X limitine güvenli)
- **Akıllı Caption:** Groq LLM, sayfa script'inden tek cümlelik tweet üretir (max 280 char, hashtag yok, CTA yok, **spesifik ürün adı yok** — jenerik kategori + tavsiye dili)
- **Notion Dedup:** Aynı video iki kez paylaşılmaz; logger DB sorgu yapar
- **Günde 3 Paylaşım:** Cron `0 8,11,14 * * *` (UTC) = TR 11/14/17

## Akış

1. Notion `Dolunay Reels & YouTube` DB → `Status = "Yayınlandı"` videoları çek (Paylaşım Tarihi DESC)
2. Logger DB'de zaten paylaşılmamış ilk video
3. `Drive` property'sindeki klasörü Service Account ile aç
4. Klasördeki dosyalardan pattern öncelikli seç: `tiktok` > `insta` (env: `VIDEO_PATTERN_PRIORITY`)
5. Drive'dan indir → kayıpsız faststart remux (gerekirse compress)
6. Notion sayfa body'sinden Groq ile tek cümle caption üret
7. X API v1.1 chunked media upload + v2 create_tweet (tweepy)
8. Logger DB'ye `page_id` ile kayıt at

## Mimari

```
main.py → Pipeline orchestration
├── core/notion_video_selector.py → Notion DB sorgu + Drive URL parse
├── core/drive_downloader.py      → Service Account ile klasör listele + dosya indir
├── core/video_processor.py       → Faststart remux (kayıpsız); >REENCODE_OVER_BYTES ise compress
├── core/content_filter.py        → CaptionGenerator + SuitabilityFilter (Groq)
├── core/x_publisher.py           → X API v1.1 (media) + v2 (tweet) — tweepy
└── core/notion_logger.py         → Logger DB (dedup birincil anahtar: page_id)
```

## Environment Variables

| Variable | Açıklama |
|----------|----------|
| `X_CONSUMER_KEY` / `X_CONSUMER_SECRET` | X API OAuth 1.0a app keys |
| `X_ACCESS_TOKEN` / `X_ACCESS_TOKEN_SECRET` | X API user tokens (User Context) |
| `X_HANDLE` | (opsiyonel) URL üretimi için, default `dolunayozeren` |
| `GROQ_API_KEY` | Groq API key |
| `GROQ_MODEL` | (opsiyonel) default `llama-3.3-70b-versatile` |
| `NOTION_SOCIAL_TOKEN` | Notion integration token |
| `NOTION_DB_REELS_KAPAK` | Kaynak DB ("Dolunay Reels & YouTube") |
| `NOTION_TWITTER_DB_ID` | Logger DB |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | (Railway) base64 encoded SA JSON; lokal: `_knowledge/credentials/google-service-account.json` |
| `VIDEO_PATTERN_PRIORITY` | (opsiyonel) Virgüllü liste, default `tiktok,insta` |
| `MAX_VIDEO_BYTES` | (opsiyonel) Üzerini skip et, default 500MB (X tweet_video limiti) |
| `REENCODE_OVER_BYTES` | (opsiyonel) Bunun üzerinde compress yap; default 200MB |

## Çalıştırma

```bash
ENV=development python main.py    # lokal DRY-RUN
RUN_MODE=cron python main.py      # Railway cron
```

## Deploy

Railway servis: `twitter-video-cron` (auto-deploy KAPALI; `serviceInstanceDeployV2` mutation
ile manuel commit deploy gerekli — bkz. `_knowledge/deploy-registry.md`).

## Notion DB Schema

Logger DB (`NOTION_TWITTER_DB_ID`) aşağıdaki kolonları içermelidir:

- `Video ID` (title) — Notion source page UUID
- `Status` (select) — `Success` / `Failed` / `Filtered`
- `Platform` (select) — `X (Twitter)`
- `Paylaşım Tarihi` (date)
- `TikTok URL` (url) — Notion source page URL (legacy isim, source_url olarak kullanılır)
- `Twitter URL` (url)
- `Caption` (rich_text)
- `Filter Sebebi` (rich_text)
