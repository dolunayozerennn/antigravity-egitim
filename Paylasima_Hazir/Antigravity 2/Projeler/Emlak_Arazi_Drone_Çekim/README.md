> ⚠️ **ÖNEMLİ BİLGİLENDİRME**  
> Bu proje, eğitim ve örnekleme amacıyla hazırlanmış olan bir **taslak (template)** projedir. Doğrudan tıklayıp "çalıştır" (plug-and-play) mantığıyla tasarlanmamıştır. Kendi sisteminize entegre etmeden önce:
> - Kimlik bilgilerinizi (API anahtarları, token'lar, email adresleri) tanımlamanız
> - Dosya yollarını (file paths) ve bağlantıları kendi ortamınıza göre güncellemeniz
> - Senaryoyu kendi hedeflerinize göre özelleştirmeniz beklenmektedir.
> Lütfen bu kodları inceleyerek ve kendi senaryonuza uyarlayarak geliştirin.

# 🏗️ Emlak Arazi Drone Çekim

> **⚠️ TASLAK PROJE:** Bu proje, bir AI otomasyon sisteminin iskelet yapısını göstermek amacıyla paylaşılmıştır. Tam çalışır durumda değildir — kendi API anahtarlarınızı ve proje gereksinimlerinizi eklemeniz beklenmektedir.

**Durum:** 🔧 Geliştirme
**Agent:** 🎬 icerik-uretim

---

## Açıklama

Dubai emlak arazi ve gayrimenkul projeleri için drone çekim simülasyonu ve görselleştirme sistemi. Google Maps verileri ile arazi analizi yapar, Kie AI ile drone perspektifli video içerikleri üretir.

## Kullanılan Servisler

- **Google Maps API** — Arazi konum ve harita verileri
- **Kie AI** — AI video üretim
- **ImgBB** — Görsel upload
- **Gemini** — AI analiz ve değerlendirme

## Çalıştırma

```bash
cp .env.example .env  # Değerleri doldur
pip install -r requirements.txt
python src/main.py
```

## Dosya Yapısı

| Dosya | Açıklama |
|-------|---------|
| `src/config.py` | Konfigürasyon |
| `src/` | Kaynak kodlar |
| `.env.example` | Env variable şablonu |
| `requirements.txt` | Python bağımlılıkları |

---

*Antigravity ile oluşturulmuş taslak projedir.*
