---
description: Projeyi GitHub'a push et ve Railway'de 7/24 çalışır hale getir — tamamen otonom, kullanıcıya hiçbir şey sordurma
---

# 🚀 Canlıya Al — Production Deploy Workflow

> ⛔ **MUTLAK KURAL:** Kullanıcıya "dashboard'a git", "linke tıkla", "repo bağla" gibi 
> manuel işlem ASLA söyleme. Tüm adımlar API ile yapılır.

// turbo-all

## Ön Koşul: Skill Dosyalarını Oku

```
view_file → _skills/canli-yayina-al/SKILL.md
view_file → _skills/use-railway/SKILL.md
```
Bu dosyaları oku ve talimatları harfiyen uygula. (Ayrıca projedeki entegrasyonlar için `_skills/` dizinindeki diğer ilgili kuralları — Supabase, Notion, Apify vb. — ihlal etmediğinden emin ol).

## Adım 1: Deploy Türünü Belirle

1. `_knowledge/deploy-registry.md` dosyasını oku → proje daha önce deploy edilmiş mi?
2. GitHub MCP → `get_file_contents(owner: "dolunayozerennn", repo: "REPO_ADI")` → repo var mı?
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

> **💡 NODE.JS BİLGİ NOTU (PRE-START SCRIPTS):**
> Eğer projeniz Node.js ise ve container kalkmadan önce `seed`, `migrate` veya `build` gibi bir komut çalıştırmak istiyorsanız bunu `nixpacks.toml`'da `[start] cmd="..."` olarak belirtmek Railway'de GÖZARDI EDİLEBİLİR. Bunun yerine en güvenli yöntem **`package.json` içindeki `start` script'ini** modifiye etmektir:
> `"start": "npm run seed && node server.js"`

### 2.5.8 — Lokal ↔ GitHub Diff Kontrolü (Re-deploy için)
```
Re-deploy ise:
1. GitHub MCP ile repo'daki dosyaları listele
2. Lokal proje klasöründeki dosyalarla karşılaştır
3. Lokal'de değişmiş ama GitHub'a push edilmemiş dosya varsa → UYAR ve bunları da push et
```

### 2.5.9 — Caller ↔ Callee İmza Doğrulaması (KRİTİK!)

> **Import testi (2.5.2) bunu YAKALAMAZ.** Import testi modülün yüklenebildiğini kontrol eder,
> ama çağrı sırasındaki argüman uyumsuzluğunu (TypeError) ancak runtime'da görürsün.
> Bu adım, `main.py` (veya entry point) içindeki fonksiyon çağrılarının gerçek tanımlarıyla
> uyumlu olup olmadığını statik olarak doğrular.

```bash
cd PROJE_KLASÖRÜ
python3 -c "
import ast, sys, os

errors = []
sys.path.insert(0, '.')

# Entry point'i bul
entry = 'main.py' if os.path.exists('main.py') else None
if not entry:
    for f in os.listdir('.'):
        if f.endswith('.py') and '__' not in f:
            entry = f; break

if not entry:
    print('⚠️ Entry point bulunamadı, atlanıyor'); sys.exit(0)

tree = ast.parse(open(entry).read())

# Tüm fonksiyon çağrılarını bul
for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    # SADECE bare function çağrılarını kontrol et: func_name(...)
    # Obje metod çağrıları (obj.method()) atlanır — false positive önleme
    if isinstance(node.func, ast.Name):
        func_name = node.func.id
    else:
        continue  # obj.method() çağrıları atlanır

    call_kwargs = [kw.arg for kw in node.keywords if kw.arg]
    if not call_kwargs:
        continue

    # Aynı projedeki modüllerde + core/ alt dizininde bu fonksiyonun tanımını ara
    search_dirs = [('.', '')]
    if os.path.isdir('core'):
        search_dirs.append(('core', 'core/'))

    for search_dir, prefix in search_dirs:
        for pyfile in os.listdir(search_dir):
            if not pyfile.endswith('.py'):
                continue
            fpath = os.path.join(search_dir, pyfile)
            try:
                ftree = ast.parse(open(fpath).read())
                for fnode in ast.walk(ftree):
                    if isinstance(fnode, ast.FunctionDef) and fnode.name == func_name:
                        defined_args = [a.arg for a in fnode.args.args]
                        defined_kwargs = [a.arg for a in (fnode.args.kwonlyargs or [])]
                        all_params = set(defined_args + defined_kwargs)
                        has_kwargs = fnode.args.kwarg is not None

                        if not has_kwargs:
                            for kwarg in call_kwargs:
                                if kwarg not in all_params:
                                    errors.append(
                                        f'{entry}:{node.lineno} → {func_name}({kwarg}=...) çağrılıyor '
                                        f'ama {prefix}{pyfile}:{fnode.lineno} tanımında \\\"{kwarg}\\\" parametresi YOK!'
                                    )
            except (SyntaxError, OSError):
                pass

if errors:
    print('❌ CALLER ↔ CALLEE UYUMSUZLUKLARI:')
    for e in errors:
        print(f'  {e}')
    sys.exit(1)
else:
    print('✅ Fonksiyon çağrı imzaları uyumlu')
"
```
- `TypeError: got an unexpected keyword argument` hatalarını **deploy'dan ÖNCE** yakalar
- Bu test `get_logger(level=...)` gibi uyumsuzlukları tespit eder
- Hata varsa → ❌ PUSH YAPMA, fonksiyon tanımını güncelle

