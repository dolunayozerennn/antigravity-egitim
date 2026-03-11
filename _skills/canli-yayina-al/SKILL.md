---
name: Production Deploy (GitHub + Railway)
description: |
  Bir projeyi Antigravity test ortamından production'a taşımak için kullan.
  GitHub MCP üzerinden kod push eder, Railway üzerinden 7/24 deploy eder.
  Kullanıcıyı hiçbir aşamada chat ortamından çıkarmaz.
  Bu skill'i şu durumlarda kullan:
  - Kullanıcı "bunu deploy et", "bu 7/24 çalışsın", "production'a al" dediğinde
  - Kullanıcı "Railway'e koy", "GitHub'a push et ve çalıştır" dediğinde
  - Bir bot, otomasyon veya servis sürekli aktif kalması gerektiğinde
  - Kullanıcı "güncelle", "redeploy" dediğinde mevcut deploy'u günceller
---

# 🚀 Production Deploy — Uçtan Uca Deployment Skill'i

Bu skill, Antigravity chat ortamından **hiç çıkmadan** bir projeyi GitHub'a push edip Railway'de 7/24 çalışır hale getirmeyi sağlar.

---

## 🎯 Felsefe: Kullanıcı Chat'ten Çıkmaz

Tüm deploy süreci Antigravity tarafından yönetilir:
- **GitHub** → MCP Server üzerinden (repo oluşturma, push, güvenlik)
- **Railway** → GraphQL API üzerinden (deploy, env variables, monitoring)
- **Kullanıcıdan istenen tek şey:** Railway Token (bir kez)

---

## ⚡ ADIM 0 — İLK ADIM: Deploy Türünü Belirle (ZORUNLU)

Her deploy talebi geldiğinde **önce mevcut durumu kontrol et**, sonra uygun akışa geç.

```
🔄 DEPLOY AKIŞI — KARAR AĞACI
│
├─ 1. Proje kayıt defterini kontrol et:
│     → `_knowledge/deploy-registry.md` dosyasını oku
│     → Bu proje daha önce deploy edilmiş mi?
│
├─ 2. GitHub'da repo var mı kontrol et:
│     → GitHub MCP → get_file_contents(owner, repo) ile repo erişimi dene
│     → 404 alırsa → repo yok
│     → Dosya dönerse → repo mevcut
│
├─ 3. Railway'de proje var mı kontrol et:
│     → GraphQL API → projects listesi al
│     → Proje adıyla eşleşen var mı bak
│
└─ SONUÇ:
   ├─ GitHub ✅ + Railway ✅ → RE-DEPLOY AKIŞI (Bölüm 🔄)
   ├─ GitHub ✅ + Railway ❌ → KISMI YENİ DEPLOY (Adım 3'ten başla)
   └─ GitHub ❌ + Railway ❌ → YENİ DEPLOY AKIŞI (Adım 1'den başla)
```

---

## 📋 Ön Gereksinimler

### Her Zaman Mevcut
- ✅ GitHub MCP Server bağlı (Antigravity zaten bu donanıma sahip)
- ✅ GitHub hesabı: `dolunayozerennn`

### 🔑 Railway Token (OTOMATİK BULUNUR — Kullanıcıya SORMA)

**Token kaynağı:** `_knowledge/api-anahtarlari.md` → Railway bölümü

**Token okuma prosedürü (HER deploy'da uygula):**
1. `view_file` tool'u ile `_knowledge/api-anahtarlari.md` dosyasını oku
2. `### Railway` bölümünden token'ı al (backtick'ler arasındaki UUID)
3. Token'ı her Railway API çağrısında `Authorization: Bearer TOKEN` header'ı olarak kullan

**⚠️ ÖNEMLİ KURALLAR:**
- Token `HENÜZ_KAYDEDİLMEDİ` yazıyorsa → kullanıcıdan **bir kez** iste ve dosyaya kaydet
- Token bir kez kaydedildikten sonra bir daha **ASLA** kullanıcıya sorma
- Token'ı hiçbir zaman commit'e veya log'a yazma

