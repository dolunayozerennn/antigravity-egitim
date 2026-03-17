# 📋 Deploy Edilmiş Projeler Kayıt Defteri

Bu dosya, Railway'e deploy edilen ve cron ile çalışan projelerin ID bilgilerini saklar.
Re-deploy'larda bu bilgiler kullanılarak gereksiz API sorguları atlanır.
Health check scripti bu dosyayı okuyarak tüm projelerin sağlık durumunu kontrol eder.

---

### shorts-demo-bot
- **Platform:** `railway`
- **Railway Project ID:** `01bf8d6e-9eb4-4a42-aaa0-0103e6e56033`
- **Service ID:** `151725ce-0416-41dd-9b94-768353c919b5`
- **Environment ID:** `64704cfe-b15e-4cb0-9256-e89575da34c4`
- **GitHub Repo:** `dolunayozerennn/shorts-demo-bot`
- **Lokal Klasör:** `Projeler/Shorts_Demo_Otomasyonu/`
- **Start Komutu:** `python bot.py`
- **Son Deploy:** 2026-03-10
- **Durum:** ✅ Aktif

---

### sweatcoin-email-automation
- **Platform:** `railway`
- **Railway Project ID:** `0c1ff084-c7a2-4e46-8372-2fb9c58ec6e4`
- **Service ID:** `08224222-4d79-43ec-b649-1a8ac4c8c8ad`
- **Environment ID:** `6b719f66-e9a6-45d3-81b5-a566fabb829f`
- **GitHub Repo:** `dolunayozerennn/sweatcoin-email-automation`
- **Lokal Klasör:** `Projeler/Swc_Email_Responder/`
- **Start Komutu:** `python railway_scheduler.py`
- **Son Deploy:** 2026-03-17
- **Durum:** ✅ Aktif (v2.4: Genuine inbound mailler artık agent'a yönlendiriliyor)

---

### tele-satis-crm
- **Platform:** `railway`
- **Railway Project ID:** `f23cb036-8434-497e-911b-5df08d6b49e6`
- **Service ID:** `faba9665-7499-4ab7-9e8a-d2a26050733f`
- **Environment ID:** `be2153d6-97b5-4b47-84f9-9bb679693b78`
- **GitHub Repo:** `dolunayozerennn/tele-satis-crm`
- **Lokal Klasör:** `Projeler/Tele_Satis_CRM/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-03-12
- **Durum:** ✅ Aktif (v2: 3 tab + WhatsApp Link + Ne zaman ulaşalım?)

---

### dolunay-reels-kapak
- **Platform:** `railway`
- **Railway Project ID:** `fed6db49-de57-4fbe-9988-528416f1b668`
- **Service ID:** `98fa5736-7e6f-454a-a648-22e47a92c28a`
- **Environment ID:** `f555d0bb-125e-4d15-838e-dbeb2936a721`
- **GitHub Repo:** `dolunayozerennn/dolunay-reels-kapak`
- **Lokal Klasör:** `Projeler/Dolunay_Reels_Kapak/`
- **Start Komutu:** `python worker.py`
- **Son Deploy:** 2026-03-12
- **Durum:** ✅ Aktif

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

### lead-notifier-bot
- **Platform:** `railway`
- **Railway Project ID:** `f23cb036-8434-497e-911b-5df08d6b49e6` (tele-satis-crm proj. içinde servis)
- **Service ID:** `4d0cfb99-8b2a-4585-86b3-44cc4967bc59`
- **Environment ID:** `be2153d6-97b5-4b47-84f9-9bb679693b78`
- **GitHub Repo:** `dolunayozerennn/lead-notifier-bot`
- **Lokal Klasör:** `Projeler/Lead_Notifier_Bot/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-03-15
- **Durum:** ✅ Aktif (v2: retry, rate-limit, reconnect, Telegram birincil kanal)

---

## 📌 Sadece Lokal Projeler (Deploy Yok)

| Proje | Klasör | Platform | Not |
|-------|--------|----------|-----|
| Dubai Emlak İçerik | `Projeler/Dubai_Emlak_İçerik_Yazarı/` | `local-only` | Lokal |
| Emlak Arazi Drone | `Projeler/Emlak_Arazi_Drone_Çekim/` | `local-only` | Lokal |

### Isbirligi_Tahsilat_Takip
- **Platform:** `railway`
- **Railway Project ID:** `8f70b293-dc33-426a-95f7-19741d3ae03c`
- **Service ID:** `533f2a47-c8f6-4e3b-a5a1-0f5b2f9b8b8d`
- **Environment ID:** `cc3aa405-1388-421c-93af-146fa91f1a1e`
- **GitHub Repo:** `dolunayozerennn/isbirligi-tahsilat-takip`
- **Lokal Klasör:** `Projeler/Isbirligi_Tahsilat_Takip/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** `2026-03-16`
- **Durum:** ✅ Aktif

### marka-is-birligi
- **Platform:** `railway`
- **Railway Project ID:** `6994adc2-edb2-4c91-b43d-237f28d41a69`
- **Service ID:** `997b869b-bd24-4be5-b37f-d5ff2f85232b`
- **Environment ID:** `5fc44142-a014-4a20-912d-c1424bfae895`
- **GitHub Repo:** `dolunayozerennn/marka-is-birligi`
- **Lokal Klasör:** `Projeler/Marka_Is_Birligi/`
- **Start Komutu:** `python railway_scheduler.py`
- **Son Deploy:** 2026-03-16
- **Durum:** ✅ Aktif (Outreach + Follow-Up + Rapor)

---

### lead-arama-zamanlayici
- **Platform:** `railway`
- **Railway Project ID:** `0aea5336-444e-4d6b-8bb3-e47614651055`
- **Service ID:** `ec68b31f-93fc-44da-8c3d-fe19a5e6eba7`
- **Environment ID:** `d90e6b8d-720e-447c-8940-00d604b0a0b8`
- **GitHub Repo:** `dolunayozerennn/lead-arama-zamanlayici`
- **Lokal Klasör:** `Projeler/Lead_Arama_Zamanlayici/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** 2026-03-16
- **Durum:** ✅ Aktif (Lead zamanlama bildirimi — dolunay@dolunay.ai → eceyarencna@gmail.com)

### akilli-watchdog
- **Platform:** `railway`
- **Railway Project ID:** `ec3ea7b1-9bdb-4886-a197-026ee2d2126c`
- **Service ID:** `ddb6ddd6-4918-4b27-bd5c-946bb829bc42`
- **Environment ID:** `45ef43a9-5ba2-475b-be50-56aaaf6b9906`
- **GitHub Repo:** `dolunayozerennn/akilli-watchdog`
- **Lokal Klasör:** `Projeler/Akilli_Watchdog/`
- **Start Komutu:** `python main.py --loop`
- **Son Deploy:** 2026-03-16
- **Durum:** ✅ Aktif (LLM-destekli pipeline sağlık izleme — 24 saatte 1 kontrol)

---

### dolunay-ai-website
- **Platform:** `railway`
- **Railway Project ID:** `58765514-d122-4653-99c5-e9958330e5a4`
- **Service ID:** `228b5ddb-680d-46d6-af71-761f046e51c7`
- **Environment ID:** `6ba7e55d-f0f0-4bd9-89f9-9b09200f00dc`
- **GitHub Repo:** `dolunayozerennn/Dolunay_AI_Website`
- **Lokal Klasör:** `Projeler/Dolunay_AI_Website/`
- **Start Komutu:** `npm run build && npm run preview -- --host --port $PORT`
- **Son Deploy:** 2026-03-16
- **Durum:** ✅ Aktif (Vite Frontend Uygulaması)

