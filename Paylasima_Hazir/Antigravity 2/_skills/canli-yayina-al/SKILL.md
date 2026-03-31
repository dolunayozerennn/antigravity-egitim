---
name: Production Deploy (GitHub + Railway)
description: |
  Bir projeyi Antigravity ortamından production'a taşımak için kullan.
  GitHub MCP üzerinden kod push eder, Railway GraphQL API ile 7/24 deploy eder.
  Kullanıcıyı hiçbir aşamada chat ortamından çıkarmaz.
  ⚠️ KULLANICIYA ASLA "dashboard'a git", "tıkla", "bağla" DEMEZSİN.
  TÜM İŞLEMLER API İLE YAPILIR.
  Bu skill'i şu durumlarda kullan:
  - Kullanıcı "bunu deploy et", "bu 7/24 çalışsın", "production'a al" dediğinde
  - Kullanıcı "Railway'e koy", "GitHub'a push et ve çalıştır" dediğinde
  - Bir bot, otomasyon veya servis sürekli aktif kalması gerektiğinde
  - Kullanıcı "güncelle", "redeploy" dediğinde mevcut deploy'u günceller
---

# 🚀 Production Deploy — Tam Otonom Deployment Skill'i

Bu skill, Antigravity chat ortamından **hiç çıkmadan** bir projeyi GitHub'a push edip Railway'de 7/24 çalışır hale getirmeyi sağlar.

---

## ⛔ MUTLAK KURAL: KULLANICIYA MANUEL İŞLEM YAPTIRMA

```
❌ ASLA şunları söyleme:
  - "Railway dashboard'a git ve repo'yu bağla"
  - "GitHub'da Settings'e gidip..."  
  - "Railway.app'i aç ve..."
  - "Şu linke tıkla..."
  - "Manuel olarak..."

✅ HER ŞEYİ KENDİN YAP:
  - GitHub repo → GitHub MCP araçları ile
  - Railway proje oluşturma → GraphQL API (projectCreate) ile  
  - Railway'e GitHub bağlama → GraphQL API (serviceCreate + source) ile
  - Environment variables → GraphQL API (variableCollectionUpsert) ile
  - Deploy tetikleme → GraphQL API (serviceInstanceRedeploy) ile
  - Log okuma → GraphQL API (deploymentLogs) ile
```

---

## 🎯 Felsefe: Kullanıcı Chat'ten Çıkmaz

Tüm deploy süreci Antigravity tarafından yönetilir:
- **GitHub** → MCP Server üzerinden (repo oluşturma, push, güvenlik)
- **Railway** → GraphQL API üzerinden (proje oluşturma, servis oluşturma, GitHub bağlama, env variables, deploy, monitoring)
- **Kullanıcıdan istenen:** HİÇBİR ŞEY

---

## 🔑 Railway Token (OTOMATİK — Kullanıcıya SORMA)

**Token:** `RAILWAY_TOKEN_BURAYA`

**Kaynaklar (sıralı):**
1. `_skills/canli-yayina-al/scripts/railway-token.txt`
2. `_knowledge/credentials/master.env` → `RAILWAY_TOKEN`
3. `_knowledge/api-anahtarlari.md` → Railway bölümü

**⚠️ ÖNEMLİ:**
- Token'ı kullanıcıdan **ASLA** sorma
- Token'ı commit'e veya log'a **ASLA** yazma
- Her Railway API çağrısında `Authorization: Bearer TOKEN` header'ı kullan

---

## ⚡ ADIM 0 — DEPLOY TÜRÜNÜ BELİRLE (ZORUNLU)

Her deploy talebi geldiğinde **önce mevcut durumu kontrol et**:

