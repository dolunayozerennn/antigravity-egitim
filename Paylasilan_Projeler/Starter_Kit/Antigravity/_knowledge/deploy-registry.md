# 🚀 Deploy Registry — Deployment Kayıt Defteri

Bu dosya, Railway'e deploy edilmiş projelerin kayıt defteridir.

---

## Aktif Deployment'lar

| Proje | Railway Proje ID | Service ID | Ortam | Tip | Durum |
|-------|-----------------|------------|-------|-----|-------|
| _(İlk deploy'unuzda buraya ekleyin)_ | | | production | | |

---

## Deploy Bilgileri Nasıl Eklenir?

Her başarılı deploy sonrasında şu bilgileri ekleyin:

```markdown
| Proje_Adı | prj_xxxxx | srv_xxxxx | production | Worker/Cron | ✅ Aktif |
```

### Gerekli Bilgiler:
- **Railway Proje ID:** GraphQL API'den veya Railway dashboard'dan alınır
- **Service ID:** Aynı projede birden fazla servis olabilir
- **Ortam:** `production` veya `staging`
- **Tip:** `Worker` (7/24), `Cron` (zamanlanmış), `Web` (HTTP)
- **Durum:** ✅ Aktif, ⏸️ Durduruldu, ❌ Kapatıldı

---

## Arşiv (Kapatılmış/Taşınmış)

| Proje | Kapatılma Tarihi | Neden |
|-------|-----------------|-------|
| _(Gerektiğinde buraya taşıyın)_ | | |
