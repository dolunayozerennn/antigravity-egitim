# 📋 Deploy Edilmiş Projeler Kayıt Defteri

Bu dosya, Railway'e deploy edilen ve cron ile çalışan projelerin ID bilgilerini saklar.
Re-deploy'larda bu bilgiler kullanılarak gereksiz API sorguları atlanır.
Health check scripti bu dosyayı okuyarak tüm projelerin sağlık durumunu kontrol eder.

> **⚠️ MİMARİ NOT (Mart 2026):** Çift-repo problemi nedeniyle **Native Mono-Repo** mimarisine geçilmiştir.
> Eskiden her projenin ayrı bir `GitHub Repo` alanı varken, yeni projelerin tamamı `dolunayozerennn/antigravity-egitim` üzerinden Railway'in "Root Directory" ayarıyla deploy edilecektir.
> Aşağıdaki eski projeler, vakit bulunduğunda monorepo'ya taşınıp eski repoları arşivlenebilir. Yeni projelerde her zaman `antigravity-egitim` reposu hedeflenmelidir.

---

## ✅ Aktif Projeler

### Hizli Referans — Tum Aktif Servisler

| Proje | Tip | Son Deploy | Durum | Hassasiyet Sayisi |
|-------|-----|------------|-------|-------------------|
| ceren-izlenme-notifier | CronJob | 2026-04-01 | ✅ Aktif | 3 |
| lead-pipeline | CronJob | 2026-04-16 | ✅ Aktif | 3 |
| shorts-demo-bot | Worker | 2026-03-17 | ✅ Aktif | 2 |
| dolunay-otonom-kapak | CronJob | 2026-04-20 | ✅ Aktif | 4 |
| isbirligi-tahsilat-takip | CronJob | 2026-04-02 | ✅ Aktif | 2 |
| marka-is-birligi | CronJob | 2026-04-16 | ✅ Aktif | 2 |
| akilli-watchdog | CronJob | 2026-04-20 | ✅ Aktif | 3 |
| linkedin-video-cron | CronJob | 2026-04-16 | ✅ Aktif | 4 |
| linkedin-text-cron | CronJob | 2026-04-20 | ✅ Aktif | 3 |
| twitter-video-cron | CronJob | 2026-04-08 | ✅ Aktif | 4 |
| supplement-telegram-bot | Worker | 2026-03-31 | ✅ Aktif | 2 |
| ecom-reklam-otomasyonu | Worker | 2026-04-25 | ✅ Aktif | 4 |
| youtube-otomasyonu-v3 | CronJob | 2026-04-19 | ✅ Aktif | 4 |
| whatsapp-onboarding | Express | 2026-04-27 | ✅ Aktif | 5 |
| lead-notifier-bot-v3 | Worker | 2026-04-26 | ✅ Aktif | 3 |
| ceren-marka-takip-cron | CronJob | 2026-04-24 | ✅ Aktif | 4 |

---

### ceren-izlenme-notifier (CronJob — Salı/Perşembe) ✅
- **Platform:** `railway-cron`
- **Railway Project ID:** `b5117788-3979-45b3-a92c-eae3606e0dc2`
- **Service ID:** `058d3d5c-9589-4c49-aca2-f6965207aa38`
- **Environment ID:** `be212401-34d1-4b34-b25b-0d43b11e1a30`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (mono-repo, Root Dir: `/Projeler/Ceren_izlenme_notifier`)
- **Lokal Klasör:** `Projeler/Ceren_izlenme_notifier/`
- **Start Komutu:** `python main.py`
- **Cron Schedule:** `0 8 * * 2,4` (Salı/Perşembe, UTC 08:00 = TR 11:00)
- **Son Deploy:** 2026-04-01 (Stabilizasyon: Worker→CronJob dönüşümü, OAuth token refresh, YouTube filtre fix, ölü kod temizliği)
- **Durum:** ✅ Aktif (Haftada 2 kez sosyal medya performans raporu — Instagram, TikTok, YouTube)
- **Hassasiyetler:** Apify kota limiti (yedek hesap gerekli), OAuth token yenileme, YouTube filtre API degisiklikleri

---

