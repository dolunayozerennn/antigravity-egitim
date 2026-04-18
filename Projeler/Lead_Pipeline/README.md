# Lead Pipeline

Tele Satış CRM + Lead Notifier Bot'un birleşik cron job versiyonu.

## Ne yapar?

1. **CRM Pipeline**: Google Sheets'ten yeni lead'leri okur → Temizler → Notion CRM'e yazar
2. **Notifier Pipeline**: Yeni lead'ler için Telegram + E-posta bildirimi gönderir

## Neden birleştirildi?

- **Eski**: 2 ayrı always-on servis → ~$4.40/ay Railway maliyeti
- **Yeni**: 1 cron job (5 dk'da bir) → ~$1.00/ay Railway maliyeti
- **Tasarruf**: ~$3.40/ay

## Çalıştırma

```bash
# Lokal test
python main.py

# Railway cron: */5 * * * * (5 dakikada bir)
```

## Gerekli Env Variables

| Değişken | Açıklama |
|----------|----------|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Google Sheets erişimi (Service Account) |
| `NOTION_API_TOKEN` | Notion API erişimi |
| `TELEGRAM_BOT_TOKEN` | Telegram bot tokeni |
| `TELEGRAM_CHAT_ID` | Telegram bildirim kanal ID'si |
| `GOOGLE_OUTREACH_TOKEN_JSON` | Gmail API OAuth token (e-posta bildirimi) |
| `NOTIFY_EMAIL` | Bildirim alacak e-posta adresi |
| `CRM_SPREADSHEET_ID` | CRM Google Sheets ID |
| `NOTIFIER_SPREADSHEET_ID` | Notifier Google Sheets ID |

## 🛡️ Stabilizasyon ve Hata Giderme (18 Nisan 2026)
- **Fix 1:** `.gitignore` eksikleri (token.json, credentials.json, \*.pyc) tamamlandı.
- **Fix 2:** Ortak olarak dinlenen sekme (`0426-Yeni`) yüzünden yaşanacak olası `_Meta` conflict'lerini önlemek amacıyla state key'ler `crm:` ve `notifier:` prefixleri ile namespace'lendi.
- **Fix 3:** `_Meta` durumu kaydedilirken tüm mevcut kayıtları ezme engellendi, sadece bu instance'a ait alanlar merge edildi.
- **Doğrulama:** Dependency audit, syntax kontrolü ve Railway deployment logs (SUCCESS) doğrulandı. Hiçbir anti-pattern tespit edilmedi.
