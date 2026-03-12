---
name: servis-izleyici
description: |
  Railway'de çalışan tüm servislerin sağlık durumunu kontrol eder. 
  deploy-registry.md'deki projeleri okur, Railway GraphQL API ile 
  deployment durumlarını sorgular ve sorun tespit ederse e-posta bildirimi gönderir.
---

# 🏥 Servis İzleyici Skill

Railway'de çalışan tüm projelerin 7/24 sağlık durumunu izler ve sorun varsa anında bildirim gönderir.

## Mimari

```
_skills/servis-izleyici/
├── SKILL.md                                      ← Bu dosya
├── scripts/
│   ├── health_check.py                           ← Ana izleme scripti
│   └── setup_cron.sh                             ← Otomatik kurulum
├── com.antigravity.servis-izleyici.plist          ← macOS LaunchAgent
├── logs/
│   └── health_check.log                          ← (otomatik oluşur)
└── templates/
    └── alert_email.html                          ← E-posta şablonu
```

## 🔑 Token Yönetimi

Token bilgileri şu kaynaklardan okunur (öncelik sırasına göre):

1. **Environment variables** — `RAILWAY_TOKEN`, `SMTP_USER`, `SMTP_APP_PASSWORD`
2. **JSON Cache** — `/tmp/antigravity_env.json` (macOS izin kısıtlamalarını aşar)
3. **master.env** — `_knowledge/credentials/master.env`

> **Not:** macOS "Full Disk Access" kısıtlaması nedeniyle script doğrudan `master.env`'e erişemeyebilir. Bu durumda `setup_cron.sh` çalıştırarak tokenlar `/tmp/antigravity_env.json` Cache dosyasına aktarılır.

## Kontrol Edilen Durumlar

Script her çalıştığında şunları kontrol eder:

| Durum | Sonuç |
|-------|-------|
| `SUCCESS` | ✅ Servis sağlıklı, log'a yaz |
| `FAILED` | 🚨 E-posta gönder + log'a yaz |
| `CRASHED` | 🚨 E-posta gönder + log'a yaz |
| `REMOVED` | ⚠️ E-posta gönder + log'a yaz |
| `BUILDING` / `DEPLOYING` | ⏳ Geçici durum, rapor et ama alarm verme |
| `SLEEPING` | 😴 Beklenen (Railway free tier), alarm verme |
| `API Hatası` | 🚨 API erişim sorunu, e-posta gönder |

## 🚀 Nasıl Çalıştırılır

### İlk Kurulum (bir kez)
```bash
bash ~/Desktop/Antigravity/_skills/servis-izleyici/scripts/setup_cron.sh
```

### Manuel Çalıştırma
```bash
python3 ~/Desktop/Antigravity/_skills/servis-izleyici/scripts/health_check.py
```

### Sadece Kontrol (E-posta Göndermeden)
```bash
python3 ~/Desktop/Antigravity/_skills/servis-izleyici/scripts/health_check.py --dry-run
```

### Belirli Bir Projeyi Kontrol
```bash
python3 ~/Desktop/Antigravity/_skills/servis-izleyici/scripts/health_check.py --project shorts-demo-bot
```

### Otomatik Çalışma (LaunchAgent — Saatlik)
```bash
# Durum kontrolü:
launchctl list com.antigravity.servis-izleyici

# Durdurmak:
launchctl unload ~/Library/LaunchAgents/com.antigravity.servis-izleyici.plist

# Tekrar başlatmak:
launchctl load ~/Library/LaunchAgents/com.antigravity.servis-izleyici.plist
```

## ❌ Hata Yönetimi

| Durum | Ne Yapılmalı? |
|-------|---------------|
| `RAILWAY_TOKEN` geçersiz | `_knowledge/api-anahtarlari.md` dosyasındaki token'ı güncelle, `master.env`'i yenile |
| Gmail SMTP hatası | App Password'ü kontrol et: Google Hesabı → Güvenlik → App Passwords |
| `deploy-registry.md` parse hatası | Dosya formatının doğru olduğundan emin ol (her proje `###` başlığı altında) |
| GraphQL rate limit | Script otomatik 2 saniye bekler, cron aralığını saatlikten daha sık yapma |

## 📊 Log Formatı

Her çalışma sonrası `logs/health_check.log` dosyasına şu formatta yazılır:

```
[2026-03-11 16:30:00] ===== SAĞLIK KONTROLÜ BAŞLADI =====
[2026-03-11 16:30:01] ✅ shorts-demo-bot: SUCCESS (son deploy: 2 saat önce)
[2026-03-11 16:30:02] ✅ sweatcoin-email-automation: SUCCESS (son deploy: 12 saat önce)
[2026-03-11 16:30:03] 🚨 tele-satis-crm: FAILED → E-posta gönderildi
[2026-03-11 16:30:03] ===== SAĞLIK KONTROLÜ TAMAMLANDI (3/3 proje, 1 sorun) =====
```

## Workflow Entegrasyonu

Bu skill `/durum-kontrol` workflow'u ile de çağrılabilir:
```
_agents/workflows/durum-kontrol.md
```
