# Bekleyen Görevler

> Bu dosya her konuşma başında otomatik okunur.
> Yarım kalan işler, TODO'lar ve takip gereken konular burada tutulur.
> Görev tamamlandığında bu dosyadan silinir.

**Son güncelleme:** 26 Nisan 2026

---

## Aktif TODO'lar


### ~~🟡 YouTube Otomasyonu V2~~ → ✅ V3'e yükseltildi (18 Nisan 2026)
- V3: Telegram kaldırıldı → CronJob (günlük 17:00 TR), Creative Engine, tam otonom
- İlk otonom video başarıyla yüklendi: https://youtube.com/shorts/zXFbB789f3Q

### ~~🟡 eCom Reklam Otomasyonu~~ → ✅ Tamamlandı, arşive taşındı (11 Nisan 2026 akşam)

---

## 📡 48-Saat İzleme (Aktif Takip)

> Deploy sonrası eklenen izleme kayıtları burada tutulur.
> Her konuşma başında bu bölüm kontrol edilir — izleme süresi dolmuş ve 2 temiz kontrol geçilmişse arşive taşınır.

### 🟡 48-Saat İzleme — Ceren_izlenme_notifier (Apify Limit Artırımı + Crash Fix)
- **Deploy tarihi:** 2026-04-20
- **İzleme bitiş:** 2026-04-22
- **Değişiklik:** Limitler (Ig:7->20, Tk:7->20, Yt:5->25) artırıldı, ApifyClient dictionary hatalarına karşı fatal error kapatılmadan exception fırlatma düzeltildi.
- **Kontrol 1:** ⏳ Bekliyor (Salı Cron tetiklemesi)
- **Kontrol 2:** ⏳ Bekliyor (Perşembe Cron tetiklemesi)
- **Sonuç:** ⏳ 2 kontrol temizse kapatılır

### ✅ 48-Saat İzleme — whatsapp-asistan (Initial Deploy — AI Assistant)
- **Deploy tarihi:** 2026-04-25
- **İzleme bitiş:** 2026-04-27
- **Railway Project:** `fb3c9636-33cf-406f-a0e0-96f4d168ba4e`
- **Domain:** `whatsapp-asistan-production.up.railway.app`
- **Değişiklikler:**
  1. Initial deploy — KVKK onboarding + RAG AI + ManyChat entegrasyonu
  2. Express server (port 3456) + Supabase (subscribers, conversations, knowledge_chunks)
  3. OpenAI gpt-4.1-mini + text-embedding-3-small RAG
- **Kontrol 1:** ✅ Health check OK
- **Kontrol 2:** ✅ ManyChat webhook aktif, KVKK mesajı gönderildi, RAG 43/43 chunk seeded
- **Sonuç:** ✅ Tüm adımlar tamamlandı, 27 Nisan'a kadar izlemede

### 🟡 48-Saat İzleme — eCom_Reklam_Otomasyonu (HTTP 512 Upstream Retry Fix)
- **Deploy tarihi:** 2026-04-24 ✅ Push tamamlandı (5c48046)
- **İzleme bitiş:** 2026-04-26
- **Değişiklik:** 
  1. `retry.py`: HTTP 512 kodu RETRYABLE_STATUS_CODES'a eklendi + genel 5xx (500-599) aralığı retry desteği
  2. `kie_api.py`: 5xx/512 upstream proxy hataları için detaylı loglama
  3. `production_pipeline.py`: Hata sınıflandırması (upstream/timeout/safety) ve Türkçe kullanıcı mesajları
- **Push durumu:** ✅ Başarıyla GitHub'a gönderildi. (Ek olarak README.md, scenario_engine.py ve replicate_service.py güncellemeleri de `53ab387` ile gönderildi)
- **Kontrol 1:** ⏳ Push sonrası Railway deploy doğrulanacak
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ 512 hatası tekrarlanmazsa kapatılır

