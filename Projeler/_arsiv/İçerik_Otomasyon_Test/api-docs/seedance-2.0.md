# Seedance 2.0 API Dokümantasyonu

Seedance 2.0 modeli ile yeni bir video üretim görevi oluşturur. Text-to-video ve image-to-video modlarını destekler.

---

## API Endpoints

- `POST /v1/generate` — Yeni video üretim görevi oluşturur
- `GET /v1/status` — Video üretim görevinin durumunu kontrol eder

Base URL:

```text
https://seedanceapi.org
```

---

## 1) Video Generation Task Oluşturma

Seedance 2.0 modeli ile yeni bir video üretim görevi oluşturur. Text-to-video ve image-to-video modlarını destekler.

### Request Body

| Parameter | Type | Required | Description |
|---|---|---|---|
| `prompt` | `string` | Required | Üretilecek videonun metin açıklaması (max 2000 karakter) |
| `aspect_ratio` | `string` | Optional | Çıktı aspect ratio. Desteklenenler: `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `21:9`, `9:21` (Varsayılan: `1:1`) |
| `resolution` | `string` | Optional | Video çözünürlüğü: `"480p"` veya `"720p"` (Varsayılan: `"720p"`) |
| `duration` | `string` | Optional | Video süresi (saniye): `"4"`, `"8"`, veya `"12"` (Varsayılan: `"8"`) |
| `generate_audio` | `boolean` | Optional | Video için AI audio üretimini açar (Varsayılan: `false`) |
| `fixed_lens` | `boolean` | Optional | Motion blur azaltmak için kamera lensini sabitler (Varsayılan: `false`) |
| `image_urls` | `string[]` | Optional | Image-to-video üretimi için referans görsel URL listesi (maksimum 1 görsel) |
| `callback_url` | `string` | Optional | Async status bildirimleri için webhook URL. Public erişilebilir olmalı (`localhost` olmaz) |

### Örnek: Text to Video

```json
{
  "prompt": "A majestic eagle soaring through golden sunset clouds over ocean waves",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": "8"
}
```

### Örnek: Image to Video

```json
{
  "prompt": "The character slowly turns and smiles at the camera",
  "image_urls": [
    "https://example.com/my-image.jpg"
  ],
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": "4"
}
```

### Örnek: Audio Generation ile

```json
{
  "prompt": "A peaceful river flowing through a forest with birds singing",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": "8",
  "generate_audio": true,
  "fixed_lens": true
}
```

### Responses

- `200 Success`
- `400 Bad Request`
- `401 Unauthorized`
- `402 Insufficient Credits`

### Task created successfully (örnek response)

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "task_id": "seed15abc123def456pro",
    "status": "IN_PROGRESS"
  }
}
```

---

## 2) Video Generation Task Durumu Sorgulama

Bir video üretim görevinin durumunu kontrol eder ve tamamlandığında sonucu döndürür.

### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `task_id` | `string` | Required | Generate endpoint’inden dönen benzersiz task ID |

### Example Request (cURL)

```bash
curl -X GET 'https://seedanceapi.org/v1/status?task_id=seed15abc123def456pro' \
  -H 'Authorization: Bearer YOUR_API_KEY'
```

> 💡 Tip: Status API response içindeki `response` alanı video URL’lerinden oluşan bir dizidir. Video URL’sini almak için doğrudan `data.response[0]` kullanabilirsiniz.

### JavaScript Örneği (Video URL çıkarma)

```javascript
// Extract video URL from response
const videoUrl = data.response[0];
```

### Responses

- `200 Completed`
- `200 Processing`
- `200 Failed`

### Örnek Success Response

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "task_id": "seed15abc123def456pro",
    "status": "SUCCESS",
    "consumed_credits": 28,
    "created_at": "2026-02-07T10:30:00Z",
    "request": {
      "prompt": "A majestic eagle soaring through golden sunset clouds",
      "aspect_ratio": "16:9",
      "resolution": "720p",
      "duration": "8"
    },
    "response": [
      "https://cdn.example.com/videos/seed15abc123def456pro.mp4"
    ],
    "error_message": null
  }
}
```

---

## API Playground

API’yi doğrudan tarayıcıdan test edebilirsiniz. `YOUR_API_KEY` yerine gerçek API anahtarınızı yazın.

### Mevcut Endpointler

- `POST /v1/generate`
- `GET /v1/status`

### Playground (POST /v1/generate)

**Base URL**

```text
https://seedanceapi.org
```

**Endpoint**

```text
/v1/generate
```

**Headers**

```json
{
  "Authorization": "Bearer YOUR_API_KEY",
  "Content-Type": "application/json"
}
```

**Request Body**

```json
{
  "prompt": "A majestic eagle soaring through golden sunset clouds over ocean waves",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": "8"
}
```

**Action:** `Send Request`

---

## Error Codes

| Status | Code | Description |
|---|---|---|
| `400 Bad Request` | `INVALID_PROMPT` | Prompt geçersiz veya boş |
| `400 Bad Request` | `INVALID_ASPECT_RATIO` | Desteklenmeyen aspect ratio değeri |
| `400 Bad Request` | `INVALID_RESOLUTION` | Resolution `480p` veya `720p` olmalı |
| `400 Bad Request` | `INVALID_DURATION` | Duration `4`, `8`, veya `12` saniye olmalı |
| `400 Bad Request` | `TOO_MANY_IMAGES` | `image_urls` array içinde maksimum 1 image URL olabilir |
| `401 Unauthorized` | `INVALID_API_KEY` | API key eksik veya geçersiz |
| `402` | `INSUFFICIENT_CREDITS` | Bu işlem için yeterli kredi yok |
| `404 Not Found` | `TASK_NOT_FOUND` | Task ID bulunamadı veya hesabınıza ait değil |
| `500 Internal Server Error` | `INTERNAL_ERROR` | Sunucu hatası, lütfen daha sonra tekrar deneyin |

---

## Hızlı Kullanım Özeti

### 1. Video üretim görevi oluştur
`POST /v1/generate` endpoint’ine `prompt` ve isteğe bağlı parametrelerle request gönder.

### 2. `task_id` al
Başarılı response içindeki `data.task_id` değerini kaydet.

### 3. Durumu kontrol et
`GET /v1/status?task_id=...` ile task durumunu sorgula.

### 4. Video URL al
Task tamamlandığında video URL’si `data.response[0]` içinde gelir.
