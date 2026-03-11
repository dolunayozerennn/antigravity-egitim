# maliyet-tahmini.md — Mesaj Başına Tahmini API Maliyeti

## Kullanım

Bu dosya, sistemin her müşteri mesajı için tahmini API maliyetini hesaplar.
Maliyetler Şubat 2026 fiyatlarına göre hesaplanmıştır. Güncel fiyatları her zaman sağlayıcının web sitesinden kontrol edin.

> Not: Aşağıdaki hesaplamalar ortalama bir müşteri mesajı senaryosuna dayanır. Gerçek maliyetler mesaj uzunluğuna, görsel/ses kullanımına ve konuşma geçmişi uzunluğuna göre değişir.

---

## Varsayımlar

| Parametre | Değer |
|-----------|-------|
| Ortalama giriş (sistem promptu + bilgi tabanı + hafıza + mesaj) | ~2.000 token |
| Ortalama çıkış (AI yanıtı) | ~200 token |
| Görsel analiz ek maliyeti | ~300 token giriş + 100 token çıkış |
| Ses transkript ortalama süre | ~15 saniye |

---

## Senaryo 1: Sadece Metin Mesajı

En yaygın senaryo. Müşteri metin yazar, AI metin ile yanıt verir.

| Sağlayıcı | Model | Giriş maliyeti | Çıkış maliyeti | Mesaj başına toplam |
|------------|-------|----------------|-----------------|---------------------|
| OpenAI | gpt-4.1 | 2.000 × $2.00/1M = $0.004 | 200 × $8.00/1M = $0.0016 | **~$0.0056** |
| OpenAI | gpt-4.1-mini | 2.000 × $0.40/1M = $0.0008 | 200 × $1.60/1M = $0.00032 | **~$0.0011** |
| Anthropic | claude-sonnet-4 | 2.000 × $3.00/1M = $0.006 | 200 × $15.00/1M = $0.003 | **~$0.009** |
| Google | gemini-2.5-flash | 2.000 × $0.15/1M = $0.0003 | 200 × $0.60/1M = $0.00012 | **~$0.0004** |

---

## Senaryo 2: Görsel Mesaj

Müşteri görsel gönderir. Sistem önce görseli analiz eder, sonra yanıt üretir. Toplamda 2 API çağrısı.

| Sağlayıcı | Görsel analiz | Yanıt üretimi | Mesaj başına toplam |
|------------|---------------|---------------|---------------------|
| OpenAI (gpt-4.1) | ~$0.003 | ~$0.0056 | **~$0.0086** |
| OpenAI (gpt-4.1-mini) | ~$0.0006 | ~$0.0011 | **~$0.0017** |
| Anthropic (claude-sonnet-4) | ~$0.005 | ~$0.009 | **~$0.014** |
| Google (gemini-2.5-flash) | ~$0.0003 | ~$0.0004 | **~$0.0007** |

---

## Senaryo 3: Sesli Mesaj

Müşteri sesli mesaj gönderir. Sistem önce sesi metne çevirir (Whisper), sonra yanıt üretir. Toplamda 2 API çağrısı.

| Sağlayıcı | Whisper transkript (15 sn) | Yanıt üretimi | Mesaj başına toplam |
|------------|---------------------------|---------------|---------------------|
| OpenAI (gpt-4.1) | ~$0.0015 | ~$0.0056 | **~$0.0071** |
| OpenAI (gpt-4.1-mini) | ~$0.0015 | ~$0.0011 | **~$0.0026** |
| Anthropic (claude-sonnet-4) | ~$0.0015 | ~$0.009 | **~$0.0105** |
| Google (gemini-2.5-flash) | ~$0.0015 | ~$0.0004 | **~$0.0019** |

> Whisper fiyatı: $0.006 / dakika. 15 saniyelik ses = $0.0015

---

## Aylık Maliyet Tahmini

Günde ortalama 50 mesaj alan bir işletme için (ayda ~1.500 mesaj):

| Sağlayıcı | Model | Aylık tahmini maliyet |
|------------|-------|-----------------------|
| OpenAI | gpt-4.1 | **~$8.40** (~270 ₺) |
| OpenAI | gpt-4.1-mini | **~$1.65** (~53 ₺) |
| Anthropic | claude-sonnet-4 | **~$13.50** (~435 ₺) |
| Google | gemini-2.5-flash | **~$0.60** (~19 ₺) |

> TL karşılıkları yaklaşık kur üzerinden hesaplanmıştır (1$ ≈ 32 ₺). Güncel kuru kontrol edin.

---

## Ek Maliyetler

| Kalem | Maliyet |
|-------|---------|
| ManyChat Pro | ~$15/ay (1.000 kontağa kadar) |
| Railway hosting | ~$5/ay (küçük işletme trafiği) |
| **Toplam platform maliyeti** | **~$20/ay sabit + API kullanım maliyeti** |

---

## Maliyet Optimizasyon Önerileri

1. **Bütçe öncelikli:** Google Gemini 2.5 Flash en ucuz seçenektir. Kalitesi çoğu müşteri hizmeti senaryosu için yeterlidir.
2. **Kalite öncelikli:** OpenAI gpt-4.1 veya Anthropic Claude Sonnet 4 daha kaliteli yanıtlar üretir ama maliyeti yüksektir.
3. **Denge:** OpenAI gpt-4.1-mini en iyi fiyat/performans oranını sunar.
4. **Bilgi tabanını kısa tutun.** Gereksiz bilgi = gereksiz token = gereksiz maliyet.
5. **Hafıza limitini ayarlayın.** Son 10 yerine son 5 mesaj tutmak maliyeti düşürür.