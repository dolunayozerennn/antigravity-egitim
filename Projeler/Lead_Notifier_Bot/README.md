# Lead Notifier Bot

Bu proje, belirlenen bir Google Sheets dosyasındaki yeni satırları (leadleri) tarar ve yeni bir ekleme algıladığı anda hem E-Posta adresine hem de Telegram botu aracılığıyla belirttiğiniz sohbete anlık bildirim atar. `Tele_Satis_CRM` alt yapısı örnek alınarak yazılmıştır ancak içerisine Notion entegrasyonu veya spesifik "telefon formatı" kuralları içermez. Sadece Sheets => Mail & Telegram mantığıyla çalışır.

## Özellikler
- **Google Sheets Entegrasyonu:** Her iterasyonda tabloya yeni eklenmiş satır(lar)ı yakalar.
- **Mail Uyarı Sistemi:** Ayarladığınız adrese "yeni lead düştü" şeklinde bilgileri forwardlar.
- **Telegram Entegrasyonu:** Ayarladığınız gruba/sohbete lead içeriğini gönderir.

## Proje Yapılandırması (Environment Variables)

Aşağıdaki yapılandırmalar `master.env` veya lokal projenizin ayar dosyalarından çekilecektir:

- `SPREADSHEET_ID`: İzlenecek Spreadhseet'in kimliği.
- `SHEET_TABS`: İzlenecek Sheet sayfa/sekme adı. Virgülle çoklu (Sayfa1,Sayfa2) ayrılabilir. Varsayılan *Sayfa1*.
- `NOTIFY_EMAIL`: Bildirimin kime/hangi hesaba gideceği. (Savaş Bey'in adresi vb.)
- `SMTP_USER`: Gönderici e-posta (genelde ozerendolunay@gmail.com).
- `SMTP_APP_PASSWORD`: Gönderici e-postanın Google App Password şifresi.
- `TELEGRAM_BOT_TOKEN`: Telegram tarafında oluşturulan botun anahtar adresi.
- `TELEGRAM_CHAT_ID`: Botun size veya bulunduğunuz gruba mesaj atabilmesi için o chat'e ait özel ID.

## Nasıl Kullanılır?

1. Her ihtimale karşı Telegram Bot Token bilgilerini ayarlayın.
2. Botun size ulaşacağı Chat ID numarası için, bota `merhaba` mesajı atın ve `python get_chat_id.py` çalıştırın. Ekranda size verilen numarayı ayarlara ekleyin.
3. Kodu çalıştırmak için `python main.py` yazmanız yeterlidir. Varsayılan olarak her 5 dakikada bir kontrol sağlar.

**Not:** Bu projenin yapısı `Tele_Satis_CRM` ile birebir aynı polling mekanizmasına sahiptir ama **ayrı** bir deployment olarak çalışması için tasarlandı. İstendiğinde Railway'e tek başına yüklenebilir.
