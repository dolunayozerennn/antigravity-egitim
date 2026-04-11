# Bekleyen Görevler

> Bu dosya her konuşma başında otomatik okunur.
> Yarım kalan işler, TODO'lar ve takip gereken konular burada tutulur.
> Görev tamamlandığında bu dosyadan silinir.

**Son güncelleme:** 11 Nisan 2026

---

## Aktif TODO'lar

### 🟡 YouTube Otomasyonu V2 — Deploy Bekliyor
- **Kaynak:** Konuşma `c5b5ac89` → Implementation `930ed4b8`
- **Plan dosyası:** `.gemini/antigravity/brain/c5b5ac89-6c9f-4719-8698-ebb8473f77ee/implementation_plan.md`
- **Açıklama:** Chat-based Telegram bot ile video üretim otomasyon sistemi. Tüm kod yazıldı, test geçti.
- **Öncelik:** Yüksek
- **Durum:** ✅ Implementation tamamlandı — Deploy öncesi adımlar bekliyor

#### ✅ Tamamlanan İşler (11 Nisan 2026 akşam):
- 4 yeni dosya: `conversation_manager.py`, `kie_client.py`, `replicate_merger.py`, README
- 5 rewrite: `main.py`, `config.py`, `prompt_generator.py`, `notion_logger.py`, `youtube_uploader.py`
- 3 güncelleme: `requirements.txt`, `nixpacks.toml`, `telegram_notifier.py`
- Syntax testi: 11/11 ✅ | Import testi: 12/12 ✅

#### Deploy Öncesi Gereken Adımlar:
1. 🔑 `YOUTUBE_CLIENT_SECRET` → Google Cloud Console'dan al (YouTube upload istemiyorsan atlayabilirsin)
2. 📋 Notion inline database oluştur (V2 property'leri ile) veya atla
3. 🚀 Railway Worker deploy + env vars ayarla

### ~~🟡 eCom Reklam Otomasyonu~~ → ✅ Tamamlandı, arşive taşındı (11 Nisan 2026 akşam)

---

## 📡 48-Saat İzleme (Aktif Takip)

> Deploy sonrası eklenen izleme kayıtları burada tutulur.
> Her konuşma başında bu bölüm kontrol edilir — izleme süresi dolmuş ve 2 temiz kontrol geçilmişse arşive taşınır.

### 🟡 48-Saat İzleme — Dolunay_Otonom_Kapak (Reels + YouTube)
- **Deploy tarihi:** 2026-04-10 → **Re-deploy:** 2026-04-11 (crash fix)
- **İzleme bitiş:** 2026-04-13
- **Kontrol 1:** ❌ (2026-04-11 — CRASHED: `get_logger() got unexpected keyword argument 'level'` → FIX: `core/logger.py`'ye `level` parametresi eklendi, redeploy SUCCESS)
- **Kontrol 2:** ⏳ (2026-04-12 — cron çalışması bekleniyor, UTC 06:00 / 07:00)
- **Kontrol 3:** ⏳ (2026-04-13 — ikinci cron çalışması)
- **Sonuç:** 2 temiz kontrol → arşive taşı

### 🟡 48-Saat İzleme — eCom_Reklam_Otomasyonu
- **Deploy tarihi:** 2026-04-11 (ilk deploy — SUCCESS)
- **İzleme bitiş:** 2026-04-13
- **Kontrol 1:** ✅ (2026-04-11 20:37 — Bot aktif, /start karşılama mesajı doğru çalışıyor)
- **Kontrol 2:** ⏳ (2026-04-13 — ikinci kontrol)
- **Sonuç:** 2 temiz kontrol → arşive taşı

---

## Tamamlanan TODO'lar (Arşiv)

> Aşağıdaki görevler tamamlanmış ve referans amaçlı saklanmaktadır.

### ✅ eCom Reklam Otomasyonu — Full Deploy (11 Nisan 2026)
- **Kaynak:** Konuşma `3c02fadd` → `8e258f23` → `637879f6` → `359dd649`
- **Yapılanlar:**
  1. Parça 1-4: Altyapı, 7 servis, 3 core modül, Telegram bot entry point, README
  2. Parça 5: Syntax (15/15 ✅), Import (12/12 ✅), Güvenlik taraması (temiz), GitHub push, Railway deploy (SUCCESS)
  3. 20 dosya, 3076 satır kod, 13 env variable
- **Railway:** Project `8797307d`, Service `98a3be1e`, Worker (7/24 polling)
- **48-saat izleme başlatıldı**

### ✅ Ekosistem Geneli Anti-Klişe Prompt Optimizasyonu (11 Nisan 2026)
- **Kaynak:** Kullanıcı Talebi — Otonom Kapak ve diğer metin jeneratörleri
- **Yapılanlar:** 
  1. Dolunay_Otonom_Kapak ("bilgisayar kullanan insan" klişesi yasaklandı, fiziksel metafor eklendi)
  2. Blog_Yazici ("Sonuç olarak", "Dijital çağda" tarzı yapay zeka kalıpları yasaklandı)
  3. LinkedIn_Text_Paylasim ("Hey network", aşırı emoji kullanımı ve sahte heyecan yasaklandı)
  4. Marka_Is_Birligi (Cold outreach "I hope this email finds you well" başlangıcı yasaklandı)
- Tüm README'ler güncellenerek GitHub'a tek seferde deploy edildi.

### ✅ Sistem Optimizasyonu — Disk & Mimari Temizliği (3 Nisan 2026)
- **Kaynak:** Teknik Audit konuşması
- **Yapılanlar:** ~3.7 GB disk alanı kazanıldı (venv'ler, node_modules, temp dosyalar). Ölü klasörler (Lead_Notifier_Bot, Tele_Satis_CRM) silindi. Orphan dosyalar arşive taşındı. 3 hayalet Railway projesi temizlendi. Dokümantasyon güncellendi.

### ✅ Gemini API Key Yenileme (2 Nisan 2026)
- **Kaynak:** Blog Yazıcı + Railway Health Check
- **Yapılanlar:** Sızdırılan key yenilendi, master.env + Railway env vars güncellendi.

### ✅ 6 Parçalı Derin Analiz (27 Mart 2026)
- **Yapılanlar:** 3 sosyal medya projesi deploy, Watchdog genişletme, requirements kilitleme, Notion logger entegrasyonu, legacy temizlik, LinkedIn token takibi.

---

> **Format:** Her TODO aşağıdaki yapıyı takip eder:
> ```
> ### 🔴/🟡/🟢 [Görev Başlığı]
> - **Kaynak:** [Hangi konuşmadan geldi]
> - **Açıklama:** [Ne yapılması gerekiyor]
> - **Öncelik:** Yüksek / Orta / Düşük
> - **Durum:** Planlandı / Devam ediyor / Bloke
> ```
>
> **48-Saat İzleme Format:**
> ```
> ### 🟡 48-Saat İzleme — [PROJE_ADI]
> - **Deploy tarihi:** [tarih]
> - **İzleme bitiş:** [tarih+48h]
> - **Kontrol 1:** ⏳/✅/❌ [tarih — sonuç]
> - **Kontrol 2:** ⏳/✅/❌ [tarih — sonuç]
> - **Sonuç:** 2 temiz kontrol → arşive taşı
> ```
