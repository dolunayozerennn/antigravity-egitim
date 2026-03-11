# ai-model-api.md — Yapay Zeka Model API Dokümantasyonu

## Kullanım

Bu dosya, sistemin kullandığı 3 farklı AI görevinin API yapılandırmasını tanımlar.
Sistem model-agnostiktir — aşağıdaki sağlayıcılardan herhangi birini seçebilirsiniz.

> 🟡 **[Köşeli parantez]** → Seçiminize göre doldurun veya uygun seçeneği bırakın.
>
> 🔵 **{Süslü parantez}** → Sistem tarafından otomatik doldurulan değerler.

---

## Desteklenen Sağlayıcılar

| Sağlayıcı | Ana Model (Metin) | Görsel Analiz | Ses Transkript |
|------------|-------------------|---------------|----------------|
| OpenAI | gpt-4.1 | gpt-4.1 (vision) | whisper-1 |
| Anthropic | claude-sonnet-4-20250514 | claude-sonnet-4-20250514 (vision) | Desteklemiyor* |
| Google | gemini-2.5-flash | gemini-2.5-flash (vision) | Desteklemiyor* |

> *Anthropic ve Google ses transkript desteklemiyor. Bu durumda ses transkripti için ek olarak OpenAI Whisper veya Google Speech-to-Text kullanılmalıdır.

---

## Görev 1: Ana AI Agent — Yanıt Üretimi

Müşteri mesajını alıp bilgi tabanına dayalı yanıt üreten ana görev.

### Yapılandırma

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| Sıcaklık (temperature) | 0.4 | Düşük = daha tutarlı yanıtlar |
| Maksimum token | 400 | Yanıt uzunluğu sınırı |
| Çıktı formatı | JSON | `{metin, link_url}` yapısında |

### OpenAI Örneği

**Endpoint:**
```
POST https://api.openai.com/v1/chat/completions
```

**Header'lar:**
```
Authorization: Bearer {AI_MODEL_API_KEY}
Content-Type: application/json
```

**Body:**
```json
{
  "model": "gpt-4.1",
  "temperature": 0.4,
  "max_tokens": 400,
  "response_format": { "type": "json_object" },
  "messages": [
    {
      "role": "system",
      "content": "{sistem-promptu.md içeriği + bilgi-tabani.md içeriği}"
    },
    {
      "role": "user",
      "content": "{kullanıcı mesajı}"
    }
  ]
}
```

### Anthropic Örneği

**Endpoint:**
```
POST https://api.anthropic.com/v1/messages
```

**Header'lar:**
```
x-api-key: {AI_MODEL_API_KEY}
anthropic-version: 2023-06-01
Content-Type: application/json
```

**Body:**
```json
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 400,
  "temperature": 0.4,
  "system": "{sistem-promptu.md içeriği + bilgi-tabani.md içeriği}",
  "messages": [
    {
      "role": "user",
      "content": "{kullanıcı mesajı}"
    }
  ]
}
```

### Google Gemini Örneği

**Endpoint:**
```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={AI_MODEL_API_KEY}
```

