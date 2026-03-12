---
name: musteri-kazanim
description: |
  Müşteri Kazanım Agenti — Herhangi bir hedef kitle için uçtan uca lead bulma, 
  iletişim bilgisi çıkarma, kişiselleştirilmiş e-posta outreach ve akıllı takip 
  sürecini tek bir orkestratör olarak yönetir. Influencer (B2C), şirket (B2B) ve 
  topluluk (Community) senaryolarını aynı pipeline ile çalıştırır.
---

# 🤖 Müşteri Kazanım Agenti

> **Versiyon:** 1.0
> **Oluşturulma:** 2026-03-11
> **Durum:** Aktif
> **Konum:** `_agents/musteri-kazanim/`

---

## 📌 Amaç ve Kapsam

Bu agent, **herhangi bir hedef kitle** için müşteri kazanım sürecini uçtan uca yönetir:

1. **Lead Bulma** — Sosyal medya, Google Maps, LinkedIn veya topluluk platformlarından hedef kitlenin profil bilgilerini toplar.
2. **İletişim Bilgisi Çıkarma** — Web sitesi, bio, Hunter.io, Apollo.io üzerinden e-posta ve telefon zenginleştirmesi (enrichment) yapar.
3. **Kişiselleştirme** — Her lead için bağlama uygun, doğal ve elle yazılmış hissi veren e-posta içeriği üretir.
4. **Gönderim** — Gmail API üzerinden kontrollü ve zamanlı outreach yapar.
5. **Takip & Sequence** — Açılma/cevaplama durumuna göre dallanmalı takip akışı yürütür.

### Bu Agent Kimin İçin?

| Senaryo | Örnek Kullanım | Referans Proje |
|---------|---------------|----------------|
| 🎬 **Influencer Outreach** | Türkiye'deki etkinlik influencer'larına ulaşma | `Projeler/Bugra_Influencer_Kampanya/` |
| 🏢 **B2B Lead Gen** | SaaS şirketlerine cold email kampanyası | `_arsiv/B2B_Outreach/` |
| 🤝 **Marka İş Birliği** | AI markalarına influencer olarak iş birliği teklifi | `Projeler/Marka_Is_Birligi/` |
| 🎨 **Creator Sourcing** | İtalyan UGC creator'larını bulma ve ulaşma | `_arsiv/Creative_Sourcing_Italy/` |
| 📱 **Sosyal Medya Scraping** | Instagram/TikTok'tan toplu profil toplama | `_arsiv/Swc_Insta_Scrape/` |

---

## 🔧 Kullandığı Skill'ler

### 1. `_skills/lead-generation/` — Lead Bulma Motoru
**Neden:** Apify merkezli mimariyle tek API anahtarından 20+ farklı aktörle her platformdan lead toplar. Hunter/Apollo sadece fallback olarak devreye girer.

**Sağladığı yetenek:**
- Instagram, TikTok, YouTube profil tarama
- Google Maps işletme bulma
- LinkedIn profil zenginleştirme (cookie-less)
- Web sitesinden e-posta/telefon çıkarma (`contact-info-scraper`)
- Skool/topluluk üye tarama

### 2. `_skills/eposta-gonderim/` — E-posta Gönderim Motoru
**Neden:** Gmail API üzerinden kişiselleştirilmiş e-posta gönderir ve durumu CSV'de takip eder. Rate limiting, hata yönetimi ve doğal Türkçe kişiselleştirme kuralları yerleşik.

**Sağladığı yetenek:**
- Gmail OAuth2 ile güvenli gönderim
- Satır bazlı CSV durum takibi
- Doğal Türkçe/İngilizce kişiselleştirme
- Günlük limit yönetimi (spam koruması)

---

## ⚙️ Kampanya Başlatma Parametreleri

Her yeni kampanya aşağıdaki parametrelerle tanımlanır. Bu parametreler `config/` altındaki YAML dosyalarında saklanır.

### Zorunlu Parametreler

| Parametre | Açıklama | Örnek |
|-----------|----------|-------|
| `kampanya_adi` | Kampanyanın benzersiz adı | `bugra-etkinlik-influencer-2026` |
| `hedef_tip` | Lead tipi | `influencer` / `b2b_sirket` / `ugc_creator` / `yerel_isletme` |
| `platform` | Arama yapılacak platform(lar) | `[instagram, tiktok]` |
| `dil` | İletişim dili | `TR` / `EN` / `IT` / `[TR, EN]` |
| `bolge` | Coğrafi hedef | `Türkiye` / `Italy` / `Global` |

