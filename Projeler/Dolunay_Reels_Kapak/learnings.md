# Kapak Fotoğrafı Öğrenimler (Learnings)

Bu dosya, kullanıcı feedback'lerinden çıkarılan öğrenimleri içerir. 
Tüm prompt'lar ve değerlendirmeler bu kurallara uymalıdır.

## 🔴 KRİTİK KURALLAR

### 1. Instagram 4:5 (2/3) Güvenli Bölge - YAZI KONUMU
- Instagram profil grid'inde kapak fotoğraflarının **üstü ve altı kırpılır** (9:16 → 4:5 oranına indirgenir).
- Bu nedenle yazı ASLA görselin en üstüne veya en altına yerleştirilmemelidir.
- **Güvenli bölge**: Görselin dikey merkezine yakın, yani yüksekliğin %25 ile %75 arasına yerleştirilmelidir.
- **En iyi konum**: Dikey olarak merkez veya merkezin hafif altı (%40-%65 arası).
- Üst %20 ve alt %20 bölgesi "tehlikeli bölge"dir — yazı buraya konulmamalıdır.

### 2. Yazı Tekrarı YASAKTIR
- AI bazen metni iki kere render eder (üst üste veya alt alta).
- Prompt'ta bu açıkça belirtilmelidir: "Write the text ONLY ONCE. Do NOT repeat or duplicate the text."
- Değerlendirme aşamasında yazı tekrarı tespit edilirse skor 0 olmalıdır.

### 3. Yazı Boyutu - KOCAMAN VE OKUNAKLI
- Sosyal medyada küçük ekranlarda kapak görülür. Yazı HER ZAMAN büyük olmalıdır.
- Minimum: Görselin genişliğinin %60-80'ini kaplamalıdır.
- İdeal: 2-4 kelimelik metin, 2 satıra bölünerek büyük punto ile yazılmalıdır.
- Bir satırda çok fazla karakter varsa (6+ karakter kelimelerde 3+ kelime), iki satıra bölünmelidir.
- Referans: Buzzy 1 Kapak 1 stili → metin devasa, net, okunabilir.

### 4. Yazı Dili - SADECE TÜRKÇE
- Kapak metninde İngilizce kelime ASLA olmamalıdır.
- Prompt'taki talimat metni İngilizce olabilir, ama görsele render edilecek metin %100 Türkçe olmalıdır.
- "EXACTLY", "THE", "AND" gibi İngilizce contamination meydana gelirse skor 0 olmalıdır.
- AI'ya prompt içinde şunu ekle: "The text language is Turkish. Do NOT include any English words in the rendered text."

### 5. Görsel-Metin Tutarlılığı
- Kapak üzerindeki metin ile görseldeki sahne/aksiyon birbiriyle uyumlu olmalıdır.
- Örnek KÖTÜ: "SEN UYU O ÇALIŞSIN" yazıyoruz ama görselde kişi oturup telefona bakıyor (uyumuyor).
- Örnek İYİ: "SEN UYU O ÇALIŞSIN" → Görselde kişi rahat bir şekilde uyuyor veya yatakta, arka planda bilgisayar/robot çalışıyor.
- Prompt'ta sahne açıklamasını metin içeriğine göre ayarla.

### 6. Kişi/Konu Yakınlığı
- Kişi/konu görselde çok uzaktan çekilmemeli. 
- Sosyal medya küçük ekranlarda görüntülenir, kişi yakın plan olmalıdır.
- İdeal: Yarım boy (belden yukarısı) veya göğüsten yukarısı çekim.
- Full-body uzak çekimler KAÇINILMALIDIR (Abacus 6 Kapak 3 hatası).

### 7. Yüz Kimliği (cref) Tutarlılığı
- AI'nın referans kişiyi (Dolunay) düzgün render etmesi kritik.
- Eğer AI farklı bir kişi üretiyorsa, bu tespit edilmeli ve yeniden üretilmelidir.
- Vision değerlendirmesinde "Does the person match the reference photo?" kontrolü eklenmeli.

