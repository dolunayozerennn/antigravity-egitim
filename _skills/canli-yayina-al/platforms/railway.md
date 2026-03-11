# Railway Deployment Detayları

## Railway Nedir?
Railway, GitHub repo'sundan otomatik deploy yapabilen bir PaaS (Platform as a Service) servisidir.
Heroku'nun modern alternatifi olarak düşünülebilir.

---

## 🔧 Bağlantı Yöntemleri

### Yöntem A: GraphQL API (BİRİNCİL — Her Zaman Çalışır)

Railway's GraphQL API, token ile **her zaman güvenilir şekilde** çalışır.
CLI'da yaşanan `Unauthorized` sorunları API'de yaşanmaz.

**Endpoint:** `https://backboard.railway.app/graphql/v2`

**Header'lar:**
```
Content-Type: application/json
Authorization: Bearer RAILWAY_TOKEN
```

**Temel cURL şablonu:**
```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "GRAPHQL_QUERY"}'
```

### Hazır GraphQL Sorgu Kataloğu

#### 📋 Bilgi Alma Sorguları

**Tüm projeleri listele:**
```graphql
{
  projects {
    edges {
      node {
        id
        name
        services { edges { node { id name } } }
      }
    }
  }
}
```

**Bir projenin environment'larını listele:**
```graphql
{
  project(id: "PROJE_ID") {
    environments {
      edges { node { id name } }
    }
  }
}
```

**Environment variable'ları oku:**
```graphql
{
  variables(
    projectId: "PROJE_ID"
    environmentId: "ENV_ID"
    serviceId: "SERVIS_ID"
  )
}
```

**Son deployment'ları kontrol et:**
```graphql
{
  deployments(
    first: 5
    input: {
      projectId: "PROJE_ID"
      environmentId: "ENV_ID"
      serviceId: "SERVIS_ID"
    }
  ) {
    edges {
      node { id status createdAt }
    }
  }
}
```

**Deployment loglarını oku:**
```graphql
{
  deploymentLogs(deploymentId: "DEPLOY_ID", limit: 50) {
    message
    timestamp
    severity
  }
}
```

#### ✏️ Değiştirme Mutation'ları

**Environment variable ekle/güncelle:**
```graphql
mutation {
  variableCollectionUpsert(input: {
    projectId: "PROJE_ID"
    environmentId: "ENV_ID"
    serviceId: "SERVIS_ID"
    variables: {
      KEY1: "VALUE1"
      KEY2: "VALUE2"
    }
  })
}
```

**Redeploy tetikle:**
```graphql
mutation {
  serviceInstanceRedeploy(
    serviceId: "SERVIS_ID"
    environmentId: "ENV_ID"
  )
}
```

---

### Yöntem B: CLI (OPSİYONEL — Güvenilirliği Düşük)

⚠️ **DİKKAT:** Railway CLI, `RAILWAY_TOKEN` env variable'ı ile tüm komutları çalıştıramayabilir.
Özellikle `link` ve `up` komutları `railway login` session'ı gerektirebilir.
**CLI `Unauthorized` verirse → zaman kaybetme, direkt GraphQL API kullan.**

```bash
# Global CLI kurulumu (varsa):
which railway

# Token ile kullan:
RAILWAY_TOKEN="token" railway <komut>
```

**CLI Komutları (Sadece çalışırsa):**
```bash
railway init               # Yeni proje oluştur
railway link               # Mevcut projeye bağlan
railway up                 # Deploy et
railway logs               # Logları gör
railway logs --tail        # Canlı log takibi
railway variables          # Env var'ları listele
railway variables set K=V  # Env var ekle
railway status             # Durum kontrolü
```

---

## Railway Token Alma
1. https://railway.app/account/tokens adresine git
2. "Create Token" tıkla
3. Token'ı kopyala
4. `_knowledge/api-anahtarlari.md` → Railway bölümüne kaydet (sadece bir kez)

## Pricing
- **Trial:** $5 kredi (yeni hesaplar)
- **Hobby:** $5/ay + kullanım bazlı
- **Pro:** $20/ay
- Bot'lar ve hafif servisler genellikle aylık $1-3 tutar

## Önemli Notlar
- Railway `Procfile` veya `railway.json` ile start komutu belirler
- Python projeleri için `requirements.txt` gerekli
- Node projeleri için `package.json` gerekli
- Environment variables Railway dashboard'dan veya API'den yönetilir
- `.env` dosyası Railway'de kullanılmaz — her şey env var olarak set edilir