### 🟡 48-Saat İzleme — eCom_Reklam_Otomasyonu (Bot URL Hafıza, Tool Parse ve Format Zorunluluğu)
- **Deploy tarihi:** 2026-04-20
- **İzleme bitiş:** 2026-04-22
- **Değişiklik:** 1) Agent'ın pending_url ile son gönderilen linki format seçimi esnasında unutması ve process_url()'yi yanlış anda başlatması düzeltildi. 2) msg.tool_calls listesinde tüm tool'ların (hem format sunumu hem URL yakalama aynı gelse bile) parse edilmesi sağlandı ve hatalı model markdown syntax'ları try/except fallback'e alındı.
- **Kontrol 1:** ⏳ Bekliyor (kullanıcının kendi denemesinde buton tıkladıktan sonra 'Nothing/Crashed' hatasının yaşanmadığı doğrulanacak)
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ 2 kontrol temizse kapatılır

### 🟡 48-Saat İzleme — eCom_Reklam_Otomasyonu (Görsel Seçim Prompt Fix)
- **Deploy tarihi:** 2026-04-19
- **İzleme bitiş:** 2026-04-21
- **Değişiklik:** Seedance 2.0 referans görsel prompt'u güçlendirildi — infografik/metin görselleri filtreleniyor
- **Kontrol 1:** ⏳ Bekliyor (bir sonraki video üretiminde infografik seçilmemesi doğrulanacak)
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ 2 kontrol temizse kapatılır

### 🟡 48-Saat İzleme — YouTube_Otomasyonu (Realism Prompt Optimizasyonu)
- **Deploy tarihi:** 2026-04-19
- **İzleme bitiş:** 2026-04-21
- **İlk otonom video:** ✅ https://youtube.com/shorts/zXFbB789f3Q (french bulldog × pottery)
- **Değişiklik:** Videolardaki "gerçekçi illüstrasyon" (uncanny valley) hissiyatını azaltmak için `photorealistic, raw camera footage` constraint'i eklendi. Süre sınırlamaları esnekleştirildi ve aşırı kısa klip üretimini (5-7sn) engellemek adına süre sınırı 8-15 saniye arası olacak şekilde yeniden ayarlandı.
- **Kontrol 1:** ⏳ Bekliyor (sıradaki cron tetiklemesinde video kalitesine bakılacak)
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ 2 ardışık videoda tamamen photorealism yakalandıysa kapatılır

### 🟡 48-Saat İzleme — LinkedIn_Text_Paylasim (Görsel Sadeleştirme ve Fix)
- **Deploy tarihi:** 2026-04-24 (commit 6a9a579)
- **İzleme bitiş:** 2026-04-26
- **Değişiklik:** Aşırı sade/boş görsel üretimi problemi düzeltildi. Görsel üretim promptu "profesyonel, 3D teknoloji illüstrasyonları (parlayan düğümler, soyut veri akışları vb.)" üretecek şekilde dengelendi.
- **Kontrol 1:** ⏳ Bekliyor (bir sonraki otonom LinkedIn paylaşımında görselin boş olmadığı ve profesyonel göründüğü doğrulanacak)
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ İki ardışık postta istenilen profesyonel/dolu görsel yapısına ulaşılırsa kapatılır


---

## Tamamlanan TODO'lar (Arşiv)

> Aşağıdaki görevler tamamlanmış ve referans amaçlı saklanmaktadır.

### ✅ Lead_Notifier_Bot V3 — Railway Fix (26 Nisan 2026)
- **Kaynak:** Watchdog Alarm — Railway FAILED
- **Yapılanlar:** OAuth fallback (GOOGLE_OUTREACH_TOKEN_JSON) eklendi, Google Sheets SA yetkilendirmesi yapıldı, share_sheet.py eklendi. Railway deploy SUCCESS, 12 yeni lead tespit edildi, bot aktif çalışıyor.
- **İzleme:** ✅ Tamamlandı (deploy logları temiz, 403 hatası çözüldü)

### ✅ eCom Reklam Otomasyonu — GitHub Push (23 Nisan 2026)
- **Kaynak:** Deploy Sonrası İzleme ve Manuel Kontrol
- **Yapılanlar:** `conversation_manager.py` ve `main.py` dosyalarının başarıyla `9405cb2` commit'iyle GitHub'da güncel olduğu ve lokal SHA'ları ile birebir eşleştiği doğrulandı.

