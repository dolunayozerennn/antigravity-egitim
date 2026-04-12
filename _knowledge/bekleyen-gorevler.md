# Bekleyen Görevler

> Bu dosya her konuşma başında otomatik okunur.
> Yarım kalan işler, TODO'lar ve takip gereken konular burada tutulur.
> Görev tamamlandığında bu dosyadan silinir.

**Son güncelleme:** 12 Nisan 2026

---

## Aktif TODO'lar


### ~~🟡 YouTube Otomasyonu V2~~ → ✅ Deploy tamamlandı (11 Nisan 2026 gece)
- Railway SUCCESS, Smoke test geçti, Pets Got Talent kanalı OAuth2 ile bağlı
- Bot: @YouTube_Otomasyon_Doluay_Bot — 7/24 polling

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

### 🟡 48-Saat İzleme — eCom_Reklam_Otomasyonu v2.1
- **Deploy tarihi:** 2026-04-12 (v2.1 Stabilizasyon — 24 bug fix)
- **İzleme bitiş:** 2026-04-14
- **Kontrol 1:** ✅ (2026-04-12 10:28 — Bot aktif, polling çalışıyor, fatal error YOK, model gpt-4.1-mini doğru)
- **Kontrol 2:** ✅ (2026-04-12 11:25 — v2.1 redeploy SUCCESS, smoke test temiz)
- **Kontrol 3:** ⏳ (2026-04-14 — izleme bitiş kontrolü)
- **v2.0 fix özeti:** product_image opsiyonel, URL scrape + teyit, metin onay, resolution REQUIRED, state-aware context, PHOTO_CONFIRMATION state
- **v2.1 fix özeti:** event loop blocking (asyncio.to_thread), Vision API NoneType retry, session bellek sızıntısı TTL cleanup, Markdown parse fallback, Perplexity exception handling, aspect_ratio/resolution validasyonu, voiceover süre kontrolü, tmpfiles.org fallback, Replicate FileOutput cast, asyncio task hata yutma fix
- **Sonuç:** 2 temiz kontrol → arşive taşı

### 🟡 48-Saat İzleme — YouTube_Otomasyonu_V2.3
- **Deploy tarihi:** 2026-04-12 (V2.2 stabilizasyon — 14 bug fix + stabilizasyon 2. tur)
- **Re-deploy:** 2026-04-12 (V2.3 — 3. tur stabilizasyon: 5 ek fix)
- **İzleme bitiş:** 2026-04-14
- **Kontrol 1:** ✅ (2026-04-12 10:27 — Bot aktif, polling çalışıyor, smoke test geçti, fatal error YOK)
- **Kontrol 2:** ⏳ (2026-04-14 — ikinci kontrol)
- **Fix özeti (1. tur):** auto_mode crash (await sync), bellek sızıntısı (TTL+msg limit), .gitignore güvenlik, exponential backoff, Markdown V1 uyumu, YouTube fail-fast, hata mesajı güvenliği
- **Fix özeti (2. tur):** FFmpeg shutil.which() ile absolute PATH resolve, video_downloader 3x retry + exponential backoff, README topic_picker.py referansı kaldırıldı
- **Fix özeti (3. tur):** auto_mode notify asyncio.to_thread(), kie_client TCP reuse, replicate_merger TCP reuse, notion_logger 3x retry + exponential backoff, nixpacks.toml temizlik (aptPkgs kaldırıldı, python311 eklendi)
- **Sonuç:** 2 temiz kontrol → arşive taşı

### 🟡 48-Saat İzleme — LinkedIn Otomasyonu (Text + Video)
- **Deploy tarihi:** 2026-04-11 (4 kritik fix — Images API migration, content filter relaxed, ops logger flush, fallback)
- **İzleme bitiş:** 2026-04-13
- **Kontrol 1:** ⏳ (2026-04-12 — Text cron: Pazartesi/Perşembe, Video cron: günlük)
- **Kontrol 2:** ⏳ (2026-04-13 — ikinci çalışma)
- **Fix özeti:** 
  - Text: v2/assets → rest/images API migration (URN format fix)
  - Video: content filter "relaxed" + fallback mekanizması (tüm videolar filtrelenince en düşük güvenli kabul)
  - Her ikisi: wait_all_loggers() ile tüm ops instance'ları flush
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
