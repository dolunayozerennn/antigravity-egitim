# Supplement Buddy — Telegram Bot

Fotoğraf gönder → Gemini Vision ile analiz → Notion'a logla → 7/24 aktif.

## Özellikler

- 📸 **Görsel Analiz:** Supplement/vitamin etiket fotoğraflarını Gemini 2.5 Flash ile analiz eder
- 📋 **Notion Loglama:** Tüm analiz sonuçlarını otomatik olarak Notion database'e yazar
- 💬 **AI Sohbet:** Gemini ile sohbet — supplement soruları ve genel konuşma
- 🔒 **Yetkilendirme:** Opsiyonel kullanıcı ID kısıtlaması

## Ortam Değişkenleri

| Değişken | Açıklama |
|----------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `GEMINI_API_KEY` | Google Gemini API key |
| `NOTION_TOKEN` | Notion integration token |
| `NOTION_DB_ID` | Hedef Notion database ID |
| `GEMINI_MODEL` | Model (varsayılan: gemini-2.5-flash) |
| `ENV` | production / development |
| `ALLOWED_USER_IDS` | Virgülle ayrılmış Telegram user ID'leri (opsiyonel) |

## Kurulum

```bash
pip install -r requirements.txt
python main.py
```
