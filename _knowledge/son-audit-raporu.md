# 🔍 Antigravity Proje Audit Raporu

**Tarih:** 16 April 2026, 13:36  
**Taranan proje:** 16  
**Taranan dosya:** 212 (37,147 satır)  
**Toplam bulgu:** 77 (6 kritik, 57 uyarı, 14 bilgi)

> [!CAUTION]
> 🔴 **6 kritik sorun** tespit edildi — acil müdahale gerekli!

---

## 📊 Özet Tablo

| Proje | Tip | Dosya | Satır | Kritik | Uyarı | Bilgi | Durum |
|-------|-----|-------|-------|--------|-------|-------|-------|
| Marka_Is_Birligi | python | 18 | 3,977 | 3 | 6 | 3 | 🔴 |
| eCom_Reklam_Otomasyonu | python | 34 | 5,951 | 2 | 6 | 3 | 🔴 |
| Dubai_Emlak_İçerik_Yazarı | python | 3 | 615 | 1 | 5 | 0 | 🔴 |
| Blog_Yazici | python | 16 | 4,535 | 0 | 6 | 3 | 🟡 |
| Lead_Pipeline | python | 10 | 2,114 | 0 | 6 | 0 | 🟡 |
| Shorts_Demo_Otomasyonu | python | 3 | 1,404 | 0 | 6 | 1 | 🟡 |
| LinkedIn_Text_Paylasim | python | 10 | 1,192 | 0 | 4 | 0 | 🟡 |
| YouTube_Otomasyonu | python | 20 | 4,349 | 0 | 4 | 2 | 🟡 |
| Akilli_Watchdog | python | 8 | 2,385 | 0 | 2 | 0 | 🟡 |
| Ceren_izlenme_notifier | python | 9 | 784 | 0 | 2 | 0 | 🟡 |
| Dolunay_Otonom_Kapak | python | 14 | 2,377 | 0 | 2 | 2 | 🟡 |
| Isbirligi_Tahsilat_Takip | python | 6 | 776 | 0 | 2 | 0 | 🟡 |
| LinkedIn_Video_Paylasim | python | 10 | 1,109 | 0 | 2 | 0 | 🟡 |
| Supplement_Telegram_Bot | python | 7 | 829 | 0 | 2 | 0 | 🟡 |
| Twitter_Video_Paylasim | python | 9 | 737 | 0 | 2 | 0 | 🟡 |
| Dolunay_AI_Website | node | 35 | 4,013 | 0 | 0 | 0 | 🟢 |

---

## 🔎 Detaylı Bulgular

### 🔴 Marka_Is_Birligi

*python projesi — 18 dosya, 3,977 satır*

**🔐 Güvenlik**

- ❌ Hardcoded API Key bulundu — `config/settings.py` satır 18
  - 💡 *Bu değeri .env dosyasına taşı, os.environ ile oku*
- ❌ Hardcoded API Key bulundu — `config/settings.py` satır 21
  - 💡 *Bu değeri .env dosyasına taşı, os.environ ile oku*
- ❌ Hardcoded API Key bulundu — `config/settings.py` satır 24
  - 💡 *Bu değeri .env dosyasına taşı, os.environ ile oku*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `src/outreach.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `src/personalizer.py` satır 195
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `src/personalizer.py` satır 203
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `src/personalizer.py` satır 211
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*
- ℹ️ Büyük dosya: 688 satır (bakım riski) — `src/contact_finder.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 544 satır (bakım riski) — `src/notion_service.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🔴 eCom_Reklam_Otomasyonu

*python projesi — 34 dosya, 5,951 satır*

**🔐 Güvenlik**

- ❌ Notion Token bulundu — `create_chat_db.py` satır 5
  - 💡 *Bu değeri .env dosyasına taşı, os.environ ile oku*
- ❌ Notion Token bulundu — `notion_test_ids.py` satır 8
  - 💡 *Bu değeri .env dosyasına taşı, os.environ ile oku*

**📝 Logging**

- ⚠️ print(e) — exception stack trace kayboluyor — `check_service.py` satır 27
  - 💡 *logging.error('...', exc_info=True) kullan*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 93
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 816
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `test_bot.py` satır 284
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `utils/retry.py` satır 76
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `services/openai_service.py` satır 321
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ Büyük dosya: 872 satır (bakım riski) — `main.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 831 satır (bakım riski) — `test_bot.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 813 satır (bakım riski) — `core/conversation_manager.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🔴 Dubai_Emlak_İçerik_Yazarı