```
🔄 DEPLOY AKIŞI — KARAR AĞACI
│
├─ 1. deploy-registry.md kontrol et:
│     → `_knowledge/deploy-registry.md` oku
│     → Bu proje daha önce deploy edilmiş mi?
│
├─ 2. GitHub'da repo var mı?
│     → GitHub MCP → get_file_contents(owner, repo) dene
│     → 404 → repo yok | Dosya → repo var
│
├─ 3. Railway'de proje var mı?
│     → GraphQL: { projects { edges { node { id name } } } }
│
└─ SONUÇ:
   ├─ GitHub ✅ + Railway ✅ → RE-DEPLOY AKIŞI (Bölüm 🔄)
   ├─ GitHub ✅ + Railway ❌ → KISMI YENİ DEPLOY (Adım 3'ten başla)
   └─ GitHub ❌ + Railway ❌ → YENİ DEPLOY AKIŞI (Adım 1'den başla)
```

---

## 🔧 Railway GraphQL API — Temel Çağrı Şablonu

**Endpoint:** `https://backboard.railway.app/graphql/v2`

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer RAILWAY_TOKEN_BURAYA" \
  -d '{"query": "GRAPHQL_QUERY"}'
```

### 📋 Tüm GraphQL Sorgu & Mutation Kataloğu

#### BİLGİ ALMA (Query)

| İşlem | GraphQL |
|-------|---------|
| Proje listesi | `{ projects { edges { node { id name services { edges { node { id name } } } } } } }` |
| Proje detay | `{ project(id: "ID") { id name environments { edges { node { id name } } } services { edges { node { id name } } } } }` |
| Env variables oku | `{ variables(projectId: "P", environmentId: "E", serviceId: "S") }` |
| Deploy durumu | `{ deployments(first: 5, input: { projectId: "P", environmentId: "E", serviceId: "S" }) { edges { node { id status createdAt } } } }` |
| Deploy logları | `{ deploymentLogs(deploymentId: "D", limit: 50) { message timestamp severity } }` |

#### OLUŞTURMA & DEĞİŞTİRME (Mutation)

| İşlem | GraphQL |
|-------|---------|
| **Proje oluştur** | `mutation { projectCreate(input: { name: "proje-adi", description: "aciklama" }) { id name environments { edges { node { id name } } } } }` |
| **Servis oluştur (GitHub'dan)** | `mutation { serviceCreate(input: { projectId: "P", name: "servis-adi", source: { repo: "owner/repo" }, branch: "main" }) { id name } }` |
| **Mevcut servise GitHub bağla** | `mutation { serviceConnect(id: "SERVIS_ID", input: { repo: "owner/repo", branch: "main" }) { id } }` |
| **Servis ayarlarını güncelle** | `mutation { serviceInstanceUpdate(serviceId: "S", environmentId: "E", input: { startCommand: "python main.py", restartPolicyType: ON_FAILURE, restartPolicyMaxRetries: 10 }) }` |
| **Env variable ekle** | `mutation { variableCollectionUpsert(input: { projectId: "P", environmentId: "E", serviceId: "S", variables: { KEY: "VALUE" } }) }` |
| **Redeploy tetikle** | `mutation { serviceInstanceRedeploy(serviceId: "S", environmentId: "E") }` |

---

## 🆕 YENİ DEPLOY AKIŞI (İlk Kez Deploy)

### Adım 1: Güvenlik Kontrolü (Pre-Deploy)

```
[ ] .env dosyası var mı? → .gitignore'a eklenmiş mi?
[ ] Kodun içinde hardcoded API key var mı? → Varsa os.environ.get() ile değiştir
[ ] token.json, credentials.json var mı? → .gitignore'a ekle
[ ] requirements.txt / package.json güncel mi?
[ ] Ana çalışma komutu belli mi? (örn: python bot.py, node index.js)
```

**⚠️ MUTLAKA YAP:**
- `.py`, `.js`, `.ts`, `.env` dosyalarını key pattern'leri için tara:
  - `sk-`, `AIza`, `ghp_`, `gsk_`, `apify_api_`, `pplx-`, `GOCSPX` gibi prefix'ler
  - `os.environ.get('KEY', 'gercek-key-burasi')` gibi fallback'ları da kontrol et

### Adım 1.5: ⚠️ KOD SAĞLIK KONTROLÜ (ZORUNLU — ATLANMAZ!)

> **Bu adım push'tan ÖNCE çalıştırılır. Başarısız olursa PUSH YAPMA.**

**1) Python Syntax Kontrolü:**
```bash
cd PROJE_KLASÖRÜ && python3 -m py_compile *.py 2>&1
```

**2) Import Zinciri Testi (KRİTİK — AttributeError, ImportError gibi hataları yakalar):**
```bash
cd PROJE_KLASÖRÜ && python3 -c "
import sys; sys.path.insert(0, '.')
import importlib, os
errors = []
for f in os.listdir('.'):
    if f.endswith('.py') and f != 'setup.py':
        mod = f[:-3]
        try:
            importlib.import_module(mod)
        except Exception as e:
            errors.append(f'{mod}: {e}')
