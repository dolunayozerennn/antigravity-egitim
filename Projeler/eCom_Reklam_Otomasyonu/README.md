# eCom Reklam Otomasyonu

> Telegram bot ile profesyonel ürün reklam videoları üretim otomasyonu.
> Seedance 2.0 + ElevenLabs + Replicate pipeline.

**Proje:** Antigravity Ecosystem  
**Tip:** Telegram Bot (Worker — Polling)  
**Durum:** 🟢 Production Ready

---

## 🎯 Ne Yapar?

Kullanıcı Telegram'dan bir ürün ve marka bilgisi paylaşır → Bot doğal sohbetle bilgi toplar → Marka araştırması yapar → AI ile reklam senaryosu üretir → Maliyet hesaplar → Onay sonrası sinematik reklam videosu üretir.

### Pipeline Adımları:
1. **Bilgi Toplama** — GPT-4.1 Mini ile doğal sohbet (form doldurmak yok)
2. **Araştırma** — Perplexity ile marka analizi + GPT-4.1 Vision ile ürün görseli analizi
3. **Senaryo** — AI ile shot listesi, dış ses metni, maliyet hesaplama
4. **Görsel** — Nano Banana 2 ile sinematik giriş karesi
5. **Video** — Seedance 2.0 ile reklam videosu üretimi
6. **Dış Ses** — ElevenLabs ile profesyonel Türkçe seslendirme
7. **Birleştirme** — Replicate ile video + ses merge
8. **Teslim** — Video Telegram'a gönderilir + Notion'a loglanır

---

## 🏗️ Mimari

```
eCom_Reklam_Otomasyonu/
├── main.py                      ← Telegram bot entry point
├── config.py                    ← Fail-fast env doğrulama
├── logger.py                    ← Standart logger
├── requirements.txt             ← Kilitli bağımlılıklar
├── nixpacks.toml                ← Railway deploy config
├── .env.example                 ← Örnek env dosyası
├── .gitignore                   ← Güvenlik
├── README.md                    ← Bu dosya
├── core/
│   ├── __init__.py
│   ├── conversation_manager.py  ← State machine + doğal sohbet
│   ├── scenario_engine.py       ← Senaryo üretim + maliyet hesaplama
│   └── production_pipeline.py   ← Video üretim orchestrator
└── services/
    ├── __init__.py
    ├── openai_service.py        ← GPT-4.1 Mini (chat + vision)
    ├── perplexity_service.py    ← Marka araştırması
    ├── imgbb_service.py         ← Görsel → Public URL
    ├── kie_api.py               ← Seedance 2.0 + Nano Banana 2
    ├── elevenlabs_service.py    ← Doğrudan ElevenLabs TTS
    ├── replicate_service.py     ← Video + ses birleştirme
    ├── notion_service.py        ← Notion loglama
    └── chat_logger.py           ← Notion Chat Hafızası
```

---

## 🔄 Conversation Flow

```
/start → Hoş geldin mesajı
   ↓
CHATTING: Doğal sohbetle bilgi toplama
   → Marka adı, ürün, fotoğraf, konsept, süre, format, dil
   ↓
RESEARCHING: Perplexity + GPT Vision
   ↓
SCENARIO_APPROVAL: Senaryo + maliyet → [Onayla] [Düzelt] [İptal]
   ↓
PRODUCING: Nano Banana 2 → Seedance 2.0 → ElevenLabs → Replicate
   ↓
DELIVERED: Video gönderildi + Notion log
```

---

## 💰 Maliyet Tablosu (Seedance 2.0)

| Çözünürlük | Image-to-Video | Text-to-Video |
|------------|---------------|---------------|
| **480p** | 11.5 credit/s ($0.058/s) | 19 credit/s ($0.095/s) |
| **720p** | 25 credit/s ($0.125/s) | 41 credit/s ($0.205/s) |

**Tipik örnekler:**
- 10s, 720p, image-to-video: $1.25
- 10s, 480p, image-to-video: $0.58
- 15s, 720p, text-to-video: $3.08

---

## ⚙️ Ortam Değişkenleri

```env
# Mod
ENV=production                    # development = dry-run

# Telegram
TELEGRAM_ECOM_BOT_TOKEN=...
TELEGRAM_ADMIN_CHAT_ID=1238877494

# OpenAI (GPT-4.1 Mini)
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini

# Perplexity
PERPLEXITY_API_KEY=...

# ImgBB
IMGBB_API_KEY=...

# Kie AI (Seedance 2.0 + Nano Banana 2)
KIE_API_KEY=...

# ElevenLabs (Türkçe dış ses)
ELEVENLABS_API_KEY=...
ELEVENLABS_MODEL=eleven_multilingual_v2

# Replicate (Video+ses birleştirme)
REPLICATE_API_TOKEN=...

# Notion (Üretim logları & Chat)
NOTION_SOCIAL_TOKEN=...
NOTION_DB_ECOM_REKLAM=...
NOTION_CHAT_DB_ID=34095514-0a32-81a2-9af3-e06cf9b8c4fd
```

---

## 🚀 Kullanım