*python projesi — 3 dosya, 615 satır*

**📦 Dependency**

- ⚠️ Python projesi ama requirements.txt yok
  - 💡 *pip freeze > requirements.txt ile oluştur*

**🔐 Güvenlik**

- ❌ Hardcoded API Key bulundu — `tools/transcript.py` satır 29
  - 💡 *Bu değeri .env dosyasına taşı, os.environ ile oku*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `tools/calculator.py` satır 356
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `tools/calculator.py` satır 361
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `tools/calculator.py` satır 366
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `tools/calculator.py` satır 371
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 Blog_Yazici

*python projesi — 16 dosya, 4,535 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ bare except: — tüm hataları yakalar, spesifik exception kullan — `run_pipeline.py` satır 62
  - 💡 *logging.error('...', exc_info=True) kullan*
- ⚠️ except...pass — hata sessizce yutuldu — `run_pipeline.py` satır 62
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `env_loader.py` satır 100
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `annotate_v3.py` satır 351
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*
- ℹ️ Büyük dosya: 632 satır (bakım riski) — `notion_video_selector.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 867 satır (bakım riski) — `annotate_v3.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🟡 Lead_Pipeline

*python projesi — 10 dosya, 2,114 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `sheets_reader.py` satır 97
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `sheets_reader.py` satır 180
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `watchdog.py` satır 194
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `notion_writer.py` satır 232
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 Shorts_Demo_Otomasyonu

*python projesi — 3 dosya, 1,404 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `bot.py` satır 90
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `bot.py` satır 400
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `bot.py` satır 405
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `bot.py` satır 422
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ Büyük dosya: 624 satır (bakım riski) — `bot.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🟡 LinkedIn_Text_Paylasim

*python projesi — 10 dosya, 1,192 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 102
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 180
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 YouTube_Otomasyonu

*python projesi — 20 dosya, 4,349 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 414
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core/prompt_sanitizer.py` satır 362
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `infrastructure/replicate_merger.py` satır 174
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `infrastructure/video_downloader.py` satır 92
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ Büyük dosya: 656 satır (bakım riski) — `test_stress.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 541 satır (bakım riski) — `main.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🟡 Akilli_Watchdog

*python projesi — 8 dosya, 2,385 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 Ceren_izlenme_notifier

*python projesi — 9 dosya, 784 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 Dolunay_Otonom_Kapak

*python projesi — 14 dosya, 2,377 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `core/ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core/ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*
- ℹ️ Büyük dosya: 613 satır (bakım riski) — `agents/reels_agent.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🟡 Isbirligi_Tahsilat_Takip

*python projesi — 6 dosya, 776 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 LinkedIn_Video_Paylasim

*python projesi — 10 dosya, 1,109 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 Supplement_Telegram_Bot

*python projesi — 7 dosya, 829 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `core/gemini_analyzer.py` satır 109
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core/gemini_analyzer.py` satır 117
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 Twitter_Video_Paylasim

*python projesi — 9 dosya, 737 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

## ✅ Temiz Projeler

- 🟢 **Dolunay_AI_Website** — Sorun bulunamadı (35 dosya, 4,013 satır)

---

## 📈 Kategori Özeti

| Kategori | Kritik | Uyarı | Bilgi |
|----------|--------|-------|-------|
| 🔐 Güvenlik | 6 | 0 | 0 |
| 📝 Logging | 0 | 56 | 0 |
| 🏗️ Proje Yapısı | 0 | 0 | 14 |
| 📦 Dependency | 0 | 1 | 0 |
