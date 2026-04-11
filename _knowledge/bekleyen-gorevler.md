# Bekleyen Görevler

> Bu dosya her konuşma başında otomatik okunur.
> Yarım kalan işler, TODO'lar ve takip gereken konular burada tutulur.
> Görev tamamlandığında bu dosyadan silinir.

**Son güncelleme:** 10 Nisan 2026

---

## Aktif TODO'lar

_Şu an bekleyen görev bulunmamaktadır._

---

## 📡 48-Saat İzleme (Aktif Takip)

> Deploy sonrası eklenen izleme kayıtları burada tutulur.
> Her konuşma başında bu bölüm kontrol edilir — izleme süresi dolmuş ve 2 temiz kontrol geçilmişse arşive taşınır.

### 🟡 48-Saat İzleme — Dolunay_Otonom_Kapak (Reels + YouTube)
- **Deploy tarihi:** 2026-04-10
- **İzleme bitiş:** 2026-04-12
- **Kontrol 1:** ⏳ (2026-04-11 — cron çalışması bekleniyor)
- **Kontrol 2:** ⏳ (2026-04-12 — ikinci cron çalışması)
- **Sonuç:** 2 temiz kontrol → arşive taşı

---

## Tamamlanan TODO'lar (Arşiv)

> Aşağıdaki görevler tamamlanmış ve referans amaçlı saklanmaktadır.

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
