> ⚠️ **ÖNEMLİ BİLGİLENDİRME**  
> Bu proje, eğitim ve örnekleme amacıyla hazırlanmış olan bir **taslak (template)** projedir. Doğrudan tıklayıp "çalıştır" (plug-and-play) mantığıyla tasarlanmamıştır. Kendi sisteminize entegre etmeden önce:
> - Kimlik bilgilerinizi (API anahtarları, token'lar, email adresleri) tanımlamanız
> - Dosya yollarını (file paths) ve bağlantıları kendi ortamınıza göre güncellemeniz
> - Senaryoyu kendi hedeflerinize göre özelleştirmeniz beklenmektedir.
> Lütfen bu kodları inceleyerek ve kendi senaryonuza uyarlayarak geliştirin.

# 🐕 Akıllı Watchdog

> **⚠️ TASLAK PROJE:** Bu proje, bir AI otomasyon sisteminin iskelet yapısını göstermek amacıyla paylaşılmıştır. Tam çalışır durumda değildir — kendi pipeline'larınıza göre uyarlamanız ve tamamlamanız beklenmektedir. İzlenecek projelerin Sheets/Notion bilgilerini ve API anahtarlarınızı eklemeniz gerekir.

**LLM-destekli pipeline sağlık izleme sistemi**

Lead pipeline'larınızın 7/24 sağlıklı çalışıp çalışmadığını kontrol eder.
Form değişiklikleri, şema kaymaları ve veri kalitesi sorunlarını **proaktif olarak** tespit eder.
Sorun bulduğunda detaylı HTML e-posta raporu gönderir.

---

## 🏗️ Mimari: 2 Katmanlı Kontrol

### Katman 1 — Yapısal Kontrol (LLM Yok)

| Modül | Kontrol |
|-------|---------|
| `sheets_checker.py` | Tab varlığı, header uyumu, veri istatistikleri |
| `notion_checker.py` | DB erişim, property uyumu, son 24h lead sayısı |

### Katman 2 — LLM Akıllı Analiz (Groq)

| Modül | Analiz |
|-------|--------|
| `llm_analyzer.py` | Şema kayması, veri kalitesi, pipeline tutarlılığı |

---

## 📁 Dosya Yapısı

```
Akilli_Watchdog/
├── main.py              # Ana orkestrasyon — CLI giriş noktası
├── config.py            # Environment variable tabanlı konfigürasyon
├── sheets_checker.py    # Google Sheets yapısal sağlık kontrolü
├── notion_checker.py    # Notion DB erişim ve property kontrolü
├── llm_analyzer.py      # Groq LLM ile akıllı analiz
├── alerter.py           # HTML alarm raporu + Gmail API ile gönderim
├── requirements.txt
├── railway.json
└── .gitignore
```

## 🚀 Kullanım

```bash
python main.py           # Tek seferlik kontrol
python main.py --force   # Her durumda rapor gönder
python main.py --loop    # Sürekli döngü (24 saatte bir)
```

## 🚨 Alarm Seviyeleri

| Seviye | Tetikleyici |
|--------|-------------|
| 🚨 **Kritik** | Tab silindi, header değişti, Notion DB erişilemez |
| ⚠️ **Uyarı** | Veri kalitesi düşük, Sheets-Notion farkı >%10 |
| ✅ **Sağlıklı** | Sorun yoksa `--force` ile tam rapor alınabilir |

## 💰 Maliyet

**$0** — Groq free tier, günlük ~5-6 LLM çağrısı

## ⚙️ Environment Variables

| Değişken | Açıklama | Zorunlu |
|----------|----------|---------|
| `GROQ_API_KEY` | Groq API anahtarı | ✅ |
| `GOOGLE_OUTREACH_TOKEN_JSON` | Gmail API OAuth2 token | ✅ |
| `NOTION_API_TOKEN` | Notion API token | ⭐ |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Service Account JSON | 🔄 |

---

*Antigravity ile oluşturulmuş taslak projedir.*
