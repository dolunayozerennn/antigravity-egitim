# LinkedIn Text Paylaşım

> n8n'den Antigravity'ye taşınan LinkedIn metin + görsel paylaşım otomasyon projesi.
> İki ayrı n8n workflow'u tek bir Python servisinde birleştirildi.

## 🚀 Ne Yapar?

Her hafta iki ayrı LinkedIn postu otomatik olarak üretir ve paylaşır:

| Gün | Saat | İçerik | n8n Kaynağı |
|-----|------|--------|------------|
| **Pazartesi** | 08:00 (TR) | Haftanın 5 AI haberi (max 700 karakter) | `LinkedIn Automation - Onaysız` |
| **Perşembe** | 08:00 (TR) | Herkesin kullanabileceği AI tavsiyesi (max 500 karakter) | `LinkedIn AI Tips - Onaysız` |

## ⚙️ Pipeline (Her İki Workflow İçin Aynı)

```
Schedule Trigger
  → Perplexity API (Güncel AI haberleri/tips araştır)
  → GPT-4.1 (LinkedIn postu yaz — Anti-klişe: Emoji spam ve 'Hey network' kullanımı yasaklı)
  → GPT-4.1-mini (Görsel prompt üret)
  → Kie AI Nano Banana 2 (Görsel üret)
  → LinkedIn Images API (rest/images — initializeUpload + binary upload)
  → LinkedIn Posts API (rest/posts — metin + urn:li:image paylaş)
  → Notion (Log yaz)
```

## 📁 Dosya Yapısı

```
LinkedIn_Text_Paylasim/
├── main.py               → Orkestratör (schedule + iki workflow)
├── config.py              → Fail-fast env doğrulama
├── logger.py              → Standart loglama
├── core/
│   ├── researcher.py      → Perplexity API (AI haberleri araştırması)
│   ├── post_writer.py     → GPT-4.1 (post yazma)
│   ├── image_generator.py → GPT-4.1-mini (prompt) + Kie AI Nano Banana 2 (görsel)
│   ├── linkedin_publisher.py → LinkedIn Images API + Posts API (paylaşım)
│   └── notion_logger.py   → Notion loglama + duplicate kontrol
├── n8n_workflows/         → Orijinal n8n JSON dosyaları (referans)
├── requirements.txt       → Pinned dependencies
├── Procfile               → Railway deploy
└── .gitignore
```

## 🔑 Gerekli Env Variables

| Variable | Açıklama |
|----------|----------|
| `PERPLEXITY_API_KEY` | AI haberleri araştırması |
| `OPENAI_API_KEY` | Post yazma + görsel prompt |
| `KIE_API_KEY` | Kie AI Nano Banana 2 görsel üretimi |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn post paylaşma (OAuth2, 60 gün süreli) |
| `LINKEDIN_PERSON_URN` | LinkedIn profil URN |
| `NOTION_SOCIAL_TOKEN` | Notion log yazma |
| `NOTION_LINKEDIN_DB_ID` | Notion database ID |
| `NOTION_DB_OPS_LOG` | Ops log database ID |
| `TZ=Europe/Istanbul` | Railway timezone |

## 🧑‍💻 Lokal Test

```bash
# Dry-run modda çalışır (gerçek API çağrısı yapmaz)
python main.py

# Production modda (gerçek paylaşım)
ENV=production python main.py
```

## 📋 Migrasyon Durumu
- ✅ n8n workflow'ları analiz edildi
- ✅ Python'a birebir çevrildi
- ✅ Syntax kontrolü geçti
- ✅ Railway'e deploy (27 Mart 2026 — CronJob: `0 5 * * 1,4`)
- ✅ Notion DB `Post Tipi` property eklendi + fail-safe bug fix (1 Nisan 2026)

## 🛡️ Stabilizasyon (2026-04-11)

- **Fix 1:** Görsel üretim Gemini → Kie AI Nano Banana 2'ye migrate edildi
- **Fix 2:** Görsel upload v2/assets (registerUpload) → rest/images (initializeUpload) API'ye geçirildi — URN format uyumsuzluğu düzeltildi
- **Fix 3:** `_create_post()` hata loglaması iyileştirildi — HTTP response body + author/image bilgisi detaylı yazılıyor
- **Fix 4:** `wait_all_loggers()` eklendi — tüm OpsLogger instance queue'ları container exit öncesi flush ediliyor

