---
name: sifre-yonetici
description: API tokenlarını ve servis bağlantılarını projeler arasında merkezi olarak yönetir. Yeni proje başlatırken otomatik olarak gerekli tokenları keşfeder ve bağlar.
---

# 🔐 Şifre Yönetici Skill

Bu skill, Antigravity ekosistemindeki tüm API token ve servis bağlantılarını merkezi olarak yönetir.

## Mimari

```
_knowledge/credentials/
├── master.env                      ← TÜM tokenlar burada (tek kaynak)
├── google-service-account.json     ← Google Cloud Service Account
├── oauth/
│   ├── gmail-outreach-token.json
│   └── gmail-swc-token.json
└── README.md

Projeler/XYZ_Proje/
├── .env → symlink → ../../_knowledge/credentials/master.env
│   VEYA
├── .env  ← master.env'den sadece gerekli satırlar kopyalanır
```

## ⚡ Otomatik Çalışma Kuralı

> **ÖNEMLİ:** Bu skill, yeni bir proje oluşturulduğunda veya bir projede API/token ihtiyacı tespit edildiğinde **otomatik olarak** devreye girer. Kullanıcının ayrıca talimat vermesine gerek yoktur.

### Otomatik Tetikleme Koşulları:
1. Yeni bir proje klasörü oluşturulduğunda
2. Bir projeye API kullanan kod eklendiğinde (import openai, requests.post vb.)
3. Kullanıcı "projeye şifreleri/tokenları bağla" dediğinde
4. Kullanıcı `/sifre-bagla` workflow'unu çağırdığında
5. Kullanıcı yeni bir API anahtarı verdiğinde → önce `master.env`'e ekle, sonra ilgili projelere dağıt

## Kullanım Senaryoları

### 1. Yeni Proje Kurulumu

Bir proje oluşturulduğunda veya kullanıcı "projeye tokenları bağla" dediğinde:

```bash
# Projenin ihtiyaçlarını analiz et
python3 _skills/sifre-yonetici/scripts/env_manager.py analyze Projeler/Yeni_Proje

# Gerekli tokenları bağla (filtrelenmiş .env oluştur)
python3 _skills/sifre-yonetici/scripts/env_manager.py generate Projeler/Yeni_Proje --services openai,telegram,kie

# VEYA symlink ile tüm tokenlara erişim ver
python3 _skills/sifre-yonetici/scripts/env_manager.py link Projeler/Yeni_Proje
```

### 2. Token Güncelleme

Bir token değiştiğinde:

```bash
# master.env'deki değeri güncelle
python3 _skills/sifre-yonetici/scripts/env_manager.py update OPENAI_API_KEY "yeni-token-değeri"

# Symlink kullanan projeler otomatik güncellenir
# Filtrelenmiş .env kullanan projeleri yenile
python3 _skills/sifre-yonetici/scripts/env_manager.py refresh-all
```

### 3. Güvenlik Taraması

```bash
# Projelerdeki hardcoded tokenları tespit et
python3 _skills/sifre-yonetici/scripts/env_manager.py scan
```

### 4. Google Service Account Bağlama

Google Cloud Service Account dosyası merkezi depoda saklanır:
```
_knowledge/credentials/google-service-account.json
```

Proje bu dosyaya ihtiyaç duyarsa:
```bash
# Symlink oluştur
ln -sf ../../_knowledge/credentials/google-service-account.json Projeler/XYZ/service-account.json

# VEYA environment variable olarak JSON string'ini .env'e ekle
python3 _skills/sifre-yonetici/scripts/env_manager.py generate Projeler/XYZ --services google_service_account
```

## AI Agent Entegrasyonu

AI agent olarak bu skill'i kullanırken şu adımları takip et:

### Adım 1: İhtiyaç Analizi
Projenin kodunu tara ve hangi servislere ihtiyaç duyduğunu belirle:
- `import openai` → `OPENAI_API_KEY` gerekli
- `import telegram` → `TELEGRAM_BOT_TOKEN` gerekli
- `from dotenv import load_dotenv` → `.env` dosyası gerekli
- `requests.post("https://api.kie.ai")` → `KIE_API_KEY` gerekli
- `service_account.Credentials` → Google Service Account dosyası gerekli