### ✅ Dolunay_Otonom_Kapak (Reels + YouTube) — İzleme Başarılı (14 Nisan 2026)
- **Kaynak:** Deploy Sonrası İzleme
- **Yapılanlar:** Railway oto-deploy hatası manuel olarak çözüldü, en güncel commit `431c6e6` ile servis stabilize edildi ve 48-saat izleme tamamlandı.

### ✅ eCom_Reklam_Otomasyonu v2.4 — İzleme Başarılı (14 Nisan 2026)
- **Kaynak:** v2.4 Kapsamlı Optimizasyon Mimarisi
- **Yapılanlar:** Merkezileştirilmiş retry, güvenli ImgBB session'ı, audio/video streaming tabanlı bellek optimizasyonu, thread starvation fixleri tamamlandı. 48-saat başarılı izlendi.

### ✅ YouTube_Otomasyonu_V2.6 — İzleme Başarılı (14 Nisan 2026)
- **Kaynak:** YouTube V2.6 Dil Güvenlik Kısıtlamaları
- **Yapılanlar:** Seedance Türkçe diyaloğu kısıtlamaları entegre edildi. Smoke test ve 48 saat kesintisiz çalışması doğrulandı.

### ✅ LinkedIn Otomasyonu (Text + Video) — İzleme Başarılı (14 Nisan 2026)
- **Kaynak:** LinkedIn API Güncellemesi
- **Yapılanlar:** Images API migration tamamlandı, içerik filtresi "relaxed" duruma getirildi ve logger gecikmeleri fixlendi.

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

### 🟡 48-Saat İzleme — Twitter_Video_Paylasim (3 Kritik Fix)
- **Deploy tarihi:** 2026-04-24 (push bekliyor — sandbox DNS kısıtlaması)
- **İzleme bitiş:** 2026-04-26
- **Lokal commit:** `fac5aaa` — push yapılması gerekiyor (`git push origin main`)
- **Değişiklikler:**
  1. `notion_logger.py`: Platform filtresi eklendi — LinkedIn/Twitter aynı DB ID'yi paylaşıyordu, duplikasyon karışıklığı düzeltildi
  2. `notion_logger.py`: Fail-safe `return True` → `return False` (API hatasında sessiz atlamayı önler)
  3. `nixpacks.toml`: `nixPkgs` → `aptPkgs` (ffmpeg PATH çözümleme güvenilirliği)
  4. `requirements.txt`: `yt-dlp` 2026.3.17 → 2026.4.24 (TikTok scraping uyumluluğu)
- **Kontrol 1:** ⏳ Push sonrası Railway deploy doğrulanacak
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ Push + ilk başarılı tweet doğrulanınca kapatılır
- **⚠️ NOT:** `NOTION_TWITTER_DB_ID` = `NOTION_LINKEDIN_DB_ID` (aynı ID). Kod seviyesinde platform filtresiyle düzeltildi ama ileride ayrı DB oluşturulması tavsiye edilir.

### 🟡 48-Saat İzleme — ecom-reklam-otomasyonu
- **Deploy tarihi:** 2026-04-20
- **İzleme bitiş:** 2026-04-22
- **Kontrol 1:** ⏳ Bekliyor (ilk konuşmada Railway logları kontrol edilecek)
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ 2 kontrol temizse kapatılır

### 🟡 48-Saat İzleme — Ceren_Marka_Takip
- **Deploy tarihi:** 2026-04-21
- **İzleme bitiş:** 2026-04-23
- **Kontrol 1:** ⏳ Bekliyor (ilk konuşmada Railway logları kontrol edilecek)
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ 2 kontrol temizse kapatılır