### 8. Video Adı ≠ Kapak Metni — KRİTİK!
- Notion'daki video isimleri (örn: "Typeless 5", "Meshy 4", "Kimi 4") tamamen **dahili takip isimleridir**.
- Bu isimler, videonun konusuyla doğrudan ilişkili DEĞİLDİR.
- "Typeless 5" → Typeless isimli AI aracının 5. tanıtım videosu demek, "tipsiz 5" veya "tarzsız 5" DEĞİL.
- Kapak metni oluştururken video adı ASLA kullanılmamalıdır.
- **Mutlaka videonun Notion sayfasındaki script/senaryo içeriği okunmalı** ve içerik bazlı bir Türkçe hook üretilmelidir.
- Eğer script mevcut değilse, kullanıcıya sorulmalı veya videonun konusu araştırılmalıdır.
- **Hata örneği**: "Typeless 5" → Kapak metni "TİPSİZ 5" olarak üretildi. BU KATEGORİK OLARAK YANLIŞ.
- **Doğru yaklaşım**: Script'te "Sekreterinizi kovabilirsiniz / Avukatların en büyük derdi çözüldü" yazıyor → Kapak metni: "SEKRETERİNİ KOV" veya "AVUKATIN SIRRI" gibi olmalıydı.

### 9. Metin Render Edilmemesi (Boş Kapak) — KRİTİK!
- Bazı üretimlerde kapak görseli oluşuyor ama üzerinde HİÇBİR METİN yazılmıyor.
- Vision değerlendirmesinde bu durum tespit edilirse skor 0 olmalıdır.
- Prompt'ta "The text MUST be clearly visible and readable" ifadesi eklenmeli.
- Değerlendirme kriterlerine "text_present" (metin var mı?) checkboxu eklenmeli.
- **Hata örnekleri**: Typeless 4 Kapak 2 (metin yok), Meshy 5 Kapak 3 (metin yok).

### 10. Görsel Yaratıcılığı — Klişelerden Kaçın
- AI her zaman aynı kalıplara düşebilir (kişi bilgisayar ekranına bakıyor, ekranda bir uygulama görünüyor).
- Daha yaratıcı görseller üretilmeli:
  - 3D karakter videoları için: Karakter bilgisayar ekranında değil, **gerçek boyutta, canlıymış gibi** gösterilebilir.
  - Ürün tanıtım videoları için: Ürünü kutunun dışında, gerçek hayatta kullanılırken göster.
  - Genel olarak "ekranı gösteren kişi" klişesinden kaçın.
- **İyi örnek**: KickResume 6 — CV'yi çöpten kurtarma metaforu, yaratıcı ve dikkat çekici.
- **ALTIN ÖRNEK**: Typeless 3 Kapak 2 (v2) — "KLAVYEYİ ÇÖPE AT" metniyle bir dağ gibi yığılmış klavyelerin üzerinde kişi duruyor. Gerçek bir fiziksel metafor! Çok yaratıcı ve dikkat çekici.
- **Kaçınılması gereken**: Her seferinde aynı "kişi bilgisayar başında" sahnesi.

### 11. Yazı Boyutu Kalibrasyonu
- Yazı boyutu "görselin genişliğinin %60-80'i" hedeflenmeli ama görsel bağlamına göre ince ayar yapılabilir.
- 2 kelimelik metinler (örn: "KOMİSYONA SON") biraz daha BÜYÜK olabilir.
- 3-4 kelimelik metinler (örn: "TASARIMCIYA PARA VERME") görselin bütünlüğünü bozmadan okunabilir boyutta olmalı.
- Metnin görseldeki kişiyi/konuyu ezmemesi önemli, ama okunabilirlik her zaman önceliklidir.

### 12. Arka Plan Karmaşıklığı — Kişi Tanınabilir Olmalı
- Kapak fotoğrafında kullanıcının (Dolunay) görselden **kolayca ayırt edilebilmesi** zorunludur.
- Arka plan çok fazla element/obje içeriyorsa, kişi kaybolur ve kapak amacına ulaşmaz.
- **Kaçınılması gereken**: Alttan veya arkadan gelen çok yoğun, karmaşık elementler (parçacıklar, patlayan objeler, çok sayıda obje) kişiyi görsel gürültüye boğuyor.
- **Doğru yaklaşım**: Arka plan dramatik olabilir ama kişi her zaman en öne çıkan element olmalı. Depth of field, blur veya ışıklandırma ile kişi vurgulanmalı.
- **Hata örneği**: Typeless 5 Kapak 3 (v2) — alt kısımda çok fazla element var, kişi arka plandan kolay ayırt edilemiyor.
- **İyi örnek**: Typeless 3 Kapak 2 (v2) — kişi klavyelerin üzerinde net bir şekilde duruyor, arka plan dramatik ama kişi baskın.