### Adım 2: .env Oluştur veya Bağla
İki strateji var:

**A. Symlink (Önerilen — küçük/güvenli projeler):**
```bash
ln -sf ../../_knowledge/credentials/master.env Projeler/XYZ/.env
```
- ✅ Token güncellendiğinde otomatik yansır
- ✅ Hiçbir kopyalama gerekli değil
- ⚠️ Tüm tokenlara erişim verir

**B. Filtrelenmiş .env (Büyük/paylaşılacak projeler):**
```bash
python3 _skills/sifre-yonetici/scripts/env_manager.py generate Projeler/XYZ --services openai,telegram
```
- ✅ Sadece gerekli tokenlar dahil edilir
- ✅ Paylaşıma daha güvenli
- ⚠️ Token güncellendiğinde yeniden oluşturulmalı

### Adım 3: Doğrulama
```bash
python3 _skills/sifre-yonetici/scripts/env_manager.py verify Projeler/XYZ
```

## Servis Haritası

Aşağıdaki tablo, her servis için hangi environment variable'ların gerektiğini gösterir:

| Servis | Gerekli Değişkenler | Opsiyonel |
|--------|---------------------|-----------|
| OpenAI | `OPENAI_API_KEY` | |
| Groq | `GROQ_API_KEY` | `GROQ_BASE_URL` |
| Perplexity | `PERPLEXITY_API_KEY` | `PERPLEXITY_BASE_URL` |
| Kie AI | `KIE_API_KEY` | `KIE_BASE_URL` |
| Fal AI | `FAL_API_KEY` | `FAL_BASE_URL` |
| ImgBB | `IMGBB_API_KEY` | `IMGBB_BASE_URL` |
| Google Cloud | `GOOGLE_CLOUD_API_KEY` | |
| Google Service Account | `google-service-account.json` dosyası | |
| Apify | `APIFY_API_KEY` | `APIFY_API_KEY_YEDEK` |
| Hunter.io | `HUNTER_API_KEY` | |
| Apollo.io | `APOLLO_API_KEY` | |
| Gmail (Outreach) | `GMAIL_OUTREACH_CLIENT_ID`, `GMAIL_OUTREACH_CLIENT_SECRET` | |
| Gmail (Sweatcoin) | `GMAIL_SWC_CLIENT_ID`, `GMAIL_SWC_CLIENT_SECRET` | |
| Telegram | `TELEGRAM_BOT_TOKEN` | `TELEGRAM_ADMIN_CHAT_ID` |
| Telegram (Shorts) | `TELEGRAM_SHORTS_BOT_TOKEN` | |
| ElevenLabs | `ELEVENLABS_API_KEY` | |
| Railway | `RAILWAY_TOKEN` | |

## OAuth Token Yönetimi

Google OAuth token dosyaları (`token.json`, `token.pickle`) merkezi klasörde saklanır:
```
_knowledge/credentials/oauth/
├── gmail-outreach-token.json    ← ozerendolunay@gmail.com
├── gmail-outreach-credentials.json
├── gmail-swc-token.pickle       ← d.ozeren@sweatco.in
└── reels-kapak-token.json       ← Drive/Sheets erişimi
```

Proje bu dosyalara ihtiyaç duyarsa:
```bash
# Symlink oluştur
ln -sf ../../../_knowledge/credentials/oauth/gmail-outreach-token.json Projeler/XYZ/token.json
```

## Güvenlik Kuralları

1. **`master.env` asla GitHub'a gitmez** — `.gitignore` ile korunur
2. **`google-service-account.json` asla GitHub'a gitmez** — `.gitignore` ile korunur
3. **Hardcoded token yasak** — Tarama scripti ile tespit et
4. **Paylaşılan projelerde `.env.example` kullan** — asıl değerler yerine placeholder
5. **Railway/Cloud deploy'da** — `master.env`'deki değerler Railway environment variables olarak ayrıca set edilir