### 🟡 48-Saat İzleme — whatsapp-onboarding v1.3.0 (Enterprise Stabilization)
- **Son deploy:** 2026-04-25 (commit `683d606` — v1.3.0 Enterprise Stabilization)
- **İzleme bitiş:** 2026-04-27
- **Tamamlanan audit:** 7/7 ✅ (Railway, Notion şema, Git sync, E2E test, ManyChat, güvenlik, dedup)
- **v1.3.0 Stabilizasyon Değişiklikleri (12+ fix):**
  1. **Güvenlik:** WEBHOOK_SECRET / ADMIN_SECRET env tabanlı middleware desteği
  2. **XSS Koruması:** resend.js'de escapeHtml, tüm firstName interpolasyonları sanitize
  3. **ManyChat Resilience:** 8s timeout'lu fetchWithRetry, cache stampede önleme, phone normalizasyonu
  4. **Phone Validator:** Groq API'ye 5s AbortSignal timeout, uluslararası numara desteği (regex + LLM)
  5. **Cron DLQ:** try-catch izolasyonu, startDate NaN koruması, zombie üye önleme
  6. **Notion:** appendNote helper (2000 char limitli güvenli append)
  7. **Email Fallback:** ManyChat başarısızlığında otomatik email onboarding (WA CTA butonlu)
  8. **Uluslararası Destek:** Yurt dışı numaralar regex fallback ile +{digits} formatında normalize
  9. **Dedup:** onboarding statü kontrolü (whatsapp/email/tamamlandı/error zaten aktifse skip)
  10. **Admin:** /admin/trigger-flow endpoint'i manuel hata onarımı için
  11. **Body Limit:** express.json() 10kb limit
  12. **Error Masking:** Production'da stack trace gizleme
  13. **BCC Fix:** Email gönderimlerinde gizli alıcı (BCC) ve custom tag'ler kaldırıldı
- **Önceki Değişiklikler:**
  1. Webhook Idempotency, Manychat System Phone fallback
  2. Skool ID number→rich_text fix, Zapier Zap 1 & 2 kurulumu
- **Durum:** ✅ Push SUCCESS (`683d606`), Railway auto-deploy bekleniyor.
- **Kontrol 1:** ✅ 25 Nisan 2026 — Zapier, ManyChat, hibrit fallback, Groq validasyonu başarılı
- **Kontrol 2:** ⏳ Railway deploy doğrulaması + gerçek kullanıcı kaydı
- **⚠️ NOT:** Railway'de WEBHOOK_SECRET ve ADMIN_SECRET env var'ları set edilmeli




### 🟡 48-Saat İzleme — whatsapp-asistan (KB Management Overhaul v2)
- **Deploy tarihi:** 2026-04-25 21:28 (mcp_railway_deploy ile tamamlandı)
- **İzleme bitiş:** 2026-04-27
- **Lokal commit:** `45eb7d5`
- **Değişiklikler (3 fazlı KB yönetimi revizyonu):**
  1. `ai-factory-asistan-bilgi-tabani-v2.md`: Fiyat Güvenlik Notu eklendi — yasak fiyatlar ($97, $197, $297, $497, $997, $1997) listelendi
  2. `services/ai_engine.js`: `[SABİT FİYATLANDIRMA]` bloğu system prompt'un en üstüne eklendi
  3. `services/knowledge_base.js`: Keyword-based pinned chunks (PRICING_KEYWORDS), threshold 0.5→0.6
  4. `scripts/seed_knowledge.js`: Akıllı chunking (min 50 merge, max 2000 split, tablo koruması)
  5. `scripts/kb_manager.js`: YENİ — CLI aracı (list, search, validate, stats, diff)
  6. `server.js`: 4 yeni admin endpoint (/admin/kb/list, search, validate, update)
  7. `package.json`: kb:* npm script'leri eklendi
- **Seed sonucu:** ✅ 47 chunk (önceki: 43) başarıyla kaydedildi, Fiyat Güvenlik Notu ayrı chunk olarak mevcut
- **Kontrol 1:** ✅ Deploy logları — seed 47/47 OK, server port 3456'da çalışıyor
- **Kontrol 2:** ✅ WhatsApp testleri yapıldı: Üyelik ücreti doğru ($39, $59, $129) yanıtlandı, YouTube otomasyonunun tam otonom olduğu teyit edildi.
- **Sonuç:** ✅ Fiyat halüsinasyonları ve otomasyon hataları tamamen giderildi, izleme süreci 27 Nisan'a kadar devam edecek.

### ✅ whatsapp-onboarding (Zapier Empty Phone Fix)
- **Kaynak:** Kullanıcı extreme case bildirimi
- **Yapılanlar:** Telefon numarası (answer_1) boş bırakıldığında webhook'un 400 Bad Request fırlatıp Zapier'ı hata durumuna sokması engellendi. Artık boşluk durumunda 200 OK dönerek doğrudan email fallback senaryosuna geçiyor. Railway'e deploy edildi.
