# 🧪 Bot Test — Telegram Bot Otomatik Test Skill'i

> **Tetikleyici:** `/bot-test` slash komutu veya deploy sonrası otomatik
> **Amaç:** Tüm Telegram botların sağlığını kontrol et, conversation flow testlerini çalıştır, API bağlantılarını doğrula ve sonuçları raporla.

---

## Kapsam

Bu skill **4 Telegram bot'u** test eder:

| Bot | Proje | Tür | Railway | Token Env |
|-----|-------|-----|---------|-----------|
| @YouTube_Otomasyon_Doluay_Bot | `Projeler/YouTube_Otomasyonu` | Worker (7/24 polling) | `87e24335` | `TELEGRAM_YOUTUBE_BOT_TOKEN` |
| eCom Reklam Botu | `Projeler/eCom_Reklam_Otomasyonu` | Worker (7/24 polling) | `8797307d` | `TELEGRAM_ECOM_BOT_TOKEN` |
| Shorts Demo Botu | `Projeler/Shorts_Demo_Otomasyonu` | Worker (7/24 polling) | `01bf8d6e` | `TELEGRAM_SHORTS_BOT_TOKEN` |
| Supplement Analyzer | `Projeler/Supplement_Telegram_Bot` | Worker (7/24 polling) | `35acfbc5` | `TELEGRAM_SUPPLEMENT_BOT_TOKEN` |

---

## Test Modları

| Mod | Süre | Kredi | Katmanlar |
|-----|------|-------|-----------|
| **Quick** (varsayılan) | ~15s | Yok | Health Check + Railway |
| **Full** | ~60s | ~$0.02 | Quick + Conversation Tests |
| **Derin** | ~3dk | ~$0.15 | Full + Stres Test + Servis + Pipeline |

---

## Test Katmanları

### Katman 1: Health Check (Hızlı — ~10 saniye) ⚡

Bot'ların **canlı** olup olmadığını kontrol eder. 4 bot birden test edilir.

**Script:** `_skills/bot-test/health_check.py`

```bash
cd ~/Desktop/Antigravity && python3 _skills/bot-test/health_check.py
```

**Ne kontrol eder:**
- Telegram Bot API `getMe` → bot token geçerli mi? (4 bot)
- Railway deployment status → son deploy başarılı mı? (4 servis)
- Railway son loglar → FATAL hata var mı?
- Her kontrol için süre ölçümü

**Çıktı formatı:**
```
🧪 BOT HEALTH CHECK — 2026-04-12 15:30:00
⏱️  Toplam süre: 8.3 saniye

📺 YouTube Otomasyonu — Deploy: 2026-04-12
  ✅ Telegram: Bot aktif: @YouTube_Otomasyon_Doluay_Bot (ID: 12345)
  ✅ Railway:  Deploy OK: SUCCESS (2026-04-12T14:28)
  ⏱️  Kontrol süresi: (2.1s)

🛒 eCom Reklam Otomasyonu — Deploy: 2026-04-12
  ✅ Telegram: Bot aktif (ID: 67890)
  ✅ Railway:  Deploy OK: SUCCESS
  ⏱️  Kontrol süresi: (1.8s)

🎬 Shorts Demo Botu — Deploy: 2026-03-17
  ✅ Telegram: Bot aktif
  ✅ Railway:  Deploy OK: SUCCESS
  ⏱️  Kontrol süresi: (1.9s)

💊 Supplement Analyzer — Deploy: 2026-03-31
  ✅ Telegram: Bot aktif
  ✅ Railway:  Deploy OK: SUCCESS
  ⏱️  Kontrol süresi: (2.5s)

📊 Kontrol: 8/8 geçti
✅ TÜM BOTLAR SAĞLIKLI
```

---

### Katman 2A: YouTube Conversation Test (Orta — ~15 saniye)

Bot'un **sohbet mantığını** doğrudan çağırarak test eder.

```bash
cd ~/Desktop/Antigravity/Projeler/YouTube_Otomasyonu && python3 test_conversation.py
```

**5 senaryo:**
1. Basit tek klip talebi (tam akış)
2. Çoklu klip + Veo modeli
3. Normal sohbet (video talebi yok)
4. Belirsiz talep (bot soru sormalı)
5. Config doğrulama (orientation + model)

---

### Katman 2B: eCom Conversation Test (Orta — ~30 saniye)

```bash
# Import kontrolü (API kredi harcamaz)
cd ~/Desktop/Antigravity/Projeler/eCom_Reklam_Otomasyonu && python3 test_bot.py --test imports

# Conversation test (GPT çağrısı yapar — ~$0.01)
cd ~/Desktop/Antigravity/Projeler/eCom_Reklam_Otomasyonu && python3 test_bot.py --test conversation
```

**Ne kontrol eder:**
- 12 modül import testi
- Config değerleri doğrulama
- ConversationManager state machine geçişleri
- LLM bilgi çıkarma (GPT yanıt kalitesi)
- Edge case'ler (boş mesaj, emoji, uzun metin, tekrar /start)

---

### Katman 2.5: YouTube Stres Test (Opsiyonel — ~60 saniye) 🔥

