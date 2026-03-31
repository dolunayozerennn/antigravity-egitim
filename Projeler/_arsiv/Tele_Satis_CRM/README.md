# 📞 Tele Satış CRM

**Durum:** ✅ Railway Active  
**Versiyon:** v3 — Bulk dedup + SHEET_TABS env config  
**Son Güncelleme:** 2026-03-17

---

## Açıklama

Notion veritabanı ile Google Sheets arasında otomatik senkronizasyon yapan CRM sistemi. Tele-satış ekibinin müşteri takip süreçlerini otomatikleştirir.

Meta reklamlarından gelen lead'leri Google Sheets'ten okur, temizler, **toplu duplikasyon kontrolü** yapar ve Notion CRM'e yazar.

### Temel Özellikler

- **Toplu Duplikasyon Kontrolü** — Tüm lead'lerin telefon/emaili tek sorguda kontrol edilir (API çağrısı minimize)
- **SHEET_TABS env config** — Yeni aya geçişte kod değişikliği gerekmez, sadece Railway env variable güncellenir
- **Timing Field** — Her lead'e eklenme zamanı kaydedilir
- **Graceful Shutdown** — `SIGTERM`/`SIGINT` sinyallerinde düzgün kapanma
- **SSL Reconnect** — Ağ kopmalarında otomatik yeniden bağlanma
- **Hata Bildirimi** — Gmail SMTP ile hata e-postası (opsiyonel)

## Kullanılan Servisler

- **Notion API** — CRM veritabanı
- **Google Sheets API** — Lead verisi kaynağı
- **Gmail SMTP** — Hata bildirimi (opsiyonel)

---

## 🔐 Authentication Mimarisi (Dual-Auth)

Bu proje **iki farklı ortam** için **iki farklı authentication yöntemi** kullanır:

```
┌─────────────────────────────────────────────────────────┐
│                    Tele_Satis_CRM                       │
│                                                         │
│  ┌──────────────────┐       ┌────────────────────────┐  │
│  │  🚂 Railway      │       │  💻 Lokal Geliştirme   │  │
│  │  (Production)    │       │                        │  │
│  │                  │       │                        │  │
│  │  Service Account │       │  Merkezi OAuth 2.0     │  │
│  │  (JSON env var)  │       │  (google_auth.py)      │  │
│  └──────┬───────────┘       └───────────┬────────────┘  │
│         │                               │               │
│         ▼                               ▼               │
│  GOOGLE_SERVICE_         _knowledge/credentials/oauth/  │
│  ACCOUNT_JSON              google_auth.py               │
│                            → get_sheets_service()       │
└─────────────────────────────────────────────────────────┘
```

### 🚂 Railway (Production) — Google Service Account

| Özellik | Değer |
|---------|-------|
| **Yöntem** | Google Service Account |
| **Email** | `gmail-n8n@massive-hexagon-369717.iam.gserviceaccount.com` |
| **Proje** | `massive-hexagon-369717` |
| **Env Variable** | `GOOGLE_SERVICE_ACCOUNT_JSON` (JSON tek satır) |
| **Scope** | `spreadsheets.readonly` |
| **Token Yenileme** | Otomatik (JWT tabanlı, süresi dolmaz) |

**Nasıl çalışır:**
1. Railway'de `GOOGLE_SERVICE_ACCOUNT_JSON` env variable'ı SA JSON'u içerir
2. `config.py` → `get_google_credentials_info()` ile parse eder
3. `sheets_reader.py` → `service_account.Credentials.from_service_account_info()` ile auth yapar
4. Token yenileme gerekmez — SA her istekte yeni JWT imzalar

### 💻 Lokal Geliştirme — Merkezi OAuth 2.0

| Özellik | Değer |
|---------|-------|
| **Yöntem** | OAuth 2.0 (merkezi Antigravity sistemi) |
| **Hesap** | `ozerendolunay@gmail.com` ("outreach" profili) |
| **Modül** | `_knowledge/credentials/oauth/google_auth.py` |
| **Scope** | Gmail + Drive + Sheets (geniş scope) |
| **Token Yenileme** | Otomatik (refresh_token ile) |

**Nasıl çalışır:**
1. `GOOGLE_SERVICE_ACCOUNT_JSON` env variable'ı tanımlı değilse lokal moda düşer
2. `_knowledge/credentials/oauth/google_auth.py` import edilir
3. `get_sheets_service("outreach")` çağrılır
4. Token otomatik yenilenir (refresh_token mevcut)

### Fallback Mantığı (`sheets_reader.py`)

