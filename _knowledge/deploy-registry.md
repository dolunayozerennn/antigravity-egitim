# 📋 Deploy Edilmiş Projeler Kayıt Defteri

Bu dosya, Railway'e deploy edilen ve cron ile çalışan projelerin ID bilgilerini saklar.
Re-deploy'larda bu bilgiler kullanılarak gereksiz API sorguları atlanır.
Health check scripti bu dosyayı okuyarak tüm projelerin sağlık durumunu kontrol eder.

> **⚠️ MİMARİ NOT (Mart 2026):** Çift-repo problemi nedeniyle **Native Mono-Repo** mimarisine geçilmiştir.
> Eskiden her projenin ayrı bir `GitHub Repo` alanı varken, yeni projelerin tamamı `dolunayozerennn/antigravity-egitim` üzerinden Railway'in "Root Directory" ayarıyla deploy edilecektir.
> Aşağıdaki eski projeler, vakit bulunduğunda monorepo'ya taşınıp eski repoları arşivlenebilir. Yeni projelerde her zaman `antigravity-egitim` reposu hedeflenmelidir.

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

### tele-satis-crm ⛔ (KALDIRILDI)
- **Platform:** `railway` → **SİLİNDİ**
- **Railway Project ID:** `f23cb036-8434-497e-911b-5df08d6b49e6`
- **Service ID:** `faba9665-7499-4ab7-9e8a-d2a26050733f` (silindi)
- **GitHub Repo:** `dolunayozerennn/tele-satis-crm`
- **Lokal Klasör:** `Projeler/Tele_Satis_CRM/` (arşiv)
- **Durum:** ⛔ Kaldırıldı (2026-03-22) — Lead Pipeline'a birleştirildi. Maliyet optimizasyonu.

---

### dolunay-reels-kapak
- **Platform:** `railway-cron`
- **Railway Project ID:** `fed6db49-de57-4fbe-9988-528416f1b668`
- **Service ID:** `98fa5736-7e6f-454a-a648-22e47a92c28a`
- **Environment ID:** `f555d0bb-125e-4d15-838e-dbeb2936a721`
- **GitHub Repo:** `dolunayozerennn/dolunay-reels-kapak`
- **Lokal Klasör:** `Projeler/Dolunay_Reels_Kapak/`
- **Start Komutu:** `python worker.py`
- **Son Deploy:** 2026-03-21 (migration: Railway Cron Job olarak ayarlandı)
- **Durum:** ✅ Aktif (multi-theme + revision engine + Railway Cron geçişi, schedule: 0 6,12,18 * * *)

### revizyon-cron (dolunay-reels-kapak projesi içinde)
- **Platform:** `railway-cron`
- **Railway Project ID:** `fed6db49-de57-4fbe-9988-528416f1b668`
- **Service ID:** `1e740cb1-3b80-47e3-a863-2d27c7f2c01a`
- **Environment ID:** `f555d0bb-125e-4d15-838e-dbeb2936a721`
- **GitHub Repo:** `dolunayozerennn/dolunay-reels-kapak`
- **Lokal Klasör:** `Projeler/Dolunay_Reels_Kapak/`
- **Start Komutu:** `python revision_cron_worker.py`
- **Son Deploy:** 2026-03-21 (migration: Railway Cron Job olarak ayarlandı)
- **Durum:** ✅ Aktif (Günde 5 kez: Railway Cron ile çalışıyor, schedule: 0 7,10,13,16,19 * * *)

---

### servis-izleyici (health check)
- **Platform:** `cron-local`
- **LaunchAgent:** `com.antigravity.servis-izleyici`
- **LogPath:** `_skills/servis-izleyici/logs/health_check.log`
- **CronSchedule:** Saatlik (her 3600 saniyede bir)
- **Lokal Klasör:** `_skills/servis-izleyici/`
- **Start Komutu:** `python3 scripts/health_check.py`
- **Durum:** ✅ Aktif — LaunchAgent ile saatlik çalışıyor

---

