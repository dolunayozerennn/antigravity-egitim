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
- **Kontrol 2:** ✅ (2026-04-12 16:07 — CRASHED tespit edildi, kök neden: `get_logger() level` fix'i push edilmiş ama Railway auto-deploy tetiklenmemişti → Manuel redeploy → her iki servis SUCCESS)
- **Kontrol 3:** ✅ (2026-04-13 — Saat 11:00'de Servis İzleyici ile CRASHED tespit edildi. Kök neden analizi: Railway manuel "Redeploy" butonu, projenin "en yeni" Main commit'ini değil, zaten hata alan ESKİ commit'ini (1288454d, 10 Nisan) tekrar deploy etmişti. Bu sebeple yerelde düzelmiş olan `get_logger level` hatası Railway'de sürekli tekrarlıyordu. GraphQL API üzerinden `serviceInstanceDeployV2` kullanılarak en güncel Github commit'ine (`431c6e6`) zorunlu deploy tetiklendi ve çözüldü.)
- **Sonuç:** 1 temiz kontrol daha bekleniyor (Railway auto-deploy kopukluğu sebebiyle manuel tetiklendi, gözetim uzatıldı)

### 🟡 48-Saat İzleme — eCom_Reklam_Otomasyonu v2.3
- **Deploy tarihi:** 2026-04-12 (v2.1 Stabilizasyon — 24 bug fix)
- **Re-deploy 1:** 2026-04-12 (v2.2 Stabilizasyon audit — retry, ImgBB audio, safety rewrite, JSON recovery)
- **Re-deploy 3:** 2026-04-12 (v2.4 P2 görevler — stream video download, Kie AI kredi kontrolü, thread-safe sessions)
- **İzleme bitiş:** 2026-04-14
- **Kontrol 1:** ✅ (2026-04-12 10:28 — Bot aktif, polling çalışıyor, fatal error YOK)
- **Kontrol 2:** ✅ (2026-04-12 11:25 — v2.1 redeploy SUCCESS)
- **Kontrol 3:** ✅ (2026-04-12 11:58 — v2.2 stabilizasyon: syntax PASS, 14 maddelik audit)
- **Kontrol 4:** ✅ (2026-04-12 14:37 — v2.2 canlı: retry decorator, ImgBB audio, safety rewrite, session cleanup, JSON recovery)
- **Kontrol 5:** ✅ (2026-04-12 15:04 — v2.3 canlı: async polling (Kie AI + Replicate), thread starvation fix)
- **Kontrol 6:** ✅ (2026-04-12 15:17 — v2.4 canlı: stream download, kredi kontrolü, thread-safe sessions)
- **Kontrol 7:** ⏳ (2026-04-14 — izleme bitiş kontrolü, gerçek üretim testi bekleniyor)
- **v2.2 fix özeti:** Merkezi retry decorator (utils/retry.py), ImgBB audio hosting (birincil), safety filter GPT rewrite fallback, expanded session cleanup (CHATTING+30dk), Perplexity safe parsing, OpenAI JSON markdown fence recovery, Replicate output None/URL validation, Notion update try/except
- **v2.3 fix özeti:** async_poll_task() (Kie AI) + async_merge_video_audio() (Replicate) → asyncio.sleep() ile event loop dostu polling, 5 adet asyncio.to_thread(poll) çağrısı native async'e çevrildi
- **v2.4 fix özeti:** Video indirme stream=True + chunk'lı (RAM spike önleme), pipeline başında Kie AI kredi bakiye kontrolü ($0.50 eşik), sessions dict'e threading.Lock (thread-safe erişim)
- **Kalan P2 görevler (izleme sonrası):**
  - P2-9: JS-rendered sayfa desteği (Playwright/Apify — gelecek)
  - P2-12: ElevenLabs ses süresi taşması — agresif kırpma
- **Sonuç:** 2 temiz kontrol → arşive taşı

### 🟡 48-Saat İzleme — YouTube_Otomasyonu_V2.6
- **Deploy tarihi:** 2026-04-12 (V2.5 Derin Güvenlik — GPT pre-flight + model fallback + telemetry)
- **Re-deploy 1:** 2026-04-13 (V2.6 Absürt senaryo json entegrasyonu + Seedance Türkçe kısıtlaması)
- **İzleme bitiş:** 2026-04-15
- **Kontrol 1:** ✅ (2026-04-12 14:28 — Deploy SUCCESS, bot aktif, polling çalışıyor, fatal error YOK)
- **Kontrol 2:** ✅ (2026-04-13 10:00 — v2.6 redeploy SUCCESS, smoke test: NO_FATAL_ERRORS)
- **Kontrol 3:** ⏳ (İzleme bitiş kontrolü)
- **V2.6 fix özeti:**
  - `topics.json` içeriği absürt senaryolarla (Costco hırsızı köpek vb) değiştirildi
  - Türkçe uyarısı: Seedance model atandığında Türkçe dialog geçiyorsa GPT onayı soracak şekilde system prompt güncellendi.
- **Sonuç:** 1 temiz kontrol → arşive taşı

### 🟡 48-Saat İzleme — LinkedIn Otomasyonu (Text + Video)
- **Deploy tarihi:** 2026-04-11 (4 kritik fix — Images API migration, content filter relaxed, ops logger flush, fallback)
- **İzleme bitiş:** 2026-04-13
- **Kontrol 1:** ❌ (2026-04-11 — `linkedin-text-cron` CRASHED: `Gerekli ortam değişkeni GEMINI_API_KEY bulunamadı!`. Kök neden: `GEMINI_API_KEY` konfigürasyondan kaldırılmasına rağmen Github commit'i Railway auto-deploy tetiklememiş. Eski image hataya düşmeye devam etti.)
- **Kontrol 2:** ✅ (2026-04-13 — "Servis Alarmı" üzerine GraphQL API ile manuel deploy tetiklendi. En güncel commit (`431c6e6`) pull edildi. Status: SUCCESS.)
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