### lead-pipeline (BİRLEŞİK CRON JOB) ✅
- **Platform:** `railway-cron`
- **Railway Project ID:** `fc91edb9-5d93-413d-b9b7-75ae81033204`
- **Service ID:** `b4a28784-6e03-473f-b8fa-c1021820d703` (Recreated to fix webhook & root path issue)
- **Environment ID:** `69c5c773-b69a-4077-a7ff-7b29258a3ad1`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (mono-repo, Root Dir: `Projeler/Lead_Pipeline`)
- **Lokal Klasör:** `Projeler/Lead_Pipeline/`
- **Start Komutu:** `python main.py`
- **Cron Schedule:** `*/10 * * * *` (10 dakikada bir)
- **Birleştirilen servisler:** tele-satis-crm + lead-notifier-bot + tele-satis-notifier
- **Son Deploy:** 2026-04-16 (fix: Notifier spreadsheet state_spreadsheet_id üzerinden izlenerek sonsuz spam loop hatası çözüldü)
- **Durum:** ✅ Aktif (Build SUCCESS, cron 10 dakikada bir çalışıyor)
- **Hassasiyetler:** Google Sheets SA yetkilendirme (manuel share gerekli), state cakismasi (namespace prefix ZORUNLU), SMTP yasak (Gmail API kullan)

---

### shorts-demo-bot
- **Platform:** `railway`
- **Railway Project ID:** `01bf8d6e-9eb4-4a42-aaa0-0103e6e56033`
- **Service ID:** `151725ce-0416-41dd-9b94-768353c919b5`
- **Environment ID:** `64704cfe-b15e-4cb0-9256-e89575da34c4`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Shorts_Demo_Otomasyonu`)
- **Lokal Klasör:** `Projeler/Shorts_Demo_Otomasyonu/`
- **Start Komutu:** `python bot.py`
- **Son Deploy:** 2026-03-17
- **Durum:** ✅ Aktif (README güncellendi, Kie AI referansı kaldırıldı)
- **Hassasiyetler:** Telegram bot conflict (deploy sirasinda gecici), requests bagimliligi (requirements.txt kontrol)

---



### dolunay-otonom-kapak (Unified Monolith V2 — 2 CronJob)
- **Platform:** `railway-cron`
- **Railway Project ID:** `9a55cc02-4e75-44f9-993c-31c6f0616c55`
- **Environment ID:** `f23dd962-8015-45aa-ab47-94e34d8023c0`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Dolunay_Otonom_Kapak`)
- **Lokal Klasör:** `Projeler/Dolunay_Otonom_Kapak/`
- **Start Komutu:** `python main.py`

#### Servis 1: reels-kapak
- **Service ID:** `3afcca6e-8f29-4ea6-bc99-b212a4269e34`
- **COVER_TYPE:** `reels`
- **Cron Schedule:** `0 6 * * *` (Günlük, UTC 06:00 = TR 09:00)
- **Son Deploy:** 2026-04-20 (fix: dotenv absolute path sorunu ve boş video listelerinde OpsLogger early-return hatası düzeltildi)
- **Durum:** ✅ Aktif (Günde 1 kez Reels kapak üretimi — 3 tema × 2 varyasyon = 6 kapak)
- **Hassasiyetler:** Kie AI API degisiklikleri, ImgBB API limiti, Notion token (NOTION_SOCIAL_TOKEN), dotenv absolute path sorunu

#### Servis 2: youtube-kapak
- **Service ID:** `0bfc46ea-887f-4a62-a3da-bc7fb824eb3c`
- **COVER_TYPE:** `youtube`
- **Cron Schedule:** `0 7 * * *` (Günlük, UTC 07:00 = TR 10:00)
- **Son Deploy:** 2026-04-20 (fix: dotenv absolute path sorunu ve boş video listelerinde OpsLogger early-return hatası düzeltildi)
- **Durum:** ✅ Aktif (Günde 1 kez YouTube thumbnail üretimi — 5 tema × 2 varyasyon = 10 kapak)
- **Hassasiyetler:** Kie AI API degisiklikleri, ImgBB API limiti, Notion token (NOTION_SOCIAL_TOKEN), dotenv absolute path sorunu

