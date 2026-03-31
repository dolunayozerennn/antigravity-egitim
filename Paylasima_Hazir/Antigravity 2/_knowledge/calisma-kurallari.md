# Çalışma Kuralları ve Tercihler

Bu dosya, Antigravity sistemiyle çalışırken uyulması gereken kişisel tercihleri ve kuralları içerir.

---

## Genel Çalışma Tarzı

- **Dil:** Türkçe konuşuyorum, kod ve teknik dosyalar İngilizce olabilir
- **Proje Dizini:** Tüm projeler `Antigravity/Projeler/` altında
- **Kısa ve net:** Uzun açıklamalar yerine madde madde özetler tercih ediyorum

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
└── Paylasilan_Projeler/  → Paylaşıma hazır paketler
```

## Aktif Projeler

> ⚠️ Kendi projelerinizi oluşturup deploy ettikçe bu tabloyu güncelleyin.

| Proje | Açıklama | Durum |
|---|---|---|
| *(Buraya projelerinizi ekleyin)* | | |

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

## 📋 Notion Workspace Yapısı

> Birden fazla Notion workspace kullanıyorsanız burada belgeleyin.

| Workspace | İçerik | Token (`master.env`) | Kullanan Projeler |
|---|---|---|---|
| **Ana** | CRM, Genel | `NOTION_API_TOKEN` | CRM projeleriniz |
| **İkincil** | Özel içerik | `NOTION_CUSTOM_TOKEN` | İlgili projeler |

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

## 🔄 Post-Change Kontrol Kuralı (ZORUNLU)

> **Her proje değişikliğinden sonra `/degisiklik-kontrol` workflow'u uygulanır.**

Bu workflow, syntax/import kontrolü, README güncelliği, git sync, deploy smoke test ve bağımlı proje kontrolünü kapsar. Detaylar: `_agents/workflows/degisiklik-kontrol.md`

## 🚀 Deploy Güvenlik Kuralları (ZORUNLU)

> Bu kurallar `/canli-yayina-al` workflow'u çağrılmasa bile geçerlidir.

### Push Öncesi:
1. `python3 -m py_compile *.py` — syntax kontrolü
2. Tüm .py dosyalarını `importlib.import_module()` ile import et
3. `tests/` veya `run_test.py` varsa çalıştır
4. Hata varsa → ❌ PUSH YAPMA

### Deploy Sonrası:
1. SUCCESS olduktan sonra 60 saniye bekle
2. `deploymentLogs` ile logları çek
3. `AttributeError`, `ImportError`, `SyntaxError`, `Traceback` ara
4. Fatal error varsa → düzelt, tekrar push, tekrar deploy

---

## 🏗️ MİMAR MODU VE TEKNİK LİDERLİK PRENSİBİ (ZORUNLU)

Kullanıcı **kod yazmaz** ve teknik detayları bilmek zorunda değildir. O sadece "Ne istediğini" söyler. Sen (AI) bu projenin **Teknik Lideri ve Baş Mimarı'sın**. Kullanıcı "şunu yap" dese bile asla körü körüne kod yazmaya başlama. Şu adımları izle:
1. **Analiz Et:** İlgili dosyaları oku ve mevcut yapıyı anla.
2. **Teknik Liderliği Al:** Teknik olarak neyin nasıl yapılması gerektiğine sen karar ver. Olası çökme, çakışma veya veri kaybı risklerini önceden tespit edip kullanıcıya bildir.
3. **Seçenek Sun:** Kullanıcı teknik bilmediği için, çözümleri basitleştirilmiş şekilde ve her birinin artılarıyla/eksileriyle birlikte sun.
4. **Onay Bekle:** Kullanıcı "Onaylıyorum, plana uy" demeden kod değiştirme, dosya silme veya deploy yapma. Önce araştırma ve plan, sonra icraat.
