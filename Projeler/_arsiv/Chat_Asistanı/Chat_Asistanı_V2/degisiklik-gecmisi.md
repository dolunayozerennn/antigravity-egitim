# degisiklik-gecmisi.md — Versiyon ve Güncelleme Kayıtları

## Versiyon Geçmişi

### v1.0 — Şubat 2026
**İlk sürüm**

- Sistem mimarisi oluşturuldu (ManyChat → Webhook → AI → ManyChat)
- Multimodal mesaj desteği eklendi (metin, görsel, ses)
- 3 bölümlü bilgi tabanı şablonu hazırlandı (Biz Kimiz, Ürünler, SSS)
- ManyChat API entegrasyonu: setCustomField + sendFlow
- 3 AI sağlayıcı desteği: OpenAI, Anthropic, Google
- Ses transkript desteği: OpenAI Whisper + Google Speech-to-Text alternatifi
- Konuşma hafızası: subscriber_id bazlı son 10 mesaj
- Yapılandırılmış çıktı: JSON formatında metin + link_url
- Yanıt temizleme ve normalize etme
- Webhook güvenliği: X-Webhook-Secret header doğrulaması
- Railway deployment rehberi
- Maliyet tahmini dokümantasyonu
- Hata çözümleri dokümantasyonu
- Sistem akış haritası (Mermaid)