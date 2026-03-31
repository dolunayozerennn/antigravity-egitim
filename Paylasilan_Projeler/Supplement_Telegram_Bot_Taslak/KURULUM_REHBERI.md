# 🤖 Supplement Buddy — Telegram Bot

> **Fotoğraf gönder → AI analiz etsin → Notion'a kaydetsin**

Bu bot, Telegram üzerinden gönderdiğin supplement/vitamin etiket fotoğraflarını Google Gemini yapay zeka modeli ile analiz eder,
içerisindeki tüm bilgileri (ürün adı, marka, içerik tablosu, kullanım önerisi vb.) çıkarır ve Notion veritabanına otomatik olarak kaydeder.

Ayrıca supplement/vitamin hakkında soru sorabilir, chatbot olarak kullanabilirsin.

---

## 🎯 Özellikler

| Özellik | Açıklama |
|---------|----------|
| 📸 **Görsel Analiz** | Fotoğraftaki supplement etiketini AI ile okur |
| 📋 **Notion Loglama** | Analiz sonuçlarını otomatik olarak Notion DB'ye yazar |
| 💬 **Chatbot** | Supplement hakkında sorulara yanıt verir |
| 🔒 **Kullanıcı Kontrolü** | Sadece yetkili kullanıcıların erişimine izin verir |
| ☁️ **7/24 Çalışır** | Railway'e deploy edersen kesintisiz çalışır |

---

## ⚡ Hızlı Kurulum

### 1. Gereksinimler

- Python 3.10+
- Telegram Bot Token ([BotFather](https://t.me/BotFather) ile oluştur)
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com))
- Notion Integration Token ([Notion Integrations](https://www.notion.so/my-integrations))

### 2. Projeyi İndir

```bash
# Klasörü kendi bilgisayarına kopyala
cd ~/Desktop
cp -r Supplement_Telegram_Bot_Taslak Supplement_Telegram_Bot
cd Supplement_Telegram_Bot
```

### 3. Sanal Ortam Oluştur

```bash
python3 -m venv venv
source venv/bin/activate    # Mac/Linux
# venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 4. Ortam Değişkenlerini Ayarla

```bash
cp .env.example .env
```

`.env` dosyasını aç ve kendi API anahtarlarını gir:

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...    # BotFather'dan aldığın token
GEMINI_API_KEY=AIza...                   # Google AI Studio'dan aldığın key
NOTION_TOKEN=ntn_...                     # Notion integration token
NOTION_DB_ID=abcdef12-3456-...           # Notion database ID'si
ENV=production
```

### 5. Notion Database Oluştur

Notion'da yeni bir **Database** oluştur ve şu sütunları ekle:

| Sütun Adı | Tür | Açıklama |
|-----------|-----|----------|
| **Ürün Adı** | Title | Ana başlık (otomatik var) |
| **Marka** | Text | Ürünün markası |
| **Tür** | Select | Tablet, Kapsül, Toz, Likit, Softjel, Diğer |
| **İçerik Sayısı** | Number | Toplam madde sayısı |
| **Porsiyon** | Text | Porsiyon büyüklüğü |
| **Toplam Porsiyon** | Text | Toplam porsiyon sayısı |
| **Bileşim** | Text | Tüm bileşenler |
| **Kullanım Önerisi** | Text | Kullanım talimatları |
| **Saklama Koşulları** | Text | Saklama bilgisi |
| **Model** | Select | Kullanılan AI modeli |
| **Durum** | Select | ✅ Başarılı, ⚠️ Kısmi, ❌ Başarısız |
| **Analiz Tarihi** | Date | Analiz tarihi |

> ⚠️ Database'i oluşturduktan sonra **Share** butonuna bas → Integration'ını davet et!

### 6. Botu Çalıştır

```bash
python main.py
```

Telegram'da botuna git ve bir supplement fotoğrafı gönder! 🎉

---

## ☁️ Railway'de 7/24 Çalıştırma (Opsiyonel)

1. [Railway.app](https://railway.app) hesabı aç
2. "New Project" → "Deploy from GitHub repo" seç
3. Proje dizinini yükle
4. **Variables** sekmesinde `.env` dosyasındaki tüm değişkenleri ekle
5. Deploy et, bot 7/24 çalışsın!

`railway.toml` dosyası zaten yapılandırılmış durumda.

---

## 📂 Proje Yapısı

```
Supplement_Telegram_Bot/
├── main.py                  # Bot ana dosyası (handlers, polling)
├── config.py                # Ortam değişkenleri doğrulama (fail-fast)
├── logger.py                # Standart log sistemi
├── core/
│   └── gemini_analyzer.py   # Gemini Vision analiz motoru
├── infrastructure/
│   └── notion_service.py    # Notion API loglama servisi
├── requirements.txt         # Python bağımlılıkları
├── railway.toml             # Railway deploy ayarları
├── .env.example             # Ortam değişkenleri şablonu
└── KURULUM_REHBERI.md       # Bu dosya
```

---

## 🔧 Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| `CRITICAL STARTUP FAILURE` | `.env` dosyasındaki gerekli değişkenleri kontrol et |
| `Notion 404 hatası` | Database'e integration'ı davet ettiğinden emin ol |
| `Telegram Conflict` | Botu tek bir yerde çalıştır (lokal VEYA Railway) |
| `Gemini hatası` | API key'in geçerli olduğunu ve bakiyenin yeterli olduğunu kontrol et |

---

## 📜 Antigravity Prompt

> Eğer Antigravity asistanın varsa, şu komutu ver:
>
> *"Bu klasördeki projeyi çalıştırmak istiyorum. Önce requirements.txt'yi kur, ardından .env.example'ı .env olarak kopyala ve benden API anahtarlarını iste."*

---

**Geliştiren:** Antigravity Otomasyon Ekibi  
**Lisans:** Eğitim amaçlı kullanım
