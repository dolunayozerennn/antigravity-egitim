# Antigravity Starter Kit Başlangıç Rehberi

Hoş geldiniz! Bu klasör, Antigravity AI sisteminin tam temelini içerir. Kendi otonom AI asistanınızı kurmak ve projelerinizi yönetmeye başlamak için aşağıdaki adımları sırasıyla uygulayın.

## 1. Profilinizi Doldurun
- `_knowledge/profil.md` dosyasını açın.
- Köşeli parantez içindeki (`[İSİM SOYAD]`, `[BİYO]`, vb.) yerleri kendi kimliğinize dürüstçe uygun doldurun. Ajanınız sizi buradan tanıyacaktır.

## 2. API Anahtarları ve Vault (Kasa) Ayarları
- Sistemdeki tüm projeler token / şifre okumak için merkezi bir dosyaya bakar.
- `_knowledge/credentials/master.env` adında bir dosya oluşturun (veya varsa düzenleyin).
- `_knowledge/api-anahtarlari.md` dosyasını okuyarak hangi servislere ihtiyacınız olduğunu belirleyin. Sahip olduğunuz API Anahtarlarını `master.env` içerisine kaydedin.

## 3. Çalışma Kurallarına Göz Atın
- `_knowledge/calisma-kurallari.md` dosyası, sistemin omurgasıdır. Lütfen ajanınızın nasıl davranacağını anlamak için bu dosyayı dikkatlice okuyun ve gerekirse kendi projenize veya çalışma tarzınıza uygun eklemeler yapın.

## 4. Yetenekleri (Skills) İnceleyin
- `_skills/` klasörü içerisinde, ajanınızın yapabildiği görevleri barındıran scriptler mevcuttur. Her bir klasördeki `SKILL.md` dosyasına göz atarak, ajanınızın yetenek kapsamını öğrenebilirsiniz.

## 5. Projeleriniz
- Mevcut `Projeler/` klasöründe çeşitli otomasyon ve yazılım işlerinizin kopyaları bulunur.
- Bu projelerin çoğu ihtiyaç duydukları API anahtarlarını doğrudan `master.env` üzerinden çekecek şekilde ayarlanmıştır. Her bir projenin `README.md` dosyasını okuyarak proje bazında yapmanız gereken özel ayarlar (kendi .env dosyasını oluşturmak gibi) olup olmadığını görebilirsiniz.

---
**Tebrikler!** Artık Antigravity Starter Kit ile çalışmaya hazırsınız. Yapay zeka ajanınıza ilk isteklerinizi göndererek otomasyon serüvenine başlayın. Başarılar dileriz!

## 🤖 Hızlı Başlangıç İçin Antigravity Promptu

Eğer her şeyi manuel yapmak yerine **Antigravity yapay zekası** üzerinden bu eksiklikleri ve dosyaları otomatik düzenlemek isterseniz, bu projeyi IDE'nizde açtıktan sonra AI asistanınıza **aşağıdaki promptu direkt kopyalayıp yapıştırabilirsiniz:**

> Merhaba Antigravity, ben bu projeyi yeni indirdim. Sistemin ana omurgasını oluşturan kişiselleştirme adımlarını (şablonları ve API keyleri) birlikte doldurmak istiyorum.
> 
> Bana sırasıyla şu adımlarda yardımcı olmanı istiyorum:
> 1. `_knowledge/profil.md` dosyasındaki kimlik bilgilerini bana tek tek sorarak doldur.
> 2. `_knowledge/api-anahtarlari.md` ve `master.env` dosyası oluşturulması için sistemdeki önemli otomasyonların (örneğin OpenAI, Apify, Github vs.) API anahtarlarını benden al ve kaydet.
> 3. İlgilenmek istediğim projenin `README.md` dosyasını okuyarak, o projeye özgü bir veritabanı ID'si veya konfigürasyon varsa bana adım adım kurdur.
> 
> Lütfen bunları tek bir seferde sormak yerine, interaktif ve adım adım bir mülakat yapıyormuş gibi ilerle. İlk adımla başlayabiliriz.
