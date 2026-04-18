# Çalışma Kuralları ve Tercihler

Bu dosya, Antigravity ile çalışırken birikmesi gereken kişisel tercihlerini ve kuralları içerir.
**Son güncelleme:** 29 Mart 2026

---

## Genel Çalışma Tarzı

- **Dil:** Türkçe konuşuyorum, kod ve teknik dosyalar İngilizce olabilir
- **Proje Dizini:** Tüm projeler `/Users/dolunayozeren/Desktop/Antigravity/Projeler/` altında
- **Kısa ve Net İletişim (KIRMIZI ÇİZGİ):** ASLA uzun metinler veya destanlar yazma. En fazla 1-2 cümlelik bullet point'ler (madde imleri) kullan. "Okumadım, kısalt" uyarısı dikkate alınarak tüm cevaplar ultrashort (çok kısa) tutulmalıdır.

## Proje Yapısı

```
Antigravity/
├── _agents/              → Agent'lar ve Workflow'lar
│   ├── musteri-kazanim/  → Lead + Outreach orkestratörü
│   ├── icerik-uretim/    → İçerik pipeline orkestratörü
│   ├── yayinla-paylas/    → Deploy + Export orkestratörü
│   └── workflows/        → Slash command workflow'ları
├── _skills/              → Kalıcı yetkinlikler (skill'ler)
├── _knowledge/           → Bu klasör (manuel hafıza)
│   └── credentials/      → 🔐 Merkezi şifre/token deposu
├── Projeler/             → Tüm proje klasörleri
└── Paylasima_Hazir/      → Dışarıyla paylaşıma hazırlanan proje ve skill paketleri
```

## Aktif Projeler
*(Son güncelleme: 23 Mart 2026)*

| Proje | Açıklama | Durum |
|---|---|---|
| Lead_Pipeline | Birleşik CRM + bildirim pipeline | Railway Cron (10dk) |
| Dolunay_AI_Website | dolunay.ai kişisel web sitesi | Netlify |
| Shorts_Demo_Otomasyonu | Telegram video demo botu | Railway 7/24 Worker |
| Swc_Email_Responder | Sweatcoin e-posta otomasyonu | Railway Cron (Pzt-Cum) |
| Dolunay_Reels_Kapak | AI kapak görseli üretimi | Railway Cron (günde 3x) |
| Isbirligi_Tahsilat_Takip | Tahsilat hatırlatma otomasyonu | Railway Cron (günde 1x) |
| Akilli_Watchdog | LLM-destekli pipeline sağlık izleme | Railway Cron (günde 1x) |
| Marka_Is_Birligi | Marka outreach + follow-up | Railway Cron (zamanlanmış) |
| Blog_Yazici | YouTube → Blog pipeline | Lokal (geliştirme) |
| Dolunay_YouTube_Kapak | YouTube thumbnail üretimi | Lokal (geliştirme) |
| Dubai_Emlak_İçerik_Yazarı | İçerik üretim sistemi | Lokal (geliştirme) |
| Emlak_Arazi_Drone_Çekim | Drone çekim video pipeline'ı | Lokal (aktif) — `/drone-cekim` |

## 🌐 Eğitim Görselleri ve Netlify Yayını (OTOMATİK)
> **Antigravity eğitim görsellerinde (`_skills/egitim-gorselleri`) bir revize yapılıp kullanıcı tarafından onaylandığında, bu klasör MUTLAKA anında Netlify üzerinde yayınlanır (Deploy edilir).**

- **Kapsam Sınırı:** SADECE `_skills/egitim-gorselleri` klasöründeki eğitim/metafor dosyaları bu kurala tabiidir. Başka konularda üretilen deneme veya dış web projeleri bu ortamda YAYINLANMAZ.
- **Hedef Netlify Sitesi:** `antigravity-egitim.netlify.app` (siteId: `32957d5f-9458-4a70-ad6b-41d17771b296`)
- **Yöntem:** GitHub (Mono-Repo) üzerinden push edilmeli VEYA anında `mcp_netlify_netlify-deploy-services-updater` aracıyla (operation: `deploy-site`, folder: `_skills/egitim-gorselleri`) deploy tetiklenmelidir. Değişiklik onaylanınca aksiyon almak zorunludur.

## 🔐 Şifre/Token Yönetim Kuralları (OTOMATİK)

