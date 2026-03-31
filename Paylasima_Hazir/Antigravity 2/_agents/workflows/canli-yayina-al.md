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
2. GitHub MCP → `get_file_contents(owner: "GITHUB_USERNAME_BURAYA", repo: "REPO_ADI")` → repo var mı?
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

### 2.5.4 — Lokal ↔ GitHub Diff Kontrolü (Re-deploy için)
```
Re-deploy ise:
1. GitHub MCP ile repo'daki dosyaları listele
2. Lokal proje klasöründeki dosyalarla karşılaştır
3. Lokal'de değişmiş ama GitHub'a push edilmemiş dosya varsa → UYAR ve bunları da push et
```

**⚠️ BU ADIM ATLANILAMAZ. HER PUSH'TAN ÖNCE ÇALIŞTIRILMALIDIR.**

## Adım 3: GitHub'a Push

1. **Repo oluştur:**
   ```
   GitHub MCP → create_repository
   - name: proje-adi (küçük harf, tire ile)  
   - private: true
   ```

2. **Dosyaları belirle ve push et:**
   ```
   GitHub MCP → push_files
   - .env, __pycache__, venv/ KESİNLİKLE PUSH ETME
   - railway.json ve .gitignore ekle
   - Tek commit'te push et
   ```

3. **Doğrula:**
   ```
   GitHub MCP → get_file_contents → hassas dosya push edilmemiş mi?
   ```

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
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "mutation { serviceCreate(input: { projectId: \"PROJE_ID\", name: \"SERVIS_ADI\", source: { repo: \"GITHUB_USERNAME_BURAYA/REPO_ADI\" }, branch: \"main\" }) { id name } }"}'

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

# 5.4 — Deploy otomatik başlar (serviceCreate repo bağladığında)
# Başlamazsa: serviceInstanceRedeploy tetikle
```

## Adım 6: RE-DEPLOY (Güncelleme)

1. `deploy-registry.md`'den Proje ID, Servis ID, Environment ID ve **GitHub Repo** oku
2. **Adım 2.5'i çalıştır** — Kod sağlık kontrolü (ZORUNLU!)
3. **⚠️ ÇIFT-REPO SYNC (KRİTİK — ATLANMAZ!):**
   - deploy-registry.md'deki **GitHub Repo** alanını oku (örn: `GITHUB_USERNAME_BURAYA/tele-satis-crm`)
   - Bu repo `antigravity-egitim` DEĞİLSE → **ayrı repo'ya push gerekiyor!**
   - Prosedür:
     ```bash
     # 1. Ayrı repoyu clone et
     git clone https://github.com/GITHUB_USERNAME_BURAYA/REPO_ADI.git /tmp/REPO_CLONE
     
     # 2. Lokal değişiklikleri kopyala (credential dosyaları HARİÇ)
     cp Projeler/PROJE_KLASÖRÜ/*.py /tmp/REPO_CLONE/
     cp Projeler/PROJE_KLASÖRÜ/requirements.txt /tmp/REPO_CLONE/ 2>/dev/null
     # ... diğer dosyalar
     
     # 3. Commit + push
     cd /tmp/REPO_CLONE
     git config user.email "EMAIL_ADRESI_BURAYA"
     git config user.name "GITHUB_USERNAME_BURAYA"
     git add -A && git commit -m "sync: Güncel lokal kod" && git push origin main
     
     # 4. Temizle
     rm -rf /tmp/REPO_CLONE
     ```
   - Railway otomatik deploy tetikler. Olmazsa → `serviceConnect` mutation'ı kullan
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
🔗 GitHub: github.com/GITHUB_USERNAME_BURAYA/repo-adi (private)
🚂 Railway: https://railway.app/project/PROJE_ID
🔒 Güvenlik: API key'ler environment variable olarak ayarlandı
🧪 Testler: X/X geçti
🔍 Smoke Test: ✅ Loglar temiz

Durum: 7/24 aktif çalışıyor ✨
```
