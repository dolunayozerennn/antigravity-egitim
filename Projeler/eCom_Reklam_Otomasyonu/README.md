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
1. **Bilgi Toplama** — GPT-5 Mini ile doğal sohbet (form doldurmak yok)
2. **Araştırma** — Perplexity ile marka analizi + GPT-5 Vision ile ürün görseli analizi
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
    ├── openai_service.py        ← GPT-5 Mini (chat + vision)
    ├── perplexity_service.py    ← Marka araştırması
    ├── imgbb_service.py         ← Görsel → Public URL
    ├── kie_api.py               ← Seedance 2.0 + Nano Banana 2
    ├── elevenlabs_service.py    ← Doğrudan ElevenLabs TTS
    ├── replicate_service.py     ← Video + ses birleştirme
    └── notion_service.py        ← Notion loglama
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

# OpenAI (GPT-5 Mini)
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5-mini

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

# Notion (Üretim logları)
NOTION_SOCIAL_TOKEN=...
NOTION_DB_ECOM_REKLAM=...
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
