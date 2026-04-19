# Bekleyen Görevler

> Bu dosya her konuşma başında otomatik okunur.
> Yarım kalan işler, TODO'lar ve takip gereken konular burada tutulur.
> Görev tamamlandığında bu dosyadan silinir.

**Son güncelleme:** 12 Nisan 2026

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
- **Değişiklik:** Videolardaki "gerçekçi illüstrasyon" (uncanny valley) hissiyatını azaltmak için videolara `photorealistic, raw camera footage` constraint'i eklendi ve süre (`10 seconds`) zorunluluğu kaldırıldı.
- **Kontrol 1:** ⏳ Bekliyor (sıradaki cron tetiklemesinde video kalitesine bakılacak)
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ 2 ardışık videoda tamamen photorealism yakalandıysa kapatılır


---

## Tamamlanan TODO'lar (Arşiv)

> Aşağıdaki görevler tamamlanmış ve referans amaçlı saklanmaktadır.

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

### 🟡 48-Saat İzleme — Twitter_Video_Paylasim
- **Deploy tarihi:** 2026-04-16
- **İzleme bitiş:** 2026-04-18
- **Durum:** ✅ ffmpeg hatası çözüldü (nixPkgs -> aptPkgs migration), sıradaki Cron tetiklenmesi bekleniyor.
- **Kontrol 1:** ⏳ Bekliyor
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ 2 kontrol temizse kapatılır
