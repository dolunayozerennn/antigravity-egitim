# 🎬 Sora 2 Pro Storyboard — Prompt Rehberi
> **Versiyon:** 2.0 — OpenAI Cookbook, community testleri ve profesyonel incelemeler dahil edilmiştir.

## Prompt Yapısı (5 Katmanlı)
Her sahne prompt'u şu yapıda olmalıdır:
**Konu → Eylem → Sahne/Ortam → Kamera → Işıklandırma & Stil**

---

## 🚨 KRİTİK KURAL 1: Prompt-Süre Uyumu (Duration Harmony)

> **Sora 2 Pro Storyboard diğer video modellerinden farklı çalışır.** Her sahne için prompt ve süre (saniye) ayrı ayrı belirlenir. Yazdığınız prompt'un karmaşıklığı ile atadığınız süre **mutlaka uyumlu** olmalıdır.

**⚠️ Bu uyum yoksa sistem ÇALIŞMAZ.**

### Neden Önemli?
```
❌ HATA: "Man walks into café, sits down, orders coffee, talks to 
barista about the weather, and picks up his cup" → duration: 3s
💥 SONUÇ: 3 saniyeye 5 farklı eylem sığmaz! Sistem çöker veya anlamsız çıktı verir.

✅ DOĞRU: "Man walks into a café, pushing the glass door open." → duration: 3s
✅ DOĞRU: "Man picks up his coffee cup and takes a slow sip." → duration: 3s
```

### ⏱️ Süre-İçerik Uyum Tablosu

| Süre | Ne Sığar | Ne SIĞMAZ | Örnek |
|------|----------|-----------|-------|
| **3s** | Tek bir basit eylem VEYA statik çekim | Hareket + kamera değişimi, konuşma | `"Product on table, soft spotlight, clean white background."` |
| **4s** | Tek eylem + basit kamera hareketi | Çoklu eylem, diyalog | `"Slow dolly in on red sneakers, studio lighting, macro detail."` |
| **5s** | Bir ana eylem + ortam tanıtımı | Çoklu karakter etkileşimi | `"Woman unboxes product, lifting lid with both hands, soft natural light."` |
| **6-7s** | Ana eylem + kişinin tepkisi VEYA yürüyüş | Karmaşık sahne geçişleri | `"Model walks toward camera wearing the jacket, slow tracking shot, fashion editorial."` |
| **8-10s** | Bir sahne + kamera hareketi + atmosfer | Tam hikaye | `"Athlete runs on trail wearing shoes, tracking shot from side, golden hour, dust particles rising, dynamic motion."` |

> **🔬 OpenAI Cookbook bulgusu:** 4 saniyelik klipler bitiştirilerek oluşturulan sahneler, tek seferde üretilen uzun kliplerden **daha tutarlı fizik ve görsel kalite** üretir. Fizik içeren sahnelerde mümkünse 4s kartlar tercih edin.

### ✍️ Pratik Test
**Prompt'unuzu yüksek sesle okuyun ve eylemi kafanızda canlandırın.**
- Okuduğunuz + canlandırdığınız süre ≈ atadığınız `duration` olmalıdır.
- Gerçek hayatta o eylem kaç saniye sürer? Yanıt = doğru duration.

### Konuşma / Diyalog Kuralı
Eğer sahnede birisi konuşuyorsa:
- **İnsan yaklaşık 2-3 kelime/saniye** hızında konuşur
- 3s sahne → max 6-9 kelimelik cümle
- 5s sahne → max 10-15 kelimelik cümle
- 8s sahne → max 16-24 kelimelik cümle

```
❌ HATA: "He says: 'Welcome to our brand new collection of 
premium handmade leather shoes designed for modern professionals'" → 3s
💥 Bu cümle 14 kelime = en az 5 saniye gerekli!

✅ DOĞRU: "He says: 'Welcome to our collection.'" → 3s (5 kelime ✓)
✅ DOĞRU: "He says: 'Discover our new premium leather 
collection, designed for modern professionals.'" → 5s (10 kelime ✓)
```

---

