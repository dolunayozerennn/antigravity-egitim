# Lead Notifier Bot 🚀

Bu proje, belirlenen bir Google Sheets dosyasındaki yeni eklenen potansiyel müşteri satırlarını (leadleri) tarar ve yeni bir ekleme algıladığı anda hem E-Posta adresine hem de Telegram botu aracılığıyla belirttiğiniz sohbete anlık (7/24) bildirim atar. 

Proje, Antigravity **Native Mono-Repo** standartlarına (`antigravity-egitim`) tam uyumlu olarak çalışır ve kendi başına otonom Railway worker'ı olarak canlıya alınmıştır!

## ✨ Özellikler
- **Google Sheets Entegrasyonu (Stateless Okuma):** Her polling döngüsünde tabloyu tarar, `.last_row_counts.json` veya memory referansıyla değişen satırları saptar.
- **Mail Uyarı Sistemi:** Ayarladığınız yetkili adrese ("Savaş Bey vb.") e-posta gönderir.
- **Telegram Entegrasyonu:** Ayarladığınız iletişim veya şirket grubuna bizzat bildirim atar.
- **Monorepo Uyumlu:** `_knowledge/credentials/google-service-account.json` üzerinden lokal ortamda global credential okuyarak çalışır. 

## 🔐 Proje Yapılandırması (Environment Variables)

Aşağıdaki yapılandırmalar `master.env` dosyasından veya canlı ortamda iseniz **Railway Environment Variables** sekmesinden çekilecektir:

- `SPREADSHEET_ID`: İzlenecek Spreadhseet'in kimliği.
- `SHEET_TABS`: İzlenecek sheet içerisindeki sayfa/sekme adı. (Örn: `Sayfa1`)
- `GOOGLE_SERVICE_ACCOUNT_JSON`: Eğer `_knowledge` içindeki JSON dosyasını okuyamıyorsa, Railway üzerinde base64 veya direkt json objesi olan authentication değeri.
- `NOTIFY_EMAIL`: Bildirimin kime/hangi hesaba gideceği. (Örn: `savasgocgen@gmail.com`)
- `SMTP_USER`: Bildirimi ateşleyecek olan bot/gönderici e-posta (genelde `ozerendolunay@gmail.com`).
- `SMTP_APP_PASSWORD`: Gönderici Gmail hesabının Google App Password güvenlik anahtarı.
- `TELEGRAM_BOT_TOKEN`: Telegram tarafında (@botfather) oluşturulan bildirim botunun anahtarı.
- `TELEGRAM_CHAT_ID`: Botun size veya bulunduğunuz şirket grubuna uyarı atabilmesi için o hedefin benzersiz ID'si.

## 🛠️ Nasıl Kullanılır?

1. Tüm credential veya API şifrelerinizi yukarıdaki liste uyarınca `master.env` dosyasına kaydedin. Eğer Telegram ID'nizi bilmiyorsanız, bota `/start` deyin ve `python get_chat_id.py` kodunu çalıştırıp ekrandaki sayıyı kaydedin.
2. Botun lokal ortamda hatasız çalışıp çalışmadığını tek bir deneme döngüsü ile doğrulamak için `python main.py --once` çalıştırın.
3. Bot 5 dakikada bir veri tarar otonom moda almak için: `python main.py` yazın.

**☁️ Railway Deploy Notu:** 
Projenin deployment'ı `antigravity-egitim` (ana repo) üzerinden sağlanır. Railway üzerinde Root Directory olarak `Projeler/Lead_Notifier_Bot` seçilmiştir ve `python main.py` start komutuyla 7/24 çalışmaktadır. Herhangi kod güncellemesi atıldığında `/canli-yayina-al` veya sadece commit sayesinde otonom deploy tetiklenir.

## 🛡️ Stabilizasyon ve Hata Giderme (2026-03-25)
- **Fix 1 (Anti-Pattern):** `smtplib` kullanımı, Railway'in SMTP port engeline takıldığı için kaldırılarak Google Gmail API (OAuth2) altyapısına geçildi. 
- **Fix 2 (Hata Yönetimi):** Bildirim hatalarını yutan `except` blokları kaldırılarak `raise` ile dışa aktarıldı, böylece hatalar ana döngüye iletilip tespit edilebilmesi sağlandı.
- **Fix 3 (Veri Kaybı Önlemi):** Ana döngüde bildirim hatası oluştuğunda state (`.last_row_counts.json`) güncellenmeyip `rollback_pending()` ile geri alınarak mesajların kaybolması engellendi (sessiz success yerine duplicate mesaj riski tercih edildi).
- **Fix 4 (Gitignore):** `.last_row_counts.json` state dosyası ana `.gitignore` dosyasına eklenerek deponun temiz kalması sağlandı.