if errors:
    for e in errors: print(f'❌ {e}')
    sys.exit(1)
else:
    print('✅ Tüm modüller başarıyla import edildi')
"
```

**3) Mevcut Testleri Çalıştır:**
- `tests/` klasörü varsa → `python3 -m pytest tests/ -v` veya `python3 tests/test_*.py`
- `run_test.py` varsa → `python3 run_test.py`
- Test başarısızsa → ❌ PUSH YAPMA

**4) Re-deploy ise: Lokal ↔ GitHub Diff Kontrolü:**
- GitHub'daki dosyalarla lokal dosyaları karşılaştır
- Push edilmemiş değişiklik varsa → bunları da push'a dahil et

**⛔ BU ADIM ATLANILAMAZ. Her push'tan önce çalıştırılmalıdır.**

### Adım 2: Push Dosyalarını Belirle

```
📁 PUSH KARAR AĞACI

1. Proje klasöründeki tüm dosyaları listele
2. .gitignore pattern'lerine göre eleme yap
3. Aşağıdakileri KESİNLİKLE PUSH ETME:
   ❌ .env, *.env, config.env
   ❌ token.json, token.pickle, credentials.json, service-account.json
   ❌ __pycache__/, venv/, .venv/, node_modules/
   ❌ .DS_Store, *.swp, .railway-bin/
   ❌ Büyük dosyalar (>500KB)
4. Listeyi kullanıcıya göster, onay al
5. push_files MCP ile TEK COMMIT'te push et
```

### Adım 3: .gitignore & railway.json Oluştur

**`.gitignore` yoksa** standart template kullan.

**`railway.json` oluştur:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "python DOSYA_ADI.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Adım 4: GitHub'a Push (MCP Üzerinden)

```
1. Private repo oluştur:
   → GitHub MCP → create_repository(name, private: true)

2. Dosyaları push et:
   → GitHub MCP → push_files (tek commit)

3. Push sonrası doğrulama:
   → GitHub MCP → get_file_contents ile kontrol
   → .env push edilmemiş olmalı
```

### Adım 5: Railway Deploy (100% API ile — KULLANICIYA HİÇBİR ŞEY SORDURMA)

Bu adım **tamamen otomatik** yapılır. Kullanıcıya dashboard linki bile verme.

#### 5.1 — Yeni Railway Projesi Oluştur

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "mutation { projectCreate(input: { name: \"PROJE_ADI\", description: \"ACIKLAMA\" }) { id name environments { edges { node { id name } } } } }"}'
```

**Dönen yanıttan al:**
- `project.id` → Proje ID
- `project.environments.edges[0].node.id` → Environment ID (production)

#### 5.2 — GitHub Repo'dan Servis Oluştur

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "mutation { serviceCreate(input: { projectId: \"PROJE_ID\", name: \"SERVIS_ADI\", source: { repo: \"GITHUB_USERNAME_BURAYA/REPO_ADI\" }, branch: \"main\" }) { id name } }"}'
```

> **⚠️ NOT:** Bu mutation direkt GitHub repo'yu Railway servisine bağlar.
> Dashboard'a gitmeye GEREK YOK. `source: { repo: "owner/repo" }` Railway'in 
> GitHub App bağlantısı üzerinden çalışır.

#### 5.3 — Servis Ayarlarını Güncelle (Start Command, Restart Policy)

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "mutation { serviceInstanceUpdate(serviceId: \"SERVIS_ID\", environmentId: \"ENV_ID\", input: { startCommand: \"python main.py\", restartPolicyType: ON_FAILURE, restartPolicyMaxRetries: 10 }) }"}'
```

