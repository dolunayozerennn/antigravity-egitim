# Web Site Satış Otomasyonu — Uygulama Planı (v2)

Bu belge, lokal işletmeleri analiz ederek onlara otonom şekilde web siteleri üreten ve pazarlama sürecini başlatan mimarinin eksiksiz ve son halidir. v1'deki muğlak noktalar somutlaştırılmış; chatleşmede kararlaştırılmış fakat plana girmemiş detaylar dahil edilmiştir.

---

## 0. Ön Koşullar ve Konfigürasyon

### Notion Kokpit
**Ana kokpit sayfası:** https://www.notion.so/Website-Sat-Otomasyonu-349955140a3280b582c5ca93633b15a4

Bu sayfa altında iki veritabanı oluşturulacak:
- **Lead Onay DB** (ana veritabanı — tüm işletme adayları burada)
- **Sistem Logları DB** (modül çıktıları, hatalar, retry olayları)

Veritabanı şemaları inşa sırasında, gerçek veri akışı netleştikçe Notion MCP üzerinden oluşturulur.

### Ortam Değişkenleri (.env)
- `APIFY_API_KEY_1` — birincil key
- `APIFY_API_KEY_2` — fail-over key (quota hatasında otomatik geçiş)
- `NOTION_TOKEN`
- `NETLIFY_TOKEN`
- `GOOGLE_WORKSPACE_CREDS` — Gmail gönderimi için
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — sıcak bildirimler için
- `GEMINI_API_KEY` (veya `GROQ_API_KEY`) — LLM skorlama + Vision analizi için
- `AJANS_DOMAIN` — demo subdomain'lerinin ana domain'i

### Ajans Domain Stratejisi
Demolar `{isletme-slug}.demo.{AJANS_DOMAIN}` formatında yayınlanacak (örn: `acme-cafe.demo.ajans.com`). Netlify üzerinde wildcard subdomain (`*.demo.AJANS_DOMAIN`) tanımlanır; DNS'te CNAME record Netlify hedefine yönlendirilir. Ana domain seçimi kullanıcı tarafından yapılır (mevcut bir domain'in alt kırılımı veya ayrı ajans domain'i olabilir).

---

## 1. Sistem ve Onay Mekanizması

**Onay Kokpiti (Notion Entegrasyonu):**
Tüm iş akışı yukarıdaki Notion sayfasındaki Lead Onay DB üzerinden yürür. Aday havuzu buraya düşer. Sen onay ("Üret") kutucuğunu işaretlemeden hiçbir üretim veya deploy maliyeti yaşanmaz. Tüm süreç "Human-in-the-Loop" (İnsan Onaylı) olarak kurgulanmıştır.

**Hedef Kitle ve Sektör Dağılımı:**
Sektör kısıtlaması yoktur (bütçesi olan lokal işletmeler asıl hedeftir). İki tür profile yaklaşılır:
1. Hiç web sitesi olmayanlar.
2. Web sitesi olan fakat 10 yıllık, mobil uyumsuz veya kötü tasarımlı sitesi olanlar.

**Sistem Loglaması:**
Oluşan durumlar, hatalar, başarı oranları Supabase yerine Notion'da kurulacak "Sistem Logları" tablosuna aktarılır. Her şey tek ekrandan takip edilir.

---

## 2. Mimari Modüller (3 Faz)

### FAZ 1: Veri Toplama, Analiz ve Filtreleme (Lead Generation)
**Hedef:** Güçlü adayları bulmak ve mevcut durumlarını (sitelerini) yapay zekayla analiz etmek.

**`[NEW] src/1_lead_generator.py`**

**Apify Konfigürasyonu (Türkiye Lokal):**
Türkiye'deki lokal işletmeler hedef alındığı için `run_input` Türkiye bağlamına uyarlanır:

