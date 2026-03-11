# ✏️ Qwen Image Edit — Prompt Rehberi

## En İyi Kullanım Alanı
Mevcut görselleri düzenleme, arka plan değişikliği, nesne ekleme/çıkarma, renk düzeltme.

## ⚠️ ÖNEMLİ: Sadece İngilizce Prompt Desteklenir

---

## ✅ Altın Kurallar

### 1. Düzenleme Talimatını Net Verin
```
❌ KÖTÜ: "Make it better"
✅ İYİ: "Change the background from white to a sunny tropical 
beach with palm trees and turquoise ocean water"
```

### 2. Strength Değerini Doğru Ayarlayın

| Düzenleme Türü | Strength | Örnek |
|----------------|----------|-------|
| Renk/ton düzeltme | 0.1-0.3 | "Warm up the color temperature" |
| Arka plan değişikliği | 0.4-0.6 | "Replace background with..." |
| Nesne ekleme/çıkarma | 0.6-0.8 | "Add a hat to the person" |
| Büyük transformasyon | 0.8-1.0 | "Transform into watercolor painting" |

### 3. Spesifik ve Eylem Odaklı Olun
```
✅ "Remove the text watermark in the bottom-right corner"
✅ "Add soft bokeh to the background while keeping the subject sharp"
✅ "Replace the sky with a dramatic sunset with orange and purple clouds"
✅ "Change the person's shirt color from blue to red"
✅ "Add realistic shadows under the product"
```

---

## 📋 Prompt Şablonları

### Arka Plan Değişikliği
```
"Replace the entire background with [YENİ ARKA PLAN AÇIKLAMASI]. 
Keep the main subject completely unchanged. Match the lighting 
direction and color temperature of the new background to the subject."
strength: 0.5
```

### Nesne Ekleme
```
"Add [NESNE] to the scene, positioned [KONUM]. Make it look 
naturally integrated with matching lighting, shadows, and 
perspective."
strength: 0.6
```

### Nesne Çıkarma
```
"Remove the [NESNE] from the image. Fill the area naturally 
with the surrounding background texture and pattern."
strength: 0.5
```

### Stil Transferi
```
"Transform this photograph into a [watercolor painting / oil 
painting / pencil sketch / anime style] while preserving the 
composition and subject details."
strength: 0.8
```

### Metin Değişikliği
```
"Change the text on the sign/poster from '[ESKİ METİN]' to 
'[YENİ METİN]'. Keep the same font style and color."
strength: 0.4
```

---

## 💡 Pro İpuçları

1. **Düşük strength kullanarak test edin** — Sonuç kötüyse artırın
2. **Orijinal görseli koruyun** — Çok yüksek strength görseli kaybettirir
3. **Türkçe talimat varsa** → Önce Groq ile İngilizce'ye çevirin
4. **Karmaşık düzenlemeleri parçalayın** — Bir seferde bir düzenleme yapın
5. **Lighting match** — Yeni eklenen nesnelerin ışık yönünün orijinalle uyumlu olmasını belirtin
