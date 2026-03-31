> ⚠️ **ÖNEMLİ BİLGİLENDİRME**  
> Bu proje, eğitim ve örnekleme amacıyla hazırlanmış olan bir **taslak (template)** projedir. Doğrudan tıklayıp "çalıştır" (plug-and-play) mantığıyla tasarlanmamıştır. Kendi sisteminize entegre etmeden önce:
> - Kimlik bilgilerinizi (API anahtarları, token'lar, email adresleri) tanımlamanız
> - Dosya yollarını (file paths) ve bağlantıları kendi ortamınıza göre güncellemeniz
> - Senaryoyu kendi hedeflerinize göre özelleştirmeniz beklenmektedir.
> Lütfen bu kodları inceleyerek ve kendi senaryonuza uyarlayarak geliştirin.

# 📞 CRM Otomasyonu

> **⚠️ TASLAK PROJE:** Bu proje, bir AI otomasyon sisteminin iskelet yapısını göstermek amacıyla paylaşılmıştır. Tam çalışır durumda değildir — kendi iş süreçlerinize göre uyarlamanız ve tamamlamanız beklenmektedir. Notion veritabanınızı, Google Sheets'inizi ve API anahtarlarınızı eklemeniz gerekir.

**Versiyon:** v3 — Bulk dedup + SHEET_TABS env config

---

## Açıklama

Notion veritabanı ile Google Sheets arasında otomatik senkronizasyon yapan CRM sistemi. Tele-satış ekibinin müşteri takip süreçlerini otomatikleştirir.

Meta reklamlarından gelen lead'leri Google Sheets'ten okur, temizler, **toplu duplikasyon kontrolü** yapar ve Notion CRM'e yazar.

### Temel Özellikler

- **Toplu Duplikasyon Kontrolü** — Tüm lead'lerin telefon/emaili tek sorguda kontrol edilir
- **SHEET_TABS env config** — Yeni aya geçişte kod değişikliği gerekmez, sadece env variable güncellenir
- **Timing Field** — Her lead'e eklenme zamanı kaydedilir
- **Graceful Shutdown** — `SIGTERM`/`SIGINT` sinyallerinde düzgün kapanma
- **SSL Reconnect** — Ağ kopmalarında otomatik yeniden bağlanma

## Kullanılan Servisler

- **Notion API** — CRM veritabanı
- **Google Sheets API** — Lead verisi kaynağı
- **Gmail API** — Hata bildirimi (opsiyonel)

---

## Dosya Yapısı

```
CRM_Otomasyonu/
├── main.py              # Ana uygulama — polling loop + toplu dedup orkestrasyon
├── config.py            # Env variable okuma + SA JSON parse + SHEET_TABS
├── sheets_reader.py     # Google Sheets okuma + dual-auth (SA / OAuth)
├── notion_writer.py     # Notion CRM'e lead yazma + toplu duplikasyon kontrolü
├── data_cleaner.py      # Veri temizleme (telefon, isim, email, bütçe)
├── notifier.py          # Hata bildirimi
├── .env.example         # Env variable şablonu
├── railway.json         # Railway deploy konfigürasyonu
├── run_test.py          # Hızlı test koşturucusu
└── tests/
    ├── test_comprehensive.py   # Kapsamlı test paketi
    └── test_data_cleaner.py    # Veri temizleme unit testleri
```

## Çalıştırma

```bash
# Lokal Geliştirme
cp .env.example .env
pip install -r requirements.txt
python main.py               # Sürekli polling (5 dk)
python main.py --once        # Tek döngü
```

## Environment Variables

| Variable | Zorunlu | Açıklama |
|----------|---------|----------|
| `NOTION_API_TOKEN` | ✅ | Notion API anahtarı |
| `NOTION_DATABASE_ID` | ❌ | Notion DB ID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ⚠️ Railway | SA JSON (lokalde gerek yok) |
| `SPREADSHEET_ID` | ❌ | Google Sheet ID |
| `SHEET_TABS` | ❌ | İzlenecek tab adları |
| `POLL_INTERVAL_SECONDS` | ❌ | Polling aralığı (varsayılan: 300) |
| `DEDUP_WINDOW_DAYS` | ❌ | Duplikasyon penceresi gün |

---

*Antigravity ile oluşturulmuş taslak projedir.*
