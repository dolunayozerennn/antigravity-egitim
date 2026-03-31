> ⚠️ **ÖNEMLİ BİLGİLENDİRME**  
> Bu proje, eğitim ve örnekleme amacıyla hazırlanmış olan bir **taslak (template)** projedir. Doğrudan tıklayıp "çalıştır" (plug-and-play) mantığıyla tasarlanmamıştır. Kendi sisteminize entegre etmeden önce:
> - Kimlik bilgilerinizi (API anahtarları, token'lar, email adresleri) tanımlamanız
> - Dosya yollarını (file paths) ve bağlantıları kendi ortamınıza göre güncellemeniz
> - Senaryoyu kendi hedeflerinize göre özelleştirmeniz beklenmektedir.
> Lütfen bu kodları inceleyerek ve kendi senaryonuza uyarlayarak geliştirin.

# 🤖 Shorts Demo Otomasyonu

> **⚠️ TASLAK PROJE:** Bu proje, bir AI otomasyon sisteminin iskelet yapısını göstermek amacıyla paylaşılmıştır. Tam çalışır durumda değildir — kendi topluluğunuza ve iş süreçlerinize göre uyarlamanız ve tamamlamanız beklenmektedir. Telegram bot, OpenAI ve Fal AI API anahtarlarınızı eklemeniz gerekir.

---

## Açıklama

Telegram üzerinden çalışan **tek seferlik YouTube Shorts demo botu**. Kullanıcılar bot'a bir video fikri yazarak AI ile video ürettirebilir. Her kullanıcı **tek bir demo hakkına** sahiptir; admin kullanıcı sınırsız kullanabilir.

### Nasıl Çalışır?

1. Kullanıcı Telegram'dan mesaj yazar (örn: "köpek marketten et çalıyor")
2. **GPT-4.1** mesajı sınıflandırır — sohbet / video fikri / belirsiz
3. Video fikri ise GPT detaylı İngilizce prompt üretir (Sora prompt kurallarına göre)
4. **Fal AI (Sora 2)** ile 9:16 portrait video üretilir (~3-5 dk)
5. Video kullanıcıya Telegram'dan gönderilir
6. Kullanıcının demo hakkı düşer

## Kullanılan Servisler

| Servis | Kullanım |
|--------|----------|
| **Telegram Bot API** | Kullanıcı arayüzü (polling) |
| **OpenAI GPT-4.1** | Mesaj sınıflandırma + prompt üretimi |
| **OpenAI GPT-4.1-mini** | Video üretimi sırasında sohbet yanıtları |
| **Fal AI (Sora 2)** | Video üretim motoru (text-to-video) |

## Özellikler

- ✅ Tek seferlik demo limiti (admin bypass)
- ✅ Video üretimi sırasında sohbet desteği
- ✅ Güvenlik kuralları (sistem/kod bilgisi paylaşmaz)
- ✅ Global error handler
- ✅ Railway container uyumu
- ✅ Progress mesajları

## Environment Variables

| Değişken | Açıklama |
|----------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot tokeni |
| `OPENAI_API_KEY` | OpenAI API anahtarı |
| `FAL_API_KEY` | Fal AI API anahtarı |
| `ADMIN_CHAT_ID` | Admin Telegram chat ID |

---

*Antigravity ile oluşturulmuş taslak projedir.*