Bu kurallar her proje oluşturma/düzenleme sırasında **otomatik olarak** uygulanır:

### Otomatik Tetikleme
- ✅ Yeni proje oluşturulduğunda → `sifre-yonetici` skill'ini oku ve çalıştır
- ✅ Bir projeye API kullanan kod eklendiğinde → ihtiyaç analizi yap
- ✅ Kullanıcı yeni API/token verdiğinde → önce `master.env`'e ekle, sonra projelere dağıt
- ✅ Deploy öncesinde → `.env` ve Service Account bağlantılarını doğrula

### 📁 Proje Değişikliği Kuralları (OTOMATİK)

Yeni proje oluşturulduğunda, arşive taşındığında veya silindiğinde şu dosyalar **mutlaka** güncellenir:

1. **Bu dosyadaki Aktif Projeler tablosu** → `_knowledge/calisma-kurallari.md`
2. **Deploy registry** → `_knowledge/deploy-registry.md` (Railway/cron varsa)
3. **Skills README** → `_skills/README.md` (yeni skill oluşturulduysa)
4. **API anahtarları** → `_knowledge/api-anahtarlari.md` + `master.env` (yeni servis eklendiyse)

### Merkezi Depo
- **Tokenlar:** `_knowledge/credentials/master.env`
- **Google Service Account:** `_knowledge/credentials/google-service-account.json`
- **OAuth Dosyaları:** `_knowledge/credentials/oauth/`
- **Skill:** `_skills/sifre-yonetici/SKILL.md`
- **Workflow:** `/sifre-bagla`

### Token Güncellemesi
Kullanıcı yeni bir token verdiğinde:
1. `master.env`'deki ilgili satırı güncelle
2. `_knowledge/api-anahtarlari.md`'yi senkronize et
3. Etkilenen projeleri bildir

## 📋 Notion Workspace Yapısı (Mart 2026+)

İki ayrı Notion workspace kullanılıyor:

| Workspace | İçerik | Token (`master.env`) | Kullanan Projeler |
|---|---|---|---|
| **Ana (Eski)** | Tele Satış CRM, Genel | `NOTION_API_TOKEN` | Tele_Satis_CRM, Akilli_Watchdog |
| **Sosyal Medya İşbirlikleri (Yeni)** | Reels DB, YouTube DB, Ceren sayfası | `NOTION_SOCIAL_TOKEN` | Dolunay_Reels_Kapak, Isbirligi_Tahsilat_Takip |

**Kural:** "Ceren", "Video İçerik Akışları", "YouTube İçerik Akışları" veya sosyal medya işbirliklerinden bahsedildiğinde → **HER ZAMAN** yeni workspace + `NOTION_SOCIAL_TOKEN` kullanılır.

**Yeni Workspace Sayfaları:**
- Ceren: `5cb95514-0a32-8245-a1b7-81309d9b2587`
- Video İçerik Akışları: `03895514-0a32-83aa-bf77-810b495fdfe7`
- YouTube İçerik Akışları: `1bb95514-0a32-8392-9730-010408018ac1`

**Yeni Workspace DB'leri:**
- Dolunay Reels DB: `27b95514-0a32-8385-89eb-813222d532a2`
- Dolunay YouTube DB: `5bb95514-0a32-821f-98cc-81605e4a971f`

### ⚠️ Notion MCP Erişim Kuralı (ZORUNLU — Mart 2026+)

> **Notion MCP (`notion-mcp-server`) sadece "antigravity" entegrasyonuyla paylaşılmış sayfalara erişebilir.**

**Notion'a erişimde 404 alındığında:**
1. Önce `API-get-self` ile bağlantı sağlığını doğrula
2. `API-post-search` ile sayfayı ada göre arat
3. Sonuç boşsa → kullanıcıya "Bu sayfayı Notion'da antigravity entegrasyonuyla paylaşman gerekiyor" de
4. Detaylı adımlar: `_knowledge/hatalar-ve-cozumler.md` → "Notion MCP — Sayfa/Veritabanı 404 Hatası"

**Yeni bir Notion sayfasına ilk erişimde:**
- Doğrudan ID ile erişmeye çalışma → önce `API-post-search` ile var mı kontrol et
- Yoksa paylaşım eksik demektir → kullanıcıyı bilgilendir

**MCP'nin görebildiği veritabanları (doğrulanmış envanter):**