---

## 🔧 Railway Komutlarını Çalıştırma

### Yöntem A — GraphQL API (BİRİNCİL — HER ZAMAN ÇALIŞIR)

GraphQL API, Railway işlemlerinin **ana yöntemidir**. Token ile her zaman çalışır.

**Temel API çağrı şablonu:**
```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer RAILWAY_TOKEN" \
  -d '{"query": "GRAPHQL_QUERY"}'
```

**Hazır GraphQL Sorguları:**

#### 1. Proje Listesi (tüm projeler + servisler):
```graphql
{ projects { edges { node { id name services { edges { node { id name } } } } } } }
```

#### 2. Environment'ları Listele:
```graphql
{ project(id: "PROJE_ID") { environments { edges { node { id name } } } } }
```

#### 3. Environment Variable Okuma:
```graphql
{ variables(projectId: "PROJE_ID", environmentId: "ENV_ID", serviceId: "SERVIS_ID") }
```

#### 4. Environment Variable Yazma/Güncelleme:
```graphql
mutation { variableCollectionUpsert(input: {
  projectId: "PROJE_ID",
  environmentId: "ENV_ID",
  serviceId: "SERVIS_ID",
  variables: { KEY: "VALUE" }
}) }
```

#### 5. Redeploy Tetikleme:
```graphql
mutation { serviceInstanceRedeploy(serviceId: "SERVIS_ID", environmentId: "ENV_ID") }
```

#### 6. Son Deployment'ların Durumunu Kontrol:
```graphql
{ deployments(first: 5, input: { projectId: "PROJE_ID", environmentId: "ENV_ID", serviceId: "SERVIS_ID" }) {
  edges { node { id status createdAt } }
} }
```

#### 7. Deployment Loglarını Oku:
```graphql
{ deploymentLogs(deploymentId: "DEPLOY_ID", limit: 50) {
  message timestamp severity
} }
```

### Yöntem B — CLI (OPSİYONEL — Sadece Global Kurulumda)

CLI, token sorunları nedeniyle **her zaman çalışmayabilir**. Yalnızca global kurulum varsa dene:

```bash
# CLI mevcut mu kontrol et:
which railway

# Varsa token ile çalıştır:
RAILWAY_TOKEN="token" railway <komut>
```

**⚠️ CLI `Unauthorized` hatası verirse → Zaman kaybetme, direkt GraphQL API'ye geç.**

---

## 🆕 YENİ DEPLOY AKIŞI (İlk Kez Deploy)

### Adım 1: Güvenlik Kontrolü (Pre-Deploy)

Deploy'dan **ÖNCE** bu kontrol listesini uygula:

```
[ ] .env dosyası var mı? → .gitignore'a eklenmiş mi?
[ ] Kodun içinde hardcoded API key var mı? → Varsa environment variable'a çevir
[ ] token.json, credentials.json gibi hassas dosyalar var mı? → .gitignore'a ekle
[ ] requirements.txt / package.json güncel mi?
[ ] Ana çalışma komutu belli mi? (örn: python bot.py, node index.js)
```

**⚠️ MUTLAKA YAP:**
- Tüm `.py`, `.js`, `.ts`, `.env` dosyalarını API key pattern'leri için tara:
  - `sk-`, `AIza`, `ghp_`, `gsk_`, `apify_api_`, `pplx-`, `GOCSPX` gibi prefix'ler
  - Hardcoded token'lar varsa `os.environ.get()` veya `os.getenv()` ile değiştir
  - ⚠️ **Fallback değerlerini de kontrol et!** `os.environ.get('KEY', 'gercek-key-burasi')` gibi kullanımlar da tehlikelidir

### Adım 2: Push Edilecek Dosyaları Belirle (Push Karar Ağacı)

GitHub'a dosya push etmeden **önce** bu karar ağacını uygula:

