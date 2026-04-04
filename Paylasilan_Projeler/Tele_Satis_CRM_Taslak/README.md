# 📞 Tele Satış CRM

Google Forms → Google Sheets → Notion CRM otomasyonu.

Gelen lead'leri otomatik temizler, duplikasyon kontrolü yapar ve Notion veritabanına aktarır. Railway üzerinde 7/24 çalışabilir.

---

## 🏗️ Mimari

```
Google Form
    ↓ (yanıtlar otomatik Sheet'e düşer)
Google Sheets
    ↓ (sheets_reader.py — Service Account ile okur)
Data Cleaner
    ↓ (isim, telefon, email, bütçe normalizasyonu)
Duplikasyon Kontrolü
    ↓ (Notion API ile mevcut lead kontrolü)
Notion CRM Veritabanı
    ↓ (opsiyonel hata bildirimi)
E-posta Bildirimi (SMTP)
```

## 📁 Dosya Yapısı

```
Tele_Satis_CRM/
├── main.py              → Ana polling döngüsü
├── config.py            → Merkezi konfigürasyon (env vars)
├── sheets_reader.py     → Google Sheets okuyucu
├── data_cleaner.py      → Veri temizleme & normalizasyon
├── notion_writer.py     → Notion API ile lead yazma
├── notifier.py          → Hata bildirim (SMTP)
├── run_test.py          → Tek döngü test scripti
├── auto_dedup_all.py    → Toplu duplike temizleme
├── check_notion.py      → Notion kayıt listesi
├── cleanup_duplicates.py→ Tarihli duplike temizleme
├── inspect_notion.py    → Veritabanı schema görüntüleyici
├── requirements.txt     → Python bağımlılıkları
├── .env.example         → Ortam değişkenleri şablonu
├── .gitignore           → Git ignore kuralları
├── railway.json         → Railway deploy yapılandırması
├── tests/               → Birim testleri
│   ├── test_data_cleaner.py
│   └── test_comprehensive.py
└── KURULUM_REHBERI.md   → Detaylı kurulum talimatları
```

## ⚡ Hızlı Başlangıç

```bash
# 1. Bağımlılıkları kur
pip install -r requirements.txt

# 2. .env dosyasını oluştur
cp .env.example .env
# .env dosyasını düzenleyip kendi API anahtarlarınızı girin

# 3. Test çalıştır
python run_test.py

# 4. Üretim modunda başlat
python main.py
```

📖 Detaylı kurulum talimatları için → [KURULUM_REHBERI.md](KURULUM_REHBERI.md)

## 🔑 Gerekli Hesaplar

| Servis | Ne İçin | Zorunlu mu? |
|---|---|---|
| Google Cloud | Sheets API erişimi | ✅ Evet |
| Notion | CRM veritabanı | ✅ Evet |
| Railway | 7/24 sunucu | ❌ Opsiyonel |
| Gmail | Hata bildirimi | ❌ Opsiyonel |

## 🔧 Temel Özellikler

- **Otomatik Polling** — Yeni form yanıtlarını düzenli kontrol eder
- **Akıllı Duplikasyon** — Telefon, email ve isim bazlı 3 katmanlı kontrol
- **Veri Temizleme** — İsim, telefon, bütçe otomatik normalizasyonu
- **WhatsApp Entegrasyonu** — Telefon numarasından otomatik WA linki
- **Hata Toleransı** — Rate limit, retry, graceful error handling
- **Bildirim Sistemi** — Hata durumunda otomatik e-posta

## 📝 Lisans

Bu proje eğitim amaçlıdır. Ticari kullanımda ilgili API servis sağlayıcılarının kullanım koşulları geçerlidir.
