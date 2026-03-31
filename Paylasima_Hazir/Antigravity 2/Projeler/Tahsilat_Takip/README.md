> ⚠️ **ÖNEMLİ BİLGİLENDİRME**  
> Bu proje, eğitim ve örnekleme amacıyla hazırlanmış olan bir **taslak (template)** projedir. Doğrudan tıklayıp "çalıştır" (plug-and-play) mantığıyla tasarlanmamıştır. Kendi sisteminize entegre etmeden önce:
> - Kimlik bilgilerinizi (API anahtarları, token'lar, email adresleri) tanımlamanız
> - Dosya yollarını (file paths) ve bağlantıları kendi ortamınıza göre güncellemeniz
> - Senaryoyu kendi hedeflerinize göre özelleştirmeniz beklenmektedir.
> Lütfen bu kodları inceleyerek ve kendi senaryonuza uyarlayarak geliştirin.

# 💰 Tahsilat Takip

> **⚠️ TASLAK PROJE:** Bu proje, bir AI otomasyon sisteminin iskelet yapısını göstermek amacıyla paylaşılmıştır. Tam çalışır durumda değildir — kendi iş süreçlerinize göre uyarlamanız ve tamamlamanız beklenmektedir. Notion veritabanınızı ve Gmail ayarlarınızı eklemeniz gerekir.

Sosyal medya işbirlikleri (YouTube & Reels) için **otomatik tahsilat hatırlatma sistemi**.
Yayınlanmış videoların ödeme durumunu Notion üzerinden takip eder ve geciken ödemeler için kademeli e-posta bildirimi gönderir.

---

## 🎯 Ne Yapar?

1. **Notion'dan veri çeker** — YouTube ve Reels işbirliği veritabanlarından "Yayınlandı" durumundaki videoları alır
2. **Gecikme hesaplar** — Yayın tarihinden itibaren kaç gün geçtiğini hesaplar
3. **Kademeli bildirim gönderir:**
   - 🟡 **7 gün** geçtiyse → Sarı uyarı e-postası
   - 🔴 **14 gün** geçtiyse → Kırmızı kritik uyarı e-postası
4. **State'i Notion'da tutar** — Bildirim geçmişi Notion page yorumları üzerinden takip edilir

---

## 🏗️ Mimari

```
Notion (YouTube DB + Reels DB)
         │
         ▼
   notion_client.py ──── Veritabanı sorgusu + yorum okuma/yazma
         │
         ▼
    database.py ──── Bildirim filtresi (gün hesabı + seviye kontrolü)
         │
         ▼
     main.py ──── Zamanlayıcı + ana akış
         │
         ▼
   email_client.py ──── Gmail API (OAuth2) ile HTML e-posta gönderimi
```

## 📁 Dosya Yapısı

| Dosya | Açıklama |
|-------|----------|
| `main.py` | Ana giriş noktası — scheduler + alert mantığı + HTML e-posta şablonu |
| `config.py` | Ortam değişkenlerini yükler, Notion DB ID'lerini tutar |
| `notion_client.py` | Notion API entegrasyonu — veritabanı sorgusu, yorum okuma/yazma |
| `database.py` | Bildirim filtresi — tarih hesabı, seviye kontrolü |
| `email_client.py` | Gmail API (OAuth2) ile e-posta gönderimi |
| `railway.json` | Railway deploy konfigürasyonu |
| `requirements.txt` | Python bağımlılıkları |

## ⚙️ Ortam Değişkenleri

| Değişken | Açıklama |
|----------|----------|
| `NOTION_SOCIAL_TOKEN` | Notion API anahtarı |
| `GOOGLE_OUTREACH_TOKEN_JSON` | Gmail API OAuth2 token |

---

*Antigravity ile oluşturulmuş taslak projedir.*
