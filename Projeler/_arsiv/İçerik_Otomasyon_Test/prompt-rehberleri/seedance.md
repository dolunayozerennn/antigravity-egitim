# ErDoor için Seedance 2.0 Prompt Rehberi (I2V / Start Frame / 12s / 720p / Ses Açık)

> Kapsam: Bu rehber yalnızca **ErDoor kapı reklam videoları** için, **Seedance 2.0 ile image-to-video (I2V)** üretim senaryosuna göre hazırlanmıştır.  
> Varsayımlar: **12 saniye**, **API üzerinden üretim**, **ses her zaman açık**, **720p**, **başlangıç karesi image URL (start frame)**, **tutarlılık öncelikli**.

---

## 1) Bu rehberin amacı

Bu rehberin amacı, ekibinizin her üretimde aynı prompt mantığını kullanmasını sağlamak:

- daha **tutarlı sonuçlar**
- daha hızlı iterasyon
- daha az prompt dağınıklığı
- API tarafındaki teknik ayarlarla prompt içeriğinin karışmaması

---

## 2) ErDoor için en kritik gerçek (kısa özet)

Siz hep **I2V (image-to-video)** çalıştığınız için en güçlü kaldıraç şudur:

1. **Start frame görseli** (image URL)  
2. **Promptun hareket ve kamera dili**  
3. **Tutarlılık kuralları** (ürün formu, renk, kaplama, kol, çerçeve, ortam)

Yani promptun görevi çoğu zaman “görseli yeniden tarif etmek” değil;  
**görseldeki ürünü bozmadan hareket, kamera, atmosfer ve hikaye akışı tanımlamak** olmalı.

---

## 3) Seedance 2.0 resmi kaynaklardan çıkan ve sizi ilgilendiren noktalar

Seedance 2.0 resmi sayfası ve resmi lansman yazısı, modelin:

- **text / image / audio / video** girişlerini desteklediğini
- **ses-görüntü birlikte üretim** (audio-video joint generation) tarafında güçlü olduğunu
- **tutarlılık ve komut takibi** tarafında geliştirmeler sunduğunu
- **15 saniyeye kadar multi-shot audio-video çıktı** ve **çift kanal ses** vurgusu yaptığını
- **reklam / ticari içerik** gibi senaryolara uygun olduğunu

belirtiyor.

Bu rehberde bunları **ErDoor özelinde, 12 saniyelik I2V reklam akışına** indiriyoruz.

---

## 4) API ayarı ile promptu ayır (çok önemli)

Aşağıdaki şeyleri **mümkünse prompt içine gömmeyin**, API parametresi olarak yönetin:

- süre (12s)
- çözünürlük (720p)
- ses açık
- aspect ratio
- output format
- varsa seed / variation kontrolü

### Neden?
Çünkü prompta “12 second 720p” yazmak çoğu zaman yaratıcı kaliteyi artırmaz.  
Asıl kaliteyi artıran şey, promptta şunları net yazmaktır:

- kamera hareketi
- ürün davranışı (kapının açılması/kapanması)
- ortam
- ışık
- ses katmanları
- final kare (packshot / logo alanı)

---

## 5) ErDoor için prompt yazım prensipleri

## 5.1 Start frame’e sadık kal
I2V’de en büyük hata: modelden fazla dönüşüm istemek.

**Doğru yaklaşım**
- Mevcut görseldeki kapıyı koru
- Kamera ve sahne hareketini tarif et
- Küçük/orta ölçekli aksiyon ver
- Finalde net ürün gösterimi iste

**Yanlış yaklaşım**
- Görseldeki kapıyı başka modele dönüştürmek
- Aynı videoda farklı kapı tipi üretmeye çalışmak
- Çok agresif kamera + çok agresif fiziksel değişim istemek

---

## 5.2 Promptu “ürün dili” ile yaz
ErDoor için promptlar sinematik olabilir ama odak şurada kalmalı:

- kapının malzeme hissi
- yüzey dokusu
- kol/aksesuar detayı
- çerçeve hizası
- açılma kapanma akışı
- kullanım hissi (sessiz, sağlam, premium, güven veren)

---

## 5.3 12 saniyede tek fikir
12 saniyelik reklamda tek videoda 4 mesaj vermeyin.

Her prompt için **tek ana mesaj** seçin:

- Premium tasarım
- Sessiz ve akıcı kullanım
- Dayanıklılık hissi
- Modern yaşam alanına uyum
- Güven / sağlamlık / mühendislik hissi

