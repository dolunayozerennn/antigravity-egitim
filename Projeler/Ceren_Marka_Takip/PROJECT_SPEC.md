# Ceren_Marka_Takip — Proje Spesifikasyonu

> Bu dosya projenin tam teknik ve iş spesifikasyonunu içerir.
> Yeni bir chat açıldığında bu dosya okunarak devam edilebilir.

**Son güncelleme:** 2026-04-24
**Durum:** Ceren-only mimariye geçirildi

---

## 1. Problem

Ceren, marka işbirliklerini e-posta üzerinden yönetiyor.
Bazı thread'ler unutuluyor/kaçırılıyor → markaya dönüş yapılmıyor → iş gecikiyor.

## 2. Çözüm

Günlük çalışan bir CronJob:
1. Gmail API ile Ceren'in inbox'ını tarar (son 15 gün)
2. 48+ iş saati sessiz thread'leri bulur
3. LLM ile marka işbirliği thread'lerini tespit eder
4. Ceren'e aksiyon gerektiren thread'ler için hatırlatma maili gönderir
5. Hata durumunda Ceren'e alert gönderir

## 3. Konfigürasyon

### E-posta Hesapları
| Hesap | OAuth Account Key | Rol |
|-------|-------------------|-----|
| `ceren@dolunay.ai` | `ceren` | TARAMA + GÖNDERİM — Ceren'in inbox'ı |

### OAuth Token'ları
Tüm token'lar merkezi depoda hazır:
- `_knowledge/credentials/oauth/gmail-ceren-token.json` ✅ (21 Nisan 2026 oluşturuldu)

Auth modülü: `_knowledge/credentials/oauth/google_auth.py`
Kullanım: `get_gmail_service("ceren")`

### LLM
- **Provider:** Groq
- **Model:** `openai/gpt-oss-120b`
- **API Key:** `master.env` → `GROQ_API_KEY`
- **Base URL:** `https://api.groq.com/openai/v1`

### Bildirimler
- **Ceren hatırlatması:** E-posta → `ceren@dolunay.ai`
- **Hata alerti:** E-posta → `ceren@dolunay.ai`
- **Haftalık rapor:** E-posta → `ceren@dolunay.ai` (her Pazartesi)

### Deploy
- **Platform:** Railway CronJob
- **Schedule:** Her gün 07:00 UTC (10:00 Türkiye)
- **Railway Token:** `master.env` → `RAILWAY_TOKEN`

## 4. İş Kuralları

### Tarama
- Son **15 gün**deki thread'ler taranır
- Sadece `ceren@dolunay.ai` inbox'ı taranır

### Stale Eşiği
- **48 iş saati** (2 iş günü) sessizlik → hatırlatma tetiklenir
- Hafta sonu (Cumartesi-Pazar) iş günü sayılmaz
- Örnek: Cuma 17:00'de atılan mail → Çarşamba 10:00'da (Pazartesi-Salı = 2 iş günü) alarm verir

### LLM Analiz Çıktısı
```json
{
  "is_brand_collaboration": true,
  "brand_name": "Nike Türkiye",
  "last_sender": "brand | ceren | other",
  "action_needed_by_ceren": true,
  "reason": "Marka fiyat teklifi istedi, Ceren henüz cevap vermedi",
  "thread_status": "active | closed | waiting_for_brand",
  "urgency": "high | medium | low"
}
```

### Karar Matrisi
| Son mesajı atan | 48+ saat sessiz | Aksiyon |
|-----------------|-----------------|---------|
| Marka | Evet | ⚠️ Ceren'e hatırlatma |
| Ceren | Evet | ℹ️ Markadan cevap bekleniyor — hatırlatma YOK |
| Thread kapanmış | - | ❌ Atla |

### Tekrar Hatırlatma
- Aynı thread için **2 iş günü** arayla tekrar hatırlatma gönderilir
- Sonsuz hatırlatma — thread cevaplandığında otomatik durur

### Monitoring
| Durum | Ceren'e Bildirim |
|-------|-----------------|
| Hatasız çalıştı, 0 stale thread | Log tutulur, bildirim yok |
| Çalıştı, N hatırlatma gönderildi | Log tutulur, bildirim yok |
| Sistem ÇALIŞAMADI (crash/API hatası) | ⚡ Anlık e-posta alert |
| Haftalık özet (her Pazartesi) | 📊 Haftalık rapor e-postası |

