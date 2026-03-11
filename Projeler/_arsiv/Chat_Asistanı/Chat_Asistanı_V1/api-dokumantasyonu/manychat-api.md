# manychat-api.md — ManyChat API Dokümantasyonu

## Kullanım

Bu dosya, sistemin ManyChat ile iletişim kurmak için kullandığı API endpoint'lerini tanımlar.
Tüm bilgiler test edilmiş ve çalışan bir sistemden alınmıştır.

> 🔵 **{Süslü parantez}** → Sistem tarafından otomatik doldurulan değerler. Bunlara dokunmayın.

---

## Genel Bilgiler

- **Base URL:** `https://api.manychat.com/fb/`
- **Yetkilendirme:** Tüm isteklerde `Authorization` header'ı gereklidir.
```
  Authorization: Bearer {MANYCHAT_API_KEY}
```
- **Content-Type:** Tüm isteklerde:
```
  Content-Type: application/json
```
- **Resmi dokümantasyon:** https://api.manychat.com/swagger

---

## 1. Webhook — Mesaj Alma

ManyChat, kullanıcı mesaj gönderdiğinde sistemimize bir POST isteği gönderir.

**Yön:** ManyChat → Bizim sistem

**ManyChat'te ayarlanması gereken webhook body:**
```json
{
  "kullanici_id": "{ManyChat subscriber ID}",
  "platform": "{Kanal adı: Instagram, Messenger, WhatsApp vs.}",
  "last_text_input": "{Kullanıcının gönderdiği metin veya medya URL'si}"
}
```

> Not: Bu alanların isimleri ManyChat'in External Request (webhook) ayarlarında kullanıcı tarafından belirlenir. Yukarıdaki isimler bu sistemin beklediği standart isimlerdir.

---

## 2. setCustomField — Yanıtı Custom Field'a Yazma

AI'ın ürettiği yanıtı kullanıcının ManyChat custom field'ına yazar. Bu sayede ManyChat flow'u bu değeri okuyup mesaj olarak gönderebilir.

**Yön:** Bizim sistem → ManyChat

**Endpoint:**
```
POST https://api.manychat.com/fb/subscriber/setCustomField
```

**Header'lar:**
```
Authorization: Bearer {MANYCHAT_API_KEY}
Content-Type: application/json
```

**Body — Metin yanıtı yazma:**
```json
{
  "subscriber_id": "{kullanici_id}",
  "field_id": "{MANYCHAT_CEVAP_FIELD_ID}",
  "field_value": "{AI'ın ürettiği yanıt metni}"
}
```

**Body — Link yazma (link varsa):**
```json
{
  "subscriber_id": "{kullanici_id}",
  "field_id": "{MANYCHAT_LINK_FIELD_ID}",
  "field_value": "{AI'ın ürettiği link URL'si}"
}
```

**Başarılı yanıt:**
```json
{
  "status": "success"
}
```

---

## 3. sendFlow — Mesaj Gönderim Flow'unu Tetikleme

Custom field'a yazılan değeri kullanıcıya mesaj olarak gönderen ManyChat flow'unu tetikler.

**Yön:** Bizim sistem → ManyChat

**Endpoint:**
```
POST https://api.manychat.com/fb/sending/sendFlow
```

**Header'lar:**
```
Authorization: Bearer {MANYCHAT_API_KEY}
Content-Type: application/json
```

**Body — Sadece metin gönderimi:**
```json
{
  "subscriber_id": "{kullanici_id}",
  "flow_ns": "{MANYCHAT_METIN_FLOW_ID}"
}
```

**Body — Metin + link gönderimi:**
```json
{
  "subscriber_id": "{kullanici_id}",
  "flow_ns": "{MANYCHAT_LINK_FLOW_ID}"
}
```

**Başarılı yanıt:**
```json
{
  "status": "success"
}
```

> **flow_ns nasıl bulunur:** ManyChat'te ilgili flow'un URL'sindeki `content...` ile başlayan değerdir.
> Örnek URL: `https://manychat.com/.../.../content20251129165026_517650`
> Bu durumda flow_ns = `content20251129165026_517650`

---

## 4. Gönderim Akışı Özeti

Sistemin ManyChat'e yanıt göndermesi iki adımlıdır:

### Senaryo A: Sadece metin
```
1. setCustomField → cevap metnini yaz
2. sendFlow → metin flow'unu tetikle
```

### Senaryo B: Metin + link
```
1. setCustomField → cevap metnini yaz
2. setCustomField → link URL'sini yaz
3. sendFlow → link flow'unu tetikle
```

> Önemli: sendFlow, custom field'ları set etmez. Önce setCustomField ile değerleri yazmalı, sonra sendFlow ile flow'u tetiklemelisiniz. Bu sıralama kritiktir.

---

## 5. Hata Kodları

| HTTP Kodu | Anlam | Çözüm |
|-----------|-------|-------|
| 200 | Başarılı | — |
| 400 | Geçersiz istek (yanlış parametre) | Body'deki field_id ve subscriber_id değerlerini kontrol et |
| 401 | Yetkisiz (API key hatalı) | credentials.env dosyasındaki MANYCHAT_API_KEY değerini kontrol et |
| 404 | Endpoint bulunamadı | URL'yi kontrol et |
| 429 | Rate limit aşıldı | Birkaç saniye bekleyip tekrar dene |
| 500 | ManyChat sunucu hatası | Birkaç dakika bekleyip tekrar dene |

---

## 6. Rate Limit

ManyChat API'sinin istek limitleri vardır. Yoğun trafik durumunda 429 hatası alınabilir. Bu durumda istek 2-3 saniye bekletilip tekrar denenmelidir (retry with backoff).