### lead-notifier-bot ⛔ (KALDIRILDI)
- **Platform:** `railway` → **SİLİNDİ**
- **Railway Project ID:** `f23cb036-8434-497e-911b-5df08d6b49e6`
- **Service ID:** `4d0cfb99-8b2a-4585-86b3-44cc4967bc59` (silindi)
- **GitHub Repo:** `dolunayozerennn/lead-notifier-bot`
- **Lokal Klasör:** `Projeler/Lead_Notifier_Bot/` (arşiv)
- **Durum:** ⛔ Kaldırıldı (2026-03-22) — Lead Pipeline'a birleştirildi. Maliyet optimizasyonu.

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
- **Son Deploy:** 2026-03-21 (fix: markalar.csv otomatik oluşturma — Railway deploy sonrası data kalıcılık sorunu çözüldü, deployment ID: 33f5b55d, smoke test ✅)
- **Durum:** ✅ Aktif (Outreach + Follow-Up + Rapor — CSV auto-init)

---

### tele-satis-notifier ⛔ (KALDIRILDI)
- **Platform:** `railway-cron` → **SİLİNDİ**
- **Railway Project ID:** `0aea5336-444e-4d6b-8bb3-e47614651055`
- **Service ID:** `ec68b31f-93fc-44da-8c3d-fe19a5e6eba7` (silindi)
- **GitHub Repo:** `dolunayozerennn/tele-satis-notifier`
- **Lokal Klasör:** `Projeler/Tele_Satis_Notifier/` (arşiv)
- **Durum:** ⛔ Kaldırıldı (2026-03-22) — Lead Pipeline'a birleştirildi. Maliyet optimizasyonu.

---

### akilli-watchdog
- **Platform:** `railway-cron`
- **Railway Project ID:** `ec3ea7b1-9bdb-4886-a197-026ee2d2126c`
- **Service ID:** `ddb6ddd6-4918-4b27-bd5c-946bb829bc42`
- **Environment ID:** `45ef43a9-5ba2-475b-be50-56aaaf6b9906`
- **GitHub Repo:** `dolunayozerennn/akilli-watchdog`
- **Lokal Klasör:** `Projeler/Akilli_Watchdog/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-03-21 (migration: Railway Cron Job olarak ayarlandı, deployment ID: bd8b7883)
- **Durum:** ✅ Aktif (Günde 1 kez çalışır — UTC 00:00. Sürekli uyanık kalmadığından fatura optmizasyonu yapıldı.)

---

### dolunay-ai-website ⛔ (KALDIRILDI)
- **Platform:** `railway` → **SİLİNDİ** (Netlify'a taşındı)
- **Railway Project ID:** `58765514-d122-4653-99c5-e9958330e5a4`
- **Service ID:** `af8d86d9-aa29-4e4b-bdca-70dd40f7c452` (silindi)
- **GitHub Repo:** `dolunayozerennn/Dolunay_AI_Website`
- **Lokal Klasör:** `Projeler/Dolunay_AI_Website/`
- **Durum:** ⛔ Kaldırıldı (2026-03-22) — Website zaten Netlify'da barınıyor, Railway'deki kopya gereksizdi.

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
- **Son Deploy:** 2026-03-24 (fix: cronSchedule railway.json'a eklendi — Railway service instance'da 0 0 1 1 * olarak kalmıştı, */10 * * * * olarak düzeltildi)
- **Durum:** ✅ Aktif (Build SUCCESS, cron 10 dakikada bir çalışıyor)
- **⚠️ Telegram Notu:** TELEGRAM_CHAT_ID=847006455 (Savaş) "chat not found" hatası. Savaş bot'a /start göndermeli.

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
- **Son Deploy:** 2026-03-24 (initial deploy: Railway CronJob olarak kuruldu)
- **Durum:** ⚠️ Beklemede — GITHUB_TOKEN eksik (blog publish için gerekli)
- **Env Vars:** GROQ_API_KEY, GEMINI_API_KEY, NOTION_SOCIAL_TOKEN, NOTION_DB_REELS_KAPAK, KIE_API_KEY, IMGBB_API_KEY, GOOGLE_SERVICE_ACCOUNT_JSON (base64)

---

## 📌 Sadece Lokal Projeler (Deploy Yok)

| Proje | Klasör | Platform | Not |
|-------|--------|----------|-----|
| Dubai Emlak İçerik | `Projeler/Dubai_Emlak_İçerik_Yazarı/` | `local-only` | Geliştirme aşamasında |
| Emlak Arazi Drone | `Projeler/Emlak_Arazi_Drone_Çekim/` | `local-only` | Geliştirme aşamasında |

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
