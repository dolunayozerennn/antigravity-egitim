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
- **Son Deploy:** 2026-04-01 (fix: rollback_pending() eklendi — Notion API hataları sessiz data kaybını önler, groq upgrade)
- **Durum:** ✅ Aktif (Build SUCCESS, cron 10 dakikada bir çalışıyor)

---

### shorts-demo-bot
- **Platform:** `railway`
- **Railway Project ID:** `01bf8d6e-9eb4-4a42-aaa0-0103e6e56033`
- **Service ID:** `151725ce-0416-41dd-9b94-768353c919b5`
- **Environment ID:** `64704cfe-b15e-4cb0-9256-e89575da34c4`
- **GitHub Repo:** `dolunayozerennn/shorts-demo-bot`
- **Lokal Klasör:** `Projeler/Shorts_Demo_Otomasyonu/`
- **Start Komutu:** `python bot.py`
- **Son Deploy:** 2026-03-17
- **Durum:** ✅ Aktif (README güncellendi, Kie AI referansı kaldırıldı)

---

### sweatcoin-email-automation
- **Platform:** `railway`
- **Railway Project ID:** `0c1ff084-c7a2-4e46-8372-2fb9c58ec6e4`
- **Service ID:** `08224222-4d79-43ec-b649-1a8ac4c8c8ad`
- **Environment ID:** `6b719f66-e9a6-45d3-81b5-a566fabb829f`
- **GitHub Repo:** `dolunayozerennn/sweatcoin-email-automation`
- **Lokal Klasör:** `Projeler/Swc_Email_Responder/`
- **Start Komutu:** `python railway_scheduler.py`
- **Son Deploy:** 2026-03-23 (fix: is_team_email domain regex bug fixed to preserve internal emails)
- **Durum:** ✅ Aktif (v2.7: is_team_email fix, Railway Cron geçişi yapıldı, schedule: 0 7,11,15 * * 1-5)

---

### dolunay-reels-kapak (Unified Worker)
- **Platform:** `railway-cron`
- **Railway Project ID:** `fed6db49-de57-4fbe-9988-528416f1b668`
- **Service ID:** `98fa5736-7e6f-454a-a648-22e47a92c28a`
- **Environment ID:** `f555d0bb-125e-4d15-838e-dbeb2936a721`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Dolunay_Reels_Kapak`)
- **Lokal Klasör:** `Projeler/Dolunay_Reels_Kapak/`
- **Start Komutu:** `python unified_worker.py`
- **Cron Schedule:** `0 6,12,18 * * *` (Günde 3 kez: 09:00, 15:00, 21:00 TR)
- **Son Deploy:** 2026-04-01 (bugfix: check_covers_exist → count_existing_covers, kısmi kapak üretimi desteği eklendi)
- **Durum:** ✅ Aktif (Kapak üretimi + revizyon kontrolü tek worker'da birleştirildi)

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
- **GitHub Repo:** `dolunayozerennn/isbirligi-tahsilat-takip`
- **Lokal Klasör:** `Projeler/Isbirligi_Tahsilat_Takip/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-03-21 (migration: Notion Workspace değiştirildi — smoke test ✅)
- **Durum:** ✅ Aktif (Notion-based state, Gmail API OAuth2 e-posta)

---

### marka-is-birligi
- **Platform:** `railway-cron`
- **Railway Project ID:** `6994adc2-edb2-4c91-b43d-237f28d41a69`
- **Service ID:** `997b869b-bd24-4be5-b37f-d5ff2f85232b`
- **Environment ID:** `5fc44142-a014-4a20-912d-c1424bfae895`
- **GitHub Repo:** `dolunayozerennn/marka-is-birligi`
- **Lokal Klasör:** `Projeler/Marka_Is_Birligi/`
- **Start Komutu:** `python railway_scheduler.py`
- **Son Deploy:** 2026-04-01 (fix: scheduler import hatası + email deliverability iyileştirmeleri — Apollo kaldırıldı, web scraper + IG bio scraper eklendi, anti-spam kuralları, plain-text öncelik, rastgele gönderim zamanı. deployment ID: 4100128a, build SUCCESS ✅)
- **Durum:** ✅ Aktif (Outreach + Follow-Up + Rapor — Notion state + ops_logger)

---