## 🚨 KRİTİK KURAL 2: Fiziksel Etkileşim Kısıtlamaları (Red Flag Actions)

> **Bu kural, otomasyon sistemleri için en kritik bölümdür.** Sora 2 Pro'nun en büyük zayıflığı **eller, ince motor hareketler ve çok adımlı fizik zincirleridir.** Aşağıdaki kategorilere giren sahneleri prompt olarak yazmadan önce alternatif bir yaklaşım seçin.

### ❌ Red Flag Eylem Kategorileri (Yazma veya Alternatif Kullan)

| Kategori | Somut Örnekler | Tipik Arıza |
|----------|---------------|-------------|
| **El-parmak hareketleri** | Kapı kolu çevirme, parmak sayma, işaret etme, kart karıştırma | Yanlış parmak sayısı, ellerin nesneye yapışmaması |
| **Yakın plan el-nesne teması** | Elin kolu tutması, makyaj uygulaması, dikiş dikme | Anatomik bozulma, el-nesne kayması |
| **Çok adımlı fizik zincirleri** | Sıvı dök → karıştır → servis et, kapıya uzan → tut → çevir → it | 3-4. adımda tutarsızlık, nesnelerin kaybolması |
| **Nesne tutma (uzun süreli)** | Elde tutulan telefon, fincan, kalem | Nesne klip ortasında kayboluyor, klipliyor |
| **Vücut-çevre karmaşık etkileşimi** | Arabaya binme, şemsiye açma, tırmanma | Mekansal tutarsızlık |
| **Hızlı hassas hareketler** | Yazı yazma, enstrüman çalma, dikiş | Zamanlama ve temas noktaları bozuluyor |

### ✅ Sora 2 Pro'nun Güçlü Olduğu Alanlar
- Atmosferik çekimler (ateş, su, sis, ışık efektleri)
- İnsan etkileşimi olmayan doğa sahneleri
- Yavaş viskoz sıvı akışları (bal, boya — çok başarılı)
- Basit yürüyüş sahneleri (medium/wide açı, el görünmüyor)
- Sinematik kamera hareketleri
- Ortam ve hava tanıtımı

### 🔄 Red Flag Sahneler İçin Kes-Geç Tekniği

El-nesne temasını **hiç göstermeden** eylemi ima etmenin yolu: Storyboard kartlarını temas anını atlayacak şekilde konumlandır. İzleyicinin beyni boşluğu kendisi dolduracaktır.

**Örnek — Kapı Açma Sahnesi:**
```
❌ YAPMA: "Close-up of hand gripping the door handle, fingers 
wrapping around the metal, slowly turning it clockwise." → 4s

✅ YAP (Kart 1 — 4s):
"A woman in a grey wool coat walks toward a heavy oak door 
at the end of a dimly lit hallway. Medium shot from behind, 
slow follow. Warm overhead light casts long shadows on 
hardwood floor."

✅ YAP (Kart 2 — 4s):
"The oak door swings open, revealing a sunlit room beyond. 
The woman steps through the doorway. Medium-wide shot from 
inside the room looking toward the hallway. Soft natural 
light floods the frame."
```
_⚙️ Sonuç: El-kol teması hiç gösterilmedi, ama kapı açılıyor. Modelin zayıf noktası bypass edildi._

**Bu teknik her el-nesne etkileşiminde uygulanabilir:**
- Şişe açma: Şişeye uzanan el (Kart 1) → Şişenin açık hali masada (Kart 2)
- Telefon açma: Telefona uzanan el (Kart 1) → Telefon ekranı aktif (Kart 2)
- Kutu açma: Kutunun üstü kapalı (Kart 1) → Kutunun içi görünüyor (Kart 2)

---

## ✅ Altın Kurallar

### 1. Detaylı ve Spesifik Olun
```
❌ KÖTÜ: "Ayakkabı göster"
✅ İYİ: "Kırmızı Nike spor ayakkabı, beyaz stüdyo arka planı, yavaş 360 derece dönüş, yumuşak gölgeler, product shot"
```

### 2. Sinematik Dil Kullanın
Sora, profesyonel film terminolojisine mükemmel yanıt verir:

