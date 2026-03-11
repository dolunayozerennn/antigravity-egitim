# Sora 2 Pro Storyboard — API Dokümantasyonu

## Genel Bilgi
- **Kullanım:** E-ticaret reklam videoları, çok sahneli hikaye anlatımı
- **Süre:** 25 saniyeye kadar video
- **Özellik:** Birden fazla sahne, referans görseller, narratif süreklilik

## Endpoint
```
POST https://api.kie.ai/api/v1/jobs/createTask
```

## Model Adı
```
sora/storyboard
```

## İstek Gövdesi (Request Body)

```json
{
  "model": "sora/storyboard",
  "input": {
    "storyboard": [
      {
        "prompt": "Sahne 1: Kırmızı spor ayakkabı yakın çekimde, beyaz arka plan, profesyonel stüdyo ışıklandırması",
        "image_url": "https://ornek.com/urun-gorseli.jpg",
        "duration": 5
      },
      {
        "prompt": "Sahne 2: Ayakkabı koşan bir atletin ayağında, dinamik hareket, bulanık arka plan",
        "duration": 8
      },
      {
        "prompt": "Sahne 3: Marka logosu ve slogan, fade-out efekti",
        "duration": 4
      }
    ]
  },
  "callBackUrl": "https://webhook.site/callback"
}
```

## Parametreler

### input.storyboard[] (Array — Zorunlu)

Her sahne için:

| Parametre | Tip | Zorunlu | Açıklama |
|-----------|-----|---------|----------|
| `prompt` | string | ✅ | Sahne açıklaması (detaylı olmalı) |
| `image_url` | string | ❌ | Referans görsel URL'si (stil/ton yönlendirmesi) |
| `duration` | number | ❌ | Sahne süresi (saniye). Toplam max 25s |

## Önemli Notlar

### 🚨 KRİTİK: Prompt-Süre Uyumu (Duration Harmony)

> **Bu modelin diğer video modellerinden temel farkı:** Her sahne için prompt ve `duration` ayrı ayrı belirlenir.
> Yazdığınız prompt'taki eylem miktarı ile verdiğiniz saniye **birbiriyle uyumlu olmazsa** sistem düzgün çalışmaz.

**Kural:** Prompt'taki eylemlerin gerçek dünyada gerçekleşme süresi ≈ `duration` değeri olmalıdır.

| duration | Prompt İçerebilir | ❌ İçeremez |
|----------|-------------------|-------------|
| 3s | Statik çekim veya tek basit eylem | Konuşma, çoklu hareket |
| 4-5s | Tek eylem + kamera hareketi | Diyalog, sahne değişimi |
| 6-8s | Ana eylem + ortam + kamera hareketi | Çoklu karakter etkileşimi |
| 8-10s | Sahne + karakter + kamera + atmosfer | Tam hikaye anlatımı |

**Konuşma kuralı:** İnsan ~2-3 kelime/saniye konuşur. 3s sahneye max 9 kelimelik cümle sığar.

```
❌ YANLIŞ: {"prompt": "Adam kafeye girer, masaya oturur, menüye bakar, 
    garsonla konuşur ve kahvesini alır", "duration": 3}
💥 5 eylem + konuşma = 3 saniyeye asla sığmaz!

✅ DOĞRU: {"prompt": "Adam kafeye girer, kapıyı iterek açar", "duration": 3}
✅ DOĞRU: {"prompt": "Adam masada oturur ve kahvesini yudumlar", "duration": 4}
```

### Diğer Notlar
- Toplam süre 25 saniyeyi aşmamalıdır
- Referans görseller, görsel tutarlılık sağlar (karakterler, renkler, aydınlatma)
- Sahneler arası geçişler otomatik olarak yumuşak yapılır
- **İnsan yüzlerinde hata verebilir** — bu durumda Veo 3.1 tercih edin
- Prompt'u İngilizce yazmak daha iyi sonuç verir

## Kullanım Senaryoları
- E-ticaret ürün tanıtım videoları
- Marka reklam filmleri
- Konsept/prototip videoları
- Karakter odaklı hikaye sekansları

# Sora 2 Pro Storyboard API Documentation

> Generate content using the Sora 2 Pro Storyboard model

## Overview

This document describes how to use the Sora 2 Pro Storyboard model for content generation. The process consists of two steps:
1. Create a generation task
2. Query task status and results

## Authentication

All API requests require a Bearer Token in the request header:

```
Authorization: Bearer YOUR_API_KEY
```

