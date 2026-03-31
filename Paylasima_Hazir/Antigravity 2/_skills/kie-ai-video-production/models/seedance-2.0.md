# Seedance 2.0 — Model Referansı

## Genel Bilgi
- **Model ID:** Kie AI üzerinden `seedance-2.0` (model adını API'den doğrula)
- **Alternatif endpoint:** `https://seedanceapi.org` (bağımsız API)
- **Tür:** Video Üretimi (Text-to-Video, Image-to-Video)
- **Geliştirici:** ByteDance
- **Süre:** 4, 8 veya 12 saniye
- **Kalite:** 480p veya 720p
- **Güçlü Yönler:**
  - Sinematik çıktı
  - Native audio üretimi
  - Kamera kontrolü
  - Gerçek dünya fiziği
  - Sabit lens (motion blur azaltma)

---

## Endpoint (Bağımsız API)

```
POST https://seedanceapi.org/v1/generate
Authorization: Bearer {API_KEY}
Content-Type: application/json
```

> ⚠️ Seedance 2.0, Kie AI'ın standart `/jobs/createTask` endpoint'i yerine
> kendi API'sini kullanabilir. Kie AI üzerinden kullanılıyorsa model adını
> Kie AI kataloğundan doğrula.

---

## Text-to-Video

```json
{
  "prompt": "Product slowly rotating on a reflective surface, dramatic lighting",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": "8"
}
```

## Image-to-Video

```json
{
  "prompt": "The product comes to life with subtle movements and dynamic lighting",
  "image_urls": ["https://public-url.com/urun.jpg"],
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": "4"
}
```

## Audio Generation ile

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

---

## Parametreler

| Parametre | Tip | Zorunlu | Açıklama |
|-----------|-----|---------|----------|
| `prompt` | string | ✅ | Video açıklaması (max 2000 karakter) |
| `aspect_ratio` | string | ❌ | `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `21:9` |
| `resolution` | string | ❌ | `"480p"` veya `"720p"` (varsayılan: `"720p"`) |
| `duration` | string | ❌ | `"4"`, `"8"`, `"12"` saniye (varsayılan: `"8"`) |
| `generate_audio` | boolean | ❌ | AI ses üretimi (varsayılan: `false`) |
| `fixed_lens` | boolean | ❌ | Kamera sabitlenir, motion blur azalır |
| `image_urls` | array[string] | ❌ | Referans görsel (max 1 görsel) |
| `callback_url` | string | ❌ | Webhook URL (localhost olmaz) |

---

## Durum Sorgulama

```
GET https://seedanceapi.org/v1/status?task_id={task_id}
```

**Durumlar:** `IN_PROGRESS`, `SUCCESS`, `FAILED`

Video URL: `data.response[0]`

---

## Kullanım Senaryoları
- ✅ Sinematik ürün videosu
- ✅ Image-to-video dönüşümü
- ✅ Sesli video üretimi
- ✅ Sabit kameralı çekimler