## 5. Dosya Yapısı

```
Ceren_Marka_Takip/
├── PROJECT_SPEC.md          # Bu dosya — proje spesifikasyonu
├── README.md                # Proje açıklaması
├── main.py                  # Ana giriş noktası (CronJob entry point)
├── requirements.txt         # Python bağımlılıkları (versiyonlar kilitli)
├── .gitignore               # Git ignore kuralları
├── .env.example             # Örnek environment variables
│
├── core/
│   ├── __init__.py
│   ├── gmail_scanner.py     # Gmail API ile thread tarama
│   ├── thread_analyzer.py   # LLM ile thread analizi
│   ├── stale_detector.py    # Stale thread tespit mantığı
│   └── notifier.py          # E-posta gönderimi (hatırlatma + alert)
│
├── services/
│   ├── __init__.py
│   ├── groq_client.py       # Groq LLM API client
│   └── gmail_service.py     # Gmail API wrapper (google_auth kullanır)
│
├── utils/
│   ├── __init__.py
│   ├── business_hours.py    # İş günü/saati hesaplama
│   ├── logger.py            # Logging konfigürasyonu
│   └── state_manager.py     # Hatırlatma geçmişi (duplicate engeli)
│
└── data/
    └── reminder_history.json # Son gönderilen hatırlatmalar (state)
```

## 6. Akış Detayı (main.py)

```python
# Pseudocode
def main():
    # 1. Ceren'in inbox'ından thread'leri topla
    threads = gmail_scanner.scan_all_inboxes(days=15)
    
    # 2. Stale thread'leri filtrele (48+ iş saati sessiz)
    stale_threads = stale_detector.filter_stale(threads, threshold_hours=48)
    
    # 3. LLM ile analiz et
    analyzed = []
    for thread in stale_threads:
        result = thread_analyzer.analyze(thread)
        if result.is_brand_collaboration and result.action_needed_by_ceren:
            analyzed.append(result)
    
    # 4. Duplicate hatırlatma kontrolü (2 gün arayla)
    to_notify = state_manager.filter_already_notified(analyzed, cooldown_days=2)
    
    # 5. Ceren'e hatırlatma gönder
    if to_notify:
        notifier.send_reminder_to_ceren(to_notify)
    
    # 6. State güncelle
    state_manager.update(to_notify)
    
    # 7. Log
    logger.info(f"Taranan: {len(threads)}, Stale: {len(stale_threads)}, Bildirim: {len(to_notify)}")
```

## 7. Environment Variables (Railway)

```env
# Gmail OAuth (JSON string olarak)
GOOGLE_CEREN_TOKEN_JSON=<ceren token json>

# Groq LLM
GROQ_API_KEY=<groq api key>

# Notion Ops Logger (State yönetimi)
NOTION_SOCIAL_TOKEN=<notion token>
NOTION_DB_OPS_LOG=<notion db id>

# Monitoring
ALERT_EMAIL=ceren@dolunay.ai
```

## 8. Notion Entegrasyonu (Phase 2 — Gelecek)

Mevcut Notion DB: `27b955140a32838589eb813222d532a2` ("Dolunay Reels")
- Thread status ile Notion status cross-check
- "Marka Onayı Bekliyor" status'ündeki kartların mail takibi
- Bu versiyon için Notion entegrasyonu YOK — sadece Gmail bazlı

## 9. Implementasyon Sırası

- [x] Credential hazırlığı (OAuth token'lar)
- [x] `requirements.txt` oluştur
- [x] `core/gmail_scanner.py` — Gmail thread tarama
- [x] `services/groq_client.py` — Groq LLM client
- [x] `core/thread_analyzer.py` — LLM analiz
- [x] `utils/business_hours.py` — İş günü hesaplama
- [x] `core/stale_detector.py` — Stale tespit
- [x] `core/notifier.py` — E-posta bildirim
- [x] `utils/state_manager.py` — Duplicate engeli
- [x] `main.py` — Ana orkestrasyon
- [x] Syntax + import + birim testleri geçti
- [x] Ceren-only mimariye geçiş (24 Nisan 2026)
- [ ] Lokal test (dry-run) → `python main.py --dry-run`
- [ ] Railway deploy
- [ ] 48-saat izleme
