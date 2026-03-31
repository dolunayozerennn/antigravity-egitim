> ⚠️ **ÖNEMLİ BİLGİLENDİRME**  
> Bu proje, eğitim ve örnekleme amacıyla hazırlanmış olan bir **taslak (template)** projedir. Doğrudan tıklayıp "çalıştır" (plug-and-play) mantığıyla tasarlanmamıştır. Kendi sisteminize entegre etmeden önce:
> - Kimlik bilgilerinizi (API anahtarları, token'lar, email adresleri) tanımlamanız
> - Dosya yollarını (file paths) ve bağlantıları kendi ortamınıza göre güncellemeniz
> - Senaryoyu kendi hedeflerinize göre özelleştirmeniz beklenmektedir.
> Lütfen bu kodları inceleyerek ve kendi senaryonuza uyarlayarak geliştirin.

# 📧 Email Responder — Multi-Agent Sistem

> **⚠️ TASLAK PROJE:** Bu proje, bir AI otomasyon sisteminin iskelet yapısını göstermek amacıyla paylaşılmıştır. Tam çalışır durumda değildir — kendi iş süreçlerinize göre uyarlamanız ve tamamlamanız beklenmektedir. API anahtarlarınızı ve iş kurallarınızı eklemeniz gerekir.

## Proje Amacı
Kurumsal email operasyonlarını (influencer pazarlama, iş birliği yönetimi vb.) **otonom bir AI agent sistemi** ile yönetir.

Gelen e-postaları akıllı bir şekilde sınıflandırır, doğru agent'a yönlendirir ve **otomatik draft** oluşturur. Ayrıca Google Sheets üzerinden outreach email gönderimi, statü takibi ve günlük raporlama yapar.

**⚠️ Hiçbir email otomatik gönderilmez — tüm yanıtlar DRAFT olarak oluşturulur, kullanıcı onaylayıp gönderir.**

---

## Mimari

```
📬 Gmail Inbox
     │
  🧭 Router (Dispatcher)
     ├── Sistem/Bot filtre
     ├── Transactional filtre
     ├── LLM İlgi analizi (Payment/Business/Irrelevant)
     ├── Thread analizi (biz mi başlattık?)
     ├── LLM Cold outreach tespiti (UGC/Cold/Genuine)
     └── Agent yönlendirme
         │
    ┌────┴────┐
    │         │
 🎬 CS      📱 IP
 Agent      Agent
    │         │
 3 Aşama:  3 Aşama:
 Intent →  Intent →
 Draft →   Draft →
 Review    Review
    │         │
    └────┬────┘
         │
      📝 Gmail Draft
```

Her agent kendi bilgi tabanı, template'leri ve LLM prompt'ları ile çalışır. LLM (Groq API) yoksa rule-based fallback otomatik devreye girer.

---

## Modül Yapısı

```
Email_Responder/
├── main.py                      # Ana giriş noktası — tüm fonksiyonları orkestre eder
├── railway_scheduler.py         # Railway scheduler — zamanlanmış görevler
├── railway.json                 # Railway deploy konfigürasyonu
├── feedback_engine.py           # AI Backtesting — agent performans ölçümü
│
├── router/                      # Email yönlendirme katmanı
│   ├── dispatcher.py            # Ana dispatcher — 5 adımlı akıllı filtre + agent yönlendirme
│   └── filters.py               # Sistem/bot/cold email filtre fonksiyonları
│
├── agents/                      # AI Agent'lar
│   ├── base_agent.py            # Ortak agent arayüzü
│   ├── creative_sourcing_agent.py  # 🎬 CS Agent — video/içerik iş birliği iletişimi
│   └── influencer_program_agent.py # 📱 IP Agent — affiliate program iletişimi
│
├── outreach/                    # Outreach email pipeline
│   ├── data_fetcher.py          # Kaynak sheet'ten hedef sheet'e veri aktarımı
│   ├── sheet_mailer.py          # Pending kontaklara outreach email gönderimi
│   ├── status_syncer.py         # Gmail thread statülerini Sheet'te güncelleme
│   └── daily_reporter.py       # Günlük outreach raporu (email ile)
│
├── shared/                      # Ortak utility modülleri
│   ├── google_auth.py           # 🔐 Merkezi OAuth yönetimi
│   ├── gmail_client.py          # Gmail API istemcisi (unread, draft, mark_as_read)
│   ├── sheets_client.py         # Google Sheets API istemcisi
│   ├── llm_client.py            # Groq LLM API istemcisi (4 fonksiyon, retry mekanizmalı)
│   ├── notifier.py              # Hata bildirimi (Email + Telegram fallback)
│   ├── credential_health_checker.py  # Credential sağlık kontrolü
│   ├── email_utils.py           # Email yardımcı fonksiyonları
│   └── api_utils.py             # Genel API yardımcıları
│
├── requirements.txt             # Python bağımlılıkları
└── .env.example                 # Gerekli environment variable şablonu
```

---

## Karar Akışı (Email Responder)

Dispatcher her okunmamış emaili şu sırayla değerlendirir:

| Adım | Kontrol | Aksiyon |
|:-----|:--------|:--------|
| 1 | **Takım üyesi** (kendi domain'iniz) | IGNORE — UNREAD bırak (manuel yanıtlanacak) |
| 2 | **Sistem/Bot** (Notion, Google, Apify vb.) | Mark as read |
| 2.5 | **Transactional** (otomatik raporlar vb.) | Mark as read |
| 2.7 | **LLM İlgi Analizi** — Email sizin işiniz mi? | PAYMENT_COMPLAINT / BUSINESS_PARTNER / IRRELEVANT → Mark as read |
| 3 | **Thread başlangıcı** — Biz mi başlattık? | Thread'in ilk mesajını kontrol et |
| 4a | **Onlar başlattıysa** → LLM Cold Outreach tespiti | UGC_COLD / COLD_EMAIL → Mark as read |
| 4b | **Onlar başlattıysa** → GENUINE | Agent'a yönlendir |
| 5 | **Biz başlattıysak** → Thread tipi belirle (3 katman) | CS Agent veya IP Agent'a yönlendir |

---

## Agent İşlem Süreci (Her İki Agent İçin)

Her agent aynı 3 aşamalı pipeline'ı takip eder:

1. **Intent Tespiti:** LLM ile yanıtın niyetini analiz et (INTERESTED, PAID_ONLY, NOT_INTERESTED, AUTO_REPLY, BOUNCE, vb.)
2. **Draft Üretimi:** Bilgi tabanı + template hint ile bağlama uygun draft üret
3. **Draft Review:** Düşük confidence'lı draft'ları LLM ile review edip iyileştir

**Sonuç:** Gmail'de DRAFT oluşturulur, email UNREAD kalır → kullanıcı kontrol edip gönderir.

---

## LLM Entegrasyonu (Groq API)

`shared/llm_client.py` üzerinden **4 LLM fonksiyonu**:

| Fonksiyon | Amaç |
|:----------|:------|
| `classify_thread_type()` | Thread Creative Sourcing mi, Influencer Program mı? |
| `classify_email_relevance()` | Email sizin sorumluluğunuzda mı? (Payment/Business/Irrelevant) |
| `classify_cold_outreach()` | Inbound email genuine mi, cold pitch mi? |
| `analyze_reply_intent()` | Yanıtın niyeti ne? (INTERESTED, PAID_ONLY, vb.) |
| `generate_draft()` | Bağlama uygun draft email üret |
| `review_and_improve_draft()` | Draft'ı kalite kontrolünden geçir |

**Retry mekanizması:** 3 deneme, exponential backoff, prompt truncation, timeout artırımı.
**Fallback:** LLM çökerse rule-based keyword filtreleri devreye girer.

---

## Deploy

- **Platform:** Railway (Native Cron Job)
- **Start Command:** `python railway_scheduler.py`
- **Cron Schedule:** `0 7,11,15 * * 1-5`
- **Restart Policy:** `NEVER`

---

*Antigravity ile oluşturulmuş taslak projedir.*