```
📁 PUSH KARAR AĞACI

1. Proje klasöründeki tüm dosyaları listele (list_dir veya find_by_name)

2. .gitignore pattern'lerine göre eleme yap

3. Aşağıdaki dosyaları KESİNLİKLE PUSH ETME:
   ❌ .env, *.env, config.env
   ❌ token.json, token.pickle, credentials.json, service-account.json
   ❌ __pycache__/, venv/, .venv/, node_modules/
   ❌ .DS_Store, *.swp, *.swo
   ❌ .railway-bin/
   ❌ Büyük dosyalar (>500KB — history_analysis.json, *.pickle gibi)
   ❌ İzleme/debug dosyaları (*.log, debug_*, test_output_*)

4. PUSH EDİLECEK dosyaları tek liste halinde kullanıcıya göster:
   "📤 Push edilecek dosyalar: bot.py, requirements.txt, railway.json, .gitignore"

5. Kullanıcıdan onay al, sonra push_files MCP ile TEK COMMIT'te push et
```

### Adım 3: .gitignore & railway.json Oluştur

**`.gitignore` yoksa veya eksikse** `templates/.gitignore.template` şablonunu kullan.

**`railway.json` oluştur** — projenin kök dizinine:

**Python projeleri için:**
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

**Node.js projeleri için:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "node DOSYA_ADI.js",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Adım 4: GitHub'a Push (MCP Üzerinden)

1. **Private repo oluştur:**
   ```
   GitHub MCP → create_repository
   - name: proje-adi (küçük harf, tire ile)
   - private: true
   - description: Kısa açıklama + "(runs on Railway)" notu
   ```