```python
def authenticate(self):
    sa_info = Config.get_google_credentials_info()
    if sa_info:
        # Railway: Service Account
        creds = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    else:
        # Lokal: Merkezi google_auth
        from google_auth import get_sheets_service
        self.service = get_sheets_service("outreach")
```

### ⚠️ Önemli Notlar

1. **Sheet paylaşımı zorunlu** — Service Account'un Sheet'e erişebilmesi için, Sheet Google Drive'da SA email adresiyle paylaşılmış olmalı
2. **SA sadece Sheets okur** — Gmail veya Drive erişimi yok (scope: `spreadsheets.readonly`)
3. **Lokal mod daha geniş** — OAuth token'ı Gmail + Drive + Sheets scope'larını kapsar
4. **SA key rotasyonu** — SA private key değişirse `GOOGLE_SERVICE_ACCOUNT_JSON` Railway'de güncellenmeli

---

## Service Account Yetki Durumu

> Son kontrol: 2026-03-17

| Kaynak | Erişim | Not |
|--------|--------|-----|
| `Skool - Dolunay Özeren Leads` | ✅ Var | Aktif tab(lar) okunabiliyor |
| Tab: `Mart-2026-Saat Bazlı-v2` | ✅ OK | Şu an izlenen tab (SHEET_TABS env ile ayarlanır) |
| Scope: `spreadsheets.readonly` | ✅ OK | Sadece okuma |

---

## Çalıştırma

```bash
# Lokal Geliştirme
cp .env.example .env        # Sadece NOTION_API_TOKEN gerekli (SA opsiyonel)
pip install -r requirements.txt
python main.py               # Sürekli polling (5 dk)
python main.py --once        # Tek döngü

# Production (Railway)
# Railway'de environment variables ayarla:
#   - NOTION_API_TOKEN
#   - GOOGLE_SERVICE_ACCOUNT_JSON (SA JSON tek satır)
# Push → otomatik deploy
```

## Dosya Yapısı

```
Tele_Satis_CRM/
├── main.py              # Ana uygulama — polling loop + toplu dedup orkestrasyon
├── config.py            # Env variable okuma + SA JSON parse + SHEET_TABS
├── sheets_reader.py     # Google Sheets okuma + dual-auth (SA / OAuth)
├── notion_writer.py     # Notion CRM'e lead yazma + toplu duplikasyon kontrolü
├── data_cleaner.py      # Veri temizleme (telefon, isim, email, bütçe)
├── notifier.py          # Hata bildirimi (Gmail SMTP)
├── .env.example         # Env variable şablonu
├── railway.json         # Railway deploy konfigürasyonu
├── run_test.py          # Hızlı test koşturucusu
├── tests/
│   ├── test_comprehensive.py   # Kapsamlı test paketi
│   └── test_data_cleaner.py    # Veri temizleme unit testleri
└── Yardımcı Scriptler (ad-hoc kullanım)
    ├── auto_dedup_all.py        # Notion'daki duplikeleri temizleme
    ├── backfill_whatsapp.py     # Mevcut lead'lere WhatsApp linki ekleme
    ├── check_notion.py          # Notion DB kontrol
    ├── cleanup_duplicates.py    # Duplike temizleme
    └── inspect_notion.py        # Notion kayıtlarını inceleme
```

## Environment Variables

| Variable | Zorunlu | Açıklama |
|----------|---------|----------|
| `NOTION_API_TOKEN` | ✅ | Notion API anahtarı |
| `NOTION_DATABASE_ID` | ❌ | Notion DB ID (varsayılan mevcut) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ⚠️ Railway | SA JSON (lokalde gerek yok) |
| `SPREADSHEET_ID` | ❌ | Google Sheet ID (varsayılan mevcut) |
| `SHEET_TABS` | ❌ | İzlenecek tab adları, virgülle ayrılır (varsayılan: config.py'da tanımlı) |
| `POLL_INTERVAL_SECONDS` | ❌ | Polling aralığı saniye (varsayılan: 300) |
| `DEDUP_WINDOW_DAYS` | ❌ | Duplikasyon penceresi gün (varsayılan: 7) |
| `ERROR_NOTIFY_EMAIL` | ❌ | Hata bildirim adresi |
| `SMTP_USER` | ❌ | Gmail SMTP kullanıcısı |
| `SMTP_APP_PASSWORD` | ❌ | Gmail App Password |

> **Yeni Aya Geçiş:** Yeni tab açıldığında sadece Railway'deki `SHEET_TABS` env variable'ını güncelle.  
> Örnek: `Mart-2026-Saat Bazlı-v2` → `Nisan-2026-Saat Bazlı-v1`  
> Kod değişikliği gerekmez.
