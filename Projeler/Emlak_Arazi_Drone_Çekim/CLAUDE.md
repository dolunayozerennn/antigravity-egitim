# CLAUDE.md — Arsa Tanıtım Drone Video Otomasyonu

## Proje Özeti

Bu otomasyon, emlakçılardan alınan arsa bilgilerini (il, ilçe, mahalle, ada, parsel) kullanarak, arsanın drone çekimi simülasyonu içeren profesyonel bir sosyal medya tanıtım videosu üretir. Süreç tamamen otomatiktir: veri toplama → uydu görseli alma → AI ile frame üretimi → video birleştirme → Instagram-ready çıktı.

---

## Mimari Genel Bakış

```
[Emlakçı Input] → [TKGM Parsel Sorgu] → [Google Maps Static API] → [AI Frame Generation] → [Video Generation] → [Final Output]
```

### Akış Detayı

```
ADIM 0: Emlakçı → il, ilçe, mahalle, ada, parsel bilgisi verir
ADIM 1: TKGM API → Parsel polygon koordinatları + yüzölçümü + nitelik bilgisi
ADIM 2: Google Maps Static API → Uydu görseli (dikey format, 2-3x zoom out)
ADIM 3: Nano Banana Pro → Uydu görselinden 45° drone perspective frame (FRAME 1)
ADIM 4: AI Image Generation → Arsanın sınırları ışıklı çizgilerle belirlenmiş frame (FRAME 2)
ADIM 5: AI Image Generation → Metrekare yazısı eklenmiş frame (FRAME 3)
ADIM 6: AI Image Generation → Arsa üzerinde proje görseli (ev/bina/havuz) (FRAME 4)
ADIM 7: AI Image Generation → Göz hizası perspektif frame (FRAME 5 - Video 4 end frame)
ADIM 8: Video AI → Frame 1 → Frame 2 (Video 1: Drone bakışı → ışıklı sınırlar)
ADIM 9: Video AI → Frame 2 → Frame 3 (Video 2: Işıklı sınırlar → metrekare)
ADIM 10: Video AI → Frame 3 → Frame 4 (Video 3: Metrekare → proje görseli)
ADIM 11: Video AI → Frame 4 → Frame 5 (Video 4: Drone bakışı → göz hizası zoom)
ADIM 12: FFmpeg veya benzeri → 4 videoyu birleştir → Final output
```

### Çıktı Spesifikasyonları
- Format: MP4 (H.264)
- Çözünürlük: 1080x1920 (dikey / Instagram Reels)
- Toplam süre: ~15-25 saniye (her video segmenti ~4-6 saniye)
- FPS: 24 veya 30

---

## ADIM 0: Emlakçı Input

### Gerekli Bilgiler
Emlakçıdan minimum şu bilgiler alınmalı:
1. **İl** (örn: "Antalya")
2. **İlçe** (örn: "Alanya")
3. **Mahalle** (örn: "Kestel")
4. **Ada No** (örn: "216")
5. **Parsel No** (örn: "13")

### Opsiyonel Bilgiler
- Proje tipi tercihi (villa, apartman, ticari, havuz — belirtilmezse AI karar verir)
- Özel metin (metrekare yerine fiyat vb. yazmak isterse)

### Input Kanalı
Form, WhatsApp veya Instagram DM üzerinden toplanabilir. Anti-gravity akışında bu bilgiyi bir değişken seti olarak tanımla.

---

## ADIM 1: TKGM Parsel Sorgu — Veri Çekme

### Yaklaşım: Web Scraping / Reverse-Engineered API

TKGM'nin resmi public API'si yok. Ancak parselsorgu.tkgm.gov.tr sitesinin arka planında kullandığı endpoint'ler reverse-engineer edilmiş durumda.

### Akış

#### 1.1 — İl Listesi Çekme
```
GET https://cbsservis.tkgm.gov.tr/megsiswebapi.v3/api/idpidrisi/ilListesi
```
Response: JSON array — her il için `id` ve `ad` alanları var.

#### 1.2 — İlçe Listesi Çekme
```
GET https://cbsservis.tkgm.gov.tr/megsiswebapi.v3/api/idpidrisi/ilceListesi/{il_id}
```

#### 1.3 — Mahalle Listesi Çekme
```
GET https://cbsservis.tkgm.gov.tr/megsiswebapi.v3/api/idpidrisi/mahalleListesi/{ilce_id}
```

