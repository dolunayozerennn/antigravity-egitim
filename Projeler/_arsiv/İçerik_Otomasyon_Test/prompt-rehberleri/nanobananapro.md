# 🖼️ NanoBanana Pro (Gemini 3.0 Pro Image) — Prompt Rehberi

## En İyi Kullanım Alanı
Instagram postları, posterler, carousel içerikler, ürün görselleri, 4K kalitesinde profesyonel görsel üretimi.

## Prompt Yapısı
**İçerik → Stil/Estetik → Kompozisyon → Renkler/Işık → Metin(varsa) → Teknik**

---

## ✅ Altın Kurallar

### 1. Somut, Görsel Detaylar Kullanın
```
❌ KÖTÜ: "Güzel bir poster yap"
✅ İYİ: "Modern minimalist poster design for a summer sale campaign. 
Large bold text '50% OFF' in white sans-serif font centered on 
the image. Background: gradient from coral pink to warm orange. 
Decorative elements: abstract geometric shapes, palm leaf shadows. 
Clean professional layout, 4K resolution, Instagram post format."
```

### 2. Tipografi ve Metin Talimatları
NanoBanana Pro, metinlerde oldukça güçlüdür:
```
✅ "Bold white sans-serif text reading 'SUMMER SALE' at the top"
✅ "Elegant script font saying 'Grand Opening' with gold color"
✅ "Clean modern typography: headline in uppercase, subtext in lighter weight"
```

**Metin İpuçları:**
- Metni tırnak içinde yazın: `"SUMMER SALE"`
- Kısa tutun (1-5 kelime ideal)
- Font stilini belirtin (sans-serif, serif, script, bold, light)
- Yerleşimi tanımlayın (centered, top-left, bottom-right)
- Rengi belirtin

### 3. Uygun Aspect Ratio Seçin
| Platform | Oran | Kullanım |
|----------|------|----------|
| Instagram Post | `4:5` | En çok etkileşim alan format |
| Instagram Kare | `1:1` | Klasik grid uyumlu |
| Instagram Story | `9:16` | Dikey tam ekran |
| YouTube Thumbnail | `16:9` | Yatay |
| Pinterest | `2:3` | Dikey uzun |

### 4. Stil Referansları Kullanın
```
✅ "Apple product marketing style — clean, minimal, white space"
✅ "Luxury fashion editorial look — dramatic lighting, high contrast"
✅ "Flat design illustration style — geometric shapes, vibrant colors"
✅ "Retro vintage aesthetic — warm grain, muted earth tones"
✅ "Glassmorphism UI style — frosted glass panels, soft gradients"
✅ "Instagram influencer aesthetic — warm filters, lifestyle casual"
```

---

## 📋 Prompt Şablonları

### Instagram Tekli Post — Ürün
```
"Professional product photography of [ÜRÜN ADI] on a [YÜZEY]. 
Clean minimal composition with ample white space. Soft studio 
lighting from above-left creating gentle shadows. [MARKA RENK] 
accent elements framing the product. Small elegant text at bottom: 
'[CTA TEXT]' in [FONT STYLE]. 4K resolution, Instagram post 
format (4:5), modern commercial photography style."
```

### Instagram Tekli Post — Kampanya
```
"Eye-catching social media post for [KAMPANYA ADI]. Bold large 
text '[İNDİRİM YÜZDESI] OFF' in [RENK] [FONT] font. Background: 
[GRADIENT/RENK PALETİ]. Decorative elements: [ŞEKİLLER]. Brand 
logo area at bottom. 4:5 aspect ratio, modern graphic design, 
clean professional layout, vibrant and attention-grabbing."
```

### Poster / Afiş
```
"Professional event poster for [ETKİNLİK ADI]. Headline: 
'[BAŞLIK]' in large bold [FONT]. Date: '[TARİH]' in smaller 
clean font below. Visual theme: [TEMA AÇIKLAMASI]. Color palette: 
[RENKLER]. Layout: centered symmetric composition with visual 
hierarchy. Background: [ARKA PLAN]. Print-ready quality, 4K, 
professional graphic design."
```

---

## 🎠 Carousel Özel Rehber

Carousel postlar için **tutarlılık** en kritik faktördür:

### System Prompt (Groq'a Verilecek)
```
Sen bir carousel post tasarımcısısın. Her slide için tutarlı 
prompt'lar üret:

1. AYNI renk paleti kullan (her slide'da belirt)
2. AYNI tipografi stili (font ve boyut tutarlı)
3. AYNI layout yapısı (metin konumu, kenar boşlukları)
4. İçerik ADIM ADIM ilerlesin
5. İlk slide = dikkat çekici kapak
6. Son slide = CTA (call-to-action)
7. Her slide'da numara belirt (1/N formatında)
8. Marka renkleri ve tonu tutarlı olsun
```

### Carousel Slide Şablonu
```
"Slide [N/TOTAL] of an Instagram carousel about [KONU]. 
[Bu slide'ın içeriği]. 

Design style: consistent with series — [RENK PALETİ] background, 
[FONT] typography, slide number '[N/TOTAL]' in top-right corner. 
Clean modern layout with [IKON/İLLÜSTRASYON]. 4:5 aspect ratio, 
professional infographic style."
```

---

## ⚠️ Kaçınılması Gerekenler

- ❌ Uzun cümleler metin olarak yazdırmaya çalışmak (5 kelimeden fazla riskli)
- ❌ "beautiful", "aesthetic" gibi soyut sıfatlar
- ❌ Birden fazla odak noktası (bir ana konu per görsel)
- ❌ Karmaşık sahne kompozisyonları (basit → güçlü)

## 💡 Pro İpuçları

1. **Kritik metin varsa → düzenleme yapın** — Görseli metinsiz üretin, sonra Canva/Photoshop ile metin ekleyin
2. **Referans görsel kullanın** — Mevcut ürün fotoğrafını `image_input` olarak verin, model bunu temel alır
3. **"4K resolution, high detail"** — Her prompt'un sonuna ekleyin
4. **Tekrarlanan tasarımlar** — Aynı seed kullanarak tutarlı sonuçlar elde edin
5. **Renk paleti kodu verin** — "#FF6B6B coral pink, #4ECDC4 teal" gibi spesifik hex renkler
