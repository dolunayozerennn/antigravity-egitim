# Supplement Telegram Bot (Supplement Buddy)

Telegram üzerinden çalışan 7/24 aktif bir supplement/vitamin analiz botu. Fotoğraf gönderdiğinizde Gemini Vision ile etiketi analiz eder, içerik tablosunu çıkarır ve Notion'a kaydeder. Metin mesajlarını da Gemini Chat ile yanıtlar.

## Ne yapar?

1. **Fotoğraf Analizi**: Supplement/vitamin etiketi fotoğrafını Gemini Vision ile analiz eder
2. **İçerik Çıkarımı**: Ürün adı, marka, tür, içerik tablosu (madde, miktar, birim, BRD%) bilgilerini parse eder
3. **Notion Loglama**: Her analiz sonucunu Notion veritabanına otomatik kaydeder
4. **Chat Modu**: Supplement hakkında soru-cevap (Gemini Chat)
5. **Güvenlik**: ALLOWED_USER_IDS ile yetkili kullanıcı kontrolü

## Pipeline Akışı

```
[Telegram] → Fotoğraf veya metin mesajı al
       ↓
[Yetki Kontrolü] → ALLOWED_USER_IDS ile doğrula
       ↓
  ┌────────────────┬──────────────────┐
  │ 📸 Fotoğraf    │ 💬 Metin         │
  │ Gemini Vision  │ Gemini Chat      │
  │ → JSON parse   │ → Yanıt üret     │
  │ → Notion'a yaz │                  │
  └────────────────┴──────────────────┘
       ↓
[Telegram] → Kullanıcıya formatlanmış yanıt gönder
```

## Bot Komutları

| Komut | Açıklama |
|-------|----------|
| `/start` | Bot hakkında bilgi |
| `/help` | Yardım mesajı |
| `/durum` | Bot durum kontrolü |

## Proje Yapısı

```
Supplement_Telegram_Bot/
├── main.py                          # Bot entry point (polling mode)
├── config.py                        # Fail-fast env validation
├── logger.py                        # Standart logger
├── requirements.txt                 # Pinned dependencies
├── railway.toml                     # Railway deploy config
├── core/
│   └── gemini_analyzer.py           # Gemini Vision + Chat modülü
└── infrastructure/
    └── notion_service.py            # Notion API loglama
```

## Çalıştırma

```bash
# Lokal test (DRY_RUN — Notion'a yazmaz)
python main.py

# Railway: 7/24 always-on worker (polling mode)
```

## Gerekli Env Variables

| Değişken | Açıklama |
|----------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API tokeni (zorunlu) |
| `GEMINI_API_KEY` | Google Gemini API anahtarı (zorunlu) |
| `GEMINI_MODEL` | Gemini model adı (varsayılan: `gemini-2.5-flash`) |
| `NOTION_TOKEN` | Notion API tokeni (zorunlu) |
| `NOTION_DB_ID` | Notion veritabanı ID (zorunlu) |
| `ALLOWED_USER_IDS` | Virgülle ayrılmış Telegram kullanıcı ID'leri (opsiyonel) |
| `ENV` | `production` veya `development` (DRY_RUN kontrolü) |

## Deploy Bilgileri

- **Platform:** Railway (Always-On Worker)
- **Mode:** 7/24 Telegram Polling
- **GitHub:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Supplement_Telegram_Bot/`)
- **Start:** `python main.py`
- **Paylaşım Taslağı:** `Paylasilan_Projeler/Supplement_Telegram_Bot_Taslak/`
