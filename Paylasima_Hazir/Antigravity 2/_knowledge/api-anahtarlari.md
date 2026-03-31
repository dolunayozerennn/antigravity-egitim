# API Anahtarları Rehberi

Antigravity sisteminin tüm projelerde kullanabilmesi için aşağıdaki anahtarlara ihtiyacınız olabilir. Kendi ihtiyaçlarınıza göre sadece kullanacağınız servislerin kodlarını alarak `credentials/master.env` dosyanıza ekleyebilirsiniz.

## Zorunlu Olmayan Ancak Sık Kullanılanlar

1. **OpenAI API Key (`OPENAI_API_KEY`)**
   - Nereden Alınır: [OpenAI Platform](https://platform.openai.com/api-keys)
   - Ne İçin Kullanılır: Metin üretimi, mail yazma, prompt analizi.

2. **Telegram Bot Token (`TELEGRAM_BOT_TOKEN`)**
   - Nereden Alınır: Telegram uygulamasında `@BotFather` ile konuşarak `/newbot` komutuyla.
   - Ne İçin Kullanılır: Sistem bildirimlerini Telegram'dan tek bir gruba ya da kişiye atabilmek için.
   - Ek Bilgi: Botu oluşturduktan sonra `TELEGRAM_ADMIN_CHAT_ID` değerini (kendi chat ID'niz) de `master.env`'ye eklemelisiniz.

3. **Notion Entegrasyon Anahtarı (`NOTION_TOKEN`)**
   - Nereden Alınır: [Notion Integrations](https://www.notion.so/my-integrations)
   - Ne İçin Kullanılır: Notion veritabanlarına (DB) okuma ve yazma yapmak için.
   - Ek Bilgi: Entegrasyon oluşturulduktan sonra Notion'daki her bir sayfa/DB için ayrıca sağ üstten "Share -> Invite" ile botunuzu eklemeyi unutmayın!

4. **Kie AI / Diğer Görüntü Üreticiler (`KIE_API_KEY`)**
   - Ne İçin Kullanılır: Reels kapak fotoğraflarını üretirken vs.

5. **Apify API Anahtarı (`APIFY_API_KEY`)**
   - Nereden Alınır: [Apify Console](https://console.apify.com/)
   - Ne İçin Kullanılır: Instagram veya diğer sitelerde gelişmiş web scraping (veri kazıma) işlemleri için.

**Not:** Bu dosyada kendi anahtarlarınızı barındırmayın, sadece referans olarak tutun. Anahtarlarınız daima `_knowledge/credentials/master.env` içerisinde durmalıdır ve hiçbir yere push edilmemelidir.
