# hata-cozumleri.md — Yaygın Hatalar ve Çözümleri

## Kullanım

Bu dosya, sistemde karşılaşılabilecek yaygın hataları ve çözümlerini listeler.
Hata oluştuğunda önce `loglar/` klasöründeki son kaydı oku, ardından bu dosyadan eşleşen hatayı bul.

---

## 1. Webhook Hataları

### Hata: Webhook'a istek gelmiyor
**Belirtiler:** Müşteri mesaj gönderiyor ama sistem hiçbir log üretmiyor.
**Olası nedenler:**
- ManyChat'te webhook URL'si yanlış girilmiş
- Railway uygulaması çalışmıyor veya uyku modunda
- ManyChat'te External Request ayarı aktif değil

**Çözüm:**
1. Railway dashboard'dan uygulamanın çalıştığını doğrula (Status: Active)
2. ManyChat'te Automation > External Request ayarını kontrol et
3. Webhook URL'sinin sonunda `/webhook` path'inin olduğundan emin ol
4. ManyChat'ten test mesajı gönderip logları kontrol et

### Hata: 401 Unauthorized (Webhook güvenlik hatası)
**Belirtiler:** Log'da `401 - Webhook secret eşleşmiyor` kaydı var.
**Çözüm:**
1. ManyChat'teki External Request header'ında `X-Webhook-Secret` değerini kontrol et
2. Bu değerin `credentials.env` dosyasındaki `WEBHOOK_SECRET` ile birebir aynı olduğundan emin ol
3. Değerin başında/sonunda boşluk olmadığından emin ol

---

## 2. ManyChat API Hataları

### Hata: 400 Bad Request — setCustomField
**Belirtiler:** Log'da `400 - ManyChat setCustomField hatası` kaydı var.
**Olası nedenler:**
- `field_id` yanlış veya silinmiş
- `subscriber_id` geçersiz
- `field_value` çok uzun

**Çözüm:**
1. ManyChat'te Settings > Fields > User Fields'a git, field ID'yi doğrula
2. `credentials.env` dosyasındaki `MANYCHAT_CEVAP_FIELD_ID` ve `MANYCHAT_LINK_FIELD_ID` değerlerini kontrol et
3. AI yanıtının 2500 karakter limitini aşmadığından emin ol

### Hata: 400 Bad Request — sendFlow
**Belirtiler:** Log'da `400 - ManyChat sendFlow hatası` kaydı var.
**Olası nedenler:**
- `flow_ns` değeri yanlış
- Flow ManyChat'te silinmiş veya devre dışı bırakılmış
- ManyChat cüzdan bakiyesi yetersiz

**Çözüm:**
1. ManyChat'te ilgili flow'un URL'sinden `flow_ns` değerini tekrar kopyala
2. Flow'un aktif (Published) durumda olduğunu kontrol et
3. ManyChat hesabında bakiye/kredi durumunu kontrol et (Settings > Billing)

### Hata: 401 Unauthorized — ManyChat API
**Belirtiler:** Tüm ManyChat API çağrıları 401 dönüyor.
**Çözüm:**
1. ManyChat'te Settings > API > API Key'i kopyala
2. `credentials.env` dosyasındaki `MANYCHAT_API_KEY` değerini güncelle
3. Key'in başında `Bearer ` yazmadığından emin ol (sistem bunu otomatik ekler)

### Hata: 429 Too Many Requests — ManyChat API
**Belirtiler:** Yoğun dönemlerde bazı mesajlar yanıtsız kalıyor.
**Çözüm:**
- Sistem otomatik olarak 2-3 saniye bekleyip tekrar dener
- Sorun devam ederse mesaj trafiğinin çok yoğun olup olmadığını kontrol et
- ManyChat Pro planının limitlerini kontrol et

---

## 3. AI Model Hataları

### Hata: 401 Unauthorized — AI API
**Belirtiler:** Log'da `401 - AI model API hatası` kaydı var.
**Çözüm:**
1. `credentials.env` dosyasındaki API key'i kontrol et
2. API key'in aktif olduğunu sağlayıcının dashboard'undan doğrula
3. API key'in ödeme yöntemi bağlı bir hesaba ait olduğundan emin ol

### Hata: 429 Rate Limit — AI API
**Belirtiler:** Yoğun dönemlerde AI yanıt üretemiyor.
**Çözüm:**
- Sistem otomatik olarak tekrar dener (maksimum 2 deneme)
- OpenAI: Usage Limits sayfasından limitinizi kontrol edin
- Anthropic: Rate Limits sayfasından planınızı kontrol edin
- Sorun sıksa daha yüksek bir plana geçmeyi düşünün

