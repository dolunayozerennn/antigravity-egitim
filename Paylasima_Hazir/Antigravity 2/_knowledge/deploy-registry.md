# 📋 Deploy Edilmiş Projeler Kayıt Defteri

Bu dosya, Railway'e deploy edilen ve cron ile çalışan projelerin ID bilgilerini saklar.
Re-deploy'larda bu bilgiler kullanılarak gereksiz API sorguları atlanır.
Health check scripti bu dosyayı okuyarak tüm projelerin sağlık durumunu kontrol eder.

> **⚠️ ŞABLON:** Bu dosya, deploy kayıt defterinin yapısını göstermek için boş bırakılmıştır. Kendi projelerinizi deploy ettikçe buraya kayıt eklemelisiniz.

---

### ornek-proje-1
- **Platform:** `railway`
- **Railway Project ID:** `RAILWAY_PROJE_ID_BURAYA`
- **Service ID:** `RAILWAY_SERVIS_ID_BURAYA`
- **Environment ID:** `RAILWAY_ENV_ID_BURAYA`
- **GitHub Repo:** `GITHUB_USERNAME_BURAYA/proje-adi`
- **Lokal Klasör:** `Projeler/Proje_Adi/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** YYYY-MM-DD
- **Durum:** ✅ Aktif

---

### ornek-proje-2 (Cron Job)
- **Platform:** `railway-cron`
- **Railway Project ID:** `RAILWAY_PROJE_ID_BURAYA`
- **Service ID:** `RAILWAY_SERVIS_ID_BURAYA`
- **Environment ID:** `RAILWAY_ENV_ID_BURAYA`
- **GitHub Repo:** `GITHUB_USERNAME_BURAYA/proje-adi`
- **Lokal Klasör:** `Projeler/Proje_Adi/`
- **Start Komutu:** `python main.py`
- **Son Deploy:** YYYY-MM-DD
- **Durum:** ✅ Aktif (Günde 1 kez çalışır — UTC 00:00)

---

### ornek-lokal-servis (health check)
- **Platform:** `cron-local`
- **LaunchAgent:** `com.antigravity.servis-adi`
- **LogPath:** `_skills/servis-izleyici/logs/health_check.log`
- **CronSchedule:** Saatlik (her 3600 saniyede bir)
- **Lokal Klasör:** `_skills/servis-izleyici/`
- **Start Komutu:** `python3 scripts/health_check.py`
- **Durum:** ✅ Aktif — LaunchAgent ile saatlik çalışıyor

---

## 📌 Sadece Lokal Projeler (Deploy Yok)

| Proje | Klasör | Platform | Not |
|-------|--------|----------|-----|
| Örnek Proje | `Projeler/Ornek_Proje/` | `local-only` | Geliştirme aşamasında |

---

> 🛠️ **Yeni proje deploy ettiğinizde buraya ekleyin. Format yukarıdaki örneklere uygun olmalıdır.**