#### 1.4 — Parsel Sorgu
```
GET https://cbsservis.tkgm.gov.tr/megsiswebapi.v3/api/idpidrisi/parselSorgu/{mahalle_id}/{ada_no}/{parsel_no}
```

### Beklenen Output
Parsel sorgu response'unda şu bilgiler olacak:
- **Yüzölçümü** (m²) — Frame 3'teki metrekare yazısı için
- **Nitelik** (tarla, arsa, bağ vb.)
- **Geometri / Koordinatlar** — Parselin polygon koordinatları

### Koordinat Alma — GeoJSON
Parsel sorgu sitesinden GeoJSON formatında veri indirilebilir. Bu GeoJSON şunları içerir:
- Parselin köşe noktalarının lat/lon koordinatları (polygon)
- Alan bilgisi
- Öznitelik bilgileri

### Alternatif Yol: Apify ile Scraping
Eğer API endpoint'leri çalışmazsa, Apify actor ile parselsorgu.tkgm.gov.tr sitesini scrape et:
1. URL oluştur: `https://parselsorgu.tkgm.gov.tr/#ara/idari/{mahalle_id}/{ada}/{parsel}`
2. Sayfayı yükle, GeoJSON indirme butonunu tetikle
3. GeoJSON dosyasını parse et

### Önemli Notlar
- TKGM koordinat hassasiyeti 4 ondalık hane (yaklaşık ±10m) — bu use case için yeterli
- Rate limiting olabilir, istekler arasında 1-2 saniye bekle
- Bu endpoint'ler resmi olmadığı için değişebilir; hata durumunda Apify fallback kullan

### Çıktı Değişkenleri (sonraki adımlara aktarılacak)
```
parcel_coordinates: [[lat1, lon1], [lat2, lon2], ...] // polygon köşeleri
parcel_area_m2: 1250 // yüzölçümü
parcel_center_lat: 36.5432
parcel_center_lon: 32.1234
parcel_nitelik: "arsa"
bounding_box: {north, south, east, west} // polygon'dan hesaplanacak
```

---

## ADIM 2: Google Maps Static API — Uydu Görseli

### Amaç
Parselin uydu görüntüsünü, 2-3 katı genişlikte zoom out yaparak, dikey formatta (1080x1920) almak.

### Bounding Box Hesaplama
```
1. Polygon koordinatlarından min/max lat ve lon değerlerini bul
2. Parsel genişliği ve yüksekliğini hesapla
3. Her yöne 2-3x genişlet (padding ekle)
4. Bu genişletilmiş bounding box'ı kullan
```

### API Çağrısı
```
https://maps.googleapis.com/maps/api/staticmap?
  center={parcel_center_lat},{parcel_center_lon}
  &zoom={hesaplanan_zoom_level}
  &size=1080x1920
  &scale=2
  &maptype=satellite
  &key={GOOGLE_MAPS_API_KEY}
```

### Zoom Level Hesaplama
Zoom level, bounding box genişliğine göre dinamik hesaplanmalı:
- Çok küçük arsa (< 500m²): zoom 19-20
- Orta arsa (500-5000m²): zoom 17-18
- Büyük arsa (> 5000m²): zoom 15-16

Formül: Bounding box'ın 1080px genişliğe sığacağı en yüksek zoom level'ı seç.

