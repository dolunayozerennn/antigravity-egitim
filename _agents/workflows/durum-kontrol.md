---
description: Durum Kontrol — Railway'deki tüm servislerin sağlık durumunu kontrol et ve raporla
---

# /durum-kontrol — Railway Servis Sağlık Kontrolü

Bu workflow, Railway'de çalışan tüm servislerin anlık durumunu kontrol eder.
Sorun tespit edilirse e-posta bildirimi gönderir.

**İlgili Skill:** `_skills/servis-izleyici/`

## Adımlar

1. Servis izleyici skill'ini oku ve anla:
```
view_file: ~/Desktop/Antigravity/_skills/servis-izleyici/SKILL.md
```

2. Deploy registry'deki projeleri kontrol et:
// turbo
```bash
python3 ~/Desktop/Antigravity/_skills/servis-izleyici/scripts/health_check.py
```

3. Log dosyasının son çıktısını göster:
// turbo
```bash
tail -30 ~/Desktop/Antigravity/_skills/servis-izleyici/logs/health_check.log
```

4. Kullanıcıya sonucu raporla. Aşağıdaki bilgileri göster:
   - Her servisin durumu (✅ Sağlıklı / 🚨 Sorunlu / ⏳ Geçici)
   - Sorun varsa gönderilen alarm e-postası
   - Son deploy zamanları
   - 📊 Özet: toplam/sağlıklı/sorunlu servis sayısı
   - ⏰ Cron job saatlik çalışıyor (her saat başı)

## Opsiyonel Parametreler

- **Sadece kontrol (e-posta göndermeden):**
```bash
python3 ~/Desktop/Antigravity/_skills/servis-izleyici/scripts/health_check.py --dry-run
```

- **Belirli bir projeyi kontrol:**
```bash
python3 ~/Desktop/Antigravity/_skills/servis-izleyici/scripts/health_check.py --project shorts-demo-bot
```

## Notlar
- Bu workflow crontab'tan bağımsız çalışır (elle tetiklenir)
- Cron job zaten saatlik otomatik kontrol yapıyor
- E-posta sadece sorun tespit edildiğinde gönderilir
- Tüm loglar `_skills/servis-izleyici/logs/health_check.log` dosyasında tutulur
- Railway token'ı `_knowledge/credentials/master.env` dosyasından okunur