**Kamera Çekim Tipleri:**
- `wide shot` — Ürünü bağlam içinde gösterir
- `medium shot` — Ürün detayı ve ortamı birlikte
- `close-up` — Malzeme, doku detayları *(insan eli veya yüzü için riskli)*
- `extreme close-up` / `macro shot` — Dikiş, logo gibi mikro detaylar *(nesne detayı için güvenli, el için değil)*
- `establishing shot` — Sahnenin genel tanıtımı

**Kamera Hareketleri:**
- `dolly in` — Kamera yaklaşırken dramatik etki
- `tracking shot` — Ürün/kişiyi takip
- `orbit around` — 360° çevre dönüşü
- `slow pan left/right` — Yavaş yatay kaydırma
- `crane shot` — Yukarıdan aşağıya veya tam tersi
- `handheld with subtle shake` — Dokumenter/doğal his

**Kamera Açıları:**
- `low angle` — Ürüne güç katmak (aşağıdan yukarı)
- `high angle` — Kuşbakışı, genel görünüm
- `eye-level` — Doğal ve samimi
- `Dutch angle` — Yaratıcı gerilim

### 3. Işıklandırma ve Renk Belirtin
```
✅ "golden hour lighting with warm orange rim light"
✅ "soft studio lighting, key light from 45 degrees"
✅ "cinematic lighting, teal and orange color grading"
✅ "volumetric lighting through fog"
✅ "high-key bright commercial lighting"
✅ "dramatic low-key chiaroscuro shadows"
```

### 4. Alan Derinliğini Belirtin
```
✅ "shallow depth of field, f/1.4, bokeh background"
✅ "deep focus, everything sharp, f/11"
```

### 5. Stil ve Estetik Referansı Verin
```
✅ "cinematic film grain, 35mm aesthetic"
✅ "hyperrealistic, photorealistic"
✅ "minimalist, clean commercial look"
✅ "Apple-style product commercial"
```

### 6. Fizik İpuçlarını Prompt'a Ekle
Nesnelerin ağırlığını ve malzeme özelliklerini prompt içinde belirt. Bu, modelin fizik simülasyonunu doğru yapmasına yardımcı olur.
```
✅ "The heavy wooden door swings open with weight."
✅ "Thick honey pours slowly off a spoon, stretching in a long thread."
✅ "Heavy velvet curtains drag slowly across the floor."
✅ "Wet nylon jacket catches the wind as she walks."
```

### 7. Zaman Damgası ile Eylem Belirt (Temporal Beats)
Sahnedeki eylemleri zamana bağlayarak modele net bir yapı ver. Bu, OpenAI Cookbook'un en güçlü önerilerinden biridir.
```
❌ ZAYIF: "Actor walks across the room."
✅ GÜÇLÜ: "Actor takes four steps to the window, pauses, 
and pulls the curtain in the final second."
```

---

## 📋 E-Ticaret Video Prompt Şablonları

> ⏱️ Her şablonda süre ile prompt karmaşıklığının nasıl dengelendiğine dikkat edin.
> Toplam süre 25 saniyeyi geçmemelidir.

### Ürün Tanıtım Videosu (3 Sahne — Toplam 17s)

**Sahne 1 — Hero Shot (5s) → Tek çekim, tek hareket:**
```
Product hero shot: [ÜRÜN ADI] centered on a [YÜZEY], [RENKLERİ]. 
Slow dolly in, shallow depth of field f/2.0, soft studio lighting 
with key light from above, neutral background, clean commercial 
aesthetic, 4K.
```
_⏱️ Neden 5s? Yavaş dolly-in + statik ürün = 5 saniyeye ideal uyum._

**Sahne 2 — Kullanımda (8s) → Bir ana eylem + ortam:**
```
[KİŞİ TANIMI] using/wearing [ÜRÜN ADI] in [MEKAN]. 
Medium tracking shot following from the side, golden hour natural 
lighting, dynamic motion, lifestyle commercial look, shallow depth 
of field with bokeh background.
```
_⏱️ Neden 8s? Kişinin ürünle etkileşimi + takip çekimi = 8 saniye dolduracak kadar içerik._
_⚠️ Dikkat: Ürünü elde tutma sahnesi planlıyorsan, ürünü tutma eylemini gösterme. Kişiyi ürünü kullanırken medium shot ile çek._