- **Env Vars:** COVER_TYPE, ENV, NOTION_SOCIAL_TOKEN, NOTION_DB_REELS_KAPAK, NOTION_DB_YOUTUBE_ISBIRLIKLERI, NOTION_DB_OPS_LOG, KIE_API_KEY, GEMINI_API_KEY, IMGBB_API_KEY, GOOGLE_OUTREACH_TOKEN_JSON

### revizyon-cron ⛔ (KALDIRILDI — unified_worker'a taşındı)
- **Railway Project ID:** `fed6db49-de57-4fbe-9988-528416f1b668`
- **Service ID:** `1e740cb1-3b80-47e3-a863-2d27c7f2c01a` (silindi)
- **Durum:** ⛔ Kaldırıldı (2026-03-24) — unified_worker.py içinde birleştirildi

---

### isbirligi-tahsilat-takip
- **Platform:** `railway-cron`
- **Railway Project ID:** `8f70b293-dc33-426a-95f7-19741d3ae03c`
- **Service ID:** `533f2a47-c8f6-4e3b-a5a1-0f5b2f9b8b8d`
- **Environment ID:** `cc3aa405-1388-421c-93af-146fa91f1a1e`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Isbirligi_Tahsilat_Takip`)
- **Lokal Klasör:** `Projeler/Isbirligi_Tahsilat_Takip/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-04-02 (auto-deploy — SUCCESS doğrulandı)
- **Durum:** ✅ Aktif (Notion-based state, Gmail API OAuth2 e-posta)
- **Hassasiyetler:** Gmail OAuth2 token yenileme, Notion state yonetimi

---

### marka-is-birligi
- **Platform:** `railway-cron`
- **Railway Project ID:** `6994adc2-edb2-4c91-b43d-237f28d41a69`
- **Service ID:** `997b869b-bd24-4be5-b37f-d5ff2f85232b`
- **Environment ID:** `5fc44142-a014-4a20-912d-c1424bfae895`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Marka_Is_Birligi`)
- **Lokal Klasör:** `Projeler/Marka_Is_Birligi/`
- **Start Komutu:** `python railway_scheduler.py`
- **Son Deploy:** 2026-04-16 (fix: Apify key rotasyonunda limit hatası durumu giderildi ve hata alındığında failover yapısı eklendi)
- **Durum:** ✅ Aktif (Outreach + Follow-Up + Rapor — Notion state + ops_logger)
- **Hassasiyetler:** Apify key rotasyonu (failover yapisi mevcut), Notion ops_logger queue flush

---

### akilli-watchdog
- **Platform:** `railway-cron`
- **Railway Project ID:** `ec3ea7b1-9bdb-4886-a197-026ee2d2126c`
- **Service ID:** `ddb6ddd6-4918-4b27-bd5c-946bb829bc42`
- **Environment ID:** `45ef43a9-5ba2-475b-be50-56aaaf6b9906`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Akilli_Watchdog`)
- **Lokal Klasör:** `Projeler/Akilli_Watchdog/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-04-20 (Fix: TikTok bağımlı sosyal medya paylaşımlarında 'Hiç yeni lead işlenmedi' diyen false-positive Watchdog alarmı expected_daily_activity: False yapılarak düzeltildi)
- **Durum:** ✅ Aktif (Günde 1 kez çalışır — UTC 00:00. Token expire takibi + Railway health check eklendi.)
- **Hassasiyetler:** False positive dongusu (kendi loglarini izleme riski), Railway Token gecerliligi, SKIPPED deploy durumu (monorepo — saglikli)
- **Env Vars:** GROQ_API_KEY, NOTION_API_TOKEN, NOTION_SOCIAL_TOKEN, GOOGLE_OUTREACH_TOKEN_JSON, GOOGLE_SERVICE_ACCOUNT_JSON, RAILWAY_TOKEN

---

### dolunay-ai-website ⛔ (KALDIRILDI)
- **Platform:** `railway` → **SİLİNDİ** (Netlify'a taşındı)
- **Railway Project ID:** `58765514-d122-4653-99c5-e9958330e5a4`
- **Service ID:** `af8d86d9-aa29-4e4b-bdca-70dd40f7c452` (silindi)
- **GitHub Repo:** `dolunayozerennn/Dolunay_AI_Website`
- **Lokal Klasör:** `Projeler/Dolunay_AI_Website/`
- **Durum:** ⛔ Kaldırıldı (2026-03-22) — Website zaten Netlify'da barınıyor, Railway'deki kopya gereksizdi.

---

### linkedin-video-cron
- **Platform:** `railway-cron`
- **Railway Project ID:** `59d79d0c-bd8c-46af-80e1-1b64ade41304`
- **Service ID:** `8e486d77-c5b1-4f70-9f29-55c8b59398f9`
- **Environment ID:** `d4f9b81a-8e72-432b-b64c-089ead41f636`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/LinkedIn_Video_Paylasim`)
- **Lokal Klasör:** `Projeler/LinkedIn_Video_Paylasim/`
- **Start Komutu:** `python main.py`
- **Cron Schedule:** `0 10 * * *` (Günlük, UTC 10:00 = TR 13:00)
- **Son Deploy:** 2026-04-16 (fix: LinkedIn video yükleme işlemi zaman aşımı 5 dakikadan 15 dakikaya çıkarıldı)
- **Durum:** ✅ Aktif (TikTok→LinkedIn video pipeline, günde 1 kez)
- **Hassasiyetler:** ffmpeg (nixpacks.toml ZORUNLU), LinkedIn Video API timeout (15dk polling), TikTok scraping (yt-dlp versiyon uyumu), filtre strictness ayari
- **Env Vars:** LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN, GROQ_API_KEY, LINKEDIN_FILTER_STRICTNESS=relaxed, NOTION_SOCIAL_TOKEN, NOTION_LINKEDIN_DB_ID, NOTION_DB_OPS_LOG