| Veritabanı | ID | Workspace |
|---|---|---|
| AI Factory Satış Leads | `31226924-bb82-800e-9ada-d6f16399eba0` | Ana (MCP erişilebilir ✅) |
| Dolunay Reels | `6567657a-241c-48b0-8ee4-6a0d6836f34a` | Ana (MCP erişilebilir ✅) |
| Dolunay YouTube | `23d26924-bb82-8059-a439-d012a877e9c1` | Ana (MCP erişilebilir ✅) |
| Antigravity Operations Log | `33095514-0a32-81b4-858a-ff81a77b6d48` | Ana (MCP erişilebilir ✅) |
| Dolunay Reels DB (Sosyal) | `27b95514-0a32-8385-89eb-813222d532a2` | Sosyal (❌ MCP göremez, `NOTION_SOCIAL_TOKEN` kullan) |
| Dolunay YouTube DB (Sosyal) | `5bb95514-0a32-821f-98cc-81605e4a971f` | Sosyal (❌ MCP göremez, `NOTION_SOCIAL_TOKEN` kullan) |

> **Bu tablo güncellenmeli:** Yeni bir Notion DB oluşturulduğunda veya paylaşıldığında buraya ekle.

## 🌐 Dolunay_AI_Website — i18n Zorunlu Kurallar (Mart 2026+)

> **Bu sitede HERHANGİ bir metin değişikliği yapıldığında 4 dil dosyası güncellenir ve tarayıcıda test edilir.**

- **Diller:** Türkçe (`tr`), İngilizce (`en`), Çince (`zh`), İspanyolca (`es`)
- **Locale dosyaları:** `src/i18n/locales/{tr,en,zh,es}.json`
- **Kullanıcı sadece Türkçe denetler** — Antigravity diğer 3 dili kendisi doğrular
- **Yeni component eklendiğinde:** Tüm text `t()` ile sarmalanır, 4 locale'e key eklenir
- **Metin değiştiğinde:** Önce `tr.json`, sonra `en.json`, `zh.json`, `es.json` güncellenir
- **Tarayıcı testi:** 4 dilde de sayfalar kontrol edilir (browser_subagent ile)

### i18n Dosya Haritası
| Component | JSON Key Prefix |
|---|---|
| Navbar, Footer | `nav.*`, `footer.*` |
| HeroSectionElevate | `hero.*` |
| ProductsSection | `products.*` |
| ServicesSection | `services.*` |
| SolutionsPage | `solutions.*` |
| AboutPage | `about.*` |
| AIFactoryPage | `aiFactory.*` |
| CollaborationsPage | `collaborations.*` |
| CorporateTrainingsPage | `corporateTrainings.*` |

## Tekrarlayan Talepler

- *(Burası zamanla dolacak — önemli kararlar ve tercihler eklenecek)*

## Kesinlikle Yapılmaması Gerekenler

- API anahtarlarını hardcode etme — her zaman `master.env` veya env variable kullan
- Skill dosyalarını gereksiz yere değiştirme — skill'ler atomik ve kararlıdır
- `_knowledge/credentials/` klasöründeki dosyaları GitHub'a push etme
- Google Service Account JSON dosyasını kod içine gömme
- **Kod sağlık kontrolü yapmadan GitHub'a push etme** — import testi + testler ZORUNLU
- **Smoke test yapmadan deploy'u tamamlanmış sayma** — deploy sonrası log kontrolü ZORUNLU
- **README güncellemeden değişiklik push etme** — dosya ekleme/silme/rename sonrası README ZORUNLU

## 🔄 Post-Change Kontrol Kuralı (ZORUNLU — Mart 2026+)

> **Her proje değişikliğinden sonra `/degisiklik-kontrol` workflow'u uygulanır.**

Bu workflow, syntax/import kontrolü, README güncelliği, git sync, deploy smoke test ve bağımlı proje kontrolünü kapsar. Detaylar: `_agents/workflows/degisiklik-kontrol.md`

## 🏗️ Mimari ve Deploy Yaklaşımı (Native Mono-Repo)

