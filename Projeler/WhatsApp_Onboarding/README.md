# WhatsApp Onboarding — AI Factory

Skool'a kayıt olan yeni üyelere 7 gün boyunca WhatsApp üzerinden onboarding videoları gönderen otomasyon sistemi.

## Akış

```
Skool (yeni üye) → Zapier (2 webhook) → Railway (Express) → Notion CRM + ManyChat API → WhatsApp
```

## Altyapı

| Bileşen | Detay |
|---------|-------|
| **Runtime** | Node.js (Express) |
| **Hosting** | Railway (Worker — 7/24) |
| **Domain** | `whatsapp-onboarding-production.up.railway.app` |
| **GitHub** | `dolunayozerennn/antigravity-egitim` (monorepo) |
| **Railway Project ID** | `5f346c33-6af1-4788-8405-34133c98451b` |
| **Service ID** | `64673112-d65a-4286-abc7-808af50901ce` |

## Webhook Endpoints

| Endpoint | Tetikleyen | Açıklama |
|----------|-----------|----------|
| `POST /webhook/new-paid-member` | Zapier Zap #1 | Yeni ödeme yapan üyeyi Notion'a kaydeder |
| `POST /webhook/membership-questions` | Zapier Zap #2 | Telefon numarasını valide eder, WhatsApp onboarding başlatır |
| `POST /webhook/wa-optin` | ManyChat | Email fallback'teki kullanıcı WhatsApp'tan mesaj attığında, kanalı WhatsApp'a geçirir |
| `POST /webhook/wa-failed` | ManyChat | WhatsApp mesajı başarısız olursa hibrit fallback email gönderir |
| `GET /health` | Monitoring | Servis sağlık kontrolü |

## Ortam Değişkenleri

| Variable | Açıklama | Railway'de Set? |
|----------|----------|----------------|
| `PORT` | Server port (3000) | ✅ |
| `NOTION_API_KEY` | Notion integration token | ✅ |
| `NOTION_DATABASE_ID` | Onboarding DB ID | ✅ |
| `MANYCHAT_API_TOKEN` | ManyChat WhatsApp API | ✅ |
| `GROQ_API_KEY` | Groq telefon validasyon | ✅ |
| `CRON_TIMEZONE` | Europe/Istanbul | ✅ |
| `CRON_SCHEDULE` | 0 12 * * * | ✅ |
| `RESEND_API_KEY` | Email fallback | ✅ |
| `RESEND_FROM_EMAIL` | Gönderici email | ✅ |
| `WA_BUSINESS_PHONE` | WhatsApp Business numarası (hibrit fallback) | ✅ |

## Dosya Yapısı

```
WhatsApp_Onboarding/
├── server.js                  # Express server + webhook endpoints
├── cron.js                    # Günlük onboarding cron job (12:00 İstanbul)
├── services/
│   ├── notion.js              # Notion CRM CRUD işlemleri
│   ├── manychat.js            # ManyChat API (subscriber + sendFlow)
│   ├── phoneValidator.js      # Groq LLM destekli telefon validasyonu
│   └── resend.js              # Email fallback + Hibrit WA CTA (Resend API)
├── config/
│   ├── templates.js           # Template ve Flow ID eşleştirmeleri
│   └── env.js                 # Fail-fast environment validation
├── utils/
│   └── logger.js              # Yapılandırılmış loglama
├── package.json               # Pinned dependencies
├── .env                       # Lokal credentials (gitignored)
└── .env.example               # Örnek env dosyası
```

## Geliştirme

```bash
npm install
cp .env.example .env  # Değerleri doldur
npm run dev
```

## Deploy

Railway üzerinde worker olarak çalışır. GitHub push → auto-deploy.

**Proje:** Antigravity Ekosistemi
**Versiyon:** 1.2.0
**İlk deploy:** 17 Nisan 2026
**Son güncelleme:** 25 Nisan 2026

## Canlı Test Geçmişi
- **25 Nisan 2026:** Zapier (new-paid-member, membership-questions) ve ManyChat (wa-failed) webhook'ları başarıyla canlı test edildi. Hibrit fallback (WhatsApp yoksa/ulaşmazsa Notion güncellenip otomatik email atılması) doğrulandı.
