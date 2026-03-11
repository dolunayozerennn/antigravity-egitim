> ⚠️ **Bu proje artık `_agents/musteri-kazanim/` agent'ı tarafından yönetilmektedir.**
> Projenin mantığı, config'leri ve scriptleri agent yapısına taşınmıştır. Bu klasör referans olarak korunmaktadır.

# Antigravity — B2B Lead Generation & Outreach Otomasyon Sistemi

## Proje Tanımı

Bu proje, B2B müşteri adaylarını (lead) bulmak, kişiselleştirilmiş e-postalar hazırlamak ve çok aşamalı bir cold outreach süreci yürütmek için tasarlanmış uçtan uca bir otomasyon sistemidir. Sistem sektör-agnostik çalışır; her kampanya için hedef sektör, ideal müşteri profili (ICP) ve iletişim stratejisi dışarıdan tanımlanır.

---

## Sistem Mimarisi — Üç Katman

### Katman 1: Lead Generation

**Amaç:** Belirlenen ICP'ye uygun şirketleri ve karar vericileri bulmak, doğrulanmış iletişim bilgilerini toplamak.

**Araçlar:**
- **Apollo.io** — Şirket araması, kişi araması, enrichment (zenginleştirme)
- **Hunter.io** — Domain tabanlı e-posta keşfi ve doğrulama (verification)

**Süreç Akışı:**