```python
run_input = {
    "language": "tr",
    "countryCode": "TR",
    "locationQuery": "İzmir, Turkey",          # dinamik, kullanıcı parametresi
    "searchStringsArray": [...],               # hedef sektör(ler)
    "skipClosedPlaces": True,                  # kapalı işletmeleri en başta ele
    "website": "allPlaces",                    # sitesi olan/olmayan herkes
    "scrapePlaceDetailPage": True,             # detay sayfa (iletişim için kritik)
    "scrapeContacts": True,                    # e-mail çekimi
    "scrapeSocialMediaProfiles": {
        "instagrams": True                     # e-mail yoksa IG'den tarama
    },
    "maxReviews": 10,                          # LLM gelir potansiyeli için
    "reviewsSort": "newest",
    "placeMinimumStars": "3.5",                # taban eşiği
}
```

**API Key Fail-over:**
Birincil key `Monthly usage hard limit exceeded` hatası verdiğinde sistem otomatik olarak `APIFY_API_KEY_2`'ye geçiş yapar. Her iki key de bittiyse o günün operasyonu durdurulur ve Telegram bildirimi gönderilir.

**İletişim Enrichment Stratejisi:**
- Web sitesinde e-posta yoksa Instagram bio/iletişim alanlarından taranır.
- Ne web sitesi ne Instagram'da e-mail varsa, işletme `Manuel İletişim Bekliyor` statüsüne geçer (telefon varsa senin elle arayabilmen için).

**Lead Scoring Formülü:**

```
Skor = 
  min(yorum_sayısı / 100, 1) × 25      # max 25 puan — müşteri yoğunluğu
  + max(0, (yıldız - 3)) × 15          # 3 yıldız = 0, 5 yıldız = 30
  + fiyat_skalası_puanı                # $ = 10, $$ = 20, $$$ = 30
  + llm_gelir_potansiyeli × 1.5        # 1-10 LLM skoru → 1.5-15

Toplam: 0-100 aralığı
```

**Eşikler:**
- **< 50:** Otomatik elenir, Notion'a bile düşmez.
- **50-69:** "Düşük Öncelik" etiketiyle Notion'a düşer.
- **≥ 70:** "Yüksek Öncelik" etiketiyle Notion'a düşer.

**LLM Gelir Potansiyeli Skoru (1-10):**
İşletmenin son 10 yorumu + kategori + fiyat skalası bilgisi LLM'e (Gemini Flash / Groq) gönderilir.

Prompt özeti:
> "Aşağıdaki işletme verisi ve müşteri yorumlarına bakarak, bu işletmenin web sitesi hizmeti satın alabilecek bütçeye sahip olma ihtimalini 1-10 arası puanla. Yorum yoğunluğu, müşteri profili, hizmet kalitesi ve işletmenin ciddiyetine bak. Sadece sayı döndür."

**"Zayıf Site" Tespit Mekanizması:**
Mevcut sitesi olan işletmeler için aşağıdaki sinyaller toplanır. **3+ sinyal** tetiklenirse "Zayıf Site" olarak işaretlenir:

