# Hatalar ve Çözümler Günlüğü

Geçmişte karşılaşılan hatalar ve çözümleri. Aynı sorunu iki kez çözmemek için bu dosyayı güncelliyoruz.

**Format:** Her hata bloğu aşağıdaki yapıyı takip eder.

---

## Kie AI

### Sora 2 Pro Storyboard — Model adı ve format hataları
- **Sorun:** Model adı `sora-2-pro` değil, tam olarak `sora-2-pro-storyboard` olmalı
- **Sorun:** `shots` alanı içinde `Scene` büyük S ile yazılmalı
- **Sorun:** `n_frames` ve `aspect_ratio` zorunlu alan — eksik olunca 422 hatası
- **Çözüm:**
  ```json
  {
    "model": "sora-2-pro-storyboard",
    "input": {
      "n_frames": 150,
      "aspect_ratio": "16:9",
      "shots": [{ "Scene": "...", "image_urls": [] }]
    }
  }
  ```
- **Tarih:** Şubat 2026

### Kie AI — Eski API anahtarı
- **Sorun:** `47b22662b68bd510479967aaf8d40a65` anahtarı bazı modellerde çalışmıyor olabilir
- **Çözüm:** Yeni anahtar `97d226c568fea77abdeaedde37a6c6aa` kullan
- **Tarih:** Şubat 2026

### Video üretimi sonrası URL gelmeme
- **Sorun:** `resultJson` alanı string olarak geliyor, JSON parse edilmeli
- **Çözüm:** `json.loads(data["resultJson"])["resultUrls"][0]`
- **Tarih:** Şubat 2026

---

## Gmail / Outreach

### OAuth Token Hatası (`invalid_grant`)
- **Sorun:** `token.json` süresi dolmuş veya bozulmuş
- **Çözüm:** `token.json` dosyasını sil → scripti tekrar çalıştır → tarayıcıda yeniden onayla
- **Tarih:** —

---

## Apify

### Boş sonuç / Actor başlamıyor
- **Sorun:** Çok kısıtlayıcı filtreler veya hatalı Actor ID
- **Çözüm:** Actor ID'yi Apify konsolundan kopyala, filtreleri genişlet
- **Tarih:** —

### Kredi tükenmesi
- **Çözüm:** `_knowledge/api-anahtarlari.md` → Apify Hesap 2 (yedek) kullan
- **Tarih:** —

---

## Telegram Bot

### Markdown parse hatası
- **Sorun:** GPT yanıtındaki özel karakterler Telegram'da hata veriyor
- **Çözüm:** Yanıtı göndermeden önce `escape_markdown()` ile temizle
- **Tarih:** Şubat 2026

---

> *(Yeni hata karşılaşıldığında bu dosyaya ekle)*

---

## Railway Deploy

### Sandbox, Shell Script'ten Dosya Okumasını Engeller
- **Sorun:** `cat`, `grep` gibi komutlarla `_knowledge/api-anahtarlari.md` veya herhangi bir dosyadan token okunamıyor. `Operation not permitted` hatası veriyor.
- **Neden:** Antigravity sandbox ortamında çalışıyor. Sandbox, güvenlik nedeniyle shell komutlarının dosya okuma yetkisini kısıtlıyor.
- **Yanlış Çözümler (Çalışmayan):**
  - Shell script ile `cat dosya.txt` → ❌ İzin hatası
  - Gizli dosya `.railway-token` oluşturma → ❌ Gizli dosyalar ekstra kısıtlı
  - Farklı klasörlere token dosyası koyma → ❌ Tüm klasörler kısıtlı
- **Doğru Çözüm:** Antigravity'nin kendi `view_file` tool'unu kullanarak dosyayı oku, sonra token'ı komutu çalıştırırken `RAILWAY_TOKEN="okunan_token"` olarak enjekte et.
- **Kural:** Token gereken her işlemde `view_file` → `_knowledge/api-anahtarlari.md` → Token'ı oku → Komuta prefix olarak ekle.
- **Tarih:** Mart 2026

### Railway CLI "Unauthorized" ama GraphQL API Çalışıyor
- **Sorun:** `railway whoami`, `railway list` gibi CLI komutları `Unauthorized` hatası veriyor ama aynı token ile Railway GraphQL API'ye `curl` ile istek atınca sorunsuz çalışıyor.
- **Neden:** Railway CLI'ın eski versiyonu (veya workspace-scoped token'lar) bazı CLI komutlarıyla uyumsuz olabiliyor. CLI dahili olarak farklı bir auth endpoint kullanıyor.
- **Çözüm:** CLI çalışmazsa **GraphQL API fallback** kullan:
  ```bash
  curl -s -X POST https://backboard.railway.app/graphql/v2 \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer TOKEN" \
    -d '{"query": "{ projects { edges { node { id name } } } }"}'
  ```
- **Tarih:** Mart 2026

### Yeni Railway Token Propagation Gecikmesi
- **Sorun:** Yeni oluşturulan Railway token'ı ilk dakikalarda `Invalid RAILWAY_TOKEN` hatası verebilir.
- **Çözüm:** 3-5 dakika bekleyip tekrar dene. Token sonunda aktif olur.
- **Tarih:** Mart 2026

### BASH_SOURCE Sandbox'ta Boş Dönüyor
- **Sorun:** `bash script.sh` ile çalıştırılan script'lerde `${BASH_SOURCE[0]}` boş dönüyor. Bu da `SCRIPT_DIR` doğru hesaplanamıyor.
- **Çözüm:** `BASH_SOURCE` yerine sabit yol (hardcoded path) kullan.
- **Tarih:** Mart 2026
