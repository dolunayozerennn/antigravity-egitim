> ⚠️ **Bu proje artık `_agents/musteri-kazanim/` agent'ı tarafından yönetilmektedir.**
> Projenin mantığı, config'leri ve scriptleri agent yapısına taşınmıştır. Bu klasör referans olarak korunmaktadır.

# 🎯 Buğra — Influencer Outreach Sistemi

Türkiye'deki etkinlikler için influencer bulma, iletişim kurma ve takip sistemi.

---

## 📁 Proje Yapısı

```
Buğra/
├── README.md                        ← Bu dosya (başlangıç noktası)
├── 1_influencer_bul.py              ← Adım 1: Instagram & TikTok'tan influencer tara
├── 2_email_topla.py                 ← Adım 2: E-posta adreslerini çek (bio + buton + Hunter/Apollo)
├── 3_outreach_gonder.py             ← Adım 3: Gmail API ile e-posta gönder
├── 4_takip_guncelle.py              ← Adım 4: CSV takip dosyasını güncelle
├── credentials.json                 ← Gmail OAuth2 credentials (seni içerir, paylaşma)
├── token.json                       ← Otomatik oluşur (ilk giriş sonrası)
├── config.py                        ← Apify, Hunter, Apollo API anahtarları
│
├── data/
│   ├── influencers_raw.json         ← Ham scraping çıktısı
│   ├── influencers_with_emails.json ← E-postalar eklenmiş liste
│   └── outreach_messages.json       ← Kişiselleştirilmiş mesajlar
│
├── Takip_Listesi.csv                ← 📊 Ana takip dosyası (kim, ne zaman, hangi mesaj)
├── Beğenilen_Influencerlar.csv      ← ⭐ Referans alınan/beğenilen profiller
│
└── İletişim Metni Örnekleri/
    ├── Email_Sablonu_TR.md          ← Türkçe e-posta şablonu
    ├── Email_Sablonu_EN.md          ← İngilizce e-posta şablonu
    └── Instagram_DM.md              ← Instagram DM şablonu
```

---

## 🚀 Adım Adım Kullanım

### 1️⃣ Influencer Bul
```bash
python3 1_influencer_bul.py
```
→ `data/influencers_raw.json` dosyası oluşur.

Önce `config.py` içindeki `ARAMA_KRITERLERI` listesini doldur.

### 2️⃣ E-posta Topla
```bash
python3 2_email_topla.py
```
→ Biyografi + Instagram buton + Hunter.io + Apollo.io sırayla denenir.
→ `data/influencers_with_emails.json` oluşur.

### 3️⃣ Outreach Gönder
```bash
python3 3_outreach_gonder.py --dry-run   # Önizleme
python3 3_outreach_gonder.py             # Gerçekten gönder
```
→ İlk çalıştırmada tarayıcıda Google hesabı onayı istenir.

### 4️⃣ Takip Listesini Güncelle
```bash
python3 4_takip_guncelle.py
```
→ `Takip_Listesi.csv` güncellenir.

---

## ⚙️ Kurulum

```bash
pip install requests openpyxl google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

---

## 📋 Takip Listesi Sütunları

| Sütun | Açıklama |
|---|---|
| `isim` | Influencer adı / kullanıcı adı |
| `platform` | Instagram / TikTok |
| `profil_url` | Profil linki |
| `takipci` | Takipçi sayısı |
| `email` | Bulunan e-posta |
| `email_kaynagi` | Bio / Buton / Hunter / Apollo |
| `gonderildi_mi` | Evet / Hayır |
| `gonderim_tarihi` | Gönderim tarihi |
| `mesaj_turu` | TR / EN |
| `yanit` | Yanıt var mı? |
| `notlar` | Serbest not alanı |

---

## 🔑 API Anahtarları

`config.py` dosyasında düzenle:
- **Apify:** Instagram & TikTok scraping
- **Hunter.io:** E-posta bulma
- **Apollo.io:** B2B kişi bulma
- **Gmail:** OAuth2 (credentials.json ile)

---

## 📞 Yardım

Sorun yaşarsan:
1. `token.json` dosyasını sil → yeniden Gmail girişi yap
2. Apify rate limit → birkaç dakika bekle
3. Hunter limit doldu → Apollo devreye girer (otomatik)