1. Lighthouse Performance skoru < 50
2. Lighthouse Mobile Friendly testi fail
3. SSL sertifikası yok / süresi geçmiş
4. Son içerik güncellemesi > 2 yıl (footer © yılı kontrolü + sayfa HTML'deki tarih izleri)
5. Sayfa yüklenmiyor veya 5 saniyeden uzun sürüyor
6. Eski framework tespiti (jQuery 1.x, Flash, Bootstrap 3 veya altı)
7. **Vision Model Final Kararı:** Sitenin tam ekran görüntüsü Gemini Vision'a gönderilir. Prompt: *"Bu site 2020 sonrası tasarım standardında mı? Mobil responsive mi? Profesyonel mi görünüyor? Her birine Evet/Hayır ver ve genel kalite skorunu 1-10 arası belirt."* Skor < 5 ise bu tek başına bir sinyal sayılır.

Süzülmüş ve skorlanmış veriler Notion Lead Onay DB'sine eklenir, `Onay Bekliyor` statüsüne geçer.

---

### FAZ 2: Bilgi Derleme ve Otonom Üretim (Akıllı Şablon Manipülasyonu)
**Hedef:** Açık kaynak modern şablonlardan en uygununu bulup, saniyeler içinde demo siteyi hazırlamak.

**`[NEW] src/2_site_builder.py`**

Notion'dan `Üret` onayı alındığı an tetiklenir.

**Idempotency Kontrolü:**
Her lead `place_id` (Google Maps'in unique identifier'ı) ile kaydedilir. Aynı `place_id` zaten Notion'da varsa:
- Yeni kayıt eklenmez.
- Sadece `Son Güncelleme` tarihi refresh edilir.
- Site tekrar üretilmez (yanlışlıkla çift deploy önlenir).

**Otonom Şablon Seçimi:**
Kategori → şablon mapping'i basit bir Python dict'i olarak tutulur. İlk üç sektör önerisi:

| Kategori | Şablon Tipi |
|----------|-------------|
| `food` (restoran, kafe, pastane) | modern foodie — sıcak tonlar, menü odaklı |
| `beauty` (güzellik salonu, berber, kuaför) | elegant/minimal — görsel galeri ağırlıklı |
| `clinic` (diş, estetik, medikal) | clean medical — güven odaklı, randevu CTA'lı |

Kategori havuzda yoksa fallback "kurumsal genel" şablonu devreye girer. Şablon kütüphanesi GitHub'daki açık kaynak HTML5/Tailwind kaynaklarından derlenecek; inşa sırasında genişletilir.

**Üretim Akışı:**
Seçilen şablonun içerisindeki tüm veriler (firma adı, adres, vizyon, harita, telefon vs.) Python `Jinja2` motoruyla işletmeye özgü hale getirilir ve `dist/` klasörüne statik site olarak basılır (sıfır build süresi).

---

### FAZ 3: Canlıya Alma ve İletişim (Deployment & Outreach)
**Hedef:** Siteyi anında buluta atıp, müşterinin kancayı yutmasını sağlayacak aksiyonu almak.

**`[NEW] src/3_deployment_outreach.py`**

Netlify API ile üretilen `dist/` klasörü `{isletme-slug}.demo.{AJANS_DOMAIN}` önizleme adresinde canlıya alınır.

**URL Tracking + Telegram Sıcak Bildirimi:**
Her demo site bir Netlify Function (veya Cloudflare Worker) arkasında servis edilir. Sayfa ilk yüklendiğinde:
1. Notion'daki ilgili lead'in `Son Tıklanma` alanı güncellenir (timestamp).
2. Telegram bot anında push mesajı gönderir: *"🔥 ACME Cafe demosuna şu an giriş yaptı! Notion kaydı: [link]"*
3. Aynı lead için 1 saat içinde tekrar tıklanma olursa yeni bildirim gönderilmez (spam önleme).

Bu sıcak anda sen manuel satış iletişimine geçersin. Bu, projenin en yüksek conversion potansiyeli olan tetikleyicisidir.

**Mail Gönderim Akışı:**
- **Eğer E-Posta Varsa:** İşletmenin e-postasına, içerisinde üretilen sitenin test linki bulunan yüksek kişiselleştirilmiş bir mail (Google Workspace MCP ile) atılır.
- **Eğer Sadece Telefon Varsa:** Sistem otomasyon sekteye uğramasın diye Notion'da `Manuel İletişim Bekliyor` statüsüne alır. Senin manuel teyidin (örn: arayarak veya WhatsApp ile URL atarak) ile süreç devam eder.

**Mail Gönderim Limiti:**
Sistem günde maksimum **50 mail** gönderir. Bu limite ulaşıldığında artan lead'ler ertesi güne kuyruğa alınır. Kişiselleştirilmiş ve demo linki içeren mailler spam riskini minimize eder, ancak muhafazakâr limit sender reputation koruması için uygulanır.

**Follow-up (Takip) Maili:**
İlk mail gönderildikten **5 gün sonra** şu iki koşul birlikte sağlanıyorsa sistem otomatik tek bir takip maili atar:
- Müşteri cevap vermedi.
- URL tracking kaydı yok (demo linki hiç tıklanmadı).

Takip maili kısa, özgün ve değer vurgulu olur (örn: *"Geçen hafta hazırladığım demo hâlâ {URL} üzerinde canlı. İsterseniz domain'i adınıza geçirip teslim edebilirim."*). 

İkinci bir takip gönderilmez. Bu süreden sonra lead `Soğuk` statüsüne geçer ve manuel kararına bırakılır.

---

## 3. Fiyatlandırma Stratejisi (Dinamik)

Mailde sabit fiyat verilmez; müşterinin skoruna, sektörüne ve şehrine göre dinamik olarak **önerilen paket aralığı** mailin alt kısmında yer alır. Gerçek pazarlık manuel sürdürülür.

**Paket Yapısı:**

| Paket | Fiyat Aralığı | Kapsam |
|-------|---------------|--------|
| **Başlangıç** | 15.000 – 20.000 TL | Tek sayfa, temel bilgi, iletişim formu, mobil uyum |
| **Standart** | 25.000 – 35.000 TL | Multi-page, galeri, iletişim formu, temel SEO, harita, sosyal medya entegrasyonu |
| **Premium** | 45.000 – 70.000 TL | Rezervasyon/randevu entegrasyonu, CMS, sezonsal içerik güncellemesi, ileri SEO, çok dilli |

**Paket Atama Algoritması:**
```
Skor ≥ 85 VE fiyat_skalası == $$$   → Premium önerilir
Skor 70-84                          → Standart önerilir
Skor 50-69                          → Başlangıç önerilir
```

**Sektör Katsayısı (Üst Paket Önerisi):**
Yüksek müşteri değeri olan sektörler bir üst paket kademesine yükseltilir:
- Klinik (diş, estetik, medikal)
- Otel / konaklama
- Hukuk bürosu / muhasebe

Örnek: Skoru 75 olan bir diş kliniği → normalde Standart, sektör katsayısıyla Premium önerilir.

**Şehir Katsayısı:**
- İstanbul, Ankara, İzmir → liste fiyatı.
- Diğer büyükşehirler (Bursa, Antalya, Adana vb.) → %10 indirim.
- Anadolu şehirleri → %15-20 indirim önerilir (mailde otomatik aşağı çekilir).

Bu katsayılar, mailde *"... paketimiz sizin işletme ölçeğinize özel X-Y TL aralığında."* gibi yumuşak bir dille belirtilir.

---

## 4. Hata Yönetimi ve Retry Stratejisi

**Genel Kural:** Hiçbir hata sessiz geçilmez. Her retry ve her nihai fail Notion Log DB'sine yazılır; kritik fail'lerde Telegram bildirimi gönderilir.

**Apify (Faz 1):**
- Quota hatası (`Monthly usage hard limit exceeded`) → `APIFY_API_KEY_2`'ye otomatik fail-over.
- Timeout / ağ hatası → 3 deneme, exponential backoff (5s → 15s → 45s).
- 3. fail sonrası lead `Hata` statüsüyle Notion'a düşer, manuel inceleme için Telegram bildirimi.

**Vision Model / LLM Skorlama (Faz 1):**
- Rate limit → 30 saniye bekle + retry (max 3 deneme).
- Tamamen fail → skor `N/A` olarak işaretlenir, lead `Manuel Değerlendirme` kuyruğuna alınır (otomasyon akışını durdurmaz).

**Jinja2 Üretim / Netlify Deploy (Faz 2-3):**
- Template render hatası → `Üretim Hatası` statüsü, log'a full traceback, Telegram bildirimi.
- Netlify deploy fail → 3 retry, exponential backoff.
- 3. fail sonrası lead `Deploy Hatası` statüsü, stack trace log'a yazılır, Telegram bildirimi.

**Mail Gönderimi (Faz 3):**
- Google Workspace geçici hata → 5 dakika sonra tek retry.
- Kalıcı hata (e-posta reddedildi, kutu dolu vb.) → `Mail Teslim Edilemedi` statüsü, manuel fallback.

**Idempotency Güvencesi:**
Her modül çağrısında `place_id` kontrolü yapılır; retry'lar duplicate kayıt veya çift mail göndermez.

---

## 5. Kapasite Planlaması ve Somut Örnekler

**Günlük Hedef (Başlangıç Fazı):**
- Apify tarama: 1 konum taraması ile günde 200-300 işletme çekilir.
- Lead Scoring eşiği (≥50) sonrası ~60-100 işletme Notion'a düşer.
- Onaylanan ortalama: günde 20-30 işletme (manuel onay kapasiten).
- Üretilen demo site: 20-30.
- Gönderilen mail: günde maksimum 50 (güvenli limit).

**Haftalık Projeksiyon:**
- 5 iş günü × ortalama 25 lead = haftada 125 demo üretimi.
- Follow-up mailleri ek olarak günde ~10-15 eklenir (5. gün kuyruğundan).

**Aylık Operasyon Maliyeti (Tahmini):**

| Kalem | Maliyet |
|-------|---------|
| Apify (aylık ~800 lead × $0.005) | ~$4 |
| LLM skorlama + Vision (lead başı ~$0.002) | ~$1.6 |
| Netlify (Free tier yeterli: 100 GB bandwidth, 2000+ demo kaldırır) | $0 |
| Google Workspace (mevcut) | $0 |
| Telegram / Notion (mevcut) | $0 |
| **Toplam** | **~$6-10 / ay** |

**Ticari Projeksiyon (Muhafazakâr):**
- Haftalık 125 demo × %1-2 conversion = haftada 1-2 satış.
- Ortalama paket 25.000 TL → aylık 100.000-200.000 TL ciro potansiyeli.
- Operasyon maliyetinin yanında marjin son derece yüksek (%99+).

**Netlify Subdomain Kapasitesi:**
Free tier site limiti 500. Bu limit dolarsa satılmamış eski demolar otomatik silme scripti ile temizlenecek (örn: 30 gün tıklanmayan demolar devreden çıkarılır). Bu temizleme mekanizması inşa sırasında 6. faz olarak eklenebilir.

---

## 6. Faz Sıralaması ve Bekleyen Konular

**İnşa Sırası (Önerilen):**
1. Ön koşullar (env, Notion DB şemaları) — 0.5 gün
2. Faz 1 (scraper + scoring + zayıf site analizi) — 2 gün
3. Faz 2 (şablon havuzu + Jinja render) — 2 gün
4. Faz 3 (Netlify deploy + mail + URL tracking + Telegram) — 1.5 gün
5. Follow-up otomasyonu — 0.5 gün
6. Hata yönetimi + log entegrasyonları — paralel

**Bekleyen / İleri Faz Konuları (Bu planın dışında):**
- Satış sonrası teslimat akışı (manuel ilerler, otomatize edilmeyecek).
- Şablon matching algoritmasının AI-powered hali (LLM'le dinamik eşleme).
- Notion DB schema'larının final hali (inşa sırasında netleşir).
- Sistem Log DB schema'sının final hali (inşa sırasında).
- Görsel kaynağı (şablonlara stock image mi AI-generated image mi besleneceği).

---

*(Bu belge v2'dir. Chatleşmede kararlaştırılan stratejik ayrıntılar, lead scoring formülü, zayıf site tanımı, URL tracking, dinamik fiyatlandırma, hata yönetimi ve kapasite planlaması artık dahildir. Yeni bir chat'e referans verilerek doğrudan kodlama aşamasına geçilebilir.)*