**⚠️ BU ADIM ATLANILAMAZ. HER PUSH'TAN ÖNCE ÇALIŞTIRILMALIDIR.**

## Adım 2.9: 🐳 DOCKER SİMÜLASYON TESTİ (ÖNERİLEN)

> **Railway'de çökecek hataları lokal'de yakala.** Sistem bağımlılığı olan projeler (ffmpeg, chromium vb.) için KRİTİK.

Docker Desktop mevcutsa ve proje sistem bağımlılığı kullanıyorsa:

```bash
cd PROJE_KLASÖRÜ

# 1. Proje için minimal Dockerfile oluştur (yoksa)
cat > /tmp/Dockerfile.railtest << 'EOF'
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py", "--dry-run"]
EOF

# 2. Build & çalıştır (env var'ları mock olarak ver)
docker build -t railtest -f /tmp/Dockerfile.railtest .
docker run --rm -e ENV=development railtest
```

- Build hatası varsa → requirements.txt veya sistem bağımlılığı eksik
- Runtime hatası varsa → path/config sorunu
- `--dry-run` flag'i yoksa → `python -c "import main"` ile sadece import testi yap

**⚠️ NOT:** Docker Desktop yoksa veya proje sistem bağımlılığı kullanmıyorsa bu adım ATLANABİLİR.

## Adım 3: GitHub'a Push ve Railway Deploy (DNS Bypass)

> **DİKKAT:** Sistemin mimarisi Native Mono-Repo'ya geçmiştir. Railway için ayrı GitHub reposu OLUŞTURULMAZ. Tüm kod `dolunayozerennn/antigravity-egitim` üzerinde yaşar.
> **KRİTİK KURAL (DNS BYPASS VE RAILWAY MCP):** Agent sandbox ortamında DNS engeli olduğu için terminalden `git push` VEYA `railway up` ÇALIŞTIRMAK YASAKTIR. Bu işlemleri her zaman MCP araçlarıyla yapacaksın!

1. **Lokal Kodu Railway'e Doğrudan Deploy Et (`mcp_railway_deploy`):**
   - Sandbox DNS engelini aşmanın EN KESİN yolu doğrudan Railway MCP Sunucusu'nu kullanmaktır.
   - `mcp_railway_deploy` aracını çağır ve `workspacePath` olarak projenin tam yolunu ver.
   - Bu araç GitHub push ihtiyacı olmadan lokaldeki kodu anında Railway'e gönderip derlemeyi başlatır.

2. **Değişiklikleri GitHub'a Senkronize Et (`mcp_github-mcp-server_push_files`):**
   - Hangi dosyaların değiştiğini bul (`git diff --name-only`).
   - Değişen dosyaları okuyup `mcp_github-mcp-server_push_files` aracına ver.
     - `owner`: "dolunayozerennn"
     - `repo`: "antigravity-egitim"
     - `branch`: "main"
     - `message`: "deploy: [PROJE_ADI] güncel kod (otonom mcp push)"
     - `files`: {path: "...", content: "..."} dizisi.
   - Sadece kodu, `requirements.txt` / `package.json` vb. anlamlı dosyaları pushla. `venv`, `__pycache__` gibi dosyaları hariç tut.

