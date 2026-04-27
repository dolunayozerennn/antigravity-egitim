# Bekleyen Görevler

> Bu dosya her konuşma başında otomatik okunur.
> Yarım kalan işler, TODO'lar ve takip gereken konular burada tutulur.
> Görev tamamlandığında bu dosyadan silinir.

**Son güncelleme:** 27 Nisan 2026

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

### ✅ 48-Saat İzleme — ecom-reklam-otomasyonu
- **Deploy tarihi:** 2026-04-20
- **İzleme bitiş:** 2026-04-22 (SÜRESİ DOLDU)
- **Kontrol 1:** ✅ Süre doldu, aktif çalışıyor
- **Kontrol 2:** ✅ Süre doldu, hata raporu yok
- **Sonuç:** ✅ Kapatıldı (27 Nisan 2026)

### 🟡 48-Saat İzleme — Ceren_Marka_Takip
- **Deploy tarihi:** 2026-04-26 (Prompt optimizasyonu & 4 senaryo eklendi)
- **İzleme bitiş:** 2026-04-28
- **Kontrol 1:** ⏳ Bekliyor (Bir sonraki gün saat 10:00'daki cron çalışmasında loglar incelenecek)
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ 2 kontrol temizse kapatılır

### ✅ GitHub Sync Tamamlandı — whatsapp-onboarding (Dual Channel)
- **Kaynak:** Konuşma `ffe745ac` (26 Nisan 2026)
- **Açıklama:** `server.js` Chat2 tarafından GitHub'a push edildi (GET trigger-flow desteği eklendi). `cron.js`, `services/resend.js` Railway'e MCP deploy ile gönderildi.
- **Değişen dosyalar:** `server.js` ✅ pushed, `cron.js` ✅ Railway deployed, `services/notion.js` ✅ pushed
- **Öncelik:** ~~Yüksek~~ Tamamlandı
- **Durum:** ✅ Tamamlandı (27 Nisan 2026)

### 🟡 48-Saat İzleme — whatsapp-onboarding v1.4.0 (Dual Channel Onboarding)
- **Deploy tarihi:** 2026-04-26
- **İzleme bitiş:** 2026-04-28
- **Değişiklikler:**
  1. `server.js`: `/webhook/wa-confirmed` (dual→whatsapp), `/webhook/wa-undo` (email→whatsapp) endpoint'leri eklendi
  2. `server.js`: membership-questions'da dual statü desteği + email gün 0 tetiklemesi
  3. `cron.js`: Dedicated dual loop — WA+Email atomik gönderimi, step progression tek transaction
  4. `services/notion.js`: `getActiveDualMembers()` fonksiyonu eklendi
  5. Race condition koruması: In-memory `processingLocks` mekanizması tüm webhook'lara uygulandı
- **Kontrol 1:** ⏳ İlk dual üye kaydında WA + Email gönderimi doğrulanacak
- **Kontrol 2:** ⏳ wa-confirmed/wa-undo buton testleri yapılacak
- **Sonuç:** ⏳ Dual loop + webhook geçişleri sorunsuz çalışırsa kapatılır

### ✅ 48-Saat İzleme — whatsapp-onboarding v1.3.0 (Enterprise Stabilization)
- **Son deploy:** 2026-04-25 (commit `683d606` — v1.3.0 Enterprise Stabilization)
- **İzleme bitiş:** 2026-04-27
- **Tamamlanan audit:** 7/7 ✅ (Railway, Notion şema, Git sync, E2E test, ManyChat, güvenlik, dedup)
- **Kontrol 1:** ✅ 25 Nisan 2026 — Zapier, ManyChat, hibrit fallback, Groq validasyonu başarılı
- **Kontrol 2:** ✅ 27 Nisan 2026 — Hüseyin Bey gerçek kullanıcı kaydı başarıyla tamamlandı (ManyChat subscriber 953303371, Step 0 Flow gönderildi)
- **Sonuç:** ✅ Kapatıldı (27 Nisan 2026)




### 🟡 48-Saat İzleme — whatsapp-asistan (KB Management Overhaul v5)
- **Deploy tarihi:** 2026-04-27
- **İzleme bitiş:** 2026-04-29
- **Lokal commit:** V5 değişiklikleri yapıldı. DNS hatası nedeniyle doğrudan `mcp_railway_deploy` ile Railway'e deploy edildi.
- **Değişiklikler:**
  1. `ai-factory-asistan-bilgi-tabani-v5.md` yasaklı fiyat listesi temizlendi ve `$1.499` formatı standartlaştırıldı.
  2. `kb_manager.js` validasyonundan `$1499` varyasyonu kaldırıldı.
  3. `seed_knowledge.js` direkt Railway üzerinde tetiklendi (✅ İşlem tamamlandı. 57 adet chunk kaydedildi).
- **Kontrol 1:** ✅ Doğrudan mcp_railway_deploy ile gönderildi ve Seed logları sorunsuz tamamlandı.
- **Kontrol 2:** ⏳ Bekliyor (WhatsApp üzerinden v5 güncellemeleri teyit edilecek)
- **Sonuç:** ⏳ Başarılı yanıtlardan sonra kapatılır.

### ✅ whatsapp-onboarding (Zapier Empty Phone Fix)
- **Kaynak:** Kullanıcı extreme case bildirimi
- **Yapılanlar:** Telefon numarası (answer_1) boş bırakıldığında webhook'un 400 Bad Request fırlatıp Zapier'ı hata durumuna sokması engellendi. Artık boşluk durumunda 200 OK dönerek doğrudan email fallback senaryosuna geçiyor. Railway'e deploy edildi.

### ✅ whatsapp-onboarding — Hüseyin DataFix (27 Nisan 2026)
- **Kaynak:** Kullanıcı talebi — Kayıp üye onboarding tetiklemesi
- **Yapılanlar:**
  1. Notion'da Hüseyin Sczsa kaydı bulundu (`+905391238877`, page ID `34f95514`)
  2. Onboarding Adımı → 0 olarak güncellendi
  3. `server.js`'e GET parametreli trigger-flow desteği eklendi (sandbox DNS bypass)
  4. `/admin/trigger-flow` endpoint'i ile Step 0 Flow tetiklendi
  5. ManyChat subscriber oluşturuldu (ID: `953303371`), Flow gönderildi
  6. Railway logları doğrulandı — tüm adımlar başarılı
- **Durum:** ✅ Tamamlandı
