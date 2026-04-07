# Çalışma Kuralları ve Tercihler

Bu dosya, Antigravity ile çalışırken birikmesi gereken kişisel tercihlerini ve kuralları içerir.
**Son güncelleme:** _(İlk kurulumda güncelleyin)_

---

## Genel Çalışma Tarzı

- **Dil:** Tercih ettiğiniz iletişim dili
- **Proje Dizini:** Tüm projeler `Projeler/` altında
- **Kısa ve net:** Uzun açıklamalar yerine madde madde özetler tercih edilir

## Proje Yapısı

```
Antigravity/
├── _agents/              → Agent'lar ve Workflow'lar
│   ├── musteri-kazanim/  → Lead + Outreach orkestratörü
│   ├── icerik-uretim/    → İçerik pipeline orkestratörü
│   ├── yayinla-paylas/   → Deploy + Export orkestratörü
│   └── workflows/        → Slash command workflow'ları
├── _skills/              → Kalıcı yetkinlikler (skill'ler)
├── _knowledge/           → Bu klasör (manuel hafıza)
│   └── credentials/      → 🔐 Merkezi şifre/token deposu
├── Projeler/             → Tüm proje klasörleri
└── Paylasilan_Projeler/  → Dışarıyla paylaşıma hazırlanan paketler
```

## Aktif Projeler

| Proje | Açıklama | Durum |
|---|---|---|
| _(İlk projenizi oluşturduğunuzda buraya ekleyin)_ | | |

## 🔐 Şifre/Token Yönetim Kuralları (OTOMATİK)

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

## 🏗️ Mimari ve Deploy Yaklaşımı (Native Mono-Repo)

- **Tek Bağımsız Repo:** Tüm platform tek bir GitHub reposu içerisinde barındırılır (Native Mono-Repo).
- **Railway Ayarları:** Railway'e bir proje deploy edileceği zaman ana repo bağlanır. Sadece o projenin çalışması için **Root Directory** ve **Watch Paths** ayarları ilgili proje klasörüne yönlendirilir.

## 🚀 Deploy Güvenlik Kuralları (ZORUNLU)

> Bu kurallar `/canli-yayina-al` workflow'u çağrılmasa bile geçerlidir.

### Push Öncesi (Mono-Repo):
1. `python3 -m py_compile *.py` — syntax kontrolü
2. Tüm .py dosyalarını import testi ile doğrula
3. `tests/` veya `run_test.py` varsa çalıştır
4. Hata varsa → ❌ PUSH YAPMA

### Deploy Sonrası:
1. SUCCESS olduktan sonra 60 saniye bekle
2. Logları çek ve kontrol et
3. `AttributeError`, `ImportError`, `SyntaxError`, `Traceback` ara
4. Fatal error varsa → düzelt, tekrar push, tekrar deploy

## 🔧 Railway Sistem Bağımlılıkları Kuralı (ZORUNLU)

> **Railway, Nixpacks builder kullanır. `Aptfile` ve `apt.txt` dosyaları YOKSAYILIR!**

| Durum | Doğru Çözüm |
|---|---|
| Sistem paketi gerekiyor (ffmpeg, chromium vb.) | `nixpacks.toml` → `[phases.setup] nixPkgs = ["ffmpeg"]` |
| `Aptfile` veya `apt.txt` bulunuyor | ❌ SİL — yanıltıcı, Nixpacks bunları yoksayar |
| Sistem binary'si kontrolü | `config.py` → `self._check_system_deps(["ffmpeg"])` (fail-fast) |

## Tekrarlayan Talepler

- _(Burası zamanla dolacak — önemli kararlar ve tercihler eklenecek)_
