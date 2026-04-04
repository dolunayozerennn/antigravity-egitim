# 📋 Tele Satış CRM — Kurulum Rehberi

Bu rehber, projeyi sıfırdan ayağa kaldırmanız için gereken tüm adımları içerir.

---

## 🔧 Ön Gereksinimler

- **Python 3.10+** yüklü olmalı
- **Google Cloud Console** hesabı (Sheets API için)
- **Notion** hesabı ve bir Integration Token
- (Opsiyonel) **Railway** hesabı — 7/24 çalıştırmak için
- (Opsiyonel) **Gmail App Password** — hata bildirim e-postaları için

---

## 1️⃣ Projeyi Klonla ve Bağımlılıkları Kur

```bash
# Projeyi klonla (veya dosyaları indir)
git clone <repo-url>
cd Tele_Satis_CRM

# Sanal ortam oluştur
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

---

## 2️⃣ Google Sheets API Erişimi

### Seçenek A: Service Account (Üretim / Railway için Önerilen)

1. [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. **"Create Credentials" → "Service Account"** oluşturun
3. Oluşturulan Service Account'a **Google Sheets API** erişimi verin
4. **JSON key** dosyasını indirin
5. Google Sheet'inizi **Service Account e-posta adresine** (xxx@xxx.iam.gserviceaccount.com) **"Editor" olarak paylaşın**

**Railway'de kullanım:**
- JSON dosyasının **tüm içeriğini** kopyalayın
- Railway'de `GOOGLE_SERVICE_ACCOUNT_JSON` environment variable'ına yapıştırın

**Lokal geliştirmede kullanım:**
- JSON dosyasını proje kök dizinine `credentials.json` olarak kaydedin

### Seçenek B: OAuth 2.0 (Lokal Geliştirme için)

1. Google Cloud Console → Credentials → **"OAuth 2.0 Client ID"** oluşturun
2. `credentials.json` dosyasını proje kök dizinine koyun
3. İlk çalıştırmada tarayıcıda yetkilendirme yapın
4. `token.json` otomatik oluşturulacaktır

---

## 3️⃣ Notion API Ayarları

1. [Notion Developers](https://www.notion.so/my-integrations) → "New Integration" oluşturun
2. **Internal Integration Token'ı** kopyalayın
3. Notion'da bir **CRM veritabanı** oluşturun (aşağıdaki yapıda)
4. Veritabanı sayfasında **"..." → "Connections" → Integration'ınızı ekleyin**
5. Veritabanı URL'sindeki ID'yi kopyalayın:  
   `https://notion.so/XXXXXXXXXXXXXXXX?v=...` → `XXXXXXXXXXXXXXXX`

### Notion Veritabanı Yapısı

| Property Adı | Tip | Açıklama |
|---|---|---|
| İsim | Title | Lead'in adı soyadı |
| Phone | Phone | Telefon numarası |
| email | Email | E-posta adresi |
| Bütçe | Select | Bütçe aralığı (`$250K-500K`, `$500K-1M`, vb.) |
| Ne zaman ulaşalım? | Select | İletişim tercihi (`Sabah`, `Öğlen`, vb.) |
| WhatsApp Link | URL | Otomatik oluşturulur |
| Durum | Status | Lead durumu (`Aranacak`, `Arandı`, vb.) |
| Komisyon | Select | Komisyon durumu (`Ödenmedi`, `Ödendi`) |

---

## 4️⃣ Environment Variable'ları Ayarla

`.env.example` dosyasını `.env` olarak kopyalayın ve değerleri doldurun:

```bash
cp .env.example .env
```

```env
# === ZORUNLU ===
NOTION_API_TOKEN=secret_XXXXXXXXXXX
NOTION_DATABASE_ID=veritabani_id_buraya

SPREADSHEET_ID=google_sheets_id_buraya
SHEET_NAME=Form Responses 1

# === OPSİYONEL ===
SMTP_USER=sizin@gmail.com
SMTP_APP_PASSWORD=xxxx_xxxx_xxxx_xxxx
ERROR_NOTIFY_EMAIL=bildirim@ornek.com
```

### Gmail App Password Alma (Opsiyonel)

1. Gmail → Ayarlar → "Google Hesabı" → Güvenlik
2. **2 Adımlı Doğrulama** aktif olmalı
3. "App Passwords" → "Mail" + "Other" → 16 haneli şifreyi alın

---

## 5️⃣ Google Form Ayarları

1. [Google Forms](https://forms.google.com/) ile bir form oluşturun
2. Formun **yanıtlarını bir Google Sheet'e bağlayın**
3. Sheet ID'sini `.env` dosyasına ekleyin
4. `SHEET_NAME` değerini Sheet'teki sekme adıyla eşleştirin

---

## 6️⃣ Çalıştırma

### Tek Seferlik Test

```bash
python run_test.py
```

### Sürekli Polling (Üretim Modu)

```bash
python main.py
```

Varsayılan olarak **30 saniyede bir** yeni yanıtları kontrol eder.

### Railway'de 7/24 Çalıştırma

1. GitHub'a push edin
2. Railway'de yeni proje → GitHub repo bağlayın
3. Environment Variables ekleyin:
   - `NOTION_API_TOKEN`
   - `NOTION_DATABASE_ID`
   - `SPREADSHEET_ID`
   - `SHEET_NAME`
   - `GOOGLE_SERVICE_ACCOUNT_JSON` (JSON dosyasının tüm içeriği)
4. Deploy edin ✅

---

## 🧰 Yardımcı Scriptler

| Script | Açıklama |
|---|---|
| `run_test.py` | Tek döngü çalıştırır — hızlı test |
| `check_notion.py` | Notion'daki son 20 kaydı listeler |
| `inspect_notion.py` | Veritabanı schema'sını gösterir |
| `auto_dedup_all.py` | Tüm duplike kayıtları arşivler |
| `cleanup_duplicates.py` | Belirli tarihten sonraki duplikeleri temizler |

---

## 🧪 Testler

```bash
# Birim testleri
python -m pytest tests/ -v

# Sadece data_cleaner testleri
python -m pytest tests/test_data_cleaner.py -v
```

---

## ❓ Sık Karşılaşılan Sorunlar

### "Google Sheets API has not been enabled"
→ Google Cloud Console'da **Google Sheets API**'yi aktifleştirin.

### "Notion API 401 Unauthorized"
→ Integration token'ınızı kontrol edin ve veritabanını integration'a bağladığınızdan emin olun.

### "Service Account erişim hatası"
→ Google Sheet'i Service Account e-posta adresine **Editor** olarak paylaştığınızdan emin olun.

### "No new rows found"
→ `PROCESSED_ROW_INDEX` değeri son satırı gösteriyor. İlk çalıştırmada form'a yeni yanıt girin.