### Lokal (DRY-RUN):
```bash
export ENV=development
# .env dosyasından değişkenleri yükle
python main.py
```

### Railway Deploy:
- **Builder:** Nixpacks (Python 3.11)
- **Start command:** `python main.py`
- **Tip:** Worker (CronJob DEĞİL — sürekli polling)

---

## 🛡️ Erişim Kontrolü

Bot sadece `TELEGRAM_ADMIN_CHAT_ID` ile tanımlanan kullanıcıya yanıt verir.
Diğer kullanıcılara "⛔ Bu botu kullanma yetkiniz yok." mesajı döner.

---

## 📊 Notion Loglama

Her üretim Notion database'ine kaydedilir:
- Marka, Ürün, Konsept
- Video Süresi, Format, Çözünürlük, Dil
- Tahmini Maliyet ($)
- Durum (Üretiliyor / Tamamlandı / Hata)
- Video URL, Hata Mesajı
- Tarih

---

## 🧪 Test Suite

Proje, 68 otonom test içeren kapsamlı bir test altyapısına sahiptir.

### Çalıştırma:
```bash
# Önce env değişkenlerini yükle (master.env veya Railway env)
source .venv/bin/activate
python test_bot.py
```

### Test Grupları:
| Grup | Test Sayısı | Açıklama |
|------|------------|----------|
| İmport & Config | 18 | Tüm modüllerin import testi + config doğrulama |
| State Machine | 7 | `/start`, session reset, fotoğraf, state koruması |
| LLM Bilgi Çıkarma | 15 | GPT-4.1 Mini ile doğal sohbet + JSON çıkarma |
| Senaryo Engine | 8 | Maliyet hesabı, senaryo özeti formatı |
| Servis Bağlantıları | 6 | OpenAI, Perplexity, Kie AI, ElevenLabs gerçek API |
| Edge Cases | 7 | Uzun mesaj, emoji, İngilizce, çoklu /start |
| Pipeline DRY-RUN | 3 | Tam production pipeline simülasyonu |
| Notion Çıkarma | 3 | URL → Page ID dönüşümü |
| Voiceover Tahmini | 2 | TTS süre hesabı |

> **Not:** Test suite gerçek API çağrıları yapar. Env değişkenleri (OPENAI_API_KEY, KIE_API_KEY vb.) tanımlı olmalıdır.

---

## 📝 Bilinen Konular & Notlar

- **Model:** GPT-4.1 Mini kullanılıyor (GPT-5 Mini reasoning modelindeki boş content sorunu nedeniyle geçiş yapıldı). Retry mekanizması korunuyor.
- **ElevenLabs ses değişiklikleri:** Sesler kaldırılabilir. Varsayılan ses: **Sarah** (Kadın, olgun, güven verici).
- **DRY-RUN:** `ENV=development` veya `DRY_RUN=1` ayarlandığında pipeline gerçek API çağrısı yapmaz, simülasyon döner.
- **Async/Sync dengesi:** Proje asyncio tabanlı; dış servisler senkron `requests` kullanır. Tüm blocking API çağrıları `asyncio.to_thread()` ile sarmalanır.
- **Audio hosting:** Birincil: tmpfiles.org (24 saat TTL), fallback: file.io (tek kullanımlık).
- **Bellek yönetimi:** Session'lar 10dk inaktivite sonrası temizlenir, chat geçmişi 20 mesajla sınırlıdır.
- **Input validasyonu:** aspect_ratio ("9:16", "16:9", "1:1"), resolution ("480p", "720p"), video_duration (int cast) otomatik normalize edilir.

---

## 📋 Değişiklik Geçmişi

| Tarih | Değişiklik |
|----------|------------|
| 2026-04-14 | **v2.6 Stabilizasyon** — Kapsamlı kod ve bağımlılık health check çalıştırıldı. Sistem tamamıyla stabil ve architecture-strict hale getirildi. |
| 2026-04-12 | **v2.5 Yeni Özellik** — Chat Hafızası (Notion Inline Database) entegrasyonu, asenkron konuşma loglaması |
| 2026-04-12 | **v2.1 Stabilizasyon** — 24 bug fix: event loop blocking aşıldı (asyncio.to_thread), Vision API NoneType retry, session bellek sızıntısı TTL cleanup, Markdown parse fallback, Perplexity exception handling, aspect_ratio/resolution validasyonu, voiceover süre kontrolü, tmpfiles.org fallback, Replicate FileOutput cast, asyncio task hata yutma fix'i |
| 2026-04-11 | İlk deploy → Railway SUCCESS |
| 2026-04-11 | GPT-5 Mini API uyumluluğu: `max_tokens`→`max_completion_tokens`, `temperature` kaldırıldı |
| 2026-04-11 | Boş content retry mekanizması (3 deneme) |
| 2026-04-11 | ElevenLabs Rachel→Sarah ses güncellemesi |
| 2026-04-11 | 68 testlik otonom test suite eklendi |
| 2026-04-11 | Model değişikliği: GPT-5 Mini → GPT-4.1 Mini (reasoning model boş content sorunu) |