- **Tek Bağımsız Repo:** Ayrı GitHub repolarına proje dosyası kopyalama (`/tmp/` kullanarak `cp` yapma) yöntemi tarihe karışmıştır. Tüm platform `dolunayozerennn/antigravity-egitim` adlı Native Mono-Repo içerisinde barındırılmaktadır.
- **Railway Ayarları:** Railway'e bir proje deploy edileceği zaman yine ana repo (antigravity-egitim) bağlanır. Sadece o projenin çalışması için **Root Directory** ve **Watch Paths** ayarları ilgili proje klasörüne (örn: `Projeler/Tele_Satis_CRM`) yönlendirilir.

## 🚀 Deploy Güvenlik Kuralları (ZORUNLU — Mart 2026+)

> Bu kurallar `/canli-yayina-al` workflow'u çağrılmasa bile geçerlidir.

### Push Öncesi (Mono-Repo):
1. `python3 -m py_compile *.py` — syntax kontrolü
2. Tüm .py dosyalarını `importlib.import_module()` ile import et
3. `tests/` veya `run_test.py` varsa çalıştır
4. **Caller ↔ Callee imza doğrulaması** — AST ile entry point'teki fonksiyon çağrı argümanlarının, tanımlarıyla uyumlu olduğunu doğrula (import testi bunu YAKALAMAZ)
5. Hata varsa → ❌ PUSH YAPMA

### Deploy Sonrası:
1. SUCCESS olduktan sonra 60 saniye bekle
2. `deploymentLogs` ile logları çek
3. `AttributeError`, `ImportError`, `SyntaxError`, `Traceback` ara
4. Fatal error varsa → düzelt, tekrar push, tekrar deploy

## 🔧 Railway Sistem Bağımlılıkları Kuralı (ZORUNLU — Nisan 2026+)

> **Railway, Nixpacks builder kullanır. `Aptfile` ve `apt.txt` dosyaları YOKSAYILIR!**

| Durum | Doğru Çözüm |
|---|---|
| Sistem paketi gerekiyor (ffmpeg, chromium vb.) | `nixpacks.toml` → `[phases.setup] nixPkgs = ["ffmpeg"]` |
| `Aptfile` veya `apt.txt` bulunuyor | ❌ SİL — yanıltıcı, Nixpacks bunları yoksayar |
| Sistem binary'si kontrolü | `config.py` → `self._check_system_deps(["ffmpeg"])` (fail-fast) |

**Detaylar:** `_knowledge/hatalar-ve-cozumler.md` → "Nixpacks vs Aptfile/apt.txt Uyumsuzluğu"

## 🔍 Hata Düzeltme Protokolü (ZORUNLU — Nisan 2026+)

> **Hata raporlandığında HEMEN koda dalma. Önce analiz, sonra plan, sonra fix.**

1. **3-Soru Analizi (fix yazmadan ÖNCE):**
   - Bu hata TAM OLARAK nereden kaynaklanıyor? (kök neden, semptom değil)
   - Bu fix başka nereleri etkiler? (`grep` ile tüm referansları tara)
   - Bu hata tipi `hatalar-ve-cozumler.md`'de var mı? (varsa o çözümü uygula)
2. **Çözüm planını kullanıcıya sun** → Onay al → Fix uygula
3. **Fix sonrası → tüm etkilenen yerleri test et**
4. **Yeni pattern ise → `hatalar-ve-cozumler.md`'ye ekle**

**Detaylı workflow:** `_agents/workflows/hata-duzeltme.md`

## 🎯 Küçük Parça Prensibi (ZORUNLU — Nisan 2026+)

> **Büyük değişiklik yapıp sonunda test etme. Her parçayı ayrı test et.**

- Her değişiklik maks 1 dosya veya 1 fonksiyon kapsamında olmalı
- Push öncesi her dosya değişikliğini ayrı ayrı test et
- 3'ten fazla dosya değişiyorsa → kullanıcıya "Bu değişikliği X parçaya bölmemi öneriyorum" de
- Her parça bittikten sonra → syntax + import testi çalıştır

## 🛡️ Stabilize-Lite + 48-Saat İzleme (ZORUNLU — Nisan 2026+)

> **Her deploy sonrası 5 dakikalık zorunlu minimum kontrol + 48 saat izleme.**

### Stabilize-Lite (5 kontrol, her deploy'da ZORUNLU):
1. Deploy status → SUCCESS mi?
2. Son 100 log'da fatal error var mı?
3. Tüm env var'lar Railway'de tanımlı mı?
4. Cron ise → manuel tetikle, 90 sn bekle, log kontrol et
5. Platform checklist → `_knowledge/platform-checklists/railway.md` kontrol et

