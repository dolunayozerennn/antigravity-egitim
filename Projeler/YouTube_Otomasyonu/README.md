# YouTube Otomasyonu

Seedance 2.0 + GPT-4.1 tabanlı tam otonom YouTube Shorts üretim pipeline'ı.

## 🎯 Ne Yapar?

Her çalıştığında:
1. **Konu seçer** — genişletilebilir `topics.json`'dan rastgele (dedup'lı)
2. **Prompt üretir** — GPT-4.1 ile Seedance 2.0'a optimize edilmiş sinematik prompt
3. **Video üretir** — Seedance 2.0 (Kie AI) ile text-to-video (sesli)
4. **YouTube'a yükler** — YouTube Data API v3 ile otomatik upload
5. **Bildirim gönderir** — Telegram'a başarı/hata raporu
6. **Notion'a loglar** — Her adımı adım adım kaydeder

## 🏗️ Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Ortam değişkenlerini ayarla (.env dosyanız varsa)
export KIE_API_KEY=your_key
export OPENAI_API_KEY=your_key
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_ADMIN_CHAT_ID=your_chat_id

# Dry-run test (API çağırmaz)
ENV=development python main.py

# Production çalıştırma
ENV=production python main.py
```

## ⚙️ Ortam Değişkenleri

| Değişken | Zorunlu | Açıklama |
|----------|---------|----------|
| `OPENAI_API_KEY` | ✅ | GPT-4.1 prompt üretimi |
| `KIE_API_KEY` | ✅ | Seedance 2.0 video üretimi |
| `TELEGRAM_BOT_TOKEN` | ✅ | Bildirim gönderimi |
| `TELEGRAM_ADMIN_CHAT_ID` | ✅ | Bildirim alıcısı |
| `YOUTUBE_ENABLED` | ❌ | `true` = YouTube'a yükle |
| `YOUTUBE_CLIENT_ID` | ❌ | YouTube OAuth2 |
| `YOUTUBE_CLIENT_SECRET` | ❌ | YouTube OAuth2 |
| `NOTION_SOCIAL_TOKEN` | ❌ | Notion API token |
| `NOTION_DB_YOUTUBE_OTOMASYON` | ❌ | Notion database ID |
| `VIDEO_DURATION` | ❌ | Video süresi (default: 10s) |
| `VIDEO_ASPECT_RATIO` | ❌ | Aspect ratio (default: 9:16) |
| `GENERATE_AUDIO` | ❌ | Ses üretimi (default: true) |

## 📁 Proje Yapısı

```
YouTube_Otomasyonu/
├── main.py                     ← Orkestratör
├── config.py                   ← Fail-fast config
├── logger.py                   ← Standart logging
├── topics.json                 ← Konu havuzu (genişletilebilir)
├── requirements.txt            ← Pinned dependencies
├── nixpacks.toml               ← Railway deploy config
├── core/
│   ├── topic_picker.py         ← Konu seçimi + dedup
│   └── prompt_generator.py     ← GPT-4.1 prompt üretimi
└── infrastructure/
    ├── seedance_client.py      ← Kie AI Seedance 2.0 client
    ├── video_downloader.py     ← Video indirme
    ├── youtube_uploader.py     ← YouTube upload
    ├── telegram_notifier.py    ← Telegram bildirim
    └── notion_logger.py        ← Notion durum takibi
```