3. **Lokal Senkronizasyon (Opsiyonel):**
   - MCP API ile push yapıldığı için lokal git ağacı geri kalabilir. Gerekirse terminale `git pull --rebase origin main` (veya `git fetch` vb.) önererek lokal senkronizasyonu sağla ama otonom pushu bekleme.

## Adım 4: Railway Proje Oluştur (API ile)

```bash
export RAILWAY_TOKEN=$(grep RAILWAY_TOKEN _knowledge/credentials/master.env | cut -d '=' -f2)

# 4.1 — Proje oluştur
_skills/use-railway/scripts/railway-api.sh 'mutation { projectCreate(input: { name: "PROJE_ADI" }) { id environments { edges { node { id name } } } } }'

# Response'dan al:
# PROJE_ID = data.projectCreate.id
# ENV_ID = data.projectCreate.environments.edges[0].node.id
```

## Adım 5: Railway Servis Oluştur + GitHub Bağla (API ile)

```bash
export RAILWAY_TOKEN=$(grep RAILWAY_TOKEN _knowledge/credentials/master.env | cut -d '=' -f2)

# 5.1 — GitHub repo'dan servis oluştur
# DİKKAT: repo her zaman "dolunayozerennn/antigravity-egitim" olmalıdır.
_skills/use-railway/scripts/railway-api.sh 'mutation { serviceCreate(input: { projectId: "PROJE_ID", name: "SERVIS_ADI", source: { repo: "dolunayozerennn/antigravity-egitim" }, branch: "main" }) { id name } }'

# Response'dan al:
# SERVIS_ID = data.serviceCreate.id

# 5.2 — Start command + restart policy ayarla
_skills/use-railway/scripts/railway-api.sh 'mutation { serviceInstanceUpdate(serviceId: "SERVIS_ID", environmentId: "ENV_ID", input: { startCommand: "python main.py", restartPolicyType: ON_FAILURE, restartPolicyMaxRetries: 10 }) }'

# 5.3 — Environment variables ayarla
_skills/use-railway/scripts/railway-api.sh 'mutation { variableCollectionUpsert(input: { projectId: "PROJE_ID", environmentId: "ENV_ID", serviceId: "SERVIS_ID", variables: { KEY1: "VALUE1" } }) }'

# 5.4 — Root Directory ve Watch Paths Ayarla (ÇOK ÖNEMLİ!)
# DİKKAT: Ana repo (antigravity-egitim) bağlandığı için projenin alt klasörde olduğunu belirtmek ZORUNLUDUR.
# Railway Dashboard -> Settings -> General -> Root Directory -> `Projeler/PROJE_ADI`
# Watch Paths -> `Projeler/PROJE_ADI/**` (Sadece bu klasör değiştiğinde otomatik deploy yapar).
# Bu işlemi API ile `builder { rootDirectory }` update atarak da yapabilirsiniz.

# 5.5 — Deploy otomatik başlar (serviceCreate repo bağladığında)
# Başlamazsa: serviceInstanceRedeploy tetikle
```

## Adım 6: RE-DEPLOY (Güncelleme)

1. `deploy-registry.md`'den Proje ID, Servis ID, Environment ID ve **GitHub Repo** oku
2. **Adım 2.5'i çalıştır** — Kod sağlık kontrolü (ZORUNLU!)
3. **⚠️ DOĞRUDAN DEPLOY (mcp_railway_deploy):**
   - Değişen proje klasöründe `mcp_railway_deploy` aracını çalıştır. Bu işlem DNS engellerine takılmadan lokal kodu Railway'e taşır ve deploy'u başlatır.
   - İşlem bittikten sonra `mcp_github-mcp-server_push_files` ile değişiklikleri GitHub repository'e gönder.
4. Deploy loglarını kontrol et (`mcp_railway_get-logs`) — fatal error pattern'leri ara.
5. Başarısızsa → düzelt, tekrar `mcp_railway_deploy` çalıştır.

## Adım 7: Deploy Durumunu Takip Et

```bash
export RAILWAY_TOKEN=$(grep RAILWAY_TOKEN _knowledge/credentials/master.env | cut -d '=' -f2)
# 30 saniye bekle, sonra kontrol et
_skills/use-railway/scripts/railway-api.sh '{ deployments(first: 3, input: { projectId: "PROJE_ID", environmentId: "ENV_ID", serviceId: "SERVIS_ID" }) { edges { node { id status createdAt } } } }'
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
export RAILWAY_TOKEN=$(grep RAILWAY_TOKEN _knowledge/credentials/master.env | cut -d '=' -f2)
_skills/use-railway/scripts/railway-api.sh '{ deploymentLogs(deploymentId: "DEPLOYMENT_ID", limit: 100) { message severity timestamp } }'
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

## Adım 7.9: 🛡️ STABİLİZE-LITE (ZORUNLU — ATLANAMAZ, ~5 dk)

> **Her deploy sonrası çalışan minimum kalite kontrolü. Tam `/stabilize` yerine bu yeterlidir.**

### Kontrol 1: Deploy Status
- Railway GraphQL → Son deployment status `SUCCESS` mi?
- Değilse → log oku, düzelt, tekrar deploy

### Kontrol 2: Runtime Log Taraması
```bash
export RAILWAY_TOKEN=$(grep RAILWAY_TOKEN _knowledge/credentials/master.env | cut -d '=' -f2)
# Son 100 log satırında fatal error ara
_skills/use-railway/scripts/railway-api.sh '{ deploymentLogs(deploymentId: "DEPLOYMENT_ID", limit: 100) { message severity timestamp } }'
```
Fatal pattern'ler: `Traceback`, `ImportError`, `SyntaxError`, `AttributeError`, `Process exited with code 1`

### Kontrol 3: Env Var Doğrulama
- Proje klasöründe `.env.example` veya `config.py` varsa → oradaki tüm env key'lerinin Railway'de tanımlı olduğunu doğrula

### Kontrol 4: Cron Tetiklemesi (Sadece cron projeler)
- Cron projesi ise → Railway'den manuel redeploy/tetikleme yap
- 90 sn bekle → tekrar log kontrol et
- Cron değilse → bu adımı atla

### Kontrol 5: Platform Checklist
- `_knowledge/platform-checklists/railway.md` → ilgili bölümleri hızlıca kontrol et

**⚠️ BU 5 KONTROL ATLANAMAZ. Bunları geçmeyen deploy "tamamlandı" SAYILMAZ.**

## Adım 8: Kayıt ve Rapor

1. `_knowledge/deploy-registry.md` dosyasına proje bilgilerini ekle/güncelle
2. Kullanıcıya rapor ver:

```
✅ Production Deploy Tamamlandı!

📦 Proje: [Proje Adı]
🔗 GitHub: github.com/dolunayozerennn/antigravity-egitim (mono-repo)
🚂 Railway: https://railway.app/project/PROJE_ID
🔒 Güvenlik: API key'ler environment variable olarak ayarlandı
🧪 Pre-push testler: ✅ Geçti
🛡️ Stabilize-Lite: ✅ 5/5 kontrol geçti

Durum: 7/24 aktif çalışıyor ✨
```

## Adım 9: 📡 48-Saat İzleme Kaydı (ZORUNLU)

> Her deploy sonrası `bekleyen-gorevler.md`'ye izleme kaydı eklenir. Sonraki konuşmalarda otomatik takip edilir.

`_knowledge/bekleyen-gorevler.md`'ye şu entry'yi ekle:
```markdown
### 🟡 48-Saat İzleme — [PROJE_ADI]
- **Deploy tarihi:** [tarih]
- **İzleme bitiş:** [tarih+48h]
- **Kontrol 1:** ⏳ Bekliyor (ilk konuşmada Railway logları kontrol edilecek)
- **Kontrol 2:** ⏳ Bekliyor
- **Sonuç:** ⏳ 2 kontrol temizse kapatılır
```

> ⚠️ İzleme süresi dolana kadar görev `bekleyen-gorevler.md`'de kalır.
> Her konuşma başında bu dosya okunduğunda, izleme görevleri için Railway logları kontrol edilir.
> 2 ardışık temiz kontrol sonrası görev arşive taşınır.