---

## 5.4 Tutarlılık için “koru” komutlarını yaz
Promptta mutlaka koruma cümleleri kullanın:

- door design remains consistent
- keep the same door color and material finish
- preserve handle shape and frame proportions
- no deformation
- no extra objects added on the door surface
- maintain architectural realism

Bu tür ifadeler özellikle I2V reklam akışında çok işe yarar.

---

## 5.5 Ses her zaman açık olduğu için sesi gerçekten yazın
Sizde ses her zaman açık olduğundan, promptta sesi boş bırakmayın.

İyi bir ses tanımı 3 katmandan oluşur:

1. **Ambiyans** (oda tonu, ev ortamı, hafif rüzgar, şehir uzak sesleri)
2. **Foley** (kapı kolu, menteşe hissi, ayak sesi, kumaş sürtünmesi)
3. **Müzik** (minimal, premium, cinematic, warm)

> Not: “sessiz video” istemeyin; sizde ses her zaman açık.

---

## 6) ErDoor için standart prompt yapısı (önerilen)

Aşağıdaki formatı ekip standardı yapabilirsiniz.

```md
[GOAL]
ErDoor kapısını [ana mesaj] odağıyla gösteren 12 saniyelik reklam videosu.

[START FRAME RULE]
Use the provided image as the exact start frame.
Preserve the same door design, color, material finish, handle shape, and frame proportions.

[SCENE & MOOD]
[mekan], [ışık], [atmosfer], [stil]

[ACTION FLOW | 12s]
0-3s: [hook / kamera başlangıcı]
3-7s: [ürün etkileşimi / kapı hareketi]
7-10s: [detay / close-up / materyal vurgusu]
10-12s: [final packshot / logo alanı / temiz bitiş]

[CAMERA]
[push-in / pan / close-up / tracking / slow move]
Smooth and controlled commercial camera movement.

[PRODUCT CONSISTENCY]
Maintain door geometry and architectural realism.
No deformation, no extra panels, no handle mutation, no text artifacts.

[AUDIO]
Stereo, synchronized audio.
Ambient: [...]
Foley: [...]
Music: [...]

[OUTPUT STYLE]
Premium commercial ad, realistic materials, clean composition, natural motion, high prompt adherence.
```

---

## 7) ErDoor için kısa ama güçlü prompt şablonları

Aşağıdaki şablonlar doğrudan kopyalanıp kullanılabilir.
İngilizce verdim çünkü video modellerinde genelde daha stabil sonuç verir.

---

## 7.1 Şablon A — Premium showroom reveal (genel ürün tanıtımı)

```md
[GOAL]
Create a premium 12-second commercial ad for an ErDoor interior door, focusing on design elegance and material quality.

[START FRAME RULE]
Use the provided image as the exact start frame.
Preserve the same door design, color, material finish, handle shape, and frame proportions.

[SCENE & MOOD]
Modern interior showroom, soft warm lighting, premium architectural atmosphere, clean and minimal styling.

[ACTION FLOW | 12s]
0-3s: Start exactly from the provided frame. Slow cinematic push-in toward the door with subtle parallax in the background.
3-7s: The camera gently shifts angle and the door opens smoothly in a controlled, premium motion.
7-10s: Close-up detail pass on the handle, edge lines, and material texture, highlighting surface finish and craftsmanship.
10-12s: Clean hero shot of the full door in frame, stable composition, premium end pose with space left for brand logo / tagline.

[CAMERA]
Slow push-in, slight lateral move, controlled close-up transition, smooth commercial-grade motion.

[PRODUCT CONSISTENCY]
Maintain door geometry and architectural realism.
Keep the same color, material finish, handle design, and frame proportions.
No deformation, no extra decorative elements, no text artifacts.

[AUDIO]
Stereo synchronized audio.
Ambient: soft indoor room tone, subtle spacious showroom ambience.
Foley: gentle handle touch, clean latch/door movement sound, soft footstep or fabric movement.
Music: minimal premium cinematic music, warm and modern, low intensity.

[OUTPUT STYLE]
High-end commercial ad, realistic materials, clean composition, natural motion, strong consistency, prompt adherence.
```

---

## 7.2 Şablon B — Sessiz ve akıcı kullanım hissi (kullanım deneyimi odaklı)