### Hata: AI yanıtı JSON formatında değil
**Belirtiler:** Log'da `JSON parse hatası` kaydı var. AI düz metin döndürmüş.
**Çözüm:**
- Sistem otomatik düzeltme denemesi yapar (düz metni `{metin: "...", link_url: ""}` formatına sarar)
- Sorun tekrarlıyorsa `prompt-rehberleri/sistem-promptu.md` dosyasındaki çıktı formatı talimatını gözden geçirin
- Temperature değerini 0.3'e düşürmeyi deneyin

### Hata: AI yanıtı boş veya anlamsız
**Belirtiler:** Müşteriye boş veya alakasız yanıt gidiyor.
**Çözüm:**
1. `prompt-rehberleri/bilgi-tabani.md` dosyasının dolu olduğundan emin ol
2. Sistem promptunun doğru yüklendiğini loglardan kontrol et
3. Hafıza (konuşma geçmişi) çok uzunsa, son 5 mesaja düşürmeyi dene

---

## 4. Medya İşleme Hataları

### Hata: Görsel/ses dosyası indirilemiyor
**Belirtiler:** Log'da `Medya indirme hatası` kaydı var.
**Olası nedenler:**
- ManyChat'ten gelen medya URL'si süresi dolmuş
- Sunucu medya sunucusuna erişemiyor

**Çözüm:**
- Medya URL'leri geçicidir. Mesaj geldiğinde hemen indirilmelidir
- Sistem bunu otomatik yapar; sorun devam ederse Railway uygulamasının internet erişimini kontrol et

### Hata: Medya türü tanınamıyor
**Belirtiler:** Log'da `Bilinmeyen medya türü` kaydı var.
**Çözüm:**
- Sistem MIME type, dosya uzantısı ve binary imza ile 3 kademeli tespit yapar
- Nadir formatlar (örn. HEIC) için dönüştürme gerekebilir
- Tanınamayan medya düz metin olarak işlenir, müşteriye "Gönderdiğiniz dosyayı anlayamadım, metin olarak yazabilir misiniz?" yanıtı verilir

### Hata: Whisper transkript hatası
**Belirtiler:** Sesli mesaj metne çevrilemiyor.
**Olası nedenler:**
- Ses dosyası 25 MB limitini aşıyor
- Ses formatı desteklenmiyor
- Whisper API key'i geçersiz

**Çözüm:**
1. Desteklenen formatlar: mp3, m4a, wav, ogg, flac, webm
2. 25 MB üzeri dosyalar reddedilir — bu durumda müşteriye daha kısa mesaj göndermesi söylenir
3. `credentials.env` dosyasındaki `WHISPER_API_KEY` veya `OPENAI_API_KEY` değerini kontrol et

---

## 5. Deployment (Railway) Hataları

### Hata: Uygulama başlamıyor
**Belirtiler:** Railway dashboard'da deploy başarısız.
**Çözüm:**
1. Railway'deki build log'larını incele
2. `requirements.txt` dosyasının eksiksiz olduğunu kontrol et
3. Python sürümünün 3.11+ olduğundan emin ol

### Hata: Uygulama çalışıyor ama webhook'a erişilemiyor
**Belirtiler:** Railway'de uygulama "Active" ama ManyChat bağlanamıyor.
**Çözüm:**
1. Railway'in verdiği public URL'yi kontrol et
2. Uygulamanın doğru portu dinlediğinden emin ol (Railway `PORT` env variable'ını otomatik sağlar)
3. URL'nin sonuna `/webhook` path'ini eklemeyi unutma

### Hata: Uygulama rastgele kapanıyor / yeniden başlıyor
**Belirtiler:** Bazı mesajlar yanıtsız kalıyor, uygulama aralıklı olarak düşüyor.
**Çözüm:**
- Railway free tier'da kaynak limiti olabilir — Starter plana geçmeyi düşünün
- Bellek sızıntısı olup olmadığını kontrol edin (hafıza depolama mekanizması)
- Railway dashboard'daki Metrics sekmesinden CPU/RAM kullanımını izleyin

---

## 6. Genel Sorun Giderme Adımları

Herhangi bir hatayla karşılaştığınızda şu adımları sırayla izleyin:

1. **Logları oku:** `loglar/` klasöründeki en son kaydı incele
2. **Hata kodunu bul:** HTTP hata kodunu bu dosyada ara
3. **Credentials kontrol et:** `credentials.env` dosyasındaki tüm değerlerin dolu ve doğru olduğunu kontrol et
4. **Servisleri kontrol et:** Railway, ManyChat ve AI sağlayıcının çalışır durumda olduğunu doğrula
5. **Tekrar dene:** Geçici hatalar genellikle birkaç dakika içinde düzelir
6. **Güncellemeleri kontrol et:** API endpoint'lerinin veya fiyatlandırmanın değişip değişmediğini sağlayıcının web sitesinden kontrol et