### akilli-watchdog
- **Platform:** `railway-cron`
- **Railway Project ID:** `ec3ea7b1-9bdb-4886-a197-026ee2d2126c`
- **Service ID:** `ddb6ddd6-4918-4b27-bd5c-946bb829bc42`
- **Environment ID:** `45ef43a9-5ba2-475b-be50-56aaaf6b9906`
- **GitHub Repo:** `dolunayozerennn/akilli-watchdog`
- **Lokal Klasör:** `Projeler/Akilli_Watchdog/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-03-27 (v3.0: Token freshness kontrolü + Railway deployment probe + 9 servis izleme)
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
- **Son Deploy:** 2026-04-01 (fix: content filter moderate→relaxed — pipeline 6 gündür kilitlenmiş durumdaydı)
- **Durum:** ✅ Aktif (TikTok→LinkedIn video pipeline, günde 1 kez)
- **Env Vars:** LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN, GROQ_API_KEY, NOTION_SOCIAL_TOKEN, NOTION_LINKEDIN_DB_ID

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
- **Son Deploy:** 2026-04-01 (fix: Notion 'Post Tipi' property eklendi + fail-safe return True→False bug fix. Build SUCCESS, deployment: 4b5350a9)
- **Durum:** ✅ Aktif (Haftalık AI Haberleri + AI Tavsiyesi LinkedIn postu)
- **Env Vars:** PERPLEXITY_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN, NOTION_SOCIAL_TOKEN, NOTION_LINKEDIN_DB_ID

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
- **Son Deploy:** 2026-04-01 (fix: yt-dlp 2024.3.10→2026.3.17 TikTok API uyum, NOTION_TOKEN→NOTION_SOCIAL_TOKEN düzeltmesi)
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
- **Cron Schedule:** `0 3 * * *` (Günlük, UTC 03:00)
- **Son Deploy:** 2026-04-01 (fix: Netlify build hook eklendi, bare except→except Exception düzeltmesi)
- **Durum:** ✅ Aktif (Günlük UTC 03:00, Notion'dan yeni "Yayınlandı" videoları seçip otomatik blog üretip dolunay.ai'ye publish eder)
- **Env Vars:** GROQ_API_KEY, GEMINI_API_KEY, NOTION_SOCIAL_TOKEN, NOTION_DB_REELS_KAPAK, KIE_API_KEY, IMGBB_API_KEY, GOOGLE_SERVICE_ACCOUNT_JSON (base64), GITHUB_TOKEN

---

### supplement-telegram-bot
- **Platform:** `railway`
- **Railway Project ID:** `35acfbc5-f058-45f9-ba76-373b47e66b07`
- **Service ID:** `0a3f240f-6fea-4176-b480-a2cdb99e4a93`
- **Environment ID:** `6f09ea79-49b6-4414-b820-6c83d5bd31cb`
- **GitHub Repo:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Supplement_Telegram_Bot/`)
- **Lokal Klasör:** `Projeler/Supplement_Telegram_Bot/`
- **Son Deploy:** 2026-03-31 (SUCCESS)
- **Durum:** ✅ Aktif (7/24 Telegram bot — takviye takibi)
- **Not:** Eğitim amaçlı paylaşılan kopyası: `Paylasilan_Projeler/Supplement_Telegram_Bot_Taslak/`

---

### dolunay-youtube-kapak (Aktif Worker)
- **Platform:** `railway`
- **Railway Project ID:** `586a7bf6-1787-4d3a-af13-1e1730ee5a15`
- **Service ID:** `b15ae2ea-87b0-4818-bb6c-c8f7458817e3`
- **Environment ID:** `fe917cd2-511f-4e73-9b75-b77ce28d16ae`
- **Son Deploy:** 2026-04-01 (SUCCESS)
- **Durum:** ✅ Aktif (YouTube thumbnail üretim worker'ı)
- **Not:** 3 adet duplikasyon projesi temizlendi (93de, ab22, b3f0 — hepsi FAILED)

---

## 📌 Askıda / Geliştirme Aşamasındaki Projeler (Deploy Yok)

| Proje | Klasör | Platform | Son Değişiklik | Durum | Not |
|-------|--------|----------|----------------|-------|-----|
| Dubai Emlak İçerik | `Projeler/Dubai_Emlak_İçerik_Yazarı/` | `local-only` | 2026-03-09 | ⏸️ Askıda | Script koleksiyonu (transcript, currency, calculator). Deploy planı yok, geliştirme aşamasında |
| Emlak Arazi Drone | `Projeler/Emlak_Arazi_Drone_Çekim/` | `local-only` | 2026-03-14 | ⏸️ Askıda | Kie AI + Unsplash tabanlı video üretimi. Lokal çalıştırılabilir ama deploy edilmemiş |

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

## 📦 Arşiv (Kaldırılmış Projeler)

### tele-satis-crm ⛔ (KALDIRILDI)
- **Platform:** `railway` → **SİLİNDİ**
- **Railway Project ID:** `f23cb036-8434-497e-911b-5df08d6b49e6`
- **Service ID:** `faba9665-7499-4ab7-9e8a-d2a26050733f` (silindi)
- **GitHub Repo:** `dolunayozerennn/tele-satis-crm`
- **Lokal Klasör:** `Projeler/Tele_Satis_CRM/` (arşiv)
- **Durum:** ⛔ Kaldırıldı (2026-03-22) — Lead Pipeline'a birleştirildi. Maliyet optimizasyonu.

---

### lead-notifier-bot ⛔ (KALDIRILDI)
- **Platform:** `railway` → **SİLİNDİ**
- **Railway Project ID:** `f23cb036-8434-497e-911b-5df08d6b49e6`
- **Service ID:** `4d0cfb99-8b2a-4585-86b3-44cc4967bc59` (silindi)
- **GitHub Repo:** `dolunayozerennn/lead-notifier-bot`
- **Lokal Klasör:** `Projeler/Lead_Notifier_Bot/` (arşiv)
- **Durum:** ⛔ Kaldırıldı (2026-03-22) — Lead Pipeline'a birleştirildi. Maliyet optimizasyonu.

---

### tele-satis-notifier ⛔ (KALDIRILDI)
- **Platform:** `railway-cron` → **SİLİNDİ**
- **Railway Project ID:** `0aea5336-444e-4d6b-8bb3-e47614651055`
- **Service ID:** `ec68b31f-93fc-44da-8c3d-fe19a5e6eba7` (silindi)
- **GitHub Repo:** `dolunayozerennn/tele-satis-notifier`
- **Lokal Klasör:** `Projeler/Tele_Satis_Notifier/` (arşiv)
- **Durum:** ⛔ Kaldırıldı (2026-03-22) — Lead Pipeline'a birleştirildi. Maliyet optimizasyonu.

---

### dolunay-ai-website ⛔ (KALDIRILDI)
- **Platform:** `railway` → **SİLİNDİ** (Netlify'a taşındı)
- **Railway Project ID:** `58765514-d122-4653-99c5-e9958330e5a4`
- **Service ID:** `af8d86d9-aa29-4e4b-bdca-70dd40f7c452` (silindi)
- **GitHub Repo:** `dolunayozerennn/Dolunay_AI_Website`
- **Lokal Klasör:** `Projeler/Dolunay_AI_Website/`
- **Durum:** ⛔ Kaldırıldı (2026-03-22) — Website zaten Netlify'da barınıyor, Railway'deki kopya gereksizdi.

---

### LinkedIn_Text_Paylasim (eski duplikasyon) ⛔ (KALDIRILDI)
- **Railway Project ID:** `d4c5a5d1-afd5-41ac-87ce-1f880217801d` (servisleri silindi)
- **Durum:** ⛔ Kaldırıldı (2026-04-01) — Aktif `linkedin-text-cron` (5465753a) ile DUPLİKAYDI. Çift post riski nedeniyle servisi silindi.

---

### Lead Notifier Bot (eski hayalet) ⛔ (KALDIRILDI)
- **Railway Project ID:** `6b5e029b-0235-4c6b-8b8d-b6dd4d4bb4e0` (servisleri silindi)
- **Durum:** ⛔ Kaldırıldı (2026-04-01) — Lead Pipeline'a birleştirilmiş ama Railway'de çalışmaya devam ediyordu.

---

### linkedin-paylasim (eski monolitik) ⛔ (TEMİZLENMELİ)
- **Railway Project ID:** `9aec063f-24f9-4cc3-8a98-90565b9b1b53`
- **Service ID:** `3d839ef6-ade2-4803-a31d-f906f2ab8183`
- **Durum:** ⛔ Hayalet Proje — linkedin-text + linkedin-video olarak ayrılmış, bu eski monolitik proje hala aktif. Servisi SİLİNMELİ.

---

### Twitter_Paylasim (eski) ⛔ (TEMİZLENMELİ)
- **Railway Project ID:** `9b8a5927-1b2b-4d0f-bb4d-fd167b4fcee0`
- **Service ID:** `twitter-paylasim`
- **Durum:** ⛔ Hayalet Proje — Yeni `twitter-video-cron` (24c3d0d1) ile DUPLİKE. Servisi SİLİNMELİ.

---

### dolunay-youtube-kapak duplikasyonları ⛔ (TEMİZLENMELİ)
- **Railway Project IDs:** `93de1226`, `ab229571`, `b3f0902b` (hepsi FAILED)
- **Aktif proje:** `586a7bf6` (SUCCESS)
- **Durum:** ⛔ 3 duplikasyon projesi — Hepsi FAILED durumunda, kaynak israfı. SİLİNMELİ.

---

### marka-is-birligi (boş duplikasyon) ⛔ (TEMİZLENMELİ)
- **Railway Project ID:** `0522fff5-ea33-4c64-9187-1e18531ab39b`
- **Durum:** ⛔ Boş proje — Servis yok, deployment yok. Aktif proje: `6994adc2`. SİLİNMELİ.
