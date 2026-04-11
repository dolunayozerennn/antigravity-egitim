---
description: Projeyi GitHub'a push et ve Railway'de 7/24 çalışır hale getir — tamamen otonom, kullanıcıya hiçbir şey sordurma
---

# 🚀 Canlıya Al — Production Deploy Workflow

> ⛔ **MUTLAK KURAL:** Kullanıcıya "dashboard'a git", "linke tıkla", "repo bağla" gibi 
> manuel işlem ASLA söyleme. Tüm adımlar API ile yapılır.

// turbo-all

## Ön Koşul: Skill Dosyasını Oku

```
view_file → _skills/canli-yayina-al/SKILL.md
```
Bu dosyayı oku ve talimatları harfiyen uygula.

## Adım 1: Deploy Türünü Belirle

1. `_knowledge/deploy-registry.md` dosyasını oku → proje daha önce deploy edilmiş mi?
2. GitHub MCP → `get_file_contents(owner: "[GITHUB_KULLANICI]", repo: "REPO_ADI")` → repo var mı?
3. Railway GraphQL → projeleri listele → Railway'de proje var mı?

**Sonuç:**
- Her ikisi de varsa → **RE-DEPLOY** akışı (Adım 6'ya atla)
- GitHub var, Railway yok → **KISMI** deploy (Adım 4'ten başla)
- Hiçbiri yok → **YENİ** deploy (Adım 2'den devam)

## Adım 2: Güvenlik Kontrolü

1. Proje klasöründeki `.py`, `.js`, `.ts` dosyalarını hardcoded key için tara
2. `.env` dosyası `.gitignore`'da mı kontrol et
3. `requirements.txt` / `package.json` güncel mi kontrol et
4. token.json, credentials.json gibi hassas dosyaları kontrol et

## Adım 2.5: ⚠️ KOD SAĞLIK KONTROLÜ (ZORUNLU — ATLANMAZ!)

> **Bu adım push'tan ÖNCE çalışır. Başarısız olursa PUSH YAPMA.**
> Bu adımın amacı: Production'da patlayacak hataları daha göndermeden yakalamak.

### 2.5.1 — Python Syntax Kontrolü
```bash
cd PROJE_KLASÖRÜ
python3 -m py_compile *.py 2>&1
```
- Hata varsa → ❌ PUSH YAPMA, hatayı düzelt

### 2.5.2 — Import Zinciri Testi (KRİTİK)
```bash
cd PROJE_KLASÖRÜ
python3 -c "
import sys; sys.path.insert(0, '.')
# Projenin ana modüllerini import et — attribute hatalarını yakalar
import importlib, pkgutil, os
errors = []
for f in os.listdir('.'):
    if f.endswith('.py') and f != 'setup.py':
        mod = f[:-3]
        try:
            importlib.import_module(mod)
        except Exception as e:
            errors.append(f'{mod}: {e}')
if errors:
    for e in errors:
        print(f'❌ {e}')
    sys.exit(1)
else:
    print('✅ Tüm modüller başarıyla import edildi')
"
```
- `AttributeError`, `ImportError`, `ModuleNotFoundError` gibi hatalar burada yakalanır
- Hata varsa → ❌ PUSH YAPMA, hatayı düzelt

### 2.5.3 — Mevcut Testleri Çalıştır
```bash
cd PROJE_KLASÖRÜ
# tests/ klasörü var mı kontrol et
if [ -d "tests" ]; then
    python3 -m pytest tests/ -v --tb=short 2>&1 || python3 tests/test_*.py 2>&1
fi
# Veya run_test.py varsa:
if [ -f "run_test.py" ]; then
    python3 run_test.py 2>&1
fi
```
- Test başarısızsa → ❌ PUSH YAPMA, hatayı düzelt
- Test yoksa → ⚠️ Uyarı ver ama devam et

### 2.5.4 — Akıllı Dependency Matching (Pip Adı ≠ Import Adı)
```bash
cd PROJE_KLASÖRÜ
# Sıkça yapılan pip vs import isimlendirme hatalarını kontrol et:
echo "=== Dependency Pin & Name Check ==="
cat requirements.txt 2>/dev/null
```
- Import adı ile pip adı eşleşmiyor veya hatalı/eski versiyon varsa → ❌ PUSH YAPMA, requirements.txt'yi düzelt. 
  - Örn: `google.genai` import ediliyorsa pip adı `google-genai` olmalıdır (eski model `google-generativeai` DEĞİL).
  - Örn: `PIL` import ediliyorsa pip adı `Pillow` olmalıdır. 
  - Örn: `telegram` import ediliyorsa pip adı `python-telegram-bot` olmalıdır.

### 2.5.5 — Version Pinning Kontrolü
```bash
cd PROJE_KLASÖRÜ
grep -v "==" requirements.txt 2>/dev/null | grep -v "^#" | grep -v "^$" && echo "⚠️ Unpinned dependency bulundu!"
```
- Versiyonu pinlenmemiş (==) kritik (`google-genai`, `openai`, `python-telegram-bot`) paket varsa → ❌ PUSH YAPMA, versiyon sabitle!

### 2.5.6 — Hardcoded Secret Taraması (Güvenlik Ağı)
```bash
cd PROJE_KLASÖRÜ
grep -rnE "(sk-|AIza|ghp_|ghs_|xoxb-|Bearer [A-Za-z0-9]|api[_-]?key\s*=\s*['\"][A-Za-z0-9])" --include="*.py" --include="*.js" . || true
```
- Bir API Key veya Token hardcode edilmişse → ❌ PUSH YAPMA, `os.environ.get()` ile değiştir.

### 2.5.7 — Sistem Bağımlılıkları Kontrolü (Nixpacks — KRİTİK!)

> **Railway, Nixpacks builder kullanır. `Aptfile` ve `apt.txt` dosyaları YOKSAYILIR!**

```bash
cd PROJE_KLASÖRÜ

# 1. Legacy dosya tuzağını tespit et — Aptfile/apt.txt varsa SİL!
if [ -f "Aptfile" ] || [ -f "apt.txt" ]; then
    echo "❌ YANILTICI DOSYA TESPİT EDİLDİ: Aptfile veya apt.txt bulundu!"
    echo "   Railway Nixpacks builder bu dosyaları YOKSAYAR."
    echo "   Bu dosyaları silin ve paketleri nixpacks.toml'a taşıyın."
fi

# 2. Sistem bağımlılığı gerektiren kütüphaneleri tara
grep -lqE "ffmpeg|ffprobe|subprocess.*ffmpeg" *.py **/*.py 2>/dev/null && SYS_DEP_NEEDED="ffmpeg"
grep -lqE "cairosvg|cairo" *.py **/*.py 2>/dev/null && SYS_DEP_NEEDED="$SYS_DEP_NEEDED cairo"
grep -lqE "chromium|puppeteer|playwright" *.py **/*.py 2>/dev/null && SYS_DEP_NEEDED="$SYS_DEP_NEEDED chromium"

# 3. Eğer sistem bağımlılığı gerekiyorsa → nixpacks.toml kontrol et
if [ -n "$SYS_DEP_NEEDED" ]; then
    if [ ! -f "nixpacks.toml" ]; then
        echo "❌ nixpacks.toml BULUNAMADI! Bu proje $SYS_DEP_NEEDED gerektiriyor."
        echo "   Oluştur: [phases.setup] nixPkgs = [\"$SYS_DEP_NEEDED\"]"
    else
        for dep in $SYS_DEP_NEEDED; do
            grep -q "$dep" nixpacks.toml || echo "❌ nixpacks.toml'da '$dep' eksik!"
        done
    fi
fi
```

- Legacy `Aptfile`/`apt.txt` varsa → ❌ SİL, paketleri `nixpacks.toml`'a taşı
- Sistem bağımlılığı gerektiren kod var ama `nixpacks.toml` yoksa → ❌ PUSH YAPMA, `nixpacks.toml` oluştur!
- `nixpacks.toml`'da gerekli paket eksikse → ❌ PUSH YAPMA, `nixPkgs`'e ekle!

### 2.5.8 — Lokal ↔ GitHub Diff Kontrolü (Re-deploy için)
```
Re-deploy ise:
1. GitHub MCP ile repo'daki dosyaları listele
2. Lokal proje klasöründeki dosyalarla karşılaştır
3. Lokal'de değişmiş ama GitHub'a push edilmemiş dosya varsa → UYAR ve bunları da push et
```

**⚠️ BU ADIM ATLANILAMAZ. HER PUSH'TAN ÖNCE ÇALIŞTIRILMALIDIR.**

## Adım 3: GitHub'a Push (Native Mono-Repo)

> **DİKKAT:** Sistemin mimarisi Native Mono-Repo'ya geçmiştir. Railway için ayrı GitHub reposu OLUŞTURULMAZ. Tüm kod `[GITHUB_KULLANICI]/[REPO_ADI]` üzerinde yaşar.

1. **Değişiklikleri Ana Repoya Pushla:**
   ```bash
   git add .
   git commit -m "deploy: [PROJE_ADI] için ilk kurulum/güncelleme"
   git push origin main
   ```

2. **Doğrula:**
   - `.env`, `__pycache__` gibi hassas dosyaların commit edilmediğinden emin ol (`git status`).

## Adım 4: Railway Proje Oluştur (API ile)

```bash
# Railway token: _skills/canli-yayina-al/scripts/railway-token.txt
TOKEN="RAILWAY_TOKEN_BURAYA"

# 4.1 — Proje oluştur
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "mutation { projectCreate(input: { name: \"PROJE_ADI\" }) { id environments { edges { node { id name } } } } }"}'

# Response'dan al:
# PROJE_ID = data.projectCreate.id
# ENV_ID = data.projectCreate.environments.edges[0].node.id
```

## Adım 5: Railway Servis Oluştur + GitHub Bağla (API ile)

```bash
# 5.1 — GitHub repo'dan servis oluştur
# DİKKAT: repo her zaman "[GITHUB_KULLANICI]/[REPO_ADI]" olmalıdır.
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "mutation { serviceCreate(input: { projectId: \"PROJE_ID\", name: \"SERVIS_ADI\", source: { repo: \"[GITHUB_KULLANICI]/[REPO_ADI]\" }, branch: \"main\" }) { id name } }"}'

# Response'dan al:
# SERVIS_ID = data.serviceCreate.id

# 5.2 — Start command + restart policy ayarla
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "mutation { serviceInstanceUpdate(serviceId: \"SERVIS_ID\", environmentId: \"ENV_ID\", input: { startCommand: \"python main.py\", restartPolicyType: ON_FAILURE, restartPolicyMaxRetries: 10 }) }"}'

# 5.3 — Environment variables ayarla
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "mutation { variableCollectionUpsert(input: { projectId: \"PROJE_ID\", environmentId: \"ENV_ID\", serviceId: \"SERVIS_ID\", variables: { KEY1: \"VALUE1\" } }) }"}'

# 5.4 — Root Directory ve Watch Paths Ayarla (ÇOK ÖNEMLİ!)
# DİKKAT: Ana repo ([REPO_ADI]) bağlandığı için projenin alt klasörde olduğunu belirtmek ZORUNLUDUR.
# Railway Dashboard -> Settings -> General -> Root Directory -> `Projeler/PROJE_ADI`
# Watch Paths -> `Projeler/PROJE_ADI/**` (Sadece bu klasör değiştiğinde otomatik deploy yapar).
# Bu işlemi API ile `builder { rootDirectory }` update atarak da yapabilirsiniz.

# 5.5 — Deploy otomatik başlar (serviceCreate repo bağladığında)
# Başlamazsa: serviceInstanceRedeploy tetikle
```

## Adım 6: RE-DEPLOY (Güncelleme)

1. `deploy-registry.md`'den Proje ID, Servis ID, Environment ID ve **GitHub Repo** oku
2. **Adım 2.5'i çalıştır** — Kod sağlık kontrolü (ZORUNLU!)
3. **⚠️ MONO-REPO SYNC (KRİTİK — ATLANMAZ!):**
   - Eski kopuk (multi-repo) mimariden **Native Mono-Repo**'ya geçilmiştir.
   - Tüm projeler `[GITHUB_KULLANICI]/[REPO_ADI]` ana reposundan çalışır. 
   - Ana repoyu commit et ve pushla:
     ```bash
     # Sadece lokal repoyu push etmek yeterlidir
     git add .
     git commit -m "deploy: [PROJE_ADI] güncel kod"
     git push origin main
     ```
   - Railway, `Root Directory` ayarı sayesinde monorepo üzerinden sadece ilgili projeyi bulup derleyecektir.
   - Eðer Railway tetiklenmezse `serviceConnect` mutation'ı kullanabilirsiniz.
4. Deploy loglarını kontrol et — fatal error pattern'leri ara
5. Başarısızsa → düzelt, tekrar push, tekrar deploy

## Adım 7: Deploy Durumunu Takip Et

```bash
# 30 saniye bekle, sonra kontrol et
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "{ deployments(first: 3, input: { projectId: \"PROJE_ID\", environmentId: \"ENV_ID\", serviceId: \"SERVIS_ID\" }) { edges { node { id status createdAt } } } }"}'
```

- `SUCCESS` → **Adım 7.5'e geç** (Smoke Test) ✅
- `FAILED/CRASHED` → Log oku, düzelt
- `BUILDING/QUEUED` → 2 dk bekle, tekrar kontrol et

## Adım 7.5: ⚠️ SMOKE TEST (ZORUNLU — ATLANMAZ!)

> **Deploy SUCCESS olduktan sonra, gerçekten çalıştığından emin ol.**
> Deployment SUCCESS olması servisin düzgün çalıştığı anlamına GELMEZ.

1. **60 saniye bekle** (servis başlasın ve logları oluşsun)

2. **Son deployment'ın loglarını çek:**
```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "{ deploymentLogs(deploymentId: \"DEPLOYMENT_ID\", limit: 100) { message severity timestamp } }"}'
```

3. **Fatal error pattern'lerini ara:**
   - `AttributeError` — bir değişken veya özellik bulunamadı
   - `ImportError` / `ModuleNotFoundError` — bir modül eksik
   - `SyntaxError` — kod yazım hatası
   - `NameError` — tanımsız değişken
   - `KeyError` — eksik sözlük anahtarı
   - `TypeError` — yanlış veri tipi
   - `Traceback (most recent call last)` — Python hata izleme
   - `Process exited with code 1` — servis çöktü

4. **Sonuç:**
   - Fatal error bulunursa → ❌ **SMOKE TEST BAŞARISIZ**
     - Kullanıcıya "Servis yayına alındı ama bir hata var, düzeltiyorum" de
     - Hatayı düzelt → Tekrar push → Tekrar deploy → Tekrar smoke test
   - Fatal error yoksa → ✅ **SMOKE TEST BAŞARILI**

**⚠️ BU ADIM ATLANILAMAZ. HER DEPLOY SONRASI ÇALIŞTIRILMALIDIR.**

## Adım 8: Kayıt ve Rapor

1. `_knowledge/deploy-registry.md` dosyasına proje bilgilerini ekle
2. Kullanıcıya rapor ver:

```
✅ Production Deploy Tamamlandı!

📦 Proje: [Proje Adı]
🔗 GitHub: github.com/[GITHUB_KULLANICI]/repo-adi (private)
🚂 Railway: https://railway.app/project/PROJE_ID
🔒 Güvenlik: API key'ler environment variable olarak ayarlandı
🧪 Testler: X/X geçti
🔍 Smoke Test: ✅ Loglar temiz

Durum: 7/24 aktif çalışıyor ✨
```

## Adım 9: ⚠️ Stabilizasyon Önerisi (ZORUNLU)

> Deploy tamamlandıktan sonra aşağıdaki mesajı **her zaman** kullanıcıya göster:

```
⚠️ Deploy tamamlandı. Kapsamlı stabilizasyon için `/stabilize <PROJE_ADI>` çalıştırmanızı öneriyorum.
Bu, 21 kontrol noktasından geçirerek projenin production-ready olduğunu garanti eder.
```

> Kullanıcı onaylarsa → `/stabilize` workflow'unu hemen başlat.
> Stabilize çalıştırılmadan deploy tam anlamıyla "tamamlanmış" SAYILMAZ.