**Script:** `Projeler/YouTube_Otomasyonu/test_stress.py`

```bash
cd ~/Desktop/Antigravity/Projeler/YouTube_Otomasyonu && python3 test_stress.py
```

**10 kategori, 60+ test case:**
1. Saçma girişler (emoji, keyboard smash, boş mesaj)
2. Prompt injection / XSS denemeleri
3. Kararsız kullanıcı (fikir değiştirme, iptal)
4. Rapid fire (eşzamanlı mesaj bombardımanı)
5. Tehlikeli / uygunsuz içerik talepleri
6. Aşırı uzun mesajlar
7. Farklı diller (Arapça, Çince, Rusça)
8. Bot'u kandırmaya çalışma
9. State tutarlılığı (çoklu kullanıcı, session karışmaması)
10. Gerçekçi kaos senaryoları

**Başarı kriteri:** %90+ geçme oranı

---

### Katman 3: Servis + Pipeline DRY-RUN (Derin — ~120 saniye) 💰

API bağlantılarını ve pipeline'ı DRY-RUN modda test eder. **API kredi harcar!**

```bash
cd ~/Desktop/Antigravity/Projeler/eCom_Reklam_Otomasyonu && python3 test_bot.py --test all
```

**Ne kontrol eder:**
- OpenAI API bağlantısı (chat + JSON)
- Perplexity API bağlantısı
- Kie AI kredi bakiyesi
- ElevenLabs ses listesi
- Pipeline DRY-RUN (mock senaryo ile tam akış)
- Maliyet hesaplaması doğruluğu
- Notion page ID çıkarma

---

## Kullanım Talimatı (AI Agent İçin)

### `/bot-test` çağrıldığında (Quick mod — varsayılan):

1. **Env yükle** — persistent terminal'de master.env'i yükle
2. **Health Check çalıştır:**
   ```
   run_command → python3 _skills/bot-test/health_check.py
   ```
   - 4 bot kontrol edilir. ❌ olan varsa → Hata Haritası'na bak.
3. **Rapor sun** — Sonuç raporunu kullanıcıya göster.

### "Full test" çağrıldığında:

1-3 yukarıdaki + ek olarak:
4. **YouTube conversation test çalıştır**
5. **eCom import + conversation test çalıştır**
6. **Genişletilmiş rapor sun**

### "Derin test" çağrıldığında:

1-6 yukarıdaki + ek olarak:
7. **YouTube stres test çalıştır** (test_stress.py)
8. **eCom servis + pipeline test çalıştır** (test_bot.py --test services + pipeline)
9. **Tam rapor sun** (tüm katmanlar dahil)

---

## Ne Zaman Çalıştırılır?

| Tetikleyici | Mod |
|-------------|-----|
| `/bot-test` komutu | Quick |
| "Full test" / "kapsamlı test" | Full |
| "Derin test" / "stres test" | Derin |
| Deploy sonrası (`/canli-yayina-al` tamamlandığında) | Full |
| 48-saat izleme kontrolü | Quick |
| Kullanıcı "testleri çalıştır" dediğinde | Full |

---

## Dikkat Edilecekler

⚠️ **API Kredi Kullanımı:**
- Katman 1 (Health Check) → Kredi harcamaz
- Katman 2 (Conversation) → OpenAI API çağrısı (~$0.01-0.02)
- Katman 2.5 (Stres Test) → OpenAI API çağrıları (~$0.05-0.10)
- Katman 3 (Services) → Perplexity, Kie AI bakiye sorgusu, Pipeline DRY-RUN (~$0.05)
- Gereksiz yere `--test all` çalıştırma

⚠️ **Env Değişkenleri:**
- Test scriptleri `master.env`'den token okur (lokal çalıştırmada)
- Railway'de env vars zaten set edilmiş durumda
- Health Check kendi `_load_env()` fonksiyonuna sahip (bağımsız çalışır)

⚠️ **Mevcut Test Dosyaları:**
- YouTube: `test_conversation.py` — 5 senaryo testi
- YouTube: `test_stress.py` — 10 kategori, 60+ stres testi
- eCom: `test_bot.py` — 9 test grubu, 30+ test case
- Bu dosyaları **değiştirme**, sadece çalıştır ve sonuçları yorumla

---

## Hata → Düzeltme Haritası

| Hata | Dosya | Aksiyon |
|------|-------|---------|
| `ImportError` | `requirements.txt` | Eksik paket ekle |
| OpenAI boş yanıt | `services/openai_service.py` | Model adı kontrol et |
| `AttributeError` CM | `core/conversation_manager.py` | State yapısı kontrol et |
| Timeout Kie/Replicate | `core/production_pipeline.py` | Retry mekanizması kontrol et |
| Railway CRASHED | Railway logları | `/hata-duzeltme` workflow'u |
| Telegram 401 | `master.env` | Token yenile |
| Telegram 409 Conflict | Eski deploy | Railway'de eski deploy'ları kaldır |
| Stres test <%90 | `test_stress.py` çıktısı | Başarısız kategorileri analiz et |