2. **Dosyaları push et (Adım 2'deki listeye göre):**
   ```
   GitHub MCP → push_files
   - Adım 2'de belirlenen dosya listesini TEK COMMIT'te push et
   - ⚠️ ASLA şunları push etme: .env, token.json, credentials.json, __pycache__, venv/
   ```

3. **Push sonrası doğrulama:**
   ```
   GitHub MCP → get_file_contents ile repo'daki dosyaları kontrol et
   - .env push edilmemiş olmalı
   - API key içeren dosya push edilmemiş olmalı
   ```

### Adım 5: Railway Deploy (GraphQL API ile)

1. **Token'ı oku** → `_knowledge/api-anahtarlari.md` dosyasından `view_file` ile

2. **Railway'de GitHub repo bağlantısı kur:**
   - Kullanıcıya Railway dashboard linkini ver:
     `https://railway.app/new/github → repo seç`
   - VEYA mevcut bir Railway projesine GitHub repo bağla

3. **Projeyi bul veya oluştur (API ile):**
   ```graphql
   { projects { edges { node { id name services { edges { node { id name } } } } } } }
   ```

4. **Environment Variables ayarla (API ile):**
   ```graphql
   mutation { variableCollectionUpsert(input: {
     projectId: "PROJE_ID", environmentId: "ENV_ID", serviceId: "SERVIS_ID",
     variables: { KEY1: "VALUE1", KEY2: "VALUE2" }
   }) }
   ```

5. **Deploy tetikle (API ile):**
   ```graphql
   mutation { serviceInstanceRedeploy(serviceId: "SERVIS_ID", environmentId: "ENV_ID") }
   ```

6. **Deployment durumunu takip et** → Aşağıdaki "Deployment Durum Takibi" bölümüne bak

### Adım 6: Post-Deploy Doğrulama & Kayıt

```
[ ] Deployment durumu SUCCESS mu? (Durum Takibi bölümüne bak)
[ ] Loglar temiz mi? Hata yok mu?
[ ] Servis başarıyla başladı mı?
[ ] GitHub Secret Scanning uyarısı var mı? → Varsa hemen düzelt
[ ] Environment variables doğru set edilmiş mi?
```

**✅ Her başarılı deploy sonrası → `_knowledge/deploy-registry.md` dosyasına kaydet** (Bölüm 📋'ye bak)

---

## 🔄 RE-DEPLOY AKIŞI (Güncelleme)

Proje zaten deploy edildiyse (Adım 0'da tespit edildiyse):

### R1: Kayıt Defterinden Bilgileri Al
```
→ _knowledge/deploy-registry.md'den proje ID, servis ID, environment ID'yi oku
→ Bu sayede API sorguları minimuma iner (proje aramaya gerek yok)
```

### R2: Kod Değişikliklerini GitHub'a Push Et
```
GitHub MCP → push_files (değişen + yeni dosyalar)
veya
GitHub MCP → create_or_update_file (tek dosya güncelleme — SHA ile)
```
**Dosyaların SHA'larını almak için:** `GitHub MCP → get_file_contents` kullan

### R3: Redeploy Tetikle
```graphql
mutation { serviceInstanceRedeploy(serviceId: "KAYITLI_SERVIS_ID", environmentId: "KAYITLI_ENV_ID") }
```
> **NOT:** Railway GitHub integration aktifse, GitHub'a push sonrası **otomatik deploy** olur. Bu durumda R3'ü atla.

### R4: Deployment Durumunu Takip Et
→ Aşağıdaki "Deployment Durum Takibi" bölümüne bak

---

## 📊 Deployment Durum Takibi

Deploy tetiklendikten sonra GraphQL API ile durumu periyodik kontrol et:

```graphql
{ deployments(first: 3, input: {
    projectId: "PROJE_ID", environmentId: "ENV_ID", serviceId: "SERVIS_ID"
  }) { edges { node { id status createdAt } } }
}
```

### Durum Tablosu

| Status      | Anlam                        | Aksiyon                                   |
|-------------|------------------------------|-------------------------------------------|
| `QUEUED`    | Build sırasında bekliyor     | ⏳ 2 dk bekle, tekrar kontrol et          |
| `BUILDING`  | Build ediliyor               | ⏳ 2 dk bekle, tekrar kontrol et          |
| `DEPLOYING` | Container başlatılıyor       | ⏳ 1 dk bekle, tekrar kontrol et          |
| `SUCCESS`   | ✅ Çalışıyor                 | Log kontrol et, kullanıcıya rapor ver     |
| `FAILED`    | ❌ Build veya start hatası   | Log oku, hatayı analiz et ve çöz          |
| `CRASHED`   | ❌ Uygulama çalışırken çöktü | Log oku, crash nedenini bul               |
| `SKIPPED`   | Önceki deploy tarafından atlandı | ⚪ Normal, yoksay                      |

### Polling Stratejisi

```
1. Deploy tetikle
2. 30 saniye bekle
3. Durum kontrol et (API çağrısı)
4. QUEUED veya BUILDING ise → 2 dk bekle, tekrar kontrol (max 3 döngü)
5. DEPLOYING ise → 1 dk bekle, tekrar kontrol
6. SUCCESS ise → Log oku, kullanıcıya rapor ver ✅
7. FAILED/CRASHED ise → Log oku, hatayı çöz
```

### ⏱️ Timeout Kuralları

- **5 dakikadan uzun QUEUED kalırsa:**
  → Kullanıcıya bilgi ver:
  > "Railway build kuyruğu yoğun, deployment sıraya alındı.
  > Dashboard'dan takip edebilirsin: https://railway.app/project/PROJE_ID"

- **Önceki SUCCESS deployment zaten aktifse:**
  → Yeni deployment QUEUED kalsa bile mevcut servis çalışmaya **devam eder**.
  → Kullanıcıya: *"Mevcut versiyon aktif çalışıyor, yeni versiyon build kuyruğunda"* de.

---

## 📋 Deploy Edilmiş Projeler Kayıt Defteri

Her başarılı deploy sonrası **`_knowledge/deploy-registry.md`** dosyasına proje bilgilerini kaydet.

**Kayıt formatı:**
```markdown
### [Proje Adı]
- **Railway Project ID:** `xxxxx-xxxx-xxxx`
- **Service ID:** `xxxxx-xxxx-xxxx`
- **Environment ID:** `xxxxx-xxxx-xxxx`
- **GitHub Repo:** `dolunayozerennn/repo-adi`
- **Start Komutu:** `python bot.py`
- **Son Deploy:** 2026-03-10
- **Durum:** ✅ Aktif
```

Bu kayıt defteri sayesinde:
- Re-deploy'larda ID araması yapılmaz (anında erişim)
- Mevcut deployment'lar kolayca kontrol edilir
- Proje bilgileri tek yerde saklanır

---

## 🛡️ Güvenlik Protokolü

### Pre-Deploy (Push öncesi)
1. **Kod taraması:** `grep -rn --include="*.py" --include="*.js" --include="*.ts" "sk-\|AIza\|ghp_\|gsk_\|apify_api_\|pplx-\|GOCSPX\|environ.get.*'[a-zA-Z0-9_-]\{10,\}'" .`
2. **Hardcoded key varsa:** `os.environ.get('KEY_NAME')` ile değiştir
3. **.gitignore:** Şablonu uygula
4. **Dosya kontrolü:** .env, token.json, credentials.json push edilmeyecek

### Post-Deploy (Push sonrası)
1. **GitHub Secret Scanning:** Push sonrası uyarı gelirse hemen:
   - Sızan key'i revoke et (servis sağlayıcıdan)
   - Yeni key al
   - Railway env variable güncelle
   - Git history'den temizle (gerekirse force push)

---

## ❌ Yaygın Hatalar ve Çözümler

| Hata | Neden | Çözüm |
|------|-------|-------|
| `ModuleNotFoundError` | requirements.txt eksik | `pip freeze > requirements.txt` ve push |
| `KeyError: 'ENV_VAR'` | Railway'de env var set edilmemiş | API ile `variableCollectionUpsert` yap |
| `401 Unauthorized` (API) | Token yanlış veya süresi dolmuş | `_knowledge/api-anahtarlari.md` kontrol et |
| `401 Unauthorized` (CLI) | CLI token uyumsuzluğu | **CLI'yı bırak, GraphQL API kullan** |
| `GitHub Secret Scanning Alert` | API key commit'e girmiş | Key'i revoke et, yenisini al, history temizle |
| `Build failed` | Python/Node versiyon uyumsuzluğu | `runtime.txt` veya `engines` alanı ekle |
| `QUEUED uzun sürüyor` | Railway build kuyruğu yoğun | Bekle veya dashboard'dan takip et |

---

## 📁 Dosya Yapısı

```
_skills/canli-yayina-al/
├── SKILL.md                          ← Bu dosya (ana yönerge)
├── scripts/
│   └── railway.sh                    ← Token otomatik bulma + API wrapper
├── platforms/
│   └── railway.md                    ← Railway GraphQL API detayları ve hazır sorgular
├── templates/
│   ├── railway.json                  ← Hazır Railway config şablonu
│   └── .gitignore.template           ← Güvenli .gitignore şablonu
└── checklists/
    └── guvenlik-kontrol.md           ← Pre-deploy güvenlik kontrol listesi
```

## 📁 İlişkili Kaynaklar

- `_knowledge/api-anahtarlari.md` — Railway Token burada (otomatik okunur)
- `_knowledge/deploy-registry.md` — Deploy edilen projelerin ID kayıt defteri
- `_skills/proje-paylasimi/SKILL.md` — Proje paylaşım güvenlik kuralları

---

## 💡 Kullanıcıya Söylenecek Prompt Şablonu

Deploy tamamlandığında kullanıcıya şu formatta rapor ver:

```
✅ Production Deploy Tamamlandı!

📦 Proje: [Proje Adı]
🔗 GitHub: github.com/dolunayozerennn/repo-adi (private)
🚂 Railway: https://railway.app/project/PROJE_ID
🔒 Güvenlik: API key'ler environment variable olarak ayarlandı

Durum: 7/24 aktif çalışıyor ✨
```