### 48-Saat İzleme:
- Deploy sonrası `bekleyen-gorevler.md`'ye izleme kaydı eklenir
- Sonraki konuşmalarda Railway logları kontrol edilir
- 2 ardışık temiz kontrol → izleme kapatılır

**Detaylı workflow:** `_agents/workflows/canli-yayina-al.md` → Adım 7.9 ve 9

## 📋 Platform Kontrol Listeleri (ZORUNLU — Nisan 2026+)

> **Yeni proje kurarken ve Railway'de hata düzeltirken bu listeyi KONTROL ET.**

- **Railway:** `_knowledge/platform-checklists/railway.md`
- İleride Netlify vb. için de oluşturulabilir

## 📊 Görev Raporu (ZORUNLU — Nisan 2026+)

> **Her görev tamamlandığında kullanıcıya teknik olmayan, anlaşılır bir rapor sunulur.**
> Kullanıcı kodlama bilmez — sonucu, durumu ve aksiyonu anlayabileceği formatta öğrenmelidir.

### Rapor Formatı:
```
📋 GÖREV RAPORU — [Proje/Görev Adı]

🎯 Ne yapıldı: [1 cümleyle açıklama]

✅ Çalışıyor mu?
   - Yayına alındı mı? → Evet/Hayır
   - Gerçekten çalışıyor mu? → Evet (log'da hata yok) / Hayır (şu hata var)
   - Bekleyen risk var mı? → Yok / "48 saat izlemeye alındı"

⚡ Bir şey yapman gerekiyor mu? → Hayır / Evet: [basit talimat]

🔢 Kalite Skoru: X/5
   1. Kod hatasız mı? ✅/❌
   2. Doğru çalışıyor mu? ✅/❌
   3. Güvenli mi (şifre sızdırmaz)? ✅/❌
   4. Başka projeleri bozmuyor mu? ✅/❌
   5. İzlemeye alındı mı? ✅/❌
```

### Kurallar:
- **Deploy görevlerinde:** Rapor ZORUNLU
- **Hata düzeltme görevlerinde:** Rapor ZORUNLU
- **Basit bilgi sorularında:** Rapor gerekmez
- Kalite skoru 5/5 değilse → eksik maddeyi açıkla ve çözüm öner

## 🔭 Pipeline Gözlemlenebilirlik (ZORUNLU — Nisan 2026+)

> **Çok adımlı projeler "kapalı kutu" olmamalı.**
> Kullanıcı, pipeline'ın hangi adımında ne olduğunu görebilmeli.

### Prensip:
Kullanıcı kodlama bilmiyor. Bir proje 6 adımlı bir pipeline çalıştırıyorsa ve sonuç hatalıysa, kullanıcı hatanın hangi adımda oluştuğunu bilemez. Bu yüzden:

1. **Her çok adımlı proje (3+ adım)**, her adımın başarı/başarısızlık durumunu gözlemlenebilir bir yere yazmalı
2. **Hedef:** Notion Operations Log DB (`33095514-0a32-81b4-858a-ff81a77b6d48`)
3. **Minimum log formatı:** Proje adı, çalışma tarihi, adım adım durum (✅/❌), hata mesajı (varsa), toplam süre

### Uygulama Kuralları:
- **Yeni projeler:** `pipeline_logger.py` modülü ile başlat (V2 Starter şablonuna eklenecek)
- **Mevcut projeler:** Peyderpey ekle — tek seferde hepsini değiştirme (Küçük Parça Prensibi)
- **Log seviyesi:** P1 (kritik hatalar) Notion'a yazılır + Telegram bildirimi. P2 (uyarılar) sadece Notion'a yazılır
- **Railway logları yeterli mi?** HAYIR — kullanıcı Railway dashboard'a girip log okuyamaz. Notion'a yazılması ZORUNLU

### Notion Operations Log DB Şeması (Minimum):
| Property | Tip | Açıklama |
|---|---|---|
| Proje | Title | Pipeline'ın adı |
| Tarih | Date | Çalışma tarihi/saati |
| Durum | Select | ✅ Başarılı / ❌ Başarısız / ⚠️ Kısmi |
| Adımlar | Rich Text | Adım adım durum özeti |
| Hata | Rich Text | Hata mesajı (varsa) |
| Süre | Number | Toplam çalışma süresi (saniye) |