1. Kampanya başlatılırken aşağıdaki parametreler tanımlanır:
   - Hedef sektör(ler)
   - Şirket büyüklüğü aralığı (çalışan sayısı veya gelir)
   - Hedef pozisyon/unvan (CEO, CTO, Marketing Director vb.)
   - Coğrafi bölge
   - Ek filtreler (teknoloji stack'i, büyüme oranı, funding durumu vb.)

2. Apollo API üzerinden filtrelere uygun şirketler ve kişiler çekilir.

3. Elde edilen e-posta adresleri Hunter.io üzerinden doğrulanır:
   - **deliverable** → lead havuzuna eklenir
   - **risky** → ikincil doğrulama veya düşük öncelikle işlenir
   - **undeliverable** → çıkarılır

4. Her lead için şu veri noktaları toplanır ve saklanır:
   - Ad, soyad
   - E-posta adresi (doğrulanmış)
   - Şirket adı
   - Pozisyon/unvan
   - Şirket sektörü
   - Şirket büyüklüğü
   - Şirket web sitesi
   - LinkedIn profili (varsa)
   - Ek enrichment verileri (teknoloji stack'i, son haberler, funding bilgisi vb.)

**API Kullanım Kuralları:**
- Apollo günlük kredi limitlerini takip et, batch istekleri optimize et.
- Hunter.io verification çağrılarını toplu (bulk) olarak yap — tek tek değil.
- Duplicate kontrolü yap: aynı kişi birden fazla kaynaktan gelebilir.
- Her lead'e benzersiz bir ID ata ve tüm veriyi yapılandırılmış formatta (JSON) sakla.

---

### Katman 2: Kişiselleştirilmiş E-posta İçeriği

**Amaç:** Her lead için, ilham maillerinin tonunu ve yapısını koruyarak kişiselleştirilmiş e-posta içerikleri üretmek.

**Girdiler:**
- İlham mailleri (template'ler) — Dolunay tarafından sağlanır
- Lead verileri (Katman 1 çıktısı)
- Kampanya bağlamı (sektör, teklif, değer önerisi)

**Kişiselleştirme Değişkenleri:**

Her e-postada aşağıdaki değişkenler dinamik olarak doldurulur:
- `{ad}` — Alıcının adı
- `{sirket}` — Alıcının şirketi
- `{pozisyon}` — Alıcının unvanı
- `{sektor_pain_point}` — Sektöre özel acı nokta
- `{deger_onerisi}` — Kampanyaya özel değer önerisi
- `{kanca}` — Kişiye/şirkete özel dikkat çekici açılış (son haberler, büyüme, ödüller vb.)
- `{cta}` — Kampanyaya özel eylem çağrısı

**İçerik Üretim Kuralları:**
- İlham maillerinin genel yapısını, tonunu ve uzunluğunu koru.
- Her mail "elle yazılmış" gibi hissettirmeli — generic veya robotic olmamalı.
- Kanca (`{kanca}`) mümkünse lead'in şirketine özel bilgi içermeli (enrichment verisinden türetilir).
- Konu satırı (subject line) da kişiselleştirilmeli.
- Aynı kampanya içinde birden fazla e-posta varyantı üret (A/B test için).

**Çok Dilli Destek:**
- Varsayılan dil: Kampanya tanımında belirlenir.
- Aynı mail birden fazla dilde üretilebilir (Türkçe, İngilizce vb.).

---

### Katman 3: Cold Outreach & Akıllı Sequence Yönetimi

**Amaç:** Kişiselleştirilmiş e-postaları göndermek ve lead'in davranışına göre dinamik bir iletişim akışı yürütmek.

**Araç:** Gmail API (Dolunay'ın mail hesabı üzerinden gönderim)

**Sequence Mantığı — Genel Çerçeve:**

Her kampanya için bir "sequence" tanımlanır. Sequence, koşullu dallanma mantığı ile çalışır:

```
ADIM 1: İlk Mail Gönderimi
  ├─ Mail AÇILMADI (X gün içinde)
  │   └─ ADIM 2a: Takip maili (farklı konu satırı, aynı değer önerisi)
  │       ├─ Mail AÇILMADI (Y gün içinde)
  │       │   └─ ADIM 3a: Son deneme veya farklı kanal (LinkedIn vb.)
  │       └─ Mail AÇILDI ama CEVAPLANMADI
  │           └─ ADIM 3b: Değer odaklı takip (case study, veri, sosyal kanıt)
  ├─ Mail AÇILDI ama CEVAPLANMADI (Z gün içinde)
  │   └─ ADIM 2b: Farklı açıdan yaklaşım (pain point değişikliği, yeni kanca)
  │       ├─ CEVAPLANMADI
  │       │   └─ ADIM 3c: Break-up mail (son şans, nazik kapanış)
  │       └─ CEVAPLANDI
  │           └─ → Yanıt İşleme Modülü
  └─ Mail CEVAPLANDI
      └─ → Yanıt İşleme Modülü
```

**Yanıt İşleme Modülü:**
- Olumlu yanıt → Toplantı planlama akışına yönlendir, bildirim gönder.
- Olumsuz yanıt (ilgi yok) → Kibarca teşekkür et, lead'i "cold" olarak işaretle.
- Soru/bilgi talebi → İlgili bilgiyi içeren otomatik veya yarı-otomatik yanıt hazırla.
- Otomatik yanıt (OOO, tatil vb.) → Bekleme süresini uzat, sonra yeniden dene.
- Bounce → Lead'i çıkar, e-posta adresini geçersiz olarak işaretle.

**Sequence Parametre Değişkenleri (Kampanya Bazlı):**

| Parametre | Açıklama | Örnek Değer |
|---|---|---|
| `toplam_adim` | Sequence'teki maksimum mail sayısı | 3-5 |
| `bekleme_suresi_acilmadi` | Açılmayan mail sonrası bekleme süresi (gün) | 3-5 |
| `bekleme_suresi_cevaplanmadi` | Açılan ama cevaplanmayan mail sonrası bekleme (gün) | 2-4 |
| `gunluk_gonderim_limiti` | Günlük maksimum gönderim sayısı | 30-50 |
| `gonderim_araligi` | İki mail arası minimum süre (dakika) | 3-10 |
| `gonderim_saatleri` | Gönderim yapılacak saat aralığı | 09:00-17:00 |
| `gonderim_gunleri` | Gönderim yapılacak günler | Pazartesi-Cuma |
| `saat_dilimi` | Alıcının saat dilimine göre gönderim | UTC+3 / dinamik |

**Sektöre Göre Önerilen Sequence Profilleri:**

- **SaaS / Teknoloji:** 4-5 adım, kısa bekleme süreleri (2-3 gün), doğrudan ve değer odaklı ton, case study ağırlıklı.
- **E-ticaret:** 3-4 adım, orta bekleme (3-4 gün), ROI ve metrik odaklı ton, sosyal kanıt ağırlıklı.
- **Kurumsal / Üretim / Sanayi:** 3 adım, uzun bekleme (5-7 gün), formal ton, güven ve referans ağırlıklı.
- **Ajans / Hizmet Sektörü:** 4 adım, kısa-orta bekleme (2-4 gün), yaratıcı ton, portfolio ve sonuç ağırlıklı.
- **Özel / Niş:** Kampanya bazlı özel konfigürasyon.

Bu profiller başlangıç noktasıdır; her kampanya için özelleştirilebilir.

---

## E-posta Sağlık ve Teslim Edilebilirlik Kuralları

- Günlük gönderim limitini aşma (yeni hesaplar için 20/gün ile başla, kademeli artır).
- Her mailde unsubscribe seçeneği bulundur.
- Bounce oranını %2'nin altında tut — yükselirse gönderimi durdur ve listeyi temizle.
- Spam tetikleyici kelimelerden kaçın (ücretsiz, garanti, hemen, sınırlı süre vb.).
- SPF, DKIM ve DMARC kayıtlarının doğru yapılandırıldığından emin ol.
- Warm-up süreci: Yeni bir sending domain/hesap kullanılıyorsa, ilk 2 hafta düşük hacimle başla.

---

## Kampanya Başlatma Kontrol Listesi

Yeni bir kampanya oluşturulurken aşağıdaki bilgiler tanımlanmalıdır:

1. **Kampanya adı ve açıklaması**
2. **Hedef sektör ve ICP tanımı** (şirket büyüklüğü, pozisyon, bölge, ek filtreler)
3. **Değer önerisi** — Ne sunuyoruz? Neden şimdi?
4. **İlham mailleri** — En az 1 ana template, ideal olarak her sequence adımı için ayrı template
5. **Sequence konfigürasyonu** — Adım sayısı, bekleme süreleri, dallanma kuralları
6. **Gönderim parametreleri** — Günlük limit, saat aralığı, günler
7. **Dil** — Kampanya dili
8. **Başarı metrikleri** — Hedef open rate, reply rate, meeting rate

---

## Veri Yapısı — Lead Kaydı (Referans)

```json
{
  "lead_id": "benzersiz_id",
  "ad": "",
  "soyad": "",
  "email": "",
  "email_dogrulama_durumu": "deliverable | risky | undeliverable",
  "sirket": "",
  "pozisyon": "",
  "sektor": "",
  "sirket_buyuklugu": "",
  "website": "",
  "linkedin": "",
  "ulke": "",
  "sehir": "",
  "enrichment": {
    "teknoloji_stacki": [],
    "son_haberler": [],
    "funding_bilgisi": "",
    "buyume_sinyalleri": []
  },
  "kampanya_id": "",
  "sequence_durumu": {
    "mevcut_adim": 1,
    "son_gonderim_tarihi": "",
    "mail_acildi": false,
    "mail_cevaplandi": false,
    "cevap_tipi": "olumlu | olumsuz | soru | ooo | bounce | yok",
    "sonraki_aksiyon_tarihi": ""
  }
}
```

---

## Önemli Notlar

- Bu sistem bir "spam makinesi" değildir. Her mail, alıcıya gerçek değer sunmalıdır.
- Kişiselleştirme yüzeysel olmamalıdır — sadece isim yazmak yetmez, şirketin bağlamını anlamak gerekir.
- Sequence kararları veriye dayalı olmalıdır. Açılma/cevaplama oranları düşükse, içerik ve strateji revize edilmelidir.
- Sistem modülerdir: her katman bağımsız çalışabilir ve ayrı ayrı geliştirilebilir.
- Yeni sektörler veya müşteri tipleri eklendiğinde, sadece kampanya konfigürasyonu değişir; sistem altyapısı sabit kalır.
