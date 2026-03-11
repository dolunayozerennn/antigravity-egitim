---
description: İçerik otomasyon sistemi — ürün reklam videosu üretme pipeline'ı
---

# Ürün Reklam Videosu Üretim Pipeline'ı

Bu workflow, müşteriden gelen ürün bilgisiyle 3 adımda reklam videosu üretir.

## Pipeline Akışı

### Adım 1 — Görsel Üretimi
1. Kullanıcı Telegram'dan ürün bilgisini gönderir (metin + opsiyonel fotoğraf)
2. Bot, ürün bilgisinden İngilizce prompt üretir
3. **NanoBanana Pro** ile başlangıç görseli üretilir
4. Görsel kullanıcıya gösterilir

### Adım 2 — Düzenleme (Opsiyonel)
- **Küçük değişiklik** (renk, arka plan vb.) → **Qwen Image Edit** ile düzenleme
- **Büyük değişiklik** → **NanoBanana Pro** ile yeniden üretim
- Kullanıcı memnun olana kadar tekrar edilebilir

### Adım 3 — Video Üretimi
1. Kullanıcı görseli onaylar
2. Video süresi seçilir (10s / 15s / 25s)
3. Video formatı seçilir (yatay 16:9 / dikey 9:16)
4. **Sora 2 Pro Storyboard** ile video üretilir
5. Video URL'si kullanıcıya gönderilir

## Modeller

| Model | Script | Kullanım |
|-------|--------|----------|
| NanoBanana Pro | `scripts/nanobananapro_image.sh` | Ürün görseli üretimi |
| Qwen Image Edit | `scripts/qwen_edit.sh` | Görsel düzenleme |
| Sora 2 Pro Storyboard | `scripts/sora_storyboard.sh` | Video üretimi |

## Bot Kullanımı

// turbo
```bash
python3 scripts/telegram_bot.py
```

## API Dokümantasyonları

- `api-docs/kie-ai-genel.md` — Ortak yapı
- `api-docs/sora-2-pro-storyboard.md`
- `api-docs/nanobananapro.md`
- `api-docs/qwen-image-edit.md`
