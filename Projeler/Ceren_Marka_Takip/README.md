# Ceren Marka Takip — Brand Collaboration Reminder Bot

Dolunay'ın influencer marka işbirliklerini yöneten Ceren için otomatik e-posta hatırlatma sistemi.

## Ne Yapar?

1. 📨 3 Gmail hesabını tarar (ceren@dolunay.ai, dolunay.ai.contact, ozerendolunay)
2. ⏰ 48+ iş saati yanıtsız kalan thread'leri tespit eder
3. 🤖 Groq LLM ile marka işbirliği olup olmadığını analiz eder
4. 📩 Ceren'e aksiyon gerektiren thread'ler için hatırlatma maili gönderir
5. 🔔 Hata durumunda Dolunay'a alert gönderir

## Teknik Altyapı

- **Runtime:** Python 3.11, Railway CronJob
- **Gmail:** OAuth2 (3 hesap)
- **LLM:** Groq / openai/gpt-oss-120b
- **State:** Notion Ops Log (Railway ephemeral disk uyumlu)
- **Schedule:** Günde 1 kez, 07:00 UTC (10:00 İstanbul)

## Kurulum

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Değerleri doldur
python main.py --dry-run  # Test modu
```

## Deploy

Railway mono-repo yapısında deploy edilir:
- **Repo:** `dolunayozerennn/antigravity-egitim`
- **Root Dir:** `/Projeler/Ceren_Marka_Takip`
- **Cron:** `0 7 * * *`
