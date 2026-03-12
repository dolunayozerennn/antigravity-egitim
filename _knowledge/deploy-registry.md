# 📋 Deploy Edilmiş Projeler Kayıt Defteri

Bu dosya, Railway'e deploy edilen ve cron ile çalışan projelerin ID bilgilerini saklar.
Re-deploy'larda bu bilgiler kullanılarak gereksiz API sorguları atlanır.
Health check scripti bu dosyayı okuyarak tüm projelerin sağlık durumunu kontrol eder.

---

### shorts-demo-bot
- **Platform:** `railway`
- **Railway Project ID:** `01bf8d6e-9eb4-4a42-aaa0-0103e6e56033`
- **Service ID:** `151725ce-0416-41dd-9b94-768353c919b5`
- **Environment ID:** —
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
- **Son Deploy:** 2026-03-10
- **Durum:** ✅ Aktif

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

## 📌 Sadece Lokal Projeler (Deploy Yok)

| Proje | Klasör | Platform | Not |
|-------|--------|----------|-----|
| Dubai Emlak İçerik | `Projeler/Dubai_Emlak_İçerik_Yazarı/` | `local-only` | Lokal |
| Marka İş Birliği | `Projeler/Marka_Is_Birligi/` | `local-only` | Lokal |
| Emlak Arazi Drone | `Projeler/Emlak_Arazi_Drone_Çekim/` | `local-only` | Lokal |