```md
[GOAL]
Create a 12-second ErDoor commercial emphasizing smooth, quiet, premium everyday use.

[START FRAME RULE]
Use the provided image as the exact start frame.
Preserve the exact door appearance and proportions from the source image.

[SCENE & MOOD]
Contemporary home interior, soft daylight, calm and refined atmosphere, realistic residential styling.

[ACTION FLOW | 12s]
0-2.5s: Start from the provided frame. Slight handheld-free cinematic move to establish the door in a lived-in premium home setting.
2.5-6.5s: A person’s hand enters frame naturally, touches the handle, and opens the door smoothly and quietly.
6.5-9.5s: Camera follows the motion through the doorway with a gentle tracking move, emphasizing fluid movement and premium feel.
9.5-12s: Camera settles into a clean final angle where the door and frame remain clearly visible, elegant and stable, ready for end-card branding.

[CAMERA]
Subtle push-in, gentle tracking, smooth follow-through, no aggressive movement.

[PRODUCT CONSISTENCY]
Door design must remain unchanged.
Preserve handle shape, frame alignment, panel lines, and material texture.
No warping, no flickering details, no unrealistic transformations.

[AUDIO]
Stereo synchronized audio.
Ambient: soft indoor ambience, faint room tone.
Foley: refined handle touch, smooth hinge/door movement, soft footsteps.
Music: light modern ambient music, elegant and unobtrusive.

[OUTPUT STYLE]
Premium lifestyle commercial, realistic motion, calm pacing, product-first framing, high consistency.
```

---

## 7.3 Şablon C — Güven ve sağlamlık hissi (sert ama premium ton)

```md
[GOAL]
Create a 12-second ErDoor ad focused on strength, precision, and trust while keeping a premium visual style.

[START FRAME RULE]
Use the provided image as the exact start frame.
Keep the same door model, finish, handle, and frame details exactly consistent.

[SCENE & MOOD]
Modern architectural interior, controlled dramatic lighting, strong contrast, premium and trustworthy tone.

[ACTION FLOW | 12s]
0-3s: Start from the provided frame. Slow low-angle camera move to make the door feel strong and solid.
3-6s: Close-up emphasis on handle, lock area, frame fit, and material edges with controlled micro camera movement.
6-9s: The door closes firmly in a precise, smooth motion (not aggressive), showing alignment and build quality.
9-12s: Final hero shot with strong composition and subtle light sweep across the door surface, leaving clean space for branding.

[CAMERA]
Low-angle start, controlled close-up inserts, smooth hero finish.
Commercial, stable, readable movement.

[PRODUCT CONSISTENCY]
Maintain exact design identity from the start frame.
No shape changes, no extra lines, no texture drift, no unrealistic reflections.

[AUDIO]
Stereo synchronized audio.
Ambient: refined interior ambience, subtle spatial room tone.
Foley: tactile handle contact, precise latch/closing sound, premium material interaction.
Music: modern cinematic pulse, confident and minimal.

[OUTPUT STYLE]
Premium commercial ad, strong product presence, realistic materials, high visual consistency, precise motion.
```

---

## 8) Tutarlılık için “negatif prompt” mantığı (Seedance tarzı koruma komutları)

Seedance tarafında klasik ayrı “negative prompt” alanı her platformda aynı olmayabilir.  
Bu yüzden koruma kurallarını promptun içine gömün.

### Kullanılabilecek koruma ifadeleri (kopyala-yapıştır)
```md
Keep the door model unchanged throughout the video.
Maintain the exact panel design and frame proportions from the start frame.
Preserve handle shape and placement.
No door surface distortion or geometry drift.
No extra objects attached to the door.
No text artifacts, no warped edges, no flickering hardware.
Maintain realistic architectural scale and perspective.
```

---

## 9) ErDoor için prompt üretim standardı (ekip içi çalışma disiplini)

Her promptta şu değişkenleri sabit formatta tutun:

- **Door Model Name**: (ör. ED-XXX)
- **Finish/Color**: (mat beyaz, ceviz, antrasit vb.)
- **Handle Type**: (siyah mat, krom vb.)
- **Scene Type**: (showroom / ev / ofis / otel)
- **Main Message**: (premium / quiet / durable / modern)
- **Camera Style**: (calm / dynamic / low-angle / detail-heavy)
- **Audio Style**: (warm / premium / confident / minimal)

Bu yapı sayesinde promptlar kişiye göre değişmez; sistematik olur.

---

## 10) 12 saniye için önerilen shot dağılımları

## Paket 1 — Denge (en güvenli)
- 0-3s: establish + hook
- 3-7s: door interaction
- 7-10s: close-up detail
- 10-12s: hero shot