---

### linkedin-text-cron
- **Platform:** `railway-cron`
- **Railway Project ID:** `5465753a-2653-400a-ae3a-d4593de9c40e`
- **Service ID:** `c1b095f4-700b-4302-ac30-efe537d5935c`
- **Environment ID:** `2a4e2f58-b0db-4a90-9ab1-689f1f403363`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/LinkedIn_Text_Paylasim`)
- **Lokal Klasör:** `Projeler/LinkedIn_Text_Paylasim/`
- **Start Komutu:** `python main.py`
- **Cron Schedule:** `0 8 * * 1,4` (Haftada 2, UTC 08:00 Pazartesi+Perşembe = TR 11:00)
- **Son Deploy:** 2026-04-20 (style: Görsel boyut ve kalitesini sade, uncluttered, yormayan, açık temalı ultra-minimalist tasarıma geçirecek prompt revizyonu yapıldı.)
- **Durum:** ✅ Aktif (Haftalık AI Haberleri + AI Tavsiyesi LinkedIn postu)
- **Hassasiyetler:** Kie AI gorsel uretim kalitesi, LinkedIn API rate limit, Perplexity API degisiklikleri
- **Env Vars:** PERPLEXITY_API_KEY, OPENAI_API_KEY, KIE_API_KEY, LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN, NOTION_SOCIAL_TOKEN, NOTION_LINKEDIN_DB_ID, NOTION_DB_OPS_LOG

---

### twitter-video-cron
- **Platform:** `railway-cron`
- **Railway Project ID:** `24c3d0d1-58e7-4213-826b-c7e2d1c45a30`
- **Service ID:** `55f76475-5b45-4050-93f7-723110ab470e`
- **Environment ID:** `1e5cfad2-c76d-4ca1-a1a5-c839a2cfdb1d`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Twitter_Video_Paylasim`)
- **Lokal Klasör:** `Projeler/Twitter_Video_Paylasim/`
- **Start Komutu:** `python main.py`
- **Cron Schedule:** `0 8,11,14 * * *` (Günde 3 kez, UTC 08/11/14 = TR 11/14/17)
- **Son Deploy:** 2026-04-08 (auto-deploy — SUCCESS doğrulandı)
- **Durum:** ✅ Aktif (TikTok→X/Twitter video pipeline, günde 3 kez)
- **Hassasiyetler:** ffmpeg (nixpacks.toml ZORUNLU), X/Twitter API rate limit, Notion DB ID cakismasi (LinkedIn ile ayni DB), yt-dlp versiyon
- **Env Vars:** NOTION_SOCIAL_TOKEN, NOTION_TWITTER_DB_ID, X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET

---