#### 5.4 — Environment Variables Ayarla

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "mutation { variableCollectionUpsert(input: { projectId: \"PROJE_ID\", environmentId: \"ENV_ID\", serviceId: \"SERVIS_ID\", variables: { KEY1: \"VALUE1\", KEY2: \"VALUE2\" } }) }"}'
```

#### 5.5 — Deploy Tetikle

Servis oluşturulduğunda GitHub repo bağlıysa **otomatik deploy başlar**.
Başlamazsa manuel tetikle:

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "mutation { serviceInstanceRedeploy(serviceId: \"SERVIS_ID\", environmentId: \"ENV_ID\") }"}'
```

#### 5.6 — Deploy Durumunu Takip Et

→ Aşağıdaki "Deployment Durum Takibi" bölümüne bak.

### Adım 6: Post-Deploy Doğrulama, Smoke Test & Kayıt

```
[ ] Deployment SUCCESS mu?
[ ] Environment variables doğru mu?
```

#### ⚠️ SMOKE TEST (ZORUNLU — ATLANMAZ!)

> **Deploy SUCCESS olması servisin çalıştığı anlamına GELMEZ.**
> Smoke test ile production'da gerçekten sağlıklı çalıştığını doğrula.

**1) 60 saniye bekle** (servis başlasın)

**2) Deployment loglarını çek:**
```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "{ deploymentLogs(deploymentId: \"DEPLOY_ID\", limit: 100) { message severity timestamp } }"}'
```

**3) Fatal error pattern'lerini ara:**
- `AttributeError` — özellik bulunamadı (örn: Config.DEDUP_WINDOW_DAYS)
- `ImportError` / `ModuleNotFoundError` — modül eksik
- `SyntaxError` — yazım hatası
- `NameError` — tanımsız değişken
- `KeyError` — eksik anahtar
- `TypeError` — yanlış tip
- `Traceback (most recent call last)` — Python crash
- `Process exited with code 1` — servis çöktü

**4) Sonuç:**
- Fatal error varsa → ❌ Düzelt → Push → Deploy → Smoke test (tekrar)
- Fatal error yoksa → ✅ Smoke test geçti

```
[ ] Smoke test geçti ✅
[ ] deploy-registry.md'ye kaydet ✅
```

**⛔ BU ADIM ATLANILAMAZ. Her deploy sonrası çalıştırılmalıdır.**

---

## 🔄 RE-DEPLOY AKIŞI (Güncelleme)

### R1: Kayıt Defterinden Bilgileri Al
```
→ _knowledge/deploy-registry.md'den proje ID, servis ID, environment ID oku
→ API sorguları minimuma iner
```

### R2: Kod Değişikliklerini GitHub'a Push Et
```
→ GitHub MCP → push_files (değişen + yeni dosyalar)
→ veya create_or_update_file (tek dosya — SHA ile)
→ SHA almak için: get_file_contents
```

### R3: Redeploy Tetikle (Otomatik değilse)
```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "mutation { serviceInstanceRedeploy(serviceId: \"KAYITLI_SERVIS_ID\", environmentId: \"KAYITLI_ENV_ID\") }"}'
```

> **NOT:** Railway GitHub integration aktifse, push sonrası **otomatik deploy** olur.

### R4: Deploy Durumunu Takip Et

---

