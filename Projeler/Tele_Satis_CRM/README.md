# 📞 Tele Satış CRM

**Durum:** ⏳ Railway Deploy (Env vars eksik)
**Agent:** —

---

## Açıklama

Notion veritabanı ile Google Sheets arasında otomatik senkronizasyon yapan CRM sistemi. Tele-satış ekibinin müşteri takip süreçlerini otomatikleştirir.

## Kullanılan Servisler

- **Notion API** — CRM veritabanı
- **Google Sheets API** — Veri senkronizasyonu
- **Gmail SMTP** — Hata bildirimi (opsiyonel)

## Çalıştırma

```bash
# Lokal
cp .env.example .env  # Değerleri doldur
pip install -r requirements.txt
python main.py

# Production (Railway)
# Railway'de environment variables ayarla → otomatik deploy
```

## Dosya Yapısı

| Dosya | Açıklama |
|-------|---------|
| `main.py` | Ana uygulama |
| `config.py` | Konfigürasyon yönetimi |
| `.env.example` | Env variable şablonu |
| `requirements.txt` | Python bağımlılıkları |
