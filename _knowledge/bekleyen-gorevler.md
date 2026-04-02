# Bekleyen Görevler

> Bu dosya her konuşma başında otomatik okunur.
> Yarım kalan işler, TODO'lar ve takip gereken konular burada tutulur.
> Görev tamamlandığında bu dosyadan silinir.

**Son güncelleme:** 2 Nisan 2026

---

## Aktif TODO'lar

### ✅ ~~Yeni Gemini API Key'in Entegrasyonu~~ (TAMAMLANDI)
- **Kaynak:** Railway Health Check & Blog Yazıcı (2 Nisan 2026)
- **Açıklama:** Sızdırılan ve bloke edilen Gemini API Key (`AIzaSyBm...`) Google Cloud'dan yenilendi. `master.env`, `api-anahtarlari.md` güncellendi. Railway env vars güncellendi.
- **Öncelik:** Yüksek (P1-Kritik - Blog üretimi çalışmıyor)
- **Durum:** ✅ Tamamlandı (2 Nisan 2026)
- **Notlar:** Yeni key: `AIzaSyByXyLOy...`. master.env + api-anahtarlari.md güncellendi. Railway projelerine yansıtıldı (Blog_Yazici, Dolunay_Reels_Kapak, Dolunay_YouTube_Kapak, LinkedIn_Text_Paylasim).

### ✅ ~~Chat 1: 3 Sosyal Medya Projesi Deploy~~ (TAMAMLANDI)
- **Kaynak:** Derin Analiz (27 Mart 2026)
- **Açıklama:** LinkedIn_Video_Paylasim, LinkedIn_Text_Paylasim, Twitter_Video_Paylasim → schedule→cron dönüşümü + Railway deploy + deploy-registry güncelleme
- **Öncelik:** Yüksek (P1-Kritik)
- **Durum:** ✅ Tamamlandı (27 Mart 2026)
- **Notlar:** 3 proje Railway CronJob olarak deploy edildi. Build SUCCESS. Duplicate lead-pipeline kaydı temizlendi.

### ✅ ~~Chat 2: Watchdog Kapsamını Genişlet~~ (TAMAMLANDI)
- **Kaynak:** Derin Analiz (27 Mart 2026)
- **Açıklama:** Akıllı Watchdog'a 7 yeni proje eklendi (Blog_Yazici, Reels_Kapak, Tahsilat, LinkedIn Video, LinkedIn Text, Twitter Video, SWC)
- **Öncelik:** Yüksek (P2)
- **Durum:** ✅ Tamamlandı (27 Mart 2026)
- **Notlar:** 4 → 11 izlenen proje. Çoklu Notion token desteği, custom_notion pipeline fix, paylaşımlı DB deduplication. NOTION_SOCIAL_TOKEN Railway'e eklendi. Deploy SUCCESS.

### ✅ ~~Chat 3: Requirements.txt Kilitleme~~ (TAMAMLANDI)
- **Kaynak:** Derin Analiz (27 Mart 2026)
- **Açıklama:** 9 projede `>=` → `==` dönüşümü + versiyonsuz paketler düzeltildi
- **Öncelik:** Orta (P2)
- **Durum:** ✅ Tamamlandı (27 Mart 2026)
- **Notlar:** 8 proje `>=` → `==`, 1 proje (Emlak_Arazi_Drone_Çekim) versiyonsuz → `==`. Toplam 9 proje, 35+ paket kilitlendi. Arşiv projeleri (`_arsiv/`) dokunulmadı.

### ✅ ~~Chat 4: Notion Logger Entegrasyonu~~ (TAMAMLANDI)
- **Kaynak:** Derin Analiz (27 Mart 2026)
- **Açıklama:** 6 projeye merkezi Notion Operations Log ekleme
- **Öncelik:** Orta (P2)
- **Durum:** ✅ Tamamlandı (27 Mart 2026)
- **Notlar:** Notion DB (33095514-0a32-81b4-858a-ff81a77b6d48) oluşturuldu. ops_logger.py 6 projeye deploy edildi: Lead_Pipeline, Isbirligi_Tahsilat_Takip, Marka_Is_Birligi, Swc_Email_Responder, Shorts_Demo_Otomasyonu, Dolunay_Reels_Kapak. Test logları doğrulandı. Railway env vars (NOTION_DB_OPS_LOG) eklenmesi gerekiyor.

### ✅ ~~Chat 5: Temizlik & Küçük Düzeltmeler~~ (TAMAMLANDI)
- **Kaynak:** Derin Analiz (27 Mart 2026)
- **Açıklama:** Legacy klasör taşıma, print(e) fix, deploy registry temizliği, orphan dosyalar
- **Öncelik:** Düşük (P3)
- **Durum:** ✅ Tamamlandı (27 Mart 2026)
- **Notlar:** Tele_Satis_CRM silindi (zaten _arsiv'de). Lead_Notifier_Bot ana dosyaları silindi (__pycache__ izin sorunu). print(e)→logging.error fix. Deploy registry askıda projeler güncellendi + YouTube_Kapak eklendi. followup_targets.json→Swc_Email_Responder, read_swc_sent.py→_arsiv taşındı.

### ✅ ~~Chat 6: LinkedIn Token Takibi + Watchdog V2~~ (TAMAMLANDI)
- **Kaynak:** Derin Analiz (27 Mart 2026)
- **Açıklama:** Token expire takibi, Railway deployment status probe
- **Öncelik:** Düşük (P3)
- **Durum:** ✅ Tamamlandı (27 Mart 2026)
- **Notlar:** 
  - Token Freshness Check: LinkedIn token 14 gün kala uyarı, expire=alarm
  - Railway Deployment Probe: 9 aktif servisin GraphQL ile son deployment kontrolü
  - api-anahtarlari.md'ye Token Expire Takip Tablosu eklendi
  - Alerter'a token + Railway bölümleri eklendi (HTML rapor)

---

## Tamamlanan TODO'lar (Arşiv)
### 🟢 Watchdog İş Metrikleri Genişletmesi
- **Kaynak:** Self-review konuşması (25-26 Mart 2026)
- **Açıklama:** Akilli_Watchdog projesine iş metrikleri eklendi. Notion boş kayıt kontrolü sağlandı. `expected_daily_activity` eklendi.
- **Öncelik:** Orta
- **Durum:** Tamamlandı

---

> **Format:** Her TODO aşağıdaki yapıyı takip eder:
> ```
> ### 🔴/🟡/🟢 [Görev Başlığı]
> - **Kaynak:** [Hangi konuşmadan geldi]
> - **Açıklama:** [Ne yapılması gerekiyor]
> - **Öncelik:** Yüksek / Orta / Düşük
> - **Durum:** Planlandı / Devam ediyor / Bloke
> ```
