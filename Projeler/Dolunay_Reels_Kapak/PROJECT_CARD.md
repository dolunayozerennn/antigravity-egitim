# 📋 Project Card
> Bu dosya Antigravity'nin projeyi hızla anlaması için hazırlanmıştır.

| Alan | Değer |
|------|-------|
| **Platform** | railway-cron |
| **Start Command 1** | `python worker.py` (Kapak üretimi) |
| **Start Command 2** | `python revision_cron_worker.py` (Revizyon kontrolü) |
| **Cron 1** | `0 6,12,18 * * *` |
| **Cron 2** | `0 7,10,13,16,19 * * *` |
| **Root Directory** | `Projeler/Dolunay_Reels_Kapak` |
| **GitHub Repo** | `dolunayozerennn/antigravity-egitim` (mono-repo) |

## Env Variables
| Variable | Kaynak | Açıklama |
|----------|--------|----------|
| `NOTION_SOCIAL_TOKEN` | master.env | İşbirlikleri Notion workspace |
| `KIE_API_KEY` | master.env | Kie AI pipeline (Reels kapak) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | master.env | Google Drive upload yetkisi |
| `OPENAI_API_KEY` | master.env | Revizyon değerlendirmesi için |

## Dosya Yapısı (kısa)
- `worker.py` → Yeni kapak üretimi tetikleyici (Cron)
- `revision_cron_worker.py` → YouTube/Reels DB'den feedback kontrol eden cron
- `autonomous_cover_agent.py` → Kie Workflow tetikleme ana motoru
- `revision_engine.py` → Verilen feedback'leri algılayıp yeni prompt üretir
- `notion_service.py` → Notion'dan meta dataları çeker
- `composition_engine.py` → Multi-theme kapak varyasyonlarını yönetir.

## Bilinen Platform Kısıtlamaları
- generate_image ARACI KULLANILMAZ. Üretim Kie AI pipeline'ı üzerinden yapılır.
- Tüm Drive ve Notion JSON tokenları env var üstünden çekilir.

## Son Doğrulama
- **Tarih:** 2026-03-23
- **Durum:** ✅ Çalışıyor
