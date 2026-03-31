> ⚠️ **ÖNEMLİ BİLGİLENDİRME**  
> Bu proje, eğitim ve örnekleme amacıyla hazırlanmış olan bir **taslak (template)** projedir. Doğrudan tıklayıp "çalıştır" (plug-and-play) mantığıyla tasarlanmamıştır. Kendi sisteminize entegre etmeden önce:
> - Kimlik bilgilerinizi (API anahtarları, token'lar, email adresleri) tanımlamanız
> - Dosya yollarını (file paths) ve bağlantıları kendi ortamınıza göre güncellemeniz
> - Senaryoyu kendi hedeflerinize göre özelleştirmeniz beklenmektedir.
> Lütfen bu kodları inceleyerek ve kendi senaryonuza uyarlayarak geliştirin.

# 📩 Lead Notifier Bot

> **⚠️ TASLAK PROJE:** Bu proje, bir AI otomasyon sisteminin iskelet yapısını göstermek amacıyla paylaşılmıştır. Tam çalışır durumda değildir — kendi iş süreçlerinize göre uyarlamanız ve tamamlamanız beklenmektedir. Google Sheets, Telegram bot ve Gmail ayarlarınızı eklemeniz gerekir.

Google Sheets'te belirtilen tablo(lar)da yeni bir lead tespit edildiğinde **Telegram** ve **E-Posta** ile anlık bildirim gönderen otomasyon botu.

Railway'de 7/24 çalışarak her 5 dakikada bir tabloyu kontrol eder; yeni satır bulunursa önce Telegram, ardından e-posta ile haber verir.

## ✨ Özellikler

- **Google Sheets Polling:** Belirtilen Spreadsheet'teki tab(lar)ı periyodik olarak tarar
- **Telegram Bildirimi (Birincil):** Yeni lead bilgisi anında Telegram botunuz aracılığıyla iletilir
- **E-Posta Bildirimi (İkincil):** Gmail API ile bildirim gönderir
- **Exponential Backoff:** Ardışık hatalarda bekleme süresini otomatik artırır
- **Graceful Shutdown:** `SIGTERM` / `SIGINT` sinyallerinde düzgünce kapanır
- **State Rollback:** Bildirim başarısız olursa state güncellenmez, tekrar denenir
- **Railway Ephemeral FS Desteği:** State hem diske hem env variable'a yazılır

## 📁 Dosya Yapısı

```
Lead_Notifier_Bot/
├── main.py            # Ana modül — polling döngüsü, signal handler
├── config.py          # Konfigürasyon — env variable'lardan ayarlar
├── sheets_reader.py   # Google Sheets okuma — yeni satır tespiti
├── notifier.py        # Bildirim modülü — Telegram API + Email
├── get_chat_id.py     # Yardımcı — Telegram Chat ID bulma aracı
├── requirements.txt
├── railway.json
└── .gitignore
```

## ⚙️ Environment Variables

| Değişken | Açıklama | Zorunlu |
|----------|----------|---------|
| `SPREADSHEET_ID` | İzlenecek Google Sheets dosyasının ID'si | ✅ |
| `SHEET_TABS` | Tab adları (virgülle ayrılabilir) | Hayır |
| `POLL_INTERVAL_SECONDS` | Kontrol sıklığı (varsayılan: 300) | Hayır |
| `NOTIFY_EMAIL` | Bildirim alacak e-posta adresi | ✅ |
| `TELEGRAM_BOT_TOKEN` | Telegram bot tokeni | ✅ |
| `TELEGRAM_CHAT_ID` | Mesaj gönderilecek sohbetin ID'si | ✅ |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Google SA JSON (Railway için) | Production |

## 🚀 Kullanım

```bash
python main.py           # Sürekli polling
python main.py --once    # Tek döngü (test amaçlı)
```

### Telegram Chat ID Bulma

1. Telegram botunuza `/start` mesajı gönderin
2. `python get_chat_id.py` çalıştırın
3. Ekranda çıkan `TELEGRAM_CHAT_ID` değerini environment'a ekleyin

---

*Antigravity ile oluşturulmuş taslak projedir.*