### 13. Metin Okunabilirliği — Aşırı Net Olmalı
- Metin sadece "var" olmamalı, göz metne çok rahatlıkla takılmalıdır.
- Metin ile arka plan arasında yüksek kontrast mutlaka olmalıdır (koyu arka plan + beyaz/sarı metin veya metin üzerinde shadow/glow).
- Göz metni "seçmek" için çaba sarf etmemeli — metin ilk bakışta apaçık okunmalı.
- **ALTIN REFERANS**: Typeless 3 Kapak 2 (v2) — metin aşırı net, göz çok rahat seçiyor. Kontrast mükemmel.

## ✅ BEĞENİLEN ÖĞELER (Korumamız Gerekenler)

### ⭐ ALTIN REFERANSLAR (En Çok Beğenilenler)
1. **Typeless 3 Kapak 2 (v2)**: "KLAVYEYİ ÇÖPE AT" — klavye dağının üzerinde duran kişi. Metin aşırı net okunuyor. Görsel metafor mükemmel. Kişi belirgin. **EN İYİ KAPAKLARdan biri.**
2. **Buzzy 1 Kapak 1**: Yazı çok rahat okunuyor, boyutu çok iyi, arka plandan güzel ayrışıyor. ALTIN REFERANS.
3. **KickResume 6 kapak yaklaşımı**: "CV'Nİ ÇÖPTEN KURTAR" — hem metin hem görsel yaratıcılık mükemmel. Metafor kullanımı çok başarılı. 3/3 kapak başarılı.

### ✅ Diğer Başarılı Örnekler
4. **Verdent 2 Kapak 3**: Ekran üstü metin stili, okunuyor, konum iyi.
5. **Cinematic, moody atmosfer**: Genel olarak ışıklandırma ve atmosfer güzel.
6. **Bold sans-serif, all-caps font**: Bu doğru yaklaşım, devam etmeliyiz.
7. **Meshy 5 Kapak 1-2**: "TASARIMCIYA PARA VERME" metni güzel. Yazı boyutu Kapak 1'de ideal.
8. **Typeless 5 (v2)**: "SEKRETERİNİ KOV" — script içeriğinden doğru hook üretildi. 3/3 kapak 10/10 skor aldı.
9. **Typeless 4 Kapak 2 (v2)**: "DİL BİLMEYE SON" — metin başarıyla render edildi, önceki boş kapak problemi aşıldı.
10. **Typeless 3 (v2)**: "KLAVYEYİ ÇÖPE AT" — tüm versiyonda yazı doğru Türkçe, hiçbirinde video adı kullanılmadı. Önceki "tipsiz 3" / "tarzsız 3" hatası aşıldı.

## 📐 TEKNİK SAFE ZONE HESAPLAMASI

Instagram 9:16 (1080x1920) → 4:5 crop (1080x1350):
- Üstten kırpılan: (1920 - 1350) / 2 = 285px
- Alttan kırpılan: 285px
- Güvenli metin alanı: y=285 ile y=1635 arası (1080x1350 merkez alan)
- En güvenli metin pozisyonu: y=500 ile y=1200 arası (tam merkez)

## 📅 VERSİYON GEÇMİŞİ

### v2 — 11 Mart 2026
- Video adı yerine script içeriğinden metin üretme (Kural 8)
- Boş kapak tespiti ve retry (Kural 9)
- Görsel yaratıcılık teşviki ve klişe cezası (Kural 10)
- Arka plan karmaşıklığı kontrolü (Kural 12)
- Safety check: üretilen metnin video adına benzeyip benzemediği otomatik kontrol
- İngilizce kelime kontrolü genişletildi (ekrandaki yazılar dahil)
- Fallback metin artık "BUNU BİLMELİSİN" (video adı değil)

### v1 — İlk Sürüm
- Temel kurallar (1-7) oluşturuldu
- Instagram 4:5 safe zone hesaplaması
- Rourke style guide entegrasyonu
