> ⚠️ **ÖNEMLİ BİLGİLENDİRME**  
> Bu proje, eğitim ve örnekleme amacıyla hazırlanmış olan bir **taslak (template)** projedir. Doğrudan tıklayıp "çalıştır" (plug-and-play) mantığıyla tasarlanmamıştır. Kendi sisteminize entegre etmeden önce:
> - Kimlik bilgilerinizi (API anahtarları, token'lar, email adresleri) tanımlamanız
> - Dosya yollarını (file paths) ve bağlantıları kendi ortamınıza göre güncellemeniz
> - Senaryoyu kendi hedeflerinize göre özelleştirmeniz beklenmektedir.
> Lütfen bu kodları inceleyerek ve kendi senaryonuza uyarlayarak geliştirin.

# 🤝 Marka Outreach — Otomatik İş Birliği Sistemi

> **⚠️ TASLAK PROJE:** Bu proje, bir AI otomasyon sisteminin iskelet yapısını göstermek amacıyla paylaşılmıştır. Tam çalışır durumda değildir — kendi iş süreçlerinize göre uyarlamanız ve tamamlamanız beklenmektedir. API anahtarlarınızı, rakip listenizi ve email template'lerinizi eklemeniz gerekir.

Markalarla iş birliği kurma, kişiselleştirilmiş outreach gönderimi ve follow-up yönetim sistemi.

---

## 📌 Amaç

Influencer olarak markalarla iş birliği kurmak için kullanılan **tam otomatik outreach pipeline'ıdır**. Rakip influencer'ların reels'lerini analiz ederek yeni markaları keşfeder, iletişim bilgilerini bulur, GPT ile kişiselleştirilmiş email üretir ve 3 adımlı email sequence ile takip eder.

## 🔄 Pipeline Akışı

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  1. Scrape    │ →  │  2. Analyze   │ →  │  3. Find Contacts │ →  │  4. Personalize   │ →  │  5. Send Email    │
│  (Apify)      │    │  (AI Brand    │    │  (Apollo + Hunter) │    │  (GPT-4.1-nano)   │    │  (Gmail API)      │
│               │    │   Detection)  │    │                    │    │                    │    │                    │
└──────────────┘    └──────────────┘    └──────────────────┘    └──────────────────┘    └──────────────────┘
```

### Detaylı Adımlar

1. **Scrape** (`scraper.py`) — Apify ile rakip influencer'ların son reels'lerini çeker
2. **Analyze** (`analyzer.py`) — Caption + mention analiziyle yeni markaları keşfeder
3. **Find Contacts** (`contact_finder.py`) — Apollo.io + Hunter.io ile email bulma + doğrulama
4. **Personalize** (`personalizer.py`) — GPT ile markaya özel email üretir
5. **Send** (`outreach.py`) — Gmail API ile gönderim, günlük 20 email limiti

### 3 Adımlı Email Sequence

| Adım | Zamanlama | Açıklama |
|------|-----------|----------|
| **İlk Outreach** | Pazartesi 10:00 | Kişiselleştirilmiş iş birliği teklifi |
| **Follow-up 1** | +5 gün | Markanın son paylaşımlarına referans veren takip |
| **Follow-up 2** | +5 gün daha | Nazik kapanış |

---

## 📂 Proje Yapısı

```
Marka_Outreach/
├── README.md
├── railway_scheduler.py               ← Railway zamanlayıcı
├── railway.json                       ← Railway deploy konfigürasyonu
├── requirements.txt
│
├── src/
│   ├── scraper.py                     ← Apify ile reels scraping
│   ├── analyzer.py                    ← AI marka keşfi
│   ├── contact_finder.py              ← Apollo.io + Hunter.io iletişim bulma
│   ├── personalizer.py                ← GPT ile email kişiselleştirme
│   ├── outreach.py                    ← İlk outreach gönderimi
│   ├── followup.py                    ← 3 adımlı follow-up sequence
│   ├── response_checker.py            ← Yanıt/bounce tespiti
│   ├── gmail_sender.py                ← Gmail API gönderim
│   └── reporter.py                    ← Haftalık Telegram raporu
│
├── config/
│   ├── kampanya.yaml                  ← Kampanya konfigürasyonu
│   └── rakipler.csv                   ← Takip edilen rakip influencer listesi
│
├── data/                              ← 🔒 .gitignore'da
│   └── markalar.csv                   ← Ana veritabanı: marka + outreach durumları
│
└── mail_templates/
    ├── collaboration_tr.html          ← Türkçe email şablonu
    ├── collaboration_en.html          ← İngilizce email şablonu
    └── followup_en.html               ← Follow-up şablonu
```

---

## 🔑 Gerekli API Anahtarları

| Servis | Env Variable | Kullanım |
|--------|-------------|----------|
| **Apify** | `APIFY_TOKEN` | Rakip reels scraping |
| **Apollo.io** | `APOLLO_API_KEY` | Kişi arama |
| **Hunter.io** | `HUNTER_API_KEY` | Email bulma + doğrulama |
| **OpenAI** | `OPENAI_API_KEY` | Email kişiselleştirme |
| **Gmail OAuth** | `GOOGLE_TOKEN_JSON` | Email gönderim |
| **Telegram** | `TELEGRAM_BOT_TOKEN` | Haftalık rapor |

---

*Antigravity ile oluşturulmuş taslak projedir.*
