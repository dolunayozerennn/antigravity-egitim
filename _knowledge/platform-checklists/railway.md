# Railway Platform Kontrol Listesi

> **Bu dosya yeni proje kurarken ve Railway'de hata düzeltirken ZORUNLU kontrol edilir.**
> Son güncelleme: 7 Nisan 2026

---

## 🌐 Ağ Kısıtlamaları

| Kontrol | Doğru Çözüm |
|---------|-------------|
| SMTP portu (25, 465, 587) kullanılıyor mu? | ❌ **YASAK** — Railway giden SMTP trafiğini engeller. Gmail API (OAuth2) kullan |
| WebSocket kalıcı bağlantı gerekli mi? | Railway idle timeout ~60s. Reconnect mekanizması ZORUNLU |
| Uzun süren HTTP request var mı? | Railway proxy timeout ~300s. Long-polling yerine webhook kullan |

## 📦 Sistem Bağımlılıkları (Nixpacks)

| Kontrol | Doğru Çözüm |
|---------|-------------|
| `ffmpeg`, `imagemagick`, `chromium` vb. gerekli mi? | `nixpacks.toml` → `[phases.setup] nixPkgs = ["ffmpeg"]` |
| `Aptfile` veya `apt.txt` var mı? | ❌ **SİL** — Nixpacks bunları tamamen yoksayar |
| Binary çağrısı yapılıyor mu? | `shutil.which("ffmpeg")` ile absolute path al, hardcode etme |
| Binary bulunamazsa ne olur? | `config.py` → fail-fast: başlangıçta kontrol et, yoksa `EnvironmentError` fırlat |

## 💾 Dosya Sistemi

| Kontrol | Doğru Çözüm |
|---------|-------------|
| Dosyaya kalıcı veri yazılıyor mu? | ❌ **Ephemeral FS** — Deploy'da silinir. Notion/Sheets/Redis kullan |
| Geçici dosya oluşturuluyor mu? | `/tmp/` kullan, işlem sonunda temizle |
| `.gitignore`'daki dosya runtime'da lazım mı? | Kod içinde auto-create / download mekanizması ekle |
| `Path.parents[N]` kullanımı var mı? | ✅ len() kontrolü ekle — Railway'de path kısa olabilir |

## 🔐 Ortam Değişkenleri

| Kontrol | Doğru Çözüm |
|---------|-------------|
| Tüm env var'lar Railway'de tanımlı mı? | Deploy öncesi `variableCollectionUpsert` ile doğrula |
| Hardcoded path var mı? (`/Users/`, `/home/`) | ❌ Relative path veya env var kullan |
| `config.py` fail-fast kontrolü var mı? | Başlangıçta tüm zorunlu env var'ları kontrol et, eksikse çök |

## 🌍 API ve Ağ Güvenilirliği

| Kontrol | Doğru Çözüm |
|---------|-------------|
| Tüm `requests` çağrılarında `timeout` var mı? | `timeout=30` (veya uygun değer) ZORUNLU |
| SSL/Connection retry var mı? | `urllib3.util.Retry` veya `tenacity` kullan |
| Rate limit yönetimi var mı? | 429 response'a backoff, API sağlayıcı limitlerini belgele |
| Webhook'lar idempotent mi? | Aynı event 2x gelirse çift işlem yapmamalı |

## ⏰ Cron Job Spesifik

| Kontrol | Doğru Çözüm |
|---------|-------------|
| Cron schedule Railway'de doğru ayarlı mı? | UTC saat dilimini kullan (Türkiye = UTC+3) |
| Cron çalışma süresi > 15dk olabilir mi? | Railway cron timeout'unu kontrol et, split yap |
| Cron çıktısı loglanıyor mu? | Her çalışmada en az 1 satır "çalıştırıldı" logu ZORUNLU |
| Cron "boş çalışma" durumunu handle ediyor mu? | İş yoksa bile başarılı çık, hata atma |

---

## ⚡ Hızlı Referans — Sık Yapılan Hatalar

```
❌ Aptfile/apt.txt  →  ✅ nixpacks.toml [phases.setup] nixPkgs = [...]
❌ SMTP port 587    →  ✅ Gmail API OAuth2
❌ open("data.json","w")  →  ✅ Notion/Sheets'e yaz
❌ subprocess.run("ffmpeg")  →  ✅ shutil.which("ffmpeg") + absolute path
❌ Path.parents[3]  →  ✅ len(path.parents) > 3 kontrolü
❌ requests.get(url)  →  ✅ requests.get(url, timeout=30)
❌ print(e)  →  ✅ logging.error("...", exc_info=True)
```
