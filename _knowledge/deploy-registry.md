# 📋 Deploy Edilmiş Projeler Kayıt Defteri

Bu dosya, Railway'e deploy edilen ve cron ile çalışan projelerin ID bilgilerini saklar.
Re-deploy'larda bu bilgiler kullanılarak gereksiz API sorguları atlanır.
Health check scripti bu dosyayı okuyarak tüm projelerin sağlık durumunu kontrol eder.

> **⚠️ MİMARİ NOT (Mart 2026):** Çift-repo problemi nedeniyle **Native Mono-Repo** mimarisine geçilmiştir.
> Eskiden her projenin ayrı bir `GitHub Repo` alanı varken, yeni projelerin tamamı `dolunayozerennn/antigravity-egitim` üzerinden Railway'in "Root Directory" ayarıyla deploy edilecektir.
> Aşağıdaki eski projeler, vakit bulunduğunda monorepo'ya taşınıp eski repoları arşivlenebilir. Yeni projelerde her zaman `antigravity-egitim` reposu hedeflenmelidir.

---

## ✅ Aktif Projeler

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
- **Son Deploy:** 2026-04-08 (auto-deploy — SUCCESS doğrulandı)
- **Durum:** ✅ Aktif (Build SUCCESS, cron 10 dakikada bir çalışıyor)

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
- **Son Deploy:** 2026-04-10 (V2 ilk deploy — SUCCESS)
- **Durum:** ✅ Aktif (Günde 1 kez Reels kapak üretimi — 3 tema × 2 varyasyon = 6 kapak)

#### Servis 2: youtube-kapak
- **Service ID:** `0bfc46ea-887f-4a62-a3da-bc7fb824eb3c`
- **COVER_TYPE:** `youtube`
- **Cron Schedule:** `0 7 * * *` (Günlük, UTC 07:00 = TR 10:00)
- **Son Deploy:** 2026-04-10 (V2 ilk deploy — SUCCESS)
- **Durum:** ✅ Aktif (Günde 1 kez YouTube thumbnail üretimi — 5 tema × 2 varyasyon = 10 kapak)

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

---