## Paket 2 — Daha ürün odaklı
- 0-2s: immediate product hook
- 2-5s: handle/detail
- 5-9s: door motion
- 9-12s: hero shot

## Paket 3 — Daha lifestyle
- 0-3s: environment + door
- 3-6s: person interaction
- 6-9s: follow-through movement
- 9-12s: premium final frame

> Tavsiye: Başlangıçta **Paket 1** ile ilerleyin. En stabil sonuçları genelde bu verir.

---

## 11) API kullanımında prompt dışı ama kaliteyi etkileyen notlar

Bu bölüm prompt rehberinin parçasıdır çünkü çıktı kalitesini direkt etkiler.

### 11.1 Start frame görsel kalitesi
Prompt çok iyi olsa bile start frame kötü ise sonuç düşer.

Kontrol listesi:
- ürün net görünüyor mu?
- kapı kenarları temiz mi?
- perspektif aşırı bozuk mu?
- handle görünür mü?
- ışık patlaması var mı?
- kapının bir kısmı crop ile kesilmiş mi?

### 11.2 Aynı kampanya içinde aynı görsel ailesi kullanın
Tutarlılık için:
- benzer lens/perspektif
- benzer ışık dili
- benzer dekor yoğunluğu
- benzer renk sıcaklığı

### 11.3 Tek değişken kuralı
Prompt iterasyonunda aynı anda 4 şeyi değiştirmeyin.

Her denemede sadece 1 değişken:
- kamera
- aksiyon
- ses
- ışık tonu
- final kare

Böylece neyin sonucu etkilediğini anlarsınız.

### 11.4 Seed / deterministic seçenek varsa sabitleyin
Kullandığınız API sağlayıcısı seed parametresi destekliyorsa:
- onaylanan promptlarda seed’i sabitleyin
- varyasyon gereken sürümlerde seed’i kontrollü değiştirin

---

## 12) Hızlı prompt checklist (yayın öncesi)

Her prompt için bu listeyi geçin:

- [ ] I2V olduğu net mi? (start frame rule yazıldı mı?)
- [ ] Kapı tasarımını koruma cümleleri var mı?
- [ ] 12 saniyelik akış 4 parçaya bölündü mü?
- [ ] Kamera dili yazıldı mı?
- [ ] Final hero shot tanımlandı mı?
- [ ] Ses 3 katmanlı tarif edildi mi? (ambiyans + foley + müzik)
- [ ] “No deformation / no artifact” benzeri koruma cümleleri eklendi mi?
- [ ] Ana mesaj tek mi? (premium / quiet / durable vb.)

---

## 13) Kısa “Master Template” (ErDoor için en pratik sürüm)

```md
Create a premium 12-second ErDoor door commercial video from the provided start-frame image.

Use the provided image as the exact start frame.
Preserve the same door design, color, material finish, handle shape, and frame proportions throughout the video.

Scene: [showroom / modern home / office / hotel corridor]
Mood: [premium / calm / confident / elegant]
Lighting: [soft warm / daylight / dramatic contrast]
Main message: [design elegance / smooth quiet use / strength and trust]

12-second flow:
0-3s: establish the door with a smooth cinematic camera move
3-7s: product interaction (door opening/closing or handle interaction) in a realistic premium way
7-10s: close-up detail on handle, edges, texture, craftsmanship
10-12s: clean hero shot with stable composition and empty space for brand logo/tagline

Camera: smooth commercial movement, controlled push-in / pan / close-up transitions, readable framing
Consistency: keep exact door identity, no deformation, no extra elements, no flicker, no text artifacts
Audio: stereo synchronized audio with premium ambience + realistic foley + minimal cinematic music
Style: realistic materials, high prompt adherence, clean composition, premium commercial ad
```

---

## 14) ErDoor için pratik kullanım önerisi (operasyon tarafı)

Ekibiniz için şu akışı öneririm:

1. **Base prompt kütüphanesi oluşturun** (A/B/C şablonları)
2. Her kapı modeli için sadece şu alanları değiştirin:
   - model adı
   - renk/kaplama
   - sahne tipi
   - ana mesaj
3. Her prompt sonucunu bir tabloya kaydedin:
   - prompt versiyonu
   - kullanılan görsel
   - seed (varsa)
   - sonuç notu (1-5)
   - sorun (deformasyon / kötü ses / kötü kamera / iyi)
4. En iyi çalışan 5 promptu “golden prompt” olarak kilitleyin

Bu, tutarlılığı ciddi şekilde artırır.
