# Qwen Image Edit — API Dokümantasyonu

## Genel Bilgi
- **Kullanım:** Mevcut görselleri düzenleme, revize etme
- **Özellikler:** Semantik ve görünüm düzenleme, çok dilli metin, nesne ekleme/çıkarma
- **Modlar:** Semantik mod (anlam bazlı) ve Görünüm modu (stil bazlı)

## Endpoint
```
POST https://api.kie.ai/api/v1/jobs/createTask
```

## Model Adı
```
qwen/image-edit
```

## İstek Gövdesi

```json
{
  "model": "qwen/image-edit",
  "input": {
    "prompt": "Change the background to a tropical beach with palm trees",
    "image_url": "https://ornek.com/orijinal-gorsel.jpg",
    "strength": 0.7,
    "output_format": "png"
  },
  "callBackUrl": "https://webhook.site/callback"
}
```

## Parametreler

| Parametre | Tip | Zorunlu | Açıklama |
|-----------|-----|---------|----------|
| `prompt` | string | ✅ | Düzenleme talimatı (**sadece İngilizce**) |
| `image_url` | string | ✅ | Düzenlenecek görselin URL'si |
| `strength` | float | ❌ | Düzenleme gücü: 0.0 (az değişiklik) - 1.0 (tam yeniden oluşturma) |
| `output_format` | string | ❌ | Çıktı formatı: `png`, `jpeg`, `webp` |
| `negative_prompt` | string | ❌ | İstenmeyen öğeler |
| `seed` | integer | ❌ | Tutarlılık için rastgele tohum |
| `acceleration` | string | ❌ | Hızlandırma: `none`, `regular`, `high` |
| `num_inference_steps` | number | ❌ | İnferans adım sayısı |
| `guidance_scale` | number | ❌ | Prompt'a bağlılık seviyesi |
| `enable_safety_checker` | boolean | ❌ | Güvenlik filtresi açık/kapalı |

## Strength Rehberi

| Değer | Kullanım |
|-------|----------|
| 0.1-0.3 | Küçük renk/ton değişiklikleri |
| 0.4-0.6 | Orta düzey düzenlemeler (arka plan değişikliği) |
| 0.7-0.8 | Büyük değişiklikler (nesne ekleme/çıkarma) |
| 0.9-1.0 | Neredeyse tamamen yeniden üretim |

## ⚠️ Önemli Notlar
- Prompt'lar **sadece İngilizce** desteklenir
- Görseli Türkçe tarif ettirmek için önce Groq ile İngilizce'ye çevirin
- Düzenleme gücünü (strength) dikkatli ayarlayın — çok yüksek değer orijinal görseli kaybettirir

## Kullanım Senaryoları
- Müşterinin beğenmediği görseli revize etme
- Arka plan değiştirme
- Metin ekleme/düzenleme
- Nesne ekleme veya çıkarma
- Renk/ton ayarlama