### Önemli Parametreler
- `maptype=satellite` — Uydu görüntüsü şart (hybrid değil, label'sız)
- `scale=2` — Retina kalite (2160x3840 efektif çözünürlük)
- `format=png` — Kayıpsız kalite

### Google Maps API Limitleri ve Maliyetler
- Static Maps API: ayda 28.000 ücretsiz yükleme
- Sonrası: $2 / 1000 istek
- Günlük limit: Varsayılan 25.000

### Çıktı
- `satellite_image.png` — 1080x1920 dikey uydu görseli

---

## ADIM 3: Frame 1 — Drone Perspective (Nano Banana Pro)

### Amaç
Düz uydu görselini, 45 derecelik açıyla yukarıdan bakan gerçekçi bir drone çekimine dönüştürmek.

### Input
- `satellite_image.png` (Adım 2'den)

### Kullanılacak AI
**Nano Banana Pro** (Image-to-Image)

### Prompt Şablonu
> Bkz: PROMPTS.md — FRAME_1_DRONE_PERSPECTIVE

### Kalite Kontrol
- Çıktının orijinal uydu görseli ile aynı bölgeyi gösterdiğinden emin ol
- 45 derece açı tutarlılığı
- Gerçekçi toprak/yeşillik dokusu
- Yapay artefakt olmaması

### Çıktı
- `frame_1_drone.png` — 1080x1920, drone perspective

---

## ADIM 4: Frame 2 — Işıklı Sınır Çizimi

### Amaç
Drone perspective üzerinde, arsanın sınırlarının parlak/neon ışıklı çizgilerle belirlendiği bir görsel.

### Yaklaşım: AI Image Generation

Frame 1'i referans alarak, arsanın sınırlarının ışıklı çizgilerle çevrelendiği bir görsel üret.

### Input
- `frame_1_drone.png`
- `parcel_coordinates` (polygon köşe noktaları)

### Prompt Şablonu
> Bkz: PROMPTS.md — FRAME_2_GLOWING_BORDERS

### Kritik Not
AI'ın sınırları doğru yere çizmesi zor olabilir. İki strateji:

**Strateji A (Tercih Edilen): Programatik Overlay + AI Refinement**
1. Python/Pillow ile polygon koordinatlarını frame_1 üzerine glow efektli çiz
2. Bu ham overlay'li görseli AI'a ver, "refine et, daha gerçekçi yap" de

**Strateji B: Tamamen AI**
1. Frame 1'i AI'a ver
2. Prompt'ta arsanın konumunu detaylı tarif et
3. AI'ın kendi yorumlamasına güven

Anti-gravity ortamında Strateji B daha kolay uygulanır. Ama tutarlılık sorunları olursa Strateji A'ya geç.

### Çıktı
- `frame_2_glowing.png` — 1080x1920, ışıklı sınırlar

---

## ADIM 5: Frame 3 — Metrekare Yazısı

### Amaç
Işıklı sınırların olduğu görsel üzerinde, arsanın ortasında büyük, 3D, kalın fontla metrekare bilgisinin yazıldığı frame.

### Input
- `frame_2_glowing.png`
- `parcel_area_m2` (örn: "1.250 m²")

### Prompt Şablonu
> Bkz: PROMPTS.md — FRAME_3_AREA_TEXT

### Metin Formatı
- `{parcel_area_m2} m²` (örn: "1.250 m²")
- Binlik ayırıcı nokta kullan (Türkiye formatı)
- Font: 3D, kalın, beyaz veya altın rengi, gölgeli
- Pozisyon: Arsanın tam ortasında, drone perspektifine uygun açıyla

### Çıktı
- `frame_3_area.png` — 1080x1920, metrekare yazısı

---

## ADIM 6: Frame 4 — Proje Görseli

### Amaç
Boş arsanın üzerine gerçekçi bir mimari proje (ev, villa, bina, havuz vb.) yerleştirmek. Arsayla ne yapılabileceğini görselleştirmek.

### Input
- `frame_3_area.png` veya `frame_1_drone.png` (drone perspective)
- `parcel_area_m2` (proje boyutunu belirlemek için)
- `parcel_nitelik` (arsa tipi ipucu verir)

### Proje Tipi Seçimi
Eğer emlakçı belirtmediyse, AI yüzölçümüne göre karar versin:
- < 500 m²: Modern villa + bahçe
- 500-2000 m²: İkiz villa veya küçük apartman
- 2000-10000 m²: Rezidans veya site projesi
- > 10000 m²: Büyük proje (otel, site, ticari)

### Prompt Şablonu
> Bkz: PROMPTS.md — FRAME_4_PROJECT_VISUALIZATION

### Çıktı
- `frame_4_project.png` — 1080x1920, proje görseli

---

## ADIM 7: Frame 5 — Göz Hizası Perspektif (Video 4 End Frame)

### Amaç
Drone bakışından (yukarıdan) göz hizasına (yerden ~1.7m) geçiş için end frame. Projenin cepheden görünümü.

### Input
- `frame_4_project.png` (referans olarak)
- Proje tipi bilgisi

### Prompt Şablonu
> Bkz: PROMPTS.md — FRAME_5_EYE_LEVEL

### Önemli
Bu frame, Frame 4'teki projenin aynısının farklı açıdan görünümü olmalı. Tutarlılık kritik.

### Çıktı
- `frame_5_eyelevel.png` — 1080x1920, göz hizası

---

## ADIM 8-11: Video Üretimi

### Kullanılacak AI
**Kling** (veya Runway Gen-3, Pika — Kling tercih edilir)

### Video 1: Frame 1 → Frame 2
- Start: `frame_1_drone.png`
- End: `frame_2_glowing.png`
- Süre: 4-5 saniye
- Hareket: Minimal kamera hareketi, ışıklı çizgiler yavaşça beliriyor
- Prompt: Bkz PROMPTS.md — VIDEO_1

### Video 2: Frame 2 → Frame 3
- Start: `frame_2_glowing.png`
- End: `frame_3_area.png`
- Süre: 3-4 saniye
- Hareket: Hafif zoom in, text beliriyor
- Prompt: Bkz PROMPTS.md — VIDEO_2

### Video 3: Frame 3 → Frame 4
- Start: `frame_3_area.png`
- End: `frame_4_project.png`
- Süre: 4-5 saniye
- Hareket: Morphing/transition — boş arsa projeye dönüşüyor
- Prompt: Bkz PROMPTS.md — VIDEO_3

### Video 4: Frame 4 → Frame 5
- Start: `frame_4_project.png`
- End: `frame_5_eyelevel.png`
- Süre: 4-5 saniye
- Hareket: Drone yukarıdan aşağıya zoom + açı değişimi (kuşbakışı → göz hizası)
- Prompt: Bkz PROMPTS.md — VIDEO_4

### Video Birleştirme
4 videoyu sırasıyla birleştir. Aralarında crossfade transition (0.5 saniye) eklenebilir.
FFmpeg komutu veya video birleştirme API'si kullanılabilir.

---

## Hata Yönetimi

### TKGM API Hatası
- Endpoint çalışmazsa → Apify scraping fallback
- Parsel bulunamazsa → Emlakçıya "parsel bulunamadı" mesajı gönder
- Koordinat boş gelirse → Emlakçıdan Google Maps linki iste

### Google Maps API Hatası
- API key limiti aşılırsa → Yedek API key kullan
- Görüntü kalitesi düşükse (bulutlu/düşük çözünürlük) → Zoom level'ı 1 artırıp tekrar dene

### AI Frame Generation Hatası
- Nano Banana Pro çıktısı beklentileri karşılamıyorsa → Prompt'u refine et, 2. deneme yap
- Maksimum 3 deneme, sonra manuel müdahale gerektiğini bildir

### Video AI Hatası
- Kling çıktısı pürüzlüyse → Farklı seed ile tekrar dene
- Frame tutarlılığı bozuksa → Start/end frame arasındaki farkı azalt

---

## Maliyet Tahmini (arsa başına)

| Hizmet | Tahmini Maliyet |
|--------|----------------|
| TKGM Sorgu | Ücretsiz |
| Google Maps Static API | ~$0.002 |
| Nano Banana Pro (1 frame) | ~$0.05-0.10 |
| AI Image Generation (3 frame) | ~$0.15-0.30 |
| Kling Video Generation (4 video) | ~$1.00-2.00 |
| **Toplam** | **~$1.20-2.50 / arsa** |

---

## Zamanlama

| Adım | Tahmini Süre |
|------|-------------|
| TKGM Sorgu | 5-10 saniye |
| Google Maps API | 2-3 saniye |
| Frame Generation (4 frame) | 2-5 dakika |
| Video Generation (4 video) | 10-20 dakika |
| Video Birleştirme | 30 saniye |
| **Toplam** | **15-30 dakika** |

Asenkron çalış: Video generation sırasında emlakçıya "videonuz hazırlanıyor" mesajı gönder.

---

## Değişkenler Referansı

Bu otomasyon boyunca taşınacak değişkenler:

```
// Input
input_il: string
input_ilce: string
input_mahalle: string
input_ada: string
input_parsel: string
input_proje_tipi: string (opsiyonel)

// TKGM'den gelen
parcel_coordinates: array of [lat, lon]
parcel_area_m2: number
parcel_center_lat: number
parcel_center_lon: number
parcel_nitelik: string
bounding_box: {north, south, east, west}

// Üretilen görseller
satellite_image: image file
frame_1_drone: image file
frame_2_glowing: image file
frame_3_area: image file
frame_4_project: image file
frame_5_eyelevel: image file

// Üretilen videolar
video_1: video file
video_2: video file
video_3: video file
video_4: video file
final_video: video file
```