Get API Key:
1. Visit [API Key Management Page](https://kie.ai/api-key) to get your API Key
2. Add to request header: `Authorization: Bearer YOUR_API_KEY`

---

## 1. Create Generation Task

### API Information
- **URL**: `POST https://api.kie.ai/api/v1/jobs/createTask`
- **Content-Type**: `application/json`

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model | string | Yes | Model name, format: `sora-2-pro-storyboard` |
| input | object | Yes | Input parameters object |
| callBackUrl | string | No | Callback URL for task completion notifications. If provided, the system will send POST requests to this URL when the task completes (success or fail). If not provided, no callback notifications will be sent. Example: `"https://your-domain.com/api/callback"` |

### Model Parameter

The `model` parameter specifies which AI model to use for content generation.

| Property | Value | Description |
|----------|-------|-------------|
| **Format** | `sora-2-pro-storyboard` | The exact model identifier for this API |
| **Type** | string | Must be passed as a string value |
| **Required** | Yes | This parameter is mandatory for all requests |

> **Note**: The model parameter must match exactly as shown above. Different models have different capabilities and parameter requirements.

### Callback URL Parameter

The `callBackUrl` parameter allows you to receive automatic notifications when your task completes.

| Property | Value | Description |
|----------|-------|-------------|
| **Purpose** | Task completion notification | Receive real-time updates when your task finishes |
| **Method** | POST request | The system sends POST requests to your callback URL |
| **Timing** | When task completes | Notifications sent for both success and failure states |
| **Content** | Query Task API response | Callback content structure is identical to the Query Task API response |
| **Parameters** | Complete request data | The `param` field contains the complete Create Task request parameters, not just the input section |
| **Optional** | Yes | If not provided, no callback notifications will be sent |

**Important Notes:**
- The callback content structure is identical to the Query Task API response
- The `param` field contains the complete Create Task request parameters, not just the input section  
- If `callBackUrl` is not provided, no callback notifications will be sent

### input Object Parameters

#### n_frames
- **Type**: `string`
- **Required**: Yes
- **Description**: Total length of the video
- **Options**:
  - `10`: 10s
  - `15`: 15s
  - `25`: 25s
- **Default Value**: `"15"`

#### image_urls
- **Type**: `array`
- **Required**: No
- **Description**: Please provide the URL of the uploaded file,Upload an image file to use as input for the API
- **Max File Size**: 10MB
- **Accepted File Types**: image/jpeg, image/png, image/webp
- **Multiple Files**: Yes
- **Default Value**: `["https://file.aiquickdraw.com/custom-page/akr/section-images/1760776438785hyue5ogz.png"]`

#### aspect_ratio
- **Type**: `string`
- **Required**: No
- **Description**: This parameter defines the aspect ratio of the image.
- **Options**:
  - `portrait`: portrait
  - `landscape`: landscape
- **Default Value**: `"landscape"`

#### upload_method
- **Type**: `string`
- **Required**: No
- **Description**: Upload destination. Defaults to s3; choose oss for Aliyun storage (better access within China). 
- **Options**:
  - `s3`: s3
  - `oss`: oss
- **Default Value**: `"s3"`

### Request Example

```json
{
  "model": "sora-2-pro-storyboard",
  "input": {
    "n_frames": "15",
    "image_urls": ["https://file.aiquickdraw.com/custom-page/akr/section-images/1760776438785hyue5ogz.png"],
    "aspect_ratio": "landscape",
    "upload_method": "s3"
  }
}
```
### Response Example

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "taskId": "281e5b0*********************f39b9"
  }
}
```

### Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| code | integer | Response status code, 200 indicates success |
| msg | string | Response message |
| data.taskId | string | Task ID for querying task status |

---

## 2. Query Task Status

### API Information
- **URL**: `GET https://api.kie.ai/api/v1/jobs/recordInfo`
- **Parameter**: `taskId` (passed via URL parameter)

### Request Example
```
GET https://api.kie.ai/api/v1/jobs/recordInfo?taskId=281e5b0*********************f39b9
```

### Response Example

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "taskId": "281e5b0*********************f39b9",
    "model": "sora-2-pro-storyboard",
    "state": "waiting",
    "param": "{\"model\":\"sora-2-pro-storyboard\",\"input\":{\"n_frames\":\"15\",\"image_urls\":[\"https://file.aiquickdraw.com/custom-page/akr/section-images/1760776438785hyue5ogz.png\"],\"aspect_ratio\":\"landscape\",\"upload_method\":\"s3\"}}",
    "resultJson": "{\"resultUrls\":[\"https://file.aiquickdraw.com/custom-page/akr/section-images/17607764967900u9630hr.mp4\"]}",
    "failCode": null,
    "failMsg": null,
    "costTime": null,
    "completeTime": null,
    "createTime": 1757584164490
  }
}
```

### Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| code | integer | Response status code, 200 indicates success |
| msg | string | Response message |
| data.taskId | string | Task ID |
| data.model | string | Model name used |
| data.state | string | Task status: `waiting`(waiting),  `success`(success), `fail`(fail) |
| data.param | string | Task parameters (JSON string) |
| data.resultJson | string | Task result (JSON string, available when task is success). Structure depends on outputMediaType: `{resultUrls: []}` for image/media/video, `{resultObject: {}}` for text |
| data.failCode | string | Failure code (available when task fails) |
| data.failMsg | string | Failure message (available when task fails) |
| data.costTime | integer | Task duration in milliseconds (available when task is success) |
| data.completeTime | integer | Completion timestamp (available when task is success) |
| data.createTime | integer | Creation timestamp |

---

## Usage Flow

1. **Create Task**: Call `POST https://api.kie.ai/api/v1/jobs/createTask` to create a generation task
2. **Get Task ID**: Extract `taskId` from the response
3. **Wait for Results**: 
   - If you provided a `callBackUrl`, wait for the callback notification
   - If no `callBackUrl`, poll status by calling `GET https://api.kie.ai/api/v1/jobs/recordInfo`
4. **Get Results**: When `state` is `success`, extract generation results from `resultJson`

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Request successful |
| 400 | Invalid request parameters |
| 401 | Authentication failed, please check API Key |
| 402 | Insufficient account balance |
| 404 | Resource not found |
| 422 | Parameter validation failed |
| 429 | Request rate limit exceeded |
| 500 | Internal server error |

