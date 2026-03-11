# NanoBanana Pro — API Dokümantasyonu

## Genel Bilgi
- **Kullanım:** Instagram postları, posterler, carousel postlar, genel görsel üretimi
- **Kalite:** 4K yüksek çözünürlük
- **Altyapı:** Gemini 3.0 Pro Image tabanlı
- **Özellikler:** Tipografi desteği, çoklu nesne tutarlılığı, esnek en/boy oranı

## Endpoint
```
POST https://api.kie.ai/api/v1/jobs/createTask
```

## Model Adı
```
nano-banana-pro
```

## İstek Gövdesi — Metin'den Görsel

```json
{
  "model": "nano-banana-pro",
  "input": {
    "prompt": "Modern minimalist Instagram postu, yaz indirimi kampanyası, %50 indirim yazısı, pastel renkler, profesyonel tipografi",
    "aspect_ratio": "4:5"
  },
  "callBackUrl": "https://webhook.site/callback"
}
```

## İstek Gövdesi — Görsel'den Görsel (Referansla)

```json
{
  "model": "nano-banana-pro",
  "input": {
    "prompt": "Bu ürünü modern bir Instagram postu olarak yeniden tasarla, şık arka plan, profesyonel ışıklandırma",
    "image_input": [
      "https://ornek.com/urun.jpg"
    ],
    "aspect_ratio": "1:1"
  }
}
```

## Parametreler

| Parametre | Tip | Zorunlu | Açıklama |
|-----------|-----|---------|----------|
| `prompt` | string | ✅ | Detaylı görsel açıklaması (İngilizce önerilir) |
| `aspect_ratio` | string | ❌ | En/boy oranı (varsayılan: `1:1`) |
| `image_input` | array of strings | ❌ | Referans/kaynak görsel URL'si listesi |

## Desteklenen Aspect Ratio'lar

| Oran | Kullanım Alanı |
|------|----------------|
| `1:1` | Instagram kare post |
| `4:5` | Instagram dikey post (önerilen) |
| `9:16` | Instagram story / Reels |
| `16:9` | YouTube thumbnail, yatay banner |
| `21:9` | Sinematik geniş ekran |

## Carousel Post Stratejisi

Carousel postlar için **aynı prompt temasını** koruyarak sıralı görseller üretin:

1. Her slide için ayrı bir `createTask` çağrısı yapın
2. System prompt'ta tutarlılık talimatı verin:
   - Aynı renk paleti
   - Aynı tipografi stili
   - İçerik adım adım ilerlemeli (1/5, 2/5, ...)
   - Her görselde marka tutarlılığı

## Kullanım Senaryoları
- Instagram tekli post
- Poster / afiş tasarımı
- Carousel (kaydırmalı) postlar
- Ürün görselleri
- Sosyal medya banner'ları