## 📊 Deployment Durum Takibi

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "{ deployments(first: 3, input: { projectId: \"P\", environmentId: \"E\", serviceId: \"S\" }) { edges { node { id status createdAt } } } }"}'
```

| Status | Anlam | Aksiyon |
|--------|-------|---------|
| `QUEUED` | Sırada | ⏳ 2 dk bekle |
| `BUILDING` | Build ediliyor | ⏳ 2 dk bekle |
| `DEPLOYING` | Container başlatılıyor | ⏳ 1 dk bekle |
| `SUCCESS` | ✅ Çalışıyor | Log kontrol et, rapor ver |
| `FAILED` | ❌ Hata | Log oku, düzelt |
| `CRASHED` | ❌ Çöktü | Log oku, düzelt |

### Polling Stratejisi
```
1. Deploy tetikle
2. 30 saniye bekle  
3. Durum kontrol et
4. QUEUED/BUILDING → 2 dk bekle (max 3 döngü)
5. DEPLOYING → 1 dk bekle
6. SUCCESS → Rapor ver ✅
7. FAILED/CRASHED → Log oku, düzelt
```

---

## 📊 Mevcut Projeye Yeni Servis Ekleme

Bazen yeni bir servis, mevcut bir Railway projesinin içine eklenmek istenir:

```bash
# 1. Mevcut projenin environment ID'sini al
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "{ project(id: \"MEVCUT_PROJE_ID\") { environments { edges { node { id name } } } } }"}'

# 2. Yeni servisi mevcut projeye ekle
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "mutation { serviceCreate(input: { projectId: \"MEVCUT_PROJE_ID\", name: \"yeni-servis\", source: { repo: \"GITHUB_USERNAME_BURAYA/repo-adi\" }, branch: \"main\" }) { id name } }"}'

# 3. Env variables ayarla (aynı environment ID kullanılır)
# 4. Otomatik deploy başlar
```

---

## 📋 Deploy Kayıt Defteri

Her başarılı deploy sonrası **`_knowledge/deploy-registry.md`** dosyasına kaydet:

```markdown
### [Proje Adı]
- **Platform:** `railway`
- **Railway Project ID:** `xxxxx-xxxx-xxxx`
- **Service ID:** `xxxxx-xxxx-xxxx`
- **Environment ID:** `xxxxx-xxxx-xxxx`
- **GitHub Repo:** `GITHUB_USERNAME_BURAYA/repo-adi`
- **Lokal Klasör:** `Projeler/Proje_Adi/`
- **Start Komutu:** `python bot.py`
- **Son Deploy:** YYYY-MM-DD
- **Durum:** ✅ Aktif
```

---

## 🛡️ Güvenlik Protokolü

### Pre-Deploy
1. Kod taraması: hardcoded key'ler → env variable'a çevir
2. .gitignore kontrolü
3. Hassas dosyaların push edilmediğini doğrula

### Post-Deploy  
1. GitHub Secret Scanning uyarısı → varsa key'i revoke et + yenile
2. Railway env variables doğru set edilmiş mi?

---

## ❌ Yaygın Hatalar

| Hata | Çözüm |
|------|-------|
| `ModuleNotFoundError` | requirements.txt eksik → oluştur + push |
| `KeyError: 'ENV_VAR'` | Railway env var eksik → `variableCollectionUpsert` |
| `401 Unauthorized` (API) | Token kontrol et |
| `GitHub Secret Scanning` | Key revoke + yenile + history temizle |
| `Build failed` | runtime.txt veya Python versiyon ekle |

---

## 📁 Dosya Yapısı

```
_skills/canli-yayina-al/
├── SKILL.md                          ← Bu dosya (ana yönerge)
├── scripts/
│   ├── railway.sh                    ← API wrapper script
│   └── railway-token.txt             ← Token (otomatik okunur)
├── platforms/
│   └── railway.md                    ← Railway GraphQL API detayları
├── templates/
│   └── railway.json                  ← Hazır Railway config şablonu
└── checklists/
    └── guvenlik-kontrol.md           ← Pre-deploy güvenlik kontrol listesi
```

---

## 💡 Deploy Tamamlandığında Kullanıcıya Rapor

```
✅ Production Deploy Tamamlandı!

📦 Proje: [Proje Adı]
🔗 GitHub: github.com/GITHUB_USERNAME_BURAYA/repo-adi (private)
🚂 Railway: https://railway.app/project/PROJE_ID
🔒 Güvenlik: API key'ler environment variable olarak ayarlandı

Durum: 7/24 aktif çalışıyor ✨
```