**Sahne 3 — Final/Logo (4s) → Basit kapanış:**
```
[ÜRÜN ADI] returns to center frame. Clean white background, soft 
spotlight from above, product slowly rotates, professional 
commercial finish.
```
_⏱️ Neden 4s? Ürünün karaya dönmesi + yavaş rotasyon = kısa ve net kapanış._

### Moda / Giyim Videosu (3 Sahne — Toplam 17s)

**Sahne 1 (6s) → Tek eylem: yürüyüş:**
```
Fashion model wearing [ÜRÜN], walking toward camera on a minimalist 
runway, front-facing medium shot, soft white lighting, slow motion, 
fashion editorial style, f/2.8 bokeh.
```
_⏱️ 6s: Yavaş çekim yürüyüş tek başına 6 saniyeyi doldurur._

**Sahne 2 (4s) → Statik detay çekimi:**
```
Close-up detail shot of fabric texture and stitching on [ÜRÜN], 
macro lens, soft directional lighting revealing texture, smooth 
dolly movement, luxury brand aesthetic.
```
_⏱️ 4s: Kumaş detayı üzerinde yavaş dolly = kısa ama etkili._
_✅ Güvenli: Bu close-up insan elini değil kumaşı gösteriyor._

**Sahne 3 (7s) → Poz + ortam:**
```
Model poses with confidence wearing [ÜRÜN] in an urban setting, 
medium wide shot, golden hour backlighting, city bokeh, cinematic 
color grading. Model turns slightly to show back detail.
```
_⏱️ 7s: Poz + hafif dönüş hareketi = 7 saniyeye uyumlu._

### Yemek / Restoran Videosu (3 Sahne — Toplam 19s)

**Sahne 1 (5s) → Tek eylem: tabak konuluyor:**
```
Top-down overhead shot of [YEMEK] being placed on a rustic wooden 
table, steam rising, warm ambient lighting, food photography style.
```
_⏱️ 5s: Tabağın konulması + buhar yükselişi._
_⚠️ Dikkat: Ellerin tabağı tutması yerine tabağın masa üzerinde belirmesini tarif etmek daha güvenli._

**Sahne 2 (6s) → Tek eylem: kesilme anı:**
```
Close-up of fork slowly cutting into [YEMEK], revealing layers 
and texture inside, shallow depth of field, warm golden lighting, 
food commercial aesthetic.
```
_⏱️ 6s: Yavaş kesme hareketi + iç dokunun ortaya çıkması._
_⚠️ Dikkat: Çatalı tutan eli gösterme. Çatalın yiyeceğe temas ettiği noktayı çerçevele, eli değil._

**Sahne 3 (8s) → Ortam reveal:**
```
Wide shot of beautifully set dining table with [YEMEK] as 
centerpiece, candles flickering, soft warm ambiance, slow dolly 
out to reveal the full restaurant scene, evening atmosphere.
```
_⏱️ 8s: Yavaş dolly-out ile masadan restorana geçiş._

### Kapı / Mekan Geçiş Sahnesi (2 Kart — Toplam 8s)
> Bu şablon, el-nesne temasını atlayan kes-geç tekniğini göstermektedir.

**Kart 1 (4s) → Yaklaşma:**
```
[KİŞİ TANIMI] walks toward a [KAPI TANIMI] at the end of 
[MEKAN TANIMI]. Medium shot from behind, slow follow. 
[IŞIK TANIMI] casts long shadows on [ZEMİN].
```

**Kart 2 (4s) → İçeri giriş:**
```
The [KAPI TANIMI] swings open, revealing [İÇ MEKAN TANIMI]. 
[KİŞİ TANIMI] steps through the doorway. Medium-wide shot 
from inside the room looking toward the hallway. 
[IŞIK TANIMI] floods the frame.
```

---

## ⚠️ Kaçınılması Gerekenler