### ICP (Ideal Customer Profile) Tanımı

```yaml
icp:
  # Influencer senaryosu
  minimum_takipci: 10000
  maksimum_takipci: 5000000
  nis: ["lifestyle", "teknoloji", "eğlence"]
  icerik_dili: ["TR"]
  
  # B2B senaryosu
  sirket_buyuklugu: "10-500"
  hedef_pozisyonlar: ["CEO", "CTO", "Marketing Director", "Growth Lead"]
  sektor: ["SaaS", "E-ticaret", "Fintech"]
  
  # UGC Creator senaryosu
  min_icerik_sayisi: 50
  icerik_turu: ["ugc", "product_review", "unboxing"]
```

### Opsiyonel Parametreler

| Parametre | Açıklama | Varsayılan |
|-----------|----------|------------|
| `arama_anahtar_kelimeleri` | Platform arama terimleri | `[]` |
| `hashtag_listesi` | Hashtag filtreleri | `[]` |
| `gunluk_gonderim_limiti` | Günlük max e-posta | `50` |
| `gonderim_saatleri` | Gönderim saat aralığı | `09:00-17:00` |
| `gonderim_gunleri` | Gönderim günleri | `[Pazartesi, Salı, Çarşamba, Perşembe, Cuma]` |
| `sablon_dili` | E-posta şablon dili | Kampanya diline göre otomatik |
| `dry_run` | Test modu (göndermeden önizleme) | `true` |
| `max_lead_sayisi` | Toplam hedef lead | `100` |

---

