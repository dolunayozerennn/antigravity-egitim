# Ceren İzlenme Notifier

Sosyal medya performans raporu botu. Haftada 2 kez (Salı/Perşembe) çalışarak Instagram, TikTok ve YouTube'daki videoları Apify ile tarar, belirlenen izlenme barajlarını aşan içerikleri tespit eder ve Ceren'e e-posta ile rapor gönderir.

## Ne yapar?

1. **Veri Toplama**: Apify actor'ları ile 3 platformdan son 7 günün video verilerini çeker
2. **Filtreleme**: Platform bazlı izlenme barajlarını aşan videoları filtreler
3. **AI Özet**: Groq (Llama 3.3 70B) ile motive edici Türkçe özet üretir
4. **Raporlama**: HTML formatında profesyonel performans raporu e-postası gönderir
5. **Hata Bildirimi**: Apify hataları için ayrı teknik hata raporu gönderir

## Pipeline Akışı

```
[Apify Actors] → Instagram + TikTok + YouTube verileri çek
       ↓
[Filtreleme] → Barajı aşan videoları belirle
       ↓
[Groq LLM] → AI destekli performans özeti üret
       ↓
[Gmail API] → HTML rapor → ceren@dolunay.ai
              Teknik hatalar → ozerendolunay@gmail.com
```

## İzlenme Barajları

| Platform | Baraj |
|----------|-------|
| Instagram Reels | ≥ 200.000 |
| TikTok | ≥ 100.000 |
| YouTube Shorts | ≥ 100.000 |
| YouTube Long-Form | ≥ 10.000 |

## Proje Yapısı

```
Ceren_izlenme_notifier/
├── main.py                      # Entry point
├── config.py                    # Fail-fast env validation
├── logger.py                    # Standart logger
├── requirements.txt             # Pinned dependencies
├── core/
│   ├── apify_client.py          # 3 platform veri çekimi (Apify)
│   └── llm_helper.py            # Groq AI özet üretimi
└── infrastructure/
    └── email_sender.py          # Gmail API ile HTML e-posta gönderimi
```

## Çalıştırma

```bash
# Lokal test (DRY_RUN — e-posta göndermez)
python main.py

# Railway cron: 0 8 * * 2,4 (Salı/Perşembe, UTC 08:00 = TR 11:00)
```

## Gerekli Env Variables

| Değişken | Açıklama |
|----------|----------|
| `APIFY_API_KEY_1` ... `APIFY_API_KEY_N` | Apify API anahtarları (en az 1 zorunlu, rotasyonlu) |
| `GROQ_API_KEY` | Groq API anahtarı (AI özet için, opsiyonel) |
| `GMAIL_OAUTH_JSON` | Gmail OAuth token JSON (Railway'de env olarak) |
| `ENV` | `production` veya `development` (DRY_RUN kontrolü) |

## Deploy Bilgileri

- **Platform:** Railway Cron Job
- **Cron:** `0 8 * * 2,4` (Salı + Perşembe, TR 11:00)
- **GitHub:** `dolunayozerennn/antigravity-egitim` (monorepo, Root Dir: `Projeler/Ceren_izlenme_notifier`)
- **Start:** `python main.py`

## 📊 Gelişmiş Loglama (OpsLogger)
Tüm operasyonel loglar (Apify Limit aşımları, başarılı çekimler, hatalar) eşzamanlı olarak Notion Operations Database'e yazılır.
- **SUCCESS/INFO**: Baraj aşan videolar ve mailler
- **WARNING**: Limit aşıldığında diğer API key'e geçiş
- **ERROR**: Apify'ın tamamen çökmesi veya mail gönderim hataları

## 🛡️ Stabilizasyon ve Hata Giderme (2026-04-20)
- **Fix 1 (Network Resilience):** `apify_client.py` içerisindeki `iterate_items` çağrılarına `tenacity` paketini kullanarak otomatik HTTP stream retry'ı eklendi. Bağlantı anlık kopsa dahi dataset API'den tekrar baştan çekilerek güvenli duruma getirildi.
- **Fix 2 (LLM Timeout):** `llm_helper.py` Groq API çağrısına 3 tekrarlı backoff/retry eklendi.
- **Fix 3 (Mail Resilience):** `email_sender.py` içerisindeki `google-api-python-client` mesaj yollama adımına `num_retries=3` eklendi, ephemeral error ve connection reset hataları çözüldü.
