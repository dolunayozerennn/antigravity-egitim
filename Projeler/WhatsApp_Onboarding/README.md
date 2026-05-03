# WhatsApp Onboarding — AI Factory

Skool'a kayıt olan yeni üyelere 7 gün boyunca WhatsApp üzerinden onboarding videoları gönderen otomasyon sistemi.

## Akış

```
Skool (yeni üye) → Zapier (2 webhook) → Railway (Express) → Notion CRM + ManyChat API → WhatsApp
                                                          ↳ Hibrit fallback: Resend (email + WA CTA)
```

## Altyapı

| Bileşen | Detay |
|---------|-------|
| **Runtime** | Node.js 20+ (Express) |
| **Hosting** | Railway (Worker — 7/24) |
| **Domain** | `whatsapp-onboarding-production.up.railway.app` |
| **GitHub (deploy)** | `dolunayozerennn/whatsapp-onboarding` ⚠️ **STANDALONE** (monorepo değil) |
| **Monorepo Yansıma** | `Projeler/Whatsapp_Onboarding/` — referans/edit, deploy tetiklemiyor |
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

**Zorunlu** (yoksa boot fail — fail-secure):

| Variable | Açıklama |
|----------|----------|
| `PORT` | Server port (3000) |
| `NOTION_API_KEY` | Notion integration token |
| `NOTION_DATABASE_ID` | Onboarding DB ID |
| `MANYCHAT_API_TOKEN` | ManyChat WhatsApp API |
| `GROQ_API_KEY` | Groq LLaMA 3.3 telefon validasyonu (OpenAI değil) |
| `CRON_TIMEZONE` | Europe/Istanbul |
| `CRON_SCHEDULE` | 0 12 * * * |
| `RESEND_API_KEY` | Email fallback |
| `RESEND_FROM_EMAIL` | Gönderici email |
| `WA_BUSINESS_PHONE` | WhatsApp Business numarası (hibrit fallback) |
| `WEBHOOK_SECRET` | **Yeni (v2.0.0):** Tüm `/webhook/*` route'ları için zorunlu. Yoksa request'ler 401 döner |

**Opsiyonel:**

| Variable | Açıklama |
|----------|----------|
| `ADMIN_SECRET` | `/admin/*` endpoint'leri için. Yoksa admin auth devre dışı (dev mode) |

## Dosya Yapısı

```
Whatsapp_Onboarding/
├── server.js                  # Express + webhook endpoints + boot validations + graceful shutdown
├── cron.js                    # Günlük cron (12:00) — Notion run-lock + 429 retry + atomic dual-channel
├── manual_onboard.js          # Tek seferlik migration script (npm run migrate)
├── services/
│   ├── notion.js              # CRUD + findByTransactionId + tryAcquireCronLock + validateSchema + bounded pagination
│   ├── manychat.js            # Subscriber + sendFlow + validateAllFlows (boot) + AbortSignal timeouts
│   ├── phoneValidator.js      # Groq LLaMA 3.3 (libphonenumber-js fast-path) — KVKK PII masked logs
│   └── resend.js              # Email fallback + Hibrit WA CTA + 10s timeout
├── config/
│   ├── templates.js           # ManyChat flow ID eşleştirmeleri
│   └── env.js                 # Fail-fast env validation (WEBHOOK_SECRET + GROQ_API_KEY zorunlu)
├── utils/
│   ├── logger.js              # Yapılandırılmış log + recursive PII redaction
│   └── phone.js               # toE164 + maskPhone (her read/write boundary'sinde)
├── tests/                     # Ad-hoc debug script'leri (deploy'a girmiyor)
├── scripts/
│   └── deploy.js              # Standalone repo'ya sync script (yedek, manuel)
├── .npmrc                     # engine-strict=true
├── package.json               # libphonenumber-js dahil pinned deps, Node >=20
├── railway.json
├── .env                       # Lokal credentials (gitignored)
└── .env.example
```

## v2.0.0 — Production Hardening (2026-05-03)

3 paralel Explore audit → 22 bulgu → 4 faza bölünmüş fix:

- **Faz 1 — Boot & Deploy:** WEBHOOK_SECRET fail-secure, ManyChat flow + Notion schema validation boot'ta, OpenAI→Groq config drift fix, Node 20+
- **Faz 2 — State & Idempotency:** Day 0 çift gönderim engellendi, in-memory lock → Notion-backed (transaction_id), 429 exponential backoff, multi-instance run-lock, SIGTERM graceful shutdown, atomic dual-channel (`lastError` marker pattern: `wa-failed-day-N`)
- **Faz 3 — External Resilience:** KVKK PII masking, `AbortSignal.timeout` her fetch'te, retry'lar AbortError + ECONNRESET'i de yakalıyor, bounded pagination (1000/cron), `utils/phone.js` E.164 normalize, **5am-cutoff bug kaldırıldı**, membership-questions race retry (3×2s)
- **Faz 4 — Cleanup:** log redaction layer (phone/email/secret keys auto-mask), admin route rate limit (10 req/60s)

Detay için: monorepo commit `3a21697`, standalone commit `0c4001f`.

## Geliştirme

```bash
npm install
cp .env.example .env  # Değerleri doldur
npm run dev
```

## Deploy

⚠️ **DİKKAT:** Railway servisi STANDALONE repo'dan deploy ediyor:

```bash
# 1. Standalone repo'yu clone et
git clone https://github.com/dolunayozerennn/whatsapp-onboarding.git /tmp/wa-standalone

# 2. Monorepo'daki güncel dosyaları sync et (services/, config/, utils/, server.js, cron.js, package.json, railway.json, .gitignore, .npmrc)
# Yeni require() varsa package.json'a dependency'yi de eklemeyi UNUTMA (libphonenumber-js gibi)
# 3. cd /tmp/wa-standalone && npm install && git add -A && git commit && git push origin main
```

GitHub push → Railway auto-deploy. Monorepo'ya commit yapmak deploy TETİKLEMEZ — sadece referans için.

## Bilinen Açık Konular
- 6 npm vulnerability (1 low, 3 mod, 2 high) — `npm audit fix --force` breaking change içerebilir, manuel review
- Monorepo'da `WhatsApp_Onboarding` vs `Whatsapp_Onboarding` case mismatch — ayrı `git mv` PR'ı ile temizlenmeli

## Versiyon Geçmişi

- **v2.0.0** (3 Mayıs 2026) — Kapsamlı 4-faz audit + production hardening
- **v1.2.0** (25 Nisan 2026) — Hibrit fallback + Zapier canlı test
- **v1.0.0** (17 Nisan 2026) — İlk deploy

**Proje:** Antigravity Ekosistemi
