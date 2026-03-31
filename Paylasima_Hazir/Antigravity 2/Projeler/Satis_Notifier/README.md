> ⚠️ **ÖNEMLİ BİLGİLENDİRME**  
> Bu proje, eğitim ve örnekleme amacıyla hazırlanmış olan bir **taslak (template)** projedir. Doğrudan tıklayıp "çalıştır" (plug-and-play) mantığıyla tasarlanmamıştır. Kendi sisteminize entegre etmeden önce:
> - Kimlik bilgilerinizi (API anahtarları, token'lar, email adresleri) tanımlamanız
> - Dosya yollarını (file paths) ve bağlantıları kendi ortamınıza göre güncellemeniz
> - Senaryoyu kendi hedeflerinize göre özelleştirmeniz beklenmektedir.
> Lütfen bu kodları inceleyerek ve kendi senaryonuza uyarlayarak geliştirin.

# 📞 Satış Notifier

> **⚠️ TASLAK PROJE:** Bu proje, bir AI otomasyon sisteminin iskelet yapısını göstermek amacıyla paylaşılmıştır. Tam çalışır durumda değildir — kendi iş süreçlerinize göre uyarlamanız ve tamamlamanız beklenmektedir. Google Sheets'inizi, email ayarlarınızı ve API anahtarlarınızı eklemeniz gerekir.

**CRM Otomasyonu'nun tamamlayıcı servisi.** Google Sheets'teki lead'lerin **"ne zaman aranmak istersiniz"** tercihine göre **satış ekibine zamanlı bilgilendirme e-postası** gönderen otomasyon.

---

## 🎯 Ne Yapar?

CRM sisteminin kullandığı Google Sheet'i 5 dakikada bir izler. Yeni lead düştüğünde zamanlama tercihine göre:

| Tercih | Davranış |
|--------|----------|
| **Gün içinde** | Lead düştüğü anda anında mail atar |
| **Akşam 6'dan sonra** | Kuyruğa alır, o gün TR saati 18:00'da topluca mail atar |
| **Haftasonu** | Hafta içi geldiyse kuyruğa alır, Cumartesi 10:00'da gönderir |
| **Aramayın mesaj atın** | Mail atılmaz, sadece log yazılır |

## 🏗️ Mimari

```
Google Sheets (Lead verisi)
    │
    ▼
SheetsReader → Yeni satır tespit (state-based)
    │
    ▼
TimingParser → Zamanlama tercihi parse
    │
    ├─ Anlık → EmailSender → Gmail API → Satış Ekibi
    └─ Zamanlı → QueueManager (Sheets "Kuyruk" tab'ı)
                    │
                    ▼
                 Saat gelince → EmailSender → Gmail API → Satış Ekibi
```

- **Kuyruk** Google Sheets'in "Kuyruk" tab'ında tutulur → Railway restart'larında veri kaybolmaz
- **Hata bildirimi:** Telegram üzerinden alarm

## 📁 Dosya Yapısı

```
Satis_Notifier/
├── main.py              # Ana orkestrasyon — polling + zamanlama
├── config.py            # Konfigürasyon (env variables)
├── sheets_reader.py     # Sheets okuyucu (state tracking + retry + reconnect)
├── timing_parser.py     # Zamanlama tercihi tespit
├── queue_manager.py     # Kuyruk yönetimi (Sheets-based)
├── email_sender.py      # Gmail API ile HTML e-posta gönderimi
├── alerter.py           # Telegram alarm sistemi
├── requirements.txt
├── railway.json
└── .gitignore
```

## ⚙️ Konfigürasyon

| Env Variable | Açıklama |
|-------------|----------|
| `SPREADSHEET_ID` | İzlenen Google Sheet ID |
| `SHEET_TABS` | Virgülle ayrılmış tab isimleri |
| `POLL_INTERVAL_SECONDS` | Polling aralığı (varsayılan: 300) |
| `SENDER_EMAIL` | Gönderen e-posta |
| `RECIPIENT_EMAIL` | Alıcı e-posta |
| `GOOGLE_TOKEN_JSON` | OAuth2 token (Railway) |

---

*Antigravity ile oluşturulmuş taslak projedir.*
