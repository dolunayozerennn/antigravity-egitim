---
name: Chat_Hafizasi
description: Telegram veya chat tabanlı botların kullanıcı etkileşimlerini merkezi Notion Inline Database'e kaydetmesi için kullanılır. Bot memory, geriye dönük debug ve "dün ne demiştin" tarzı taleplerin analizinde tetiklenir.
---

# 🧠 SKILL: Chat Hafızası (Bot Memory)

## 🎯 Amaç
Bu skill, Antigravity ekosistemindeki herhangi bir Telegram (veya chat tabanlı) botun kullanıcıyla girdiği etkileşimleri merkezi bir Notion Inline Database içerisine kaydetmesini sağlar.
Bu yetenek, botların geriye dönük debug edilmesini ve "Dün saat 15:00'te bana şöyle dedin" gibi taleplerin analiz edilebilmesini sağlar.

## 📦 Kurulum ve Entegrasyon
Bu skill'i farklı bir projeye uygulamak istediğinde aşağıdaki standartları takip et:

### 1. Çevresel Değişkenler (ENV) Eklemesi
Tüm botlar, etkileşimleri **Ortak Bot Hafızası** adlı Notion tablosuna kaydeder.
`master.env` ve Railway'deki ilgili projenin değişkenlerine şu eklenmelidir:
```env
NOTION_CHAT_DB_ID=34095514-0a32-81c9-94a6-f269b060c377
NOTION_SOCIAL_TOKEN=secret_xxx  # Workspace 2 yetkisi
```

*(Kullanıcı Deneyimi Notu - Railway Bypass):* Eğer kullanıcının Railway paneline girip manuel iş yapmasını istemiyorsan, bu ID statik ve güvenli bir tablo ID'si olduğu için `config.py` içerisine `os.environ.get("NOTION_CHAT_DB_ID", "34095514-...")` şeklinde fallback / hardcoded olarak doğrudan gömebilirsin.

### 2. Modül: `infrastructure/chat_logger.py`
Yeni projede bir `chat_logger.py` dosyası oluştur:
- `requests` kullanılmalı, API url: `https://api.notion.com/v1/pages`.
- Timeout: 5 saniye (uzun süren network işlemlerinin botu tıkamaması için).
- Fonksiyon, `asyncio.to_thread` ile asenkron (non-blocking) olarak arka planda çalıştırılmalıdır (Event Loop'u bloklamamak esastır).

**Gerekli Alanlar (Properties):**
- `Session ID` (Title): Genellikle kullanıcının Telegram ID'si veya uuid.
- `Kullanıcı Mesajı` (Rich Text): Kullanıcının attığı mesaj.
- `Bot Yanıtı` (Rich Text): Sistem/Bot tarafından üretilen yanıt.
- `Bot` (Select): Botun Adı (örn: "E-Com Bot").
- `Tarih` (Created Time): Zaman damgası. *(Notion tarafından otomatik atandığı için, log koduna ayrıca zaman yazılmasına gerek kalmaz).*

### 3. Kullanım (Ana Handler İçerisine Inject Etme)
Telegram mesajlarını karşılayan `Controller` / `Handler` modüllerinde entegre edilir:

```python
from infrastructure.chat_logger import chat_tracker

# Kullanıcıya yanıt gönderildikten HEMEN SONRA:
await chat_tracker.log_interaction(
    session_id=str(user.id),
    user_msg=text,
    bot_reply=reply,
    bot_name="Yeni Bot Adı"
)
```

## ⚠️ Kritik Çökme Korumaları (Safety Guardrails)
1. **Asenkron Çalışma:** Asla `await` ile doğrudan `requests.post` çağrısı YAPMA! Bu, Telegram polling altyapısını kilitler. Her zaman `await asyncio.to_thread(_do_request)` kullan.
2. **Karakter Limitleri:** Notion zengin metinleri maksimum 2000 karakter destekler, Notion API hatasını önlemek için gelen yazıları ve yanıtları formatla: `str(user_msg)[:2000]`.
3. **Kesinti Koruma:** Notion server yanıt vermezse veya bağlantı koparsa `log_interaction` fonksiyonu, `try/except` ile exception yutmalı ve ana bot/uygulama pipeline'ını asla durdurmamalıdır.
