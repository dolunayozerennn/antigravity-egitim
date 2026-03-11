# INSTRUCTIONS.md — Sosyal Medya Otomatik Yanıtlama Sistemi

## 1. Proje Açıklaması

Bu sistem, ManyChat üzerinden gelen müşteri mesajlarını (metin, görsel, sesli mesaj) bir yapay zeka modeli aracılığıyla otomatik olarak yanıtlar.

Desteklenen platformlar: Instagram, Facebook Messenger, WhatsApp, TikTok (ManyChat'in desteklediği tüm kanallar).

### Sistemin kısa özeti:
1. Müşteri ManyChat üzerinden mesaj gönderir.
2. ManyChat, mesajı webhook ile bu sisteme iletir.
3. Sistem mesajı işler (metin/görsel/ses ayrımı yapar).
4. Yapay zeka modeli, işletmenin bilgi tabanına bakarak yanıt üretir.
5. Yanıt, ManyChat API üzerinden müşteriye geri gönderilir.

### Mimari:
- **Giriş:** ManyChat webhook (POST request)
- **İşleme:** Python (FastAPI) web uygulaması
- **Yapay Zeka:** Herhangi bir LLM API (OpenAI, Anthropic, Google vs.)
- **Çıkış:** ManyChat API (setCustomField + sendFlow)
- **Yayınlama:** Railway (veya benzeri hosting platformu)

---

## 2. Dil Kuralı

Tüm çıktılar, planlar, görev listeleri, açıklamalar ve kullanıcıyla iletişim Türkçe olmalıdır.

---

## 3. Kimlik Bilgileri Kuralı

API anahtarlarını `kimlik-bilgileri/credentials.env` dosyasından oku. Bu anahtarları asla kod içine doğrudan yazma; her zaman ortam değişkeni (environment variable) olarak oku.

---

## 4. Loglama Kuralı

Her API çağrısı ve hata durumunu `loglar/` klasörüne tarih-saat damgasıyla kaydet. Log formatı:
```
[2025-01-15 14:32:05] [INFO] ManyChat webhook alındı — subscriber_id: 123456
[2025-01-15 14:32:06] [INFO] Mesaj türü: metin
[2025-01-15 14:32:07] [INFO] AI yanıt üretildi — token: 145
[2025-01-15 14:32:08] [ERROR] ManyChat API hatası — 429 Too Many Requests
```

---

## 5. Hata Yönetimi Kuralı

Hata oluştuğunda `loglar/` klasöründeki son kaydı oku ve sorunu teşhis et. Yaygın hatalar ve çözümleri için `hata-cozumleri.md` dosyasına bak.

---

## 6. Sistem Akışı (Adım Adım)

### Adım 1: Webhook ile Mesaj Alma

ManyChat'ten gelen POST isteğini al. Beklenen JSON yapısı:
```json
{
  "kullanici_id": "subscriber_id_degeri",
  "platform": "Instagram",
  "last_text_input": "mesaj metni veya medya URL'si"
}
```

Webhook güvenliği için gelen istekte `X-Webhook-Secret` header'ını kontrol et. Bu değer `credentials.env` dosyasındaki `WEBHOOK_SECRET` ile eşleşmelidir. Eşleşmezse 401 döndür.

### Adım 2: Mesaj Türü Tespiti

`last_text_input` alanını incele:

- **Medya URL'si mi?** → Şu kalıpları kontrol et:
  - `lookaside.fbsbx.com/ig_messaging_cdn/` (Instagram görseli/sesi)
  - `manybot-files.s3.amazonaws.com/` (ManyChat medya deposu)
  - Eğer URL bu kalıplara uyuyorsa → Adım 3'e git
- **Düz metin mi?** → Adım 4'e git

### Adım 3: Medya İşleme

Medya URL'sini indir ve türünü tespit et:

**3a. Tür tespiti (sırasıyla kontrol et):**
1. HTTP yanıtının `Content-Type` header'ına bak (image/*, audio/*, video/*)
2. Dosya uzantısına bak (.jpg, .png, .mp3, .m4a, .mp4 vs.)
3. İkisi de belirsizse dosya başlığındaki binary imzaya bak (JPEG: FFD8FF, PNG: 89504E47)

**3b. Türe göre işleme:**
- **Görsel** (image/*) → LLM'in vision özelliği ile analiz et. Prompt: "Görselde ne olduğunu açıkla." Sonucu kullanıcı mesajı olarak kaydet: "Kullanıcı görsel iletti, gönderdiği görselin içeriği: [analiz sonucu]"
- **Ses veya Video** (audio/*, video/*) → Ses transkript API'si (Whisper veya benzeri) ile metne çevir. Dil: Türkçe. Sonucu kullanıcı mesajı olarak kaydet.

### Adım 4: Yapay Zeka ile Yanıt Üretimi

Kullanıcı mesajını AI Agent'a gönder:

- **Sistem promptu:** `prompt-rehberleri/sistem-promptu.md` dosyasından oku.
- **Bilgi tabanı:** `prompt-rehberleri/bilgi-tabani.md` dosyasını AI'a referans olarak ver. AI, yanıtlarını bu bilgi tabanına dayandırmalı.
- **Konuşma hafızası:** Her kullanıcı (subscriber_id bazlı) için son 10 mesajı hafızada tut. Bu sayede AI, önceki mesajların bağlamını bilir.
- **Yapılandırılmış çıktı:** AI'dan şu JSON formatında yanıt iste:
```json
{
  "metin": "Müşteriye gönderilecek yanıt metni",
  "link_url": "https://ornek.com/urun-sayfasi"
}
```

- `metin` → Her zaman dolu olmalı. Maksimum 2500 karakter. İçinde asla URL bulunmamalı.
- `link_url` → Opsiyonel. Gerekiyorsa tek bir URL. Boşsa boş string ("") olmalı.

### Adım 5: Yanıt Temizleme

AI yanıtını ManyChat'e göndermeden önce temizle:
- Baştaki/sondaki boşlukları kaldır
- Ardışık 3+ satır sonunu 2'ye indir
- 2500 karakteri aşıyorsa kes
- `link_url` varsa ve `www.` ile başlıyorsa `https://` ekle

### Adım 6: ManyChat'e Yanıt Gönderme

İki senaryo var:

**Senaryo A — Sadece metin yanıtı (link_url boş):**
1. `setCustomField` API'si ile yanıt metnini kullanıcının custom field'ına yaz
2. `sendFlow` API'si ile metin gönderim flow'unu tetikle

**Senaryo B — Metin + link yanıtı (link_url dolu):**
1. `setCustomField` ile yanıt metnini custom field'a yaz
2. `setCustomField` ile link'i ayrı bir custom field'a yaz
3. `sendFlow` ile link gönderim flow'unu tetikle

ManyChat API detayları için `api-dokumantasyonu/manychat-api.md` dosyasına bak.

---

## 7. Kullanıcı Talimatları (İşletmeci İçin)

Bu sistemi kendi işletmeniz için kurmak için şu adımları izleyin:

### Adım 1: API Anahtarlarınızı Hazırlayın
`kimlik-bilgileri/credentials.env` dosyasını açın ve şu bilgileri doldurun:
- ManyChat API anahtarınız
- Seçtiğiniz AI model API anahtarı (OpenAI, Anthropic veya Google)
- Webhook güvenlik şifreniz (kendiniz belirleyin)

### Adım 2: Bilgi Tabanınızı Doldurun
`prompt-rehberleri/bilgi-tabani.md` dosyasını açın. İşletmenize ait bilgileri doldurun:
- İşletme tanıtımı, şubeler, çalışma saatleri
- Ürünler/hizmetler ve fiyatlar
- Sık sorulan sorular ve politikalar

### Adım 3: Sistemi İnşa Edin
Bu klasörü AntiGravity'ye (Claude Code) bağlayın ve şu komutu verin:

> "Bu klasördeki INSTRUCTIONS.md dosyasını oku ve sistemi adım adım inşa et."

### Adım 4: ManyChat'i Yapılandırın
ManyChat hesabınızda:
1. Automation > External Request ile bir webhook bağlantısı oluşturun
2. Webhook URL'si olarak sisteminizin adresini girin
3. Gönderilen veride `kullanici_id`, `platform`, `last_text_input` alanlarını ekleyin
4. İki adet custom field oluşturun: biri AI yanıtı, biri link için
5. İki adet flow oluşturun: biri sadece metin gönderimi, biri metin + buton (link) gönderimi
6. Custom field ID'lerini ve flow ID'lerini `credentials.env` dosyasına yazın

### Adım 5: Yayınlama (Deploy)
Sistemi Railway'e yayınlayın:
1. GitHub'a yükleyin
2. Railway.app'te yeni proje oluşturun
3. GitHub repo'nuzu bağlayın
4. Environment variables kısmına `credentials.env` içeriğini ekleyin
5. Deploy edin — sistem otomatik çalışmaya başlar

---

## 8. Teknik Gereksinimler

- **Dil:** Python 3.11+
- **Framework:** FastAPI
- **Bağımlılıklar:** httpx (HTTP istekleri), python-dotenv (env dosyası okuma), uvicorn (ASGI sunucu)
- **AI SDK:** Seçilen modele göre (openai, anthropic, google-generativeai vs.)

---

## 9. Dosya Referansları

| Dosya | Açıklama |
|-------|----------|
| `kimlik-bilgileri/credentials.env` | API anahtarları ve yapılandırma |
| `api-dokumantasyonu/manychat-api.md` | ManyChat API kullanım detayları |
| `api-dokumantasyonu/ai-model-api.md` | LLM API kullanım detayları |
| `prompt-rehberleri/sistem-promptu.md` | AI Agent sistem promptu |
| `prompt-rehberleri/bilgi-tabani.md` | İşletme bilgi tabanı şablonu |
| `maliyet-tahmini.md` | Mesaj başına tahmini API maliyeti |
| `hata-cozumleri.md` | Yaygın hatalar ve çözümleri |
| `sistem-haritasi.mermaid` | Görsel sistem akış haritası |