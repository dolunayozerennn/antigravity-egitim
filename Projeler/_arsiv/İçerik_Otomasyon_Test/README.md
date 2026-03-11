# 🎬 Ürün Reklam Videosu Otomasyon Sistemi

Müşteriden gelen ürün bilgisini alıp, 3 adımlı pipeline ile profesyonel reklam videosu üreten Telegram botu.

## 📋 Pipeline

```
1. Görsel Üretimi (NanoBanana Pro)
   → Ürün açıklamasından 4K başlangıç görseli üret

2. Düzenleme (Qwen Image Edit / NanoBanana Pro)
   → Küçük değişiklik: Qwen ile edit
   → Büyük değişiklik: NanoBanana ile yeniden üret

3. Video Üretimi (Sora 2 Pro Storyboard)
   → Onaylanan görseli referans alarak reklam videosu üret (10-25s)
```

## 📁 Klasör Yapısı

```
├── api-docs/                  # API dokümantasyonları
│   ├── kie-ai-genel.md        # Kie AI ortak yapı
│   ├── sora-2-pro-storyboard.md
│   ├── nanobananapro.md
│   └── qwen-image-edit.md
├── scripts/                   # Bot ve yardımcı scriptler
│   ├── telegram_bot.py        # Ana Telegram botu
│   ├── kie_poll.sh            # Ortak helper (task polling)
│   ├── nanobananapro_image.sh # Tekli görsel üretimi
│   ├── sora_storyboard.sh     # Video üretimi
│   └── qwen_edit.sh           # Görsel düzenleme
├── prompt-rehberleri/          # Prompt yazma kılavuzları
│   ├── sora-2-storyboard.md
│   ├── nanobananapro.md
│   └── qwen-image-edit.md
└── .agent/workflows/
    └── icerik-uretimi.md
```

## 🚀 Bot'u Başlatma

```bash
cd "/Users/dolunayozeren/Desktop/Antigravity/İçerik Otomasyon Test"
python3 scripts/telegram_bot.py
```

## 📋 Desteklenen Modeller

| Model | Kullanım | Çıktı |
|-------|----------|-------|
| NanoBanana Pro | Ürün görseli üretimi | 4K görsel |
| Qwen Image Edit | Görsel düzenleme | Revize görsel |
| Sora 2 Pro Storyboard | Reklam videosu | 10-25s video |

## ⚙️ Gereksinimler
- Python 3.10+
- `pip install python-telegram-bot httpx`
- `curl` + `jq` (shell scriptler için)