### supplement-telegram-bot
- **Platform:** `railway`
- **Railway Project ID:** `35acfbc5-f058-45f9-ba76-373b47e66b07`
- **Service ID:** `0a3f240f-6fea-4176-b480-a2cdb99e4a93`
- **Environment ID:** `6f09ea79-49b6-4414-b820-6c83d5bd31cb`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Supplement_Telegram_Bot/`)
- **Lokal Klasör:** `Projeler/Supplement_Telegram_Bot/`
- **Son Deploy:** 2026-03-31 (SUCCESS — Railway API doğrulandı)
- **Durum:** ✅ Aktif (7/24 Telegram bot — takviye takibi)
- **Hassasiyetler:** Telegram bot conflict (deploy gecici), GitHub monorepo push senkronizasyonu
- **Not:** Eğitim amaçlı paylaşılan kopyası: `Paylasilan_Projeler/Supplement_Telegram_Bot_Taslak/`
- **⚠️ DİKKAT:** Lokal klasör `Paylasilan_Projeler/Supplement_Telegram_Bot_Taslak/` dosyalarından oluşturuldu (2026-04-08). GitHub monorepo'ya henüz push edilmedi — bir sonraki push ile senkronize olacak.

---



### ecom-reklam-otomasyonu (Worker — Telegram Polling)
- **Platform:** `railway`
- **Railway Project ID:** `8797307d-7b80-41cb-add0-976c09eaeed4`
- **Service ID:** `98a3be1e-f6f4-4ca2-8780-2b88bbd2125a`
- **Environment ID:** `b8353ac5-0ec4-4785-8d72-7aae17f18e56`
- **Deployment ID:** `a1790e37-08ee-45a7-b3ec-a522ebaf9fec`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/eCom_Reklam_Otomasyonu`)
- **Lokal Klasör:** `Projeler/eCom_Reklam_Otomasyonu/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-04-28 (feat: Aspect Ratio normalization ve exception handling iyileştirmesi tamamlandı)
- **Durum:** ✅ Aktif (7/24 Telegram bot — ürün reklam videosu üretim otomasyonu)
- **Hassasiyetler:** Bellek sizintisi (UserSession 10dk idle timeout), asyncio task hata yutma, Seedance API parametre isimleri (model bazli farklilik), Kie AI 512 upstream hatasi (retry mevcut)
- **Env Vars:** ENV, TELEGRAM_ECOM_BOT_TOKEN, TELEGRAM_ADMIN_CHAT_ID, OPENAI_API_KEY, OPENAI_MODEL=gpt-4.1-mini, PERPLEXITY_API_KEY, IMGBB_API_KEY, KIE_API_KEY, ELEVENLABS_API_KEY, ELEVENLABS_MODEL, REPLICATE_API_TOKEN, NOTION_SOCIAL_TOKEN, NOTION_DB_ECOM_REKLAM, NOTION_CHAT_DB_ID, FIRECRAWL_API_KEY

---

### youtube-otomasyonu-v3 (CronJob — Günlük) ✅
- **Platform:** `railway-cron`
- **Railway Project ID:** `87e24335-52c9-460f-8b2e-0f481f5501bd`
- **Service ID:** `d17abb9e-3ef1-4f50-98c1-f4290bb2f090`
- **Environment ID:** `30bb2f27-0297-4148-88f0-d28f2ac58a6c`
- **Deployment ID:** `07b822d1-aa2c-4c86-88de-a9d82df4b3da`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/YouTube_Otomasyonu`)
- **Lokal Klasör:** `Projeler/YouTube_Otomasyonu/`
- **Start Komutu:** `python main.py`
- **Cron Schedule:** `0 14 * * *` (Günlük, UTC 14:00 = TR 17:00)
- **Son Deploy:** 2026-04-19 (fix: Creative Engine prompt optimizasyonu — videolardaki çizim izlenimini gidermek için strict realism kuralları eklendi)
- **YouTube Kanalı:** Pets Got Talent (UCvj1A1gds6jZUgsPbhF3Muw) — OAuth2 bağlı
- **Durum:** ✅ Aktif (Günde 1 kez otonom video — Creative Engine: 2686 kombinasyon)
- **Hassasiyetler:** YouTube OAuth2 token yenileme, Kie AI API, Replicate API, Creative Engine prompt hassasiyeti (realism kurallari)
- **Env Vars:** ENV, OPENAI_API_KEY, KIE_API_KEY, REPLICATE_API_TOKEN, NOTION_SOCIAL_TOKEN, NOTION_DB_YOUTUBE_OTOMASYON, YOUTUBE_ENABLED, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN, YOUTUBE_CATEGORY_ID, YOUTUBE_PRIVACY