## 🔄 Orkestrasyon Akışı — 5 Adım

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MÜŞTERİ KAZANIM AGENTİ                        │
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ 1. LEAD  │───▶│ 2. EMAIL │───▶│ 3. KİŞİ- │───▶│ 4. GÖN-  │───▶│ 5. TAKİP │ │
│  │  BULMA   │    │  TOPLAMA │    │ SELLEŞTİR│    │  DERİM   │    │ & SEQU-  │ │
│  │          │    │          │    │  ME      │    │          │    │  ENCE    │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       │               │               │               │               │      │
│  lead-generation  lead-generation   LLM Engine      outreach       outreach  │
│  SKILL            SKILL (enrichment)                SKILL          SKILL     │
└─────────────────────────────────────────────────────────────────────┘
```

### Adım 1: Lead Bulma — `_skills/lead-generation/SKILL.md`

**Girdi:** Kampanya config YAML dosyası
**Çıktı:** `data/{kampanya_adi}_raw.json`

1. Config YAML'dan `hedef_tip` ve `platform` oku
2. Skill'deki **Model Seçim Algoritması**'na göre doğru Apify aktörünü seç:

   | Hedef Tip | Platform | Apify Aktör |
   |-----------|----------|-------------|
   | `influencer` | Instagram | `apify/instagram-profile-scraper` |
   | `influencer` | TikTok | `clockworks/tiktok-user-search-scraper` |
   | `b2b_sirket` | LinkedIn | `anchor/linkedin-profile-enrichment` |
   | `b2b_sirket` | Web | `code_crafter/leads-finder` |
   | `yerel_isletme` | Google Maps | `compass/crawler-google-places` |
   | `topluluk` | Skool | `memo23/skool-members-scraper` |

3. `arama_anahtar_kelimeleri` ve `hashtag_listesi`'ni aktör input'una dönüştür
4. Apify asenkron görev modelini kullan (başlat → polling → dataset çek)
5. `_knowledge/api-anahtarlari.md`'den Apify token al
6. Ham sonuçları `data/{kampanya_adi}_raw.json` olarak kaydet

**ICP Filtresi:** Ham sonuçlardan ICP'ye uymayan profilleri çıkar:
- Takipçi sayısı aralık dışı → filtrele
- Dil/bölge uyumsuz → filtrele
- Bot/fake profil şüphesi → filtrele

### Adım 2: Email Toplama — `_skills/lead-generation/SKILL.md` (Enrichment)

**Girdi:** `data/{kampanya_adi}_raw.json`
**Çıktı:** `data/{kampanya_adi}_enriched.json`

3 katmanlı waterfall email bulma stratejisi (Buğra + Instagram İş Birliği Scraper mantığı):

```
Profil
  │
  ├─ 1. BİO / BUTON EMAİL (ücretsiz, en hızlı)
  │     Instagram bio'sunda veya business butonunda email var mı?
  │     ├─ EVET → email_kaynagi: "bio" → sonraki profile geç
  │     └─ HAYIR ↓
  │
  ├─ 2. WEB SİTESİ ENRICHMENT (Apify — düşük maliyet)
  │     Profilin web sitesi var mı?
  │     ├─ EVET → vdrmota/contact-info-scraper ile tara
  │     │         ├─ Email bulundu → email_kaynagi: "website" → sonraki profile geç
  │     │         └─ Email bulunamadı ↓
  │     └─ HAYIR ↓
  │
  ├─ 3a. HUNTER.IO (domain bazlı — fallback #1)
  │     Domain varsa Hunter API ile ara
  │     ├─ Kişisel email bulundu → email_kaynagi: "hunter" → sonraki profile geç
  │     ├─ Sadece generic email → düşük önceliğe at
  │     └─ Bulunamadı ↓
  │
  └─ 3b. APOLLO.IO (B2B kişi arama — fallback #2)
        Apollo people search API ile pozisyon bazlı ara
        ├─ Email bulundu → email_kaynagi: "apollo" → sonraki profile geç
        └─ Bulunamadı → email_durumu: "not_found" → outreach listesinden hariç tut
```

**Email Doğrulama:**
- Hunter.io'dan dönen `deliverable` → ✅ direkt havuza
- Hunter.io'dan dönen `risky` → ⚠️ düşük öncelik
- Hunter.io'dan dönen `undeliverable` → ❌ listeden çıkar

**Duplicate Kontrolü:**
- Handle bazlı: Aynı Instagram/LinkedIn handle iki kez giremez
- Email bazlı: Aynı e-posta adresine iki kez gönderim yapılamaz
- İsim bazlı: Fuzzy matching ile benzer isimler kontrol edilir

### Adım 3: Kişiselleştirme — LLM Engine

**Girdi:** `data/{kampanya_adi}_enriched.json` + `templates/` şablonları
**Çıktı:** `data/{kampanya_adi}_messages.json`

1. Kampanya config'inden `sablon_dili` belirle
2. `templates/` altından uygun şablonu yükle:
   - `email-tr.md` → Türkçe kampanyalar
   - `email-en.md` → İngilizce kampanyalar
3. Her lead için kişiselleştirme değişkenlerini doldur:

   ```
   {ad}          → Lead'in adı
   {sirket}      → Şirket/marka adı
   {pozisyon}    → Unvan (B2B) veya platform rolü (Influencer)
   {kanca}       → Kişiye özel dikkat çekici açılış
   {deger_onerisi} → Kampanyaya özel değer önerisi
   {cta}         → Eylem çağrısı
   {platform}    → Kaynak platform
   ```

4. **Kişiselleştirme Kuralları** (B2B_Outreach Instruction.md'den):
   - Her mail "elle yazılmış" gibi hissettirmeli — generic/robotic olmamalı
   - `{kanca}` mümkünse lead'in şirketine özel enrichment verisinden türetilmeli
   - Konu satırı da kişiselleştirilmeli
   - Aynı kampanyada birden fazla varyant üret (A/B test)

5. **Türkçe Kişiselleştirme Kuralları** (Outreach SKILL'den):
   - Çeviri kokmayan doğal Türkçe kullan
   - İlk paragraf (icebreaker) max 2 cümle
   - CSV'deki bilgiye spesifik atıf yap
   - Ton: bağlama göre kurumsal veya samimi

### Adım 4: Gönderim — `_skills/eposta-gonderim/SKILL.md`

**Girdi:** `data/{kampanya_adi}_messages.json`
**Çıktı:** `data/{kampanya_adi}_log.csv` (güncellenmiş)

1. **Dry Run Kontrolü:**
   - `dry_run: true` ise → sadece önizleme çıktısı ver, göndermeden dur
   - Kullanıcıdan onay al → `dry_run: false` yap → gerçek gönderime geç

2. **Gmail Bağlantı Kurulumu:**
   - Credentials: `_knowledge/api-anahtarlari.md` (Google OAuth 2.0)
   - Token: `token.json` yoksa otomatik tarayıcı onayı ister

3. **Rate Limiting (Spam Koruması):**
   - `gunluk_gonderim_limiti` (varsayılan: 50)
   - İki mail arası minimum bekleme: `gonderim_araligi` (varsayılan: 5 dakika)
   - Sadece `gonderim_saatleri` içinde gönder
   - Sadece `gonderim_gunleri`'nde gönder (hafta sonu yok)
   - Yeni hesaplar için warm-up: İlk 2 hafta 20/gün

4. **Gönderim:**
   ```bash
   python3 _skills/eposta-gonderim/scripts/send_email.py \
     --to "{email}" \
     --subject "{konu}" \
     --body "{mesaj}" \
     --csv "data/{kampanya_adi}_log.csv" \
     --row_id {satir_no}
   ```

5. **Durum Takibi:**
   - Her gönderimde CSV güncellenir:
     - `Outreach_Status`: `Pending` → `Sent` / `Failed` / `No Email`
     - `Outreach_Date`: Gönderim tarihi
     - `Personalized_Message`: Gönderilen mesajın kopyası

### Adım 5: Takip & Sequence Yönetimi

**Bu adım B2B_Outreach'teki akıllı sequence mantığından esinlenilmiştir.**

#### Sequence Akışı — Koşullu Dallanma

```
ADIM 1: İlk Mail Gönderimi
  │
  ├─ ❌ Mail AÇILMADI (bekleme_suresi_acilmadi gün sonra)
  │   └─ ADIM 2a: Takip maili
  │       │   → Farklı konu satırı, aynı değer önerisi
  │       ├─ ❌ Yine AÇILMADI (bekleme_suresi_acilmadi gün sonra)
  │       │   └─ ADIM 3a: Son deneme VEYA farklı kanal (LinkedIn DM)
  │       │       └─ Cevap yoksa → sequence_durumu: "exhausted" ⏹️
  │       └─ 👁️ AÇILDI ama CEVAPLANMADI
  │           └─ ADIM 3b: Değer odaklı takip
  │               → Case study, veri, sosyal kanıt paylaş
  │
  ├─ 👁️ Mail AÇILDI ama CEVAPLANMADI (bekleme_suresi_cevaplanmadi gün sonra)
  │   └─ ADIM 2b: Farklı açıdan yaklaşım
  │       │   → Pain point değişikliği, yeni kanca
  │       ├─ ❌ CEVAPLANMADI
  │       │   └─ ADIM 3c: Break-up mail
  │       │       → Nazik kapanış, son şans
  │       │       → sequence_durumu: "exhausted" ⏹️
  │       └─ ✅ CEVAPLANDI → Yanıt İşleme Modülü
  │
  └─ ✅ Mail CEVAPLANDI → Yanıt İşleme Modülü
```

#### Yanıt İşleme Modülü

| Yanıt Tipi | Aksiyon |
|------------|---------|
| ✅ **Olumlu** | Toplantı planlama, kullanıcıya bildirim |
| ❌ **Olumsuz** (ilgi yok) | Kibarca teşekkür, lead'i "cold" işaretle |
| ❓ **Soru / bilgi talebi** | İlgili bilgiyi içeren yarı-otomatik yanıt hazırla |
| 🏖️ **OOO / tatil** | Bekleme süresini uzat, sonra yeniden dene |
| 🔴 **Bounce** | E-posta geçersiz işaretle, listeden çıkar |

#### Sequence Parametreleri (Kampanya Bazlı)

```yaml
sequence:
  toplam_adim: 3                    # Max email sayısı
  bekleme_suresi_acilmadi: 4        # Açılmazsa kaç gün bekle (gün)
  bekleme_suresi_cevaplanmadi: 3    # Açılıp cevaplanmazsa kaç gün bekle
  gunluk_gonderim_limiti: 50        # Günlük max
  gonderim_araligi: 5               # İki mail arası (dakika)
  gonderim_saatleri: "09:00-17:00"  # Gönderim penceresi
  gonderim_gunleri: ["Pzt", "Sal", "Car", "Per", "Cum"]
  saat_dilimi: "UTC+3"             # Varsayılan: Türkiye
```

#### Sektöre Göre Önerilen Sequence Profilleri

| Profil | Adım | Bekleme | Ton | Ağırlık |
|--------|------|---------|-----|---------|
| **SaaS / Teknoloji** | 4-5 | 2-3 gün | Doğrudan, değer odaklı | Case study |
| **E-ticaret** | 3-4 | 3-4 gün | ROI ve metrik odaklı | Sosyal kanıt |
| **Kurumsal / Sanayi** | 3 | 5-7 gün | Formal | Güven, referans |
| **Ajans / Hizmet** | 4 | 2-4 gün | Yaratıcı | Portfolio, sonuç |
| **Influencer** | 2-3 | 5-7 gün | Samimi, kısa | Viral sonuçlar |
| **UGC Creator** | 2-3 | 3-5 gün | Samimi, profesyonel | Ödeme, brief |

---

## 📄 Config Dosya Formatı (YAML Şablon)

Yeni kampanya açarken `config/` altına şu formatı kullan:

```yaml
# ═══════════════════════════════════════════════════
# Kampanya Konfigürasyonu
# ═══════════════════════════════════════════════════

# --- 🏷️ KAMPANYA BİLGİLERİ ---
kampanya_adi: "ornek-kampanya-2026"
aciklama: "Kısa kampanya açıklaması"
hedef_tip: "influencer"       # influencer | b2b_sirket | ugc_creator | yerel_isletme | topluluk
durum: "draft"                # draft | active | paused | completed

# --- 🎯 HEDEF KİTLE (ICP) ---
icp:
  platform: ["instagram"]     # instagram | tiktok | youtube | linkedin | google_maps | skool
  bolge: "Türkiye"
  dil: ["TR"]
  
  # Influencer / Creator parametreleri
  minimum_takipci: 10000
  maksimum_takipci: 5000000
  nis: []                     # ["lifestyle", "teknoloji", "eğlence"]
  icerik_dili: ["TR"]
  
  # B2B parametreleri (hedef_tip: b2b_sirket ise)
  sirket_buyuklugu: ""        # "10-500" çalışan
  hedef_pozisyonlar: []       # ["CEO", "CTO", "Marketing Director"]
  sektor: []                  # ["SaaS", "E-ticaret"]
  
# --- 🔍 ARAMA KRİTERLERİ ---
arama:
  anahtar_kelimeler: []       # ["etkinlik istanbul", "festival türkiye"]
  hashtag_listesi: []         # ["#istanbuletkinlik", "#festivalturkiye"]
  rakip_hesaplar: []          # ["@rakip1", "@rakip2"] → takipçilerini tara
  max_lead_sayisi: 100

# --- 📧 OUTREACH AYARLARI ---
outreach:
  gonderen_email: ""          # Kampanya gönderen adresi
  sablon_dili: "TR"           # TR | EN | IT
  sablon_dosyasi: ""          # templates/email-tr.md (boşsa otomatik seçilir)
  deger_onerisi: ""           # Kampanyaya özel değer önerisi
  cta: ""                     # Eylem çağrısı metni
  dry_run: true               # İlk çalıştırmada true → onay sonrası false yap

# --- ⏱️ SEQUENCE AYARLARI ---
sequence:
  profil: "influencer"        # saas | eticaret | kurumsal | ajans | influencer | ugc | ozel
  toplam_adim: 3
  bekleme_suresi_acilmadi: 5  # gün
  bekleme_suresi_cevaplanmadi: 3  # gün
  gunluk_gonderim_limiti: 50
  gonderim_araligi: 5         # dakika
  gonderim_saatleri: "09:00-17:00"
  gonderim_gunleri: ["Pzt", "Sal", "Car", "Per", "Cum"]
  saat_dilimi: "UTC+3"

# --- 📁 DOSYA YOLLARI ---
dosyalar:
  ham_cikti: "data/{kampanya_adi}_raw.json"
  zenginlestirilmis: "data/{kampanya_adi}_enriched.json"
  mesajlar: "data/{kampanya_adi}_messages.json"
  log: "data/{kampanya_adi}_log.csv"
  takip: "data/{kampanya_adi}_takip.csv"
```

---

## 📊 Çıktı Formatı

### Lead Veri Standardı (JSON)

Her lead aşağıdaki yapıda saklanır (B2B_Outreach + Buğra + Instagram İş Birliği Scraper birleşik format):

```json
{
  "lead_id": "benzersiz_uuid",
  "kampanya_id": "kampanya-adi-2026",
  
  "kisi": {
    "ad": "",
    "soyad": "",
    "kullanici_adi": "",
    "platform": "instagram",
    "profil_url": "",
    "bio": ""
  },
  
  "iletisim": {
    "email": "",
    "email_kaynagi": "bio | website | hunter | apollo",
    "email_dogrulama": "deliverable | risky | undeliverable",
    "telefon": "",
    "linkedin": "",
    "website": ""
  },
  
  "metrikler": {
    "takipci_sayisi": 0,
    "icerik_sayisi": 0,
    "etkilesim_orani": 0.0,
    "dil": "TR",
    "bolge": "Türkiye"
  },
  
  "sirket": {
    "ad": "",
    "sektor": "",
    "buyukluk": "",
    "website": "",
    "pozisyon": ""
  },
  
  "enrichment": {
    "teknoloji_stacki": [],
    "son_haberler": [],
    "funding_bilgisi": "",
    "buyume_sinyalleri": []
  },
  
  "sequence_durumu": {
    "mevcut_adim": 0,
    "son_gonderim_tarihi": "",
    "mail_acildi": false,
    "mail_cevaplandi": false,
    "cevap_tipi": "",
    "sonraki_aksiyon_tarihi": "",
    "durum": "pending"
  }
}
```

### Takip Listesi CSV Standardı

Tüm kampanyaların çıktıları şu standart sütunları kullanır:

| Sütun | Açıklama | Tip |
|-------|----------|-----|
| `lead_id` | Benzersiz ID | string |
| `ad` | Ad soyad / kullanıcı adı | string |
| `platform` | Instagram / TikTok / LinkedIn / Web | string |
| `profil_url` | Profil linki | url |
| `takipci` | Takipçi sayısı | integer |
| `email` | Bulunan e-posta | string |
| `email_kaynagi` | Bio / Website / Hunter / Apollo | string |
| `sirket` | Şirket/marka adı (varsa) | string |
| `pozisyon` | Unvan (varsa) | string |
| `outreach_status` | Pending / Sent / Failed / No Email | string |
| `outreach_date` | Gönderim tarihi | datetime |
| `sequence_adim` | Kaçıncı mail | integer |
| `acildi_mi` | Evet / Hayır | boolean |
| `cevaplandi_mi` | Evet / Hayır | boolean |
| `cevap_tipi` | Olumlu / Olumsuz / Soru / OOO / Bounce | string |
| `notlar` | Serbest not alanı | string |

---

## ❌ Hata Senaryoları ve Fallback'ler

### Lead Bulma Hataları

| Hata | Çözüm |
|------|-------|
| Apify `402 Payment Required` | `_knowledge/api-anahtarlari.md`'den yedek Apify hesabına geç. Yoksa kullanıcıya bildir. |
| Apify aktör 0 sonuç döndü | Arama parametrelerini genişlet (keyword'leri azalt, bölgeyi genişlet). Aktörün input şemasını kontrol et. |
| `contact-info-scraper` çok yavaş | `maxDepth` ve `maxPagesPerDomain` limitlerini düşür. |
| Hunter.io limit doldu | Apollo.io'ya geç (otomatik fallback). |
| Apollo.io limit doldu | Kullanıcıya bildir, ertesi güne ertele. |

### Email Gönderim Hataları

| Hata | Çözüm |
|------|-------|
| `invalid_grant` / Token hatası | `token.json` sil, scripti terminalde 1 kez çalıştır (tarayıcı onay). |
| `quota_exceeded` / Gmail limiti | Kampanyayı pausa al, kalanlar `Pending` kalır. Ertesi gün devam et. |
| Boş e-posta adresi | `Outreach_Status: "No Email"` yaz, atla. |
| Bounce (geri dönen mail) | E-postayı geçersiz işaretle, lead'i listeden çıkar. |
| Bounce oranı > %2 | 🚨 GÖNDERİMİ DURDUR. Listeyi temizle, email doğrulamasını tekrarla. |

### Genel Fallback Stratejisi

```
Her adımda hata → Logla → Sonraki lead'e geç → Kampanya sonunda özet rapor ver

Kritik hata (API tamamen erişilemez) → Kampanyayı durdur → Kullanıcıya bildir
                                     → Kalan lead'ler "Pending" kalır
                                     → Kaldığı yerden devam edilebilir
```

---

## 📁 Agent Dosya Yapısı

```
_agents/musteri-kazanim/
├── AGENT.md                         ← Bu dosya (ana yönerge — orkestrasyon mantığı)
├── config/
│   ├── ornek-kampanya.yaml          ← Yeni kampanyalar için şablon
│   ├── bugra-influencer.yaml        ← Buğra etkinlik influencer config
│   ├── sweatcoin-outreach.yaml      ← Sweatcoin marka iş birliği config
│   ├── creative-sourcing.yaml       ← İtalyan UGC creator config
│   └── marka-isbirligi.yaml         ← Marka İş Birliği kampanya config
├── templates/
│   ├── email-tr.md                  ← Türkçe email şablonları
│   ├── email-en.md                  ← İngilizce email şablonları
│   └── sequence-profilleri.md       ← Sektöre göre sequence konfigürasyonları
├── data/                            ← Kampanya çıktıları (gitignore'da)
│   └── .gitkeep
└── scripts/
    ├── kampanya_baslat.py           ← Lead bulma + email toplama (birleşik)
    ├── outreach_gonder.py           ← Kişiselleştirme + gönderim
    └── takip_guncelle.py            ← Sequence takip + güncelleme
```

---

## 🚀 Kullanım — Hızlı Başlangıç

### Yeni Kampanya Oluştur

```
1. config/ornek-kampanya.yaml dosyasını kopyala
2. Kampanya parametrelerini doldur (ICP, platform, dil, bölge)
3. Şu komutla agent'ı çalıştır:
   → "/lead-toplama" ile lead topla
   → "/mail-gonder" ile mail at
```

### Mevcut Kampanyayı Devam Ettir

```
1. Var olan config YAML'ını aç
2. durum: "active" olduğundan emin ol
3. data/ altındaki log CSV'sine bak — "Pending" olanlar otomatik devam eder
```

---

## 🔗 İlişkili Kaynaklar

| Kaynak | Yol | Açıklama |
|--------|-----|----------|
| Lead Generation Skill | `_skills/lead-generation/SKILL.md` | Apify aktör kataloğu ve pipeline'lar |
| Outreach Skill | `_skills/eposta-gonderim/SKILL.md` | Gmail API gönderim motoru |
| Lead Toplama Workflow | `_agents/workflows/lead-toplama.md` | Bağımsız kullanılabilir workflow |
| Outreach Workflow | `_agents/workflows/mail-gonder.md` | Bağımsız kullanılabilir workflow |
| Marka Outreach Workflow | `_agents/workflows/marka-outreach.md` | Marka iş birliği özel pipeline |
| API Anahtarları | `_knowledge/api-anahtarlari.md` | Tüm servis credential'ları |

### Referans Projeler (Öğrenim Kaynağı)

| Proje | Ne Öğrenildi |
|-------|-------------|
| `Projeler/Bugra_Influencer_Kampanya/` | 4 adımlı pipeline yapısı, config.py formatı, takip CSV sütunları |
| `Projeler/Marka_Is_Birligi/` | ✅ **AKTİF** — Marka iş birliği outreach, HTML şablonlu mail, kişiselleştirilmiş kampanya |
| `Projeler/_arsiv/B2B_Outreach/` | 3 katmanlı mimari, ICP tanımı, sequence dallanma mantığı, lead JSON şeması |
| `Projeler/_arsiv/Instagram_İş_Birliği_Scraper/` | Contact bulma waterfall'u (Hunter → Apollo), DM/Email şablonları, false positive filtreleme |
| `Projeler/_arsiv/Creative_Sourcing_Italy/` | Çok dilli outreach, UGC creator parametreleri |
| `Projeler/_arsiv/Swc_Insta_Scrape/` | Apify scraper entegrasyonu, batch profil toplama |

---

## ⚠️ Güvenlik & Kurallar

1. **API anahtarları HARDCODE EDİLMEZ** — Her zaman `_knowledge/api-anahtarlari.md` veya env variable kullan
2. **Spam yapma** — Her mail gerçek değer sunmalı, kişiselleştirme yüzeysel olmamalı
3. **SPF/DKIM/DMARC** — Gönderim domain'inin email authentication kayıtları doğru olmalı
4. **Günlük limit** — İlk 2 hafta 20/gün ile warm-up yap, kademeli artır
5. **Bounce takibi** — %2'yi geçerse gönderimi durdur
6. **Unsubscribe** — Her mailde çıkış seçeneği olmalı
7. **Veri gizliliği** — Toplanan kişisel veriler sadece kampanya amacıyla kullanılır