### marka-is-birligi
- **Platform:** `railway-cron`
- **Railway Project ID:** `6994adc2-edb2-4c91-b43d-237f28d41a69`
- **Service ID:** `997b869b-bd24-4be5-b37f-d5ff2f85232b`
- **Environment ID:** `5fc44142-a014-4a20-912d-c1424bfae895`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Marka_Is_Birligi`)
- **Lokal Klasör:** `Projeler/Marka_Is_Birligi/`
- **Start Komutu:** `python railway_scheduler.py`
- **Son Deploy:** 2026-04-06 (fix: YouTube URL filtreleme — Apify actor sadece Instagram URL kabul ediyor, karışık URL'ler 400 Bad Request hatasına yol açıyordu)
- **Durum:** ✅ Aktif (Outreach + Follow-Up + Rapor — Notion state + ops_logger)

---

### akilli-watchdog
- **Platform:** `railway-cron`
- **Railway Project ID:** `ec3ea7b1-9bdb-4886-a197-026ee2d2126c`
- **Service ID:** `ddb6ddd6-4918-4b27-bd5c-946bb829bc42`
- **Environment ID:** `45ef43a9-5ba2-475b-be50-56aaaf6b9906`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Akilli_Watchdog`)
- **Lokal Klasör:** `Projeler/Akilli_Watchdog/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-04-05 (auto-deploy — SUCCESS doğrulandı)
- **Durum:** ✅ Aktif (Günde 1 kez çalışır — UTC 00:00. Token expire takibi + Railway health check eklendi.)
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
- **Son Deploy:** 2026-04-11 (4 kritik fix: content filter relaxed + fallback mekani̅zması + wait_all_loggers + ops loglama iyileştirmesi)
- **Durum:** ✅ Aktif (TikTok→LinkedIn video pipeline, günde 1 kez)
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
- **Son Deploy:** 2026-04-11 (4 kritik fix: v2/assets→rest/images API migration + hata loglaması + wait_all_loggers + Gemini→Kie AI geçişi)
- **Durum:** ✅ Aktif (Haftalık AI Haberleri + AI Tavsiyesi LinkedIn postu)
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
- **Env Vars:** NOTION_SOCIAL_TOKEN, NOTION_TWITTER_DB_ID, X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET

---

### blog-yazici-cron
- **Platform:** `railway-cron`
- **Railway Project ID:** `49e850fc-df64-43eb-a839-18976b3965ff`
- **Service ID:** `bdaaa906-abed-477c-b67c-dacec39fe733`
- **Environment ID:** `84e15123-336f-4a16-8fea-5c12fa932760`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo)
- **Root Directory:** `Projeler/Blog_Yazici/`
- **Lokal Klasör:** `Projeler/Blog_Yazici/`
- **Start Komutu:** `python run_pipeline.py --from-notion`
- **Cron Schedule:** `0 3 * * 1` (Haftalık Pazartesi, UTC 03:00 = TR 06:00)
- **Son Deploy:** 2026-04-11 (fix: Gemini → OpenAI GPT-4.1 geçişi — Gemini free tier quota crash çözüldü)
- **Cron Değişiklik:** 2026-04-10 — Günlükten haftalığa çekildi (Netlify free plan kredi optimizasyonu: her deploy 15 kredi, günlük=450/ay aşım, haftalık=60/ay güvenli)
- **Durum:** ✅ Aktif (Haftalık Pazartesi UTC 03:00, Notion'dan yeni "Yayınlandı" videoları seçip otomatik blog üretip dolunay.ai'ye publish eder)
- **Env Vars:** GROQ_API_KEY, OPENAI_API_KEY_DOLUNAY_AI, NOTION_SOCIAL_TOKEN, NOTION_DB_REELS_KAPAK, KIE_API_KEY, IMGBB_API_KEY, GOOGLE_SERVICE_ACCOUNT_JSON (base64), GITHUB_TOKEN

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
- **Not:** Eğitim amaçlı paylaşılan kopyası: `Paylasilan_Projeler/Supplement_Telegram_Bot_Taslak/`
- **⚠️ DİKKAT:** Lokal klasör `Paylasilan_Projeler/Supplement_Telegram_Bot_Taslak/` dosyalarından oluşturuldu (2026-04-08). GitHub monorepo'ya henüz push edilmedi — bir sonraki push ile senkronize olacak.

---



### ecom-reklam-otomasyonu (Worker — Telegram Polling)
- **Platform:** `railway`
- **Railway Project ID:** `8797307d-7b80-41cb-add0-976c09eaeed4`
- **Service ID:** `98a3be1e-f6f4-4ca2-8780-2b88bbd2125a`
- **Environment ID:** `b8353ac5-0ec4-4785-8d72-7aae17f18e56`
- **Deployment ID:** `fa43beac-a0e0-4258-8f26-2f104f37e3bb`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/eCom_Reklam_Otomasyonu`)
- **Lokal Klasör:** `Projeler/eCom_Reklam_Otomasyonu/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-04-12 (v2.1 Stabilizasyon — 24 bug fix: event loop blocking, Vision NoneType, bellek sızıntısı, Markdown parse, Perplexity exception, input validasyonu, voiceover süre kontrolü)
- **Durum:** ✅ Aktif (7/24 Telegram bot — ürün reklam videosu üretim otomasyonu)
- **Env Vars:** ENV, TELEGRAM_ECOM_BOT_TOKEN, TELEGRAM_ADMIN_CHAT_ID, OPENAI_API_KEY, OPENAI_MODEL=gpt-4.1-mini, PERPLEXITY_API_KEY, IMGBB_API_KEY, KIE_API_KEY, ELEVENLABS_API_KEY, ELEVENLABS_MODEL, REPLICATE_API_TOKEN, NOTION_SOCIAL_TOKEN, NOTION_DB_ECOM_REKLAM

---

### youtube-otomasyonu-v2 (Worker — Telegram Polling)
- **Platform:** `railway`
- **Railway Project ID:** `87e24335-52c9-460f-8b2e-0f481f5501bd`
- **Service ID:** `d17abb9e-3ef1-4f50-98c1-f4290bb2f090`
- **Environment ID:** `30bb2f27-0297-4148-88f0-d28f2ac58a6c`
- **Deployment ID:** `daf47055-105f-4e9f-85c4-a228f0eca0b5`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/YouTube_Otomasyonu`)
- **Lokal Klasör:** `Projeler/YouTube_Otomasyonu/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-04-12 (V2.2 Stabilizasyon — 14 bug fix + 2. tur: FFmpeg PATH resolve, video download retry, README düzeltme)
- **YouTube Kanalı:** Pets Got Talent (UCvj1A1gds6jZUgsPbhF3Muw) — OAuth2 bağlı
- **Durum:** ✅ Aktif (7/24 Telegram bot — YouTube video üretim otomasyonu)
- **Env Vars:** ENV, OPENAI_API_KEY, KIE_API_KEY, REPLICATE_API_TOKEN, TELEGRAM_YOUTUBE_BOT_TOKEN, TELEGRAM_ADMIN_CHAT_ID, ALLOWED_USER_IDS, NOTION_SOCIAL_TOKEN, NOTION_DB_YOUTUBE_OTOMASYON, DEFAULT_MODEL, YOUTUBE_ENABLED, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN, YOUTUBE_CATEGORY_ID, YOUTUBE_PRIVACY

---

| Proje | Klasör | Platform | Son Değişiklik | Durum | Not |
|-------|--------|----------|----------------|-------|-----|
| Dubai Emlak İçerik | `Projeler/Dubai_Emlak_İçerik_Yazarı/` | `local-only` | 2026-03-09 | ⏸️ Askıda | Script koleksiyonu (transcript, currency, calculator). Deploy planı yok, geliştirme aşamasında |

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
- ~~`dolunay-reels-kapak`~~ (`fed6db49`) — V2'ye (Dolunay_Otonom_Kapak) taşındı. **ARŞİVLENDİ** (2026-04-09)
- ~~`dolunay-youtube-kapak`~~ (`586a7bf6`) — V2'ye (Dolunay_Otonom_Kapak) taşındı. **ARŞİVLENDİ** (2026-04-09)
- ~~`sweatcoin-email-automation`~~ (`0c1ff084`) — Proje tamamen kapatıldı, Railway'den silindi, lokal arşive taşındı. **SİLİNDİ** (2026-04-08)
- ~~`Emlak Arazi Drone Çekim`~~ — Local-only proje, hiç deploy edilmemişti. Lokal arşive taşındı. **ARŞİVLENDİ** (2026-04-08)
