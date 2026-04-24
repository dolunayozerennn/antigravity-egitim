# Ceren Marka Takip — Brand Collaboration Reminder Bot

Ceren'in marka işbirliği e-postalarını takip eden otomatik hatırlatma sistemi.

## Ne Yapar?

1. 📨 Ceren'in Gmail hesabını tarar (ceren@dolunay.ai)
2. ⏰ 48+ iş saati yanıtsız kalan thread'leri tespit eder
3. 🤖 Groq LLM ile marka işbirliği olup olmadığını analiz eder
4. 📩 Ceren'e aksiyon gerektiren thread'ler için hatırlatma maili gönderir
5. 🔔 Hata durumunda Ceren'e alert gönderir
6. 📊 Her Pazartesi haftalık özet rapor gönderir

## Teknik Altyapı

- **Runtime:** Python 3.11, Railway CronJob
- **Gmail:** OAuth2 (ceren@dolunay.ai)
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

## Klasör Yapısı

```
├── main.py              # Giriş noktası (CronJob entry)
├── core/
│   ├── gmail_scanner.py # Ceren inbox tarama
│   ├── thread_analyzer.py # LLM analiz
│   ├── stale_detector.py  # 48h iş saati filtreleme
│   └── notifier.py        # E-posta gönderimi (Gmail OAuth)
├── services/
│   ├── gmail_service.py   # Gmail API auth
│   └── groq_client.py     # Groq LLM client
├── utils/
│   ├── state_manager.py   # Notion-backed cooldown/dedup
│   └── business_hours.py  # İş saati hesaplama
├── nixpacks.toml          # Railway deploy config
└── requirements.txt
```

## Deploy

Railway mono-repo yapısında deploy edilir:
- **Repo:** `dolunayozerennn/antigravity-egitim`
- **Root Dir:** `/Projeler/Ceren_Marka_Takip`
- **Cron:** `0 7 * * *`