---

### whatsapp-onboarding (Worker — Express + Cron)
- **Platform:** `railway`
- **Railway Project ID:** `5f346c33-6af1-4788-8405-34133c98451b`
- **Service ID:** `64673112-d65a-4286-abc7-808af50901ce`
- **Environment ID:** `f2000489-b711-4224-9fd4-44791bdb59d4`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/WhatsApp_Onboarding`)
- **Lokal Klasör:** `Projeler/WhatsApp_Onboarding/`
- **Start Komutu:** `node server.js`
- **Cron Schedule:** `0 12 * * *` (Günlük, UTC 09:00 = TR 12:00 — app-level cron)
- **Domain:** `whatsapp-onboarding-production.up.railway.app`
- **Webhook URL'ler:**
  - `POST /webhook/new-paid-member` (Zapier Zap #1)
  - `POST /webhook/membership-questions` (Zapier Zap #2)
  - `POST /webhook/wa-optin` (ManyChat — Email→WhatsApp kanal geçişi)
  - `POST /webhook/wa-failed` (ManyChat — Hibrit fallback email tetikleyici)
  - `GET /health` (Monitoring)
- **Son Deploy:** 2026-04-28 (fix: Zapier membership-questions webhook ReferenceError çözüldü, ManyChat API subscriber lookup hatası fatal error'dan fallback warning seviyesine çekildi)
- **Durum:** ✅ Aktif (Health check OK — Zapier webhook replay SUCCESS)
- **Hassasiyetler:** Webhook idempotency, ManyChat API timeout (8s), Notion rate limit (429), race condition (lock mekanizmasi mevcut), Groq API timeout (5s)
- **Env Vars:** PORT, NOTION_API_KEY, NOTION_DATABASE_ID, MANYCHAT_API_TOKEN, GROQ_API_KEY, CRON_TIMEZONE, CRON_SCHEDULE, RESEND_API_KEY, RESEND_FROM_EMAIL, WA_BUSINESS_PHONE
- **Not:** ✅ Hibrit fallback aktif: WA teslim başarısızsa → Resend email (dolunay.ai) + WhatsApp CTA butonu. v1.2.0

---

| Proje | Klasör | Platform | Son Değişiklik | Durum | Not |
|-------|--------|----------|----------------|-------|-----|
| Dubai Emlak İçerik | `Projeler/Dubai_Emlak_İçerik_Yazarı/` | `local-only` | 2026-03-09 | ⏸️ Askıda | Script koleksiyonu (transcript, currency, calculator). Deploy planı yok, geliştirme aşamasında |

---

### lead-notifier-bot-v3
- **Platform:** `railway`
- **Railway Project ID:** `7c5d3081-1487-4b02-a60f-1cb7a04bb135`
- **Service ID:** `2563df9f-37ac-4ab2-80f6-06ac8d19aec3`
- **Environment ID:** `a0ffd17c-0de3-4759-ba48-c04b96bb96b8`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Lead_Notifier_Bot`)
- **Lokal Klasör:** `Projeler/Lead_Notifier_Bot/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-04-26 (Fix: OAuth fallback (GOOGLE_OUTREACH_TOKEN_JSON) eklendi, manuel yetki için share_sheet.py eklendi)
- **Durum:** ✅ Aktif (Railway deploy başarılı ve çalışıyor)
- **Hassasiyetler:** Google Sheets SA yetkilendirme (manuel share ZORUNLU), GOOGLE_OUTREACH_TOKEN_JSON fallback, SMTP yasak
- **Env Vars:** TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_OUTREACH_TOKEN_JSON, NOTIFY_EMAIL, SENDER_EMAIL, POLL_INTERVAL_SECONDS, MAX_BATCH_SIZE

### ceren-marka-takip-cron
- **Platform:** `railway-cron`
- **Railway Project ID:** `c563b334-2a3c-49bf-8461-9852ca649112`
- **Service ID:** `128e496f-9f8a-437e-b401-e89c3b0a1e08`
- **Environment ID:** `817dd65c-57f2-4cb7-a4df-92422f9fd36a`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `/Projeler/Ceren_Marka_Takip`)
- **Lokal Klasör:** `Projeler/Ceren_Marka_Takip/`
- **Start Komutu:** `cd Projeler/Ceren_Marka_Takip && pip install -r requirements.txt && python main.py`
- **Cron Schedule:** `0 7 * * *` (Günde 1 kez, UTC 07:00 = İstanbul 10:00)
- **Son Deploy:** 2026-04-24 (Fix: Groq timeout bug, business_hours fix, SMTP cleanup, nixpacks.toml eklendi, cron 2h→günlük)
- **Durum:** ✅ Aktif (Günde 1 kez, sabah 10:00 İstanbul)
- **Hassasiyetler:** Groq timeout, nixpacks.toml (ffmpeg yoksa da nixpacks gerekli), SMTP yasak (Gmail API), business_hours hesaplama
- **Env Vars:** GOOGLE_CEREN_TOKEN_JSON, GOOGLE_DOLUNAY_AI_TOKEN_JSON, GOOGLE_OUTREACH_TOKEN_JSON, GROQ_API_KEY, NOTION_SOCIAL_TOKEN, NOTION_DB_OPS_LOG

---

## 🗂 Lokal Servisler (LaunchAgent / Cron)

### servis-izleyici (health check)
- **Platform:** `cron-local`
- **LaunchAgent:** `com.antigravity.servis-izleyici`
- **LogPath:** `_skills/servis-izleyici/logs/health_check.log`
- **CronSchedule:** Saatlik (her 3600 saniyede bir)
- **Lokal Klasör:** `_skills/servis-izleyici/`
- **Start Komutu:** `python3 scripts/health_check.py`
- **Durum:** ✅ Aktif — LaunchAgent ile saatlik çalışıyor

---

## 📦 Arşiv (Kalıcı Olarak Silinen / Kaldırılmış Projeler)

**Not:** Bu sekme altında listelenen ve geçmişte pasif, duplike ya da hayalet hale gelen birçok eski proje (Örn: *tele-satis-crm, lead-notifier-bot, tele-satis-notifier, dolunay-ai-website, LinkedIn_Text_Paylasim, dolunay-youtube-kapak klonları*) Railway GraphQL API üzerinden kalıcı olarak silinmiştir.
Sistemde şu an arayüz karmaşası yaratmamaları ve health check denetimlerinden tamamen çıkarılmaları amacıyla Project ID'leri kayıt defterinden tamamen kaldırılmıştır.

Aşağıdaki projeler ilerleyen dönemde platformdan silinmek üzere işaretlenmişti ve tamamı **silinmiştir**:

- ~~`linkedin-paylasim`~~ (`9aec063f`) — Hayalet, linkedin-text + linkedin-video olarak ayrılmıştı. **SİLİNDİ** (2026-04-03)
- ~~`Twitter_Paylasim`~~ (`9b8a5927`) — Hayalet, twitter-video-cron ile duplike. **SİLİNDİ** (2026-04-03)
- ~~`marka-is-birligi (boş)`~~ (`0522fff5`) — Boş proje. Aktif: `6994adc2`. **SİLİNDİ** (2026-04-03)
- ~~`dolunay-reels-kapak`~~ (`fed6db49`) — V2'ye (Dolunay_Otonom_Kapak) taşındı. **SİLİNDİ** (2026-04-16)
- ~~`dolunay-youtube-kapak`~~ (`586a7bf6`) — V2'ye (Dolunay_Otonom_Kapak) taşındı. **SİLİNDİ** (2026-04-16)
- ~~`sweatcoin-email-automation`~~ (`0c1ff084`) — Proje tamamen kapatıldı, Railway'den silindi, lokal arşive taşındı. **SİLİNDİ** (2026-04-08)
- ~~`Emlak Arazi Drone Çekim`~~ — Local-only proje, hiç deploy edilmemişti. Lokal arşive taşındı. **ARŞİVLENDİ** (2026-04-08)
- ~~`blog-yazici-cron`~~ (`49e850fc`) — Lokal arşive taşındı. **ARŞİVLENDİ** (2026-04-24)

