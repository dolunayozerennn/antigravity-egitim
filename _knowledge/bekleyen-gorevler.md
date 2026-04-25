# Bekleyen Görevler

> Bu dosya her konuşma başında otomatik okunur.
> Yarım kalan işler, TODO'lar ve takip gereken konular burada tutulur.
> Görev tamamlandığında bu dosyadan silinir.

**Son güncelleme:** 22 Nisan 2026

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

### 🟡 48-Saat İzleme — whatsapp-onboarding (Idempotency ve System Fallback + Zapier Kurulumu)
- **Son deploy:** 2026-04-25 (commit `a6cfce94` — Skool ID number→rich_text fix)
- **İzleme bitiş:** 2026-04-27
- **Tamamlanan audit:** 7/7 ✅ (Railway, Notion şema, Git sync, E2E test, ManyChat, güvenlik, dedup)
- **Değişiklikler:**
  1. Webhook Idempotency: API'ler (Manychat, Resend) Notion güncellenmeden önce tetiklenerek Zapier retry'larına dirençli hale getirildi.
  2. Manychat servisi custom_field ile numara bulamazsa System Phone üzerinden (lookup_user_by_system_field) arama yapacak şekilde fallback eklendi.
  3. Resend template'lerinde `firstName` değişkenleri ve yeni YouTube URL (Day 4) aktif edildi.
  4. Notion şemasına `errorCount`, `lastError`, `error` status eklendi, Dedup kontrolü genişletildi.
  5. YENİ — Skool ID property number→rich_text'e çevrildi, `notion.js` filtresi güncellendi (hex transaction_id kısaltılmadan saklanıyor).
  6. YENİ — Zapier Zap 1 (new-paid-member) ve Zap 2 (membership-questions) kuruldu, test edildi ve **publish** edildi.
- **Durum:** ✅ Deploy SUCCESS (`a6cfce94`), Health check OK, Zapier canlı testleri başarılı.
- **Kontrol 1:** ✅ 25 Nisan 2026 — Zapier Zap 1 & 2 canlı webhook testi başarılı. Railway logları hatasız. Groq validasyonu, Notion CRUD, dedup kontrolü çalışıyor. Test kayıtları temizlendi.
- **Kontrol 2:** ⏳ Bekliyor (gerçek kullanıcı kaydı ile doğrulanacak)
- **Sonuç:** ⏳ Kontrol 2 temizse kapatılır

### 🟡 48-Saat İzleme — Lead_Notifier_Bot
- **Deploy tarihi:** 2026-04-24
- **İzleme bitiş:** 2026-04-26
- **Değişiklik:** V3 yükseltmesi yapıldı. Satır sayısı bazlı takip ID bazlı (benzersiz UUID) state'e geçirildi. Filtreleme eklendi (sadece lead_status == "CREATED"). Fail-fast environment validation ve Spam koruması eklendi.
- **Kontrol 1:** ✅ Local dry-run ve bağlantı testi başarılı. (Railway üzerindeki servis loglarında ilk gerçek lead gelişinin kontrolü bekleniyor)
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ 2 kontrol temizse kapatılır