### Teknik Kısıtlamalar
- ❌ **Prompt-süre uyumsuzluğu** — En kritik hata! 3 saniyeye 5 eylem sığdırmaya çalışmak sistemi bozar
- ❌ **Kısa süreye diyalog yazmak** — Konuşma sahneleri minimum 5s olmalı, uzun cümleler 8s+
- ❌ Çok uzun ve karmaşık tek bir prompt (basit tutun, her sahne net olsun)
- ❌ Soyut kavramlar ("güzel", "harika" gibi) — somut görsel detaylar kullanın
- ❌ Sahne başına birden fazla ana eylem (kısa sürelerde KESİNLİKLE tek eylem)
- ❌ Toplam sürenin 25 saniyeyi aşması

### Fiziksel Etkileşim Kısıtlamaları (Araştırmayla Doğrulanmış)
- ❌ **Yakın plan el-nesne teması** — Kol tutma, düğme basma, kaldırma gibi close-up el çekimleri anatomik bozulmaya yol açar
- ❌ **Parmak odaklı sahneler** — Parmak sayma, işaret etme, yazı yazma parmak sayısı hatası üretir
- ❌ **Çok adımlı zincirleme fizik** — 3'ten fazla ardışık eylem içeren sahneler tutarsızlaşır
- ❌ **Uzun süreli nesne tutma** — Klip ortasında nesne kaybolabilir veya klip oluşabilir
- ❌ İnsan yüzleri (Sora yüzlerde hata yapabilir → Veo 3 kullanın)
- ❌ Karmaşık insan-çevre etkileşimleri (arabaya binme, şemsiye açma)

---

## 🧮 Prompt Yazarken Kontrol Listesi

Prompt'unuzu yazmadan önce kendinize şu soruları sorun:

1. ✅ Bu sahnede kaç ayrı **eylem** var? → Süre başına max 1 ana eylem
2. ✅ Bu sahnede kaç ayrı **kamera hareketi** var? → Kısa sürelerde max 1 hareket
3. ✅ Sahnede **konuşma** var mı? → Konuşma varsa süreyi mesajın okunma hızına göre ayarla
4. ✅ Sahne **gerçek hayatta** bu sürede gerçekleşebilir mi? → Gerçekçi düşünün
5. ✅ Toplam tüm sahneler **25s'yi** geçmiyor mu?
6. ✅ Sahnede **el görünüyor mu**? → Görünüyorsa close-up yerine medium/wide tercih et
7. ✅ **El-nesne teması** var mı? → Varsa kes-geç tekniği ile temas anını atlat
8. ✅ Sahnede **3'ten fazla ardışık eylem** var mı? → Varsa sahnelere böl
9. ✅ Sahne fizik zincirine bağımlı mı? → 4s kartlara böl ve bitiştir

---

## 💡 Pro İpuçları

1. **Referans görsel kullanın** — Marka renkleri ve tonu için referans görsel yükleyin
2. **İlk sahneyi en çarpıcı yapın** — Dikkat çeken hook'larla başlayın
3. **Kart aralarında boşluk bırakın** — Kartlar arası 1-2 saniyelik boşluk yumuşak geçiş sağlar; çok yakın kartlar hard cut üretir
4. **Süreleri dengeli dağıtın** — Hero shot kısa (3-5s), kullanım sahnesi uzun (6-10s)
5. **İngilizce prompt kullanın** — En iyi sonuçlar İngilizce prompt'larla alınır
6. **Prompt'u yüksek sesle okuyun** — Okuduğunuz sürenin atadığınız süreye yakın olması gerekir
7. **Şüpheye düşerseniz bölün** — Uzun bir sahneyi 2 kısa sahneye bölmek her zaman daha iyidir
8. **Hareket basit tutun** — OpenAI Cookbook: "Movement is often the hardest part to get right, so keep it simple."
9. **Karakter tutarlılığı için tekrarlayın** — Her kartta aynı karakterin ayırt edici özelliklerini yeniden belirt ("same curls, same navy blazer from Shot 1")
10. **Fizik sahnelerinde 4s kartları bitiştirin** — Tek uzun klip yerine iki 4s klip daha tutarlı fizik üretir
