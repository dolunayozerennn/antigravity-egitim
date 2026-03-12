# 🤖 Shorts Demo Otomasyonu

**Durum:** ✅ Railway 7/24 Aktif
**Agent:** 🚀 yayinla-paylas

---

## Açıklama

Telegram botu üzerinden AI video üretim pipeline'ı. Kullanıcılar bot'a mesaj/görsel göndererek reklam videoları ürettirebilir.

## Kullanılan Servisler

- **Telegram Bot API** — Kullanıcı arayüzü
- **OpenAI GPT-4.1** — Prompt üretimi
- **Kie AI** — Sora 2 Pro ile video üretimi
- **Fal AI** — Yedek video üretim

## Çalıştırma

```bash
# Lokal
cp config.env .env  # veya .env.example'dan kopyala
pip install -r requirements.txt
python bot.py

# Production (Railway)
# Railway'de environment variables ayarla → otomatik deploy
```

## Dosya Yapısı

| Dosya | Açıklama |
|-------|---------|
| `bot.py` | Ana bot mantığı |
| `config.env` | Lokal env dosyası (git'te yok) |
| `.env.example` | Env variable şablonu |
| `requirements.txt` | Python bağımlılıkları |