**Header'lar:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "system_instruction": {
    "parts": [{ "text": "{sistem-promptu.md içeriği + bilgi-tabani.md içeriği}" }]
  },
  "contents": [
    {
      "role": "user",
      "parts": [{ "text": "{kullanıcı mesajı}" }]
    }
  ],
  "generationConfig": {
    "temperature": 0.4,
    "maxOutputTokens": 400,
    "responseMimeType": "application/json"
  }
}
```

---

## Görev 2: Görsel Analiz (Vision)

Müşterinin gönderdiği görseli analiz edip içeriğini metne çevirir.

### Yapılandırma

| Parametre | Değer |
|-----------|-------|
| Prompt | "Görselde ne olduğunu açıkla" |
| Giriş | Base64 encoded görsel veya görsel URL |

### OpenAI Örneği

**Endpoint:** Aynı (`/v1/chat/completions`)

**Body:**
```json
{
  "model": "gpt-4.1",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Görselde ne olduğunu açıkla"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,{base64_encoded_gorsel}",
            "detail": "auto"
          }
        }
      ]
    }
  ]
}
```

### Anthropic Örneği

**Endpoint:** Aynı (`/v1/messages`)

**Body:**
```json
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 300,
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image",
          "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": "{base64_encoded_gorsel}"
          }
        },
        {
          "type": "text",
          "text": "Görselde ne olduğunu açıkla"
        }
      ]
    }
  ]
}
```

### Google Gemini Örneği

**Body:**
```json
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "inline_data": {
            "mime_type": "image/jpeg",
            "data": "{base64_encoded_gorsel}"
          }
        },
        {
          "text": "Görselde ne olduğunu açıkla"
        }
      ]
    }
  ]
}
```

---

## Görev 3: Ses Transkript (Speech-to-Text)

Müşterinin gönderdiği sesli mesajı metne çevirir.

### OpenAI Whisper (Önerilen)

Ses transkripti için en yaygın ve kolay çözüm. Hangi ana modeli seçerseniz seçin, ses transkripti için OpenAI Whisper kullanabilirsiniz.

**Endpoint:**
```
POST https://api.openai.com/v1/audio/transcriptions
```

**Header'lar:**
```
Authorization: Bearer {OPENAI_API_KEY}
```

**Body (multipart/form-data):**
```
file: {ses dosyası (mp3, m4a, wav, ogg vs.)}
model: whisper-1
language: tr
```

**Başarılı yanıt:**
```json
{
  "text": "Merhaba, bu ürün hakkında bilgi almak istiyorum..."
}
```

> Not: Whisper API multipart/form-data bekler, JSON değil. Maksimum dosya boyutu 25 MB.

### Alternatif: Google Speech-to-Text

Anthropic veya Google ana model kullananlar için alternatif ses transkript çözümü.

**Endpoint:**
```
POST https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}
```

**Body:**
```json
{
  "config": {
    "encoding": "OGG_OPUS",
    "sampleRateHertz": 48000,
    "languageCode": "tr-TR"
  },
  "audio": {
    "content": "{base64_encoded_ses}"
  }
}
```

---

## Konuşma Hafızası

AI Agent her kullanıcıyla olan son 10 mesajı hafızada tutar. Bu, API çağrısında `messages` dizisine önceki mesajların eklenmesiyle sağlanır.

**Örnek (OpenAI formatı):**
```json
{
  "messages": [
    { "role": "system", "content": "{sistem promptu + bilgi tabanı}" },
    { "role": "user", "content": "Saç kesim fiyatı ne kadar?" },
    { "role": "assistant", "content": "{\"metin\": \"Klasik erkek saç kesimi 350 ₺...\", \"link_url\": \"\"}" },
    { "role": "user", "content": "Randevu alabilir miyim?" },
    { "role": "assistant", "content": "{\"metin\": \"Tabii! Hangi şubemize...\", \"link_url\": \"\"}" },
    { "role": "user", "content": "{yeni mesaj}" }
  ]
}
```

> Hafıza subscriber_id bazlı tutulur. Her kullanıcının kendi konuşma geçmişi vardır. Son 10 mesaj çifti (user + assistant) saklanır, eski mesajlar otomatik silinir.

---

## Hata Yönetimi

Tüm sağlayıcılar için ortak hata kodları:

| HTTP Kodu | Anlam | Çözüm |
|-----------|-------|-------|
| 200 | Başarılı | — |
| 400 | Geçersiz istek | Body formatını kontrol et |
| 401 | API key hatalı | credentials.env dosyasını kontrol et |
| 429 | Rate limit / kota aşıldı | Birkaç saniye bekle, tekrar dene |
| 500 | Sunucu hatası | Birkaç dakika bekle, tekrar dene |

Her API çağrısında retry mekanizması kullanılmalıdır. Maksimum 2 tekrar denemesi yeterlidir.