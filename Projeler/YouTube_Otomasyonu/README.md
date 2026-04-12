# YouTube Otomasyonu V2.3

> Chat-based Telegram bot ile otonom video üretimi sistemi.
> **Pets Got Talent** kanalı — 7/24 otonom çalışır.

## 🎯 Ne Yapıyor?

Telegram üzerinden doğal dilde sohbet ederek video üretimini başlatır:

1. **Sohbet** — Kullanıcı video fikrini anlatır
2. **Bilgi Toplama** — Bot sorular sorarak detayları netleştirir (model, format, süre)
3. **Viral Prompt Üretimi** — 21 kanıtlanmış senaryo havuzu + GPT-4.1 zenginleştirme
4. **Video Üretimi** — Kie AI üzerinden Seedance 2.0 veya Veo 3.1 ile video üretir
5. **Birleştirme** — Çoklu klipleri Replicate API (veya FFmpeg fallback) ile birleştirir
6. **YouTube Upload** — Data API v3 ile YouTube'a yükler (ENV-based OAuth2)
7. **Loglama** — Notion'a detaylı pipeline kaydı yazar

## 🏗️ Mimari

```
Kullanıcı → Telegram Bot → GPT-4.1 → Kie AI (Seedance/Veo) → Replicate Merge → YouTube Upload → Notion Log
```

### Desteklenen Modeller

| Model | Kalite | Fiyat | Kullanım |
|-------|--------|-------|----------|
| **Seedance 2.0** | 720p | 💰 Uygun | Genel amaçlı, kamera kontrolü, hızlı |
| **Veo 3.1** | 1080p | 💰💰💰 Premium | Sinematik, insan yüzleri |

### Telegram Komutları

| Komut | Açıklama |
|-------|----------|
| `/start` | Bot hakkında bilgi |
| `/yeni` | Yeni video talebi başlat |
| `/durum` | Bot ve pipeline durumu |
| `/modeller` | Kullanılabilir model bilgisi |
| 🎤 Sesli mesaj | Whisper ile transkript + işlem |

## 🔧 Ortam Değişkenleri

| Değişken | Zorunlu | Açıklama |
|----------|---------|----------|
| `TELEGRAM_YOUTUBE_BOT_TOKEN` | ✅ | YouTube bot token'ı |
| `OPENAI_API_KEY` | ✅ | GPT-4.1 + Whisper |
| `KIE_API_KEY` | ✅ | Kie AI video üretimi |
| `REPLICATE_API_TOKEN` | ✅ | Video birleştirme |
| `YOUTUBE_CLIENT_ID` | ⚡ | YouTube upload (Railway'de zorunlu) |
| `YOUTUBE_CLIENT_SECRET` | ⚡ | YouTube upload (Railway'de zorunlu) |
| `YOUTUBE_REFRESH_TOKEN` | ⚡ | YouTube OAuth2 refresh token (Railway'de zorunlu) |
| `YOUTUBE_ENABLED` | ❌ | `true` → YouTube'a yükle |
| `NOTION_SOCIAL_TOKEN` | ❌ | Notion API token |
| `NOTION_DB_YOUTUBE_OTOMASYON` | ❌ | Notion database ID |
| `ALLOWED_USER_IDS` | ❌ | Virgülle ayrılmış user ID'ler |
| `ENV` | ❌ | `production` veya `development` |

## 📁 Dosya Yapısı

```
YouTube_Otomasyonu/
├── main.py                          ← Telegram bot entry point
├── config.py                        ← Fail-fast config  
├── logger.py                        ← Standart logging
├── requirements.txt                 ← Pinned bağımlılıklar
├── nixpacks.toml                    ← Railway build config
├── core/
│   ├── conversation_manager.py      ← Chat-based sohbet motoru (GPT-4.1)
│   └── prompt_generator.py          ← Viral-optimized prompt üretimi
├── infrastructure/
│   ├── kie_client.py                ← Seedance + Veo unified client
│   ├── replicate_merger.py          ← Video birleştirme (Replicate + FFmpeg)
│   ├── youtube_uploader.py          ← YouTube Data API v3 upload
│   ├── notion_logger.py             ← Notion DB execution tracking
│   ├── telegram_notifier.py         ← Bildirim gönderici
│   └── video_downloader.py          ← Video indirici
└── topics.json                      ← Konu havuzu (ilham)
```

## 🚀 Deploy

Railway **Worker** servisi olarak deploy edilir (7/24 polling).

```bash
# Lokal test (dry-run)
export ENV=development
python main.py

# Production
export ENV=production
python main.py
```

## 🛡️ Stabilizasyon Geçmişi

| Tur | Tarih | Fix Sayısı | Öne Çıkan |
|-----|-------|------------|----------|
| V2.1 | 11 Nisan 2026 | 14 | Viral prompt engine, ENV-based YouTube upload |
| V2.2 | 12 Nisan 2026 | 2 | FFmpeg PATH resolve, video download retry |
| V2.3 | 12 Nisan 2026 | 5 | Event loop blocking fix, HTTP client reuse, Notion retry, nixpacks temizliği |

---

*Antigravity V2 — Enterprise standardında.*
