# Kie AI — Genel API Dokümantasyonu

## Base URL
```
https://api.kie.ai/api/v1/
```

## Kimlik Doğrulama (Authentication)
Tüm istekler şu header'ları gerektirir:
```
Authorization: Bearer 47b22662b68bd510479967aaf8d40a65
Content-Type: application/json
```

## Asenkron Görev Modeli

Kie AI tüm üretim görevlerini **asenkron** olarak işler:

### 1. Görev Oluşturma
```
POST https://api.kie.ai/api/v1/jobs/createTask
```

**İstek gövdesi:**
```json
{
  "model": "model-adı",
  "input": { ... },
  "callBackUrl": "opsiyonel-webhook-url"
}
```

**Başarılı yanıt:**
```json
{
  "code": 200,
  "data": {
    "taskId": "abc123-task-id"
  }
}
```

### 2. Durum Sorgulama
```
GET https://api.kie.ai/api/v1/jobs/recordInfo?taskId={taskId}
```

**Yanıt:**
```json
{
  "code": 200,
  "data": {
    "taskId": "abc123-task-id",
    "model": "model-adı",
    "state": "success | processing | failed",
    "resultJson": "{\"resultUrls\":[\"https://...\"]}",
    "failCode": "",
    "failMsg": "",
    "completeTime": 1700000000000,
    "createTime": 1700000000000,
    "updateTime": 1700000000000
  }
}
```

**state değerleri:**
- `processing` — Hâlâ işleniyor, tekrar sorgula
- `success` — Tamamlandı, `resultJson` içinden URL'leri al
- `failed` — Hata oluştu, `failMsg` kontrol et

### 3. İndirme URL'si Oluşturma (opsiyonel)
```
POST https://api.kie.ai/api/v1/common/download-url
```

### 4. Kredi Bakiye Sorgulama
```
GET https://api.kie.ai/api/v1/chat/credit
```

## Ortak Parametreler

| Parametre | Tip | Zorunlu | Açıklama |
|-----------|-----|---------|----------|
| `model` | string | ✅ | Kullanılacak model adı |
| `input` | object | ✅ | Model-spesifik parametreler |
| `callBackUrl` | string | ❌ | Tamamlandığında bildirim URL'si |

## Dosya Saklama Süresi
Üretilen dosyalar **14 gün** boyunca saklanır.
