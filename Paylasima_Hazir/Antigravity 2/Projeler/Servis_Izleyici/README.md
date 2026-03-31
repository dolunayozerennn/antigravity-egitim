> ⚠️ **ÖNEMLİ BİLGİLENDİRME**  
> Bu proje, eğitim ve örnekleme amacıyla hazırlanmış olan bir **taslak (template)** projedir. Doğrudan tıklayıp "çalıştır" (plug-and-play) mantığıyla tasarlanmamıştır. Kendi sisteminize entegre etmeden önce:
> - Kimlik bilgilerinizi (API anahtarları, token'lar, email adresleri) tanımlamanız
> - Dosya yollarını (file paths) ve bağlantıları kendi ortamınıza göre güncellemeniz
> - Senaryoyu kendi hedeflerinize göre özelleştirmeniz beklenmektedir.
> Lütfen bu kodları inceleyerek ve kendi senaryonuza uyarlayarak geliştirin.

# 🏥 Servis İzleyici — Railway Edition

> **⚠️ TASLAK PROJE:** Bu proje, bir AI otomasyon sisteminin iskelet yapısını göstermek amacıyla paylaşılmıştır. Tam çalışır durumda değildir — kendi Railway servislerinize göre uyarlamanız ve tamamlamanız beklenmektedir. İzlenecek servis listesini ve API anahtarlarınızı eklemeniz gerekir.

Railway üzerinde çalışan bağımsız izleme servisi. Tüm servislerinizi saatlik olarak kontrol eder, sorunları otomatik düzeltir veya e-posta ile bildirir.

## 🏗️ Mimari

```
Servis_Izleyici/
├── railway_scheduler.py      ← Ana giriş noktası
├── health_check.py            ← İzleme + self-healing motoru
├── templates/
│   ├── alert_email.html       ← Alarm e-posta şablonu
│   └── healing_report.html    ← Self-heal rapor şablonu
├── requirements.txt
├── Procfile
└── .gitignore
```

## 🔍 Ne Kontrol Eder?

| Kontrol | Açıklama |
|---------|----------|
| 🚂 Deployment Durumu | SUCCESS / FAILED / CRASHED / REMOVED |
| 📋 Log Taraması | Son 24 saatteki error/exception/critical logları |
| 🩺 Self-Healing | Crash → otomatik redeploy, SSL hatası → geçici bekleme |
| 📧 E-posta Bildirimi | Sorun varsa alarm, düzeltildiyse rapor gönderir |

## 📡 İzlenen Servisler (Örnek)

- `proje-1`
- `proje-2`
- `proje-3`

> İzlenecek servis listesi `health_check.py` içindeki konfigürasyondan ayarlanır. Kendi Railway projelerinizin ID'lerini ekleyin.

## 🔑 Environment Variables (Railway)

| Variable | Açıklama |
|----------|----------|
| `RAILWAY_TOKEN` | Railway API token (zorunlu) |
| `SMTP_USER` | Gmail adresi (e-posta için) |
| `SMTP_APP_PASSWORD` | Gmail App Password (e-posta için) |
| `PORT` | HTTP port (Railway otomatik verir) |

---

*Antigravity ile oluşturulmuş taslak projedir.*
