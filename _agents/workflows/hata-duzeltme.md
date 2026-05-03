---
description: Hata düzeltme — kök neden analizi, etki analizi ve doğrulamalı fix uygulama protokolü
---

# 🔍 Hata Düzeltme Protokolü

> ⛔ **MUTLAK KURAL:** Hata raporlandığında HEMEN koda dalma. Önce analiz, sonra plan, sonra fix.

## Adım 1: DURDUR — Kök Neden Analizi (3 Soru)

Kullanıcı bir hata bildirdiğinde veya log'da hata görüldüğünde, fix yazmadan ÖNCE şu 3 soruyu cevapla:

### Soru 1: "Bu hata TAM OLARAK nereden kaynaklanıyor?"
- Sadece hata mesajını değil, **kök nedeni** bul
- Hata mesajı = semptom, kök neden = hastalık
- Gerekirse `grep -rn` ile ilgili kodu tüm dosyalarda ara
- Railway/production loglarını oku (sadece son deployment değil, son 24 saat)

### Soru 2: "Bu fix başka nereleri etkiler?"
```bash
# Değişecek fonksiyonu/değişkeni tüm projede ara
grep -rn "FONKSIYON_ADI" PROJE_KLASORU/
```
- Fonksiyon parametreleri değişiyorsa → çağıran TÜM yerleri güncelle
- Import değişiyorsa → tüm dosyaları kontrol et
- Config değişiyorsa → env var'ları ve Railway ayarlarını kontrol et

### Soru 3: "Bu hata tipi daha önce görüldü mü?"
```
view_file → _knowledge/hatalar-ve-cozumler.md
```
- Aynı pattern varsa → kanıtlanmış çözümü uygula, tekerleği yeniden icat etme
- Yoksa → web araştırması yap (platform belgelerini kontrol et)

### Soru 4: "Bu hata sistem skill'lerine aykırı mı?"
- Hata bir entegrasyonla ilgiliyse (Railway, Supabase, Apify, Notion, Telegram vb.)
- Kod yazmadan önce `_skills/` dizinindeki ilgili `SKILL.md` kurallarını oku. Sorun kural ihlali kaynaklı olabilir.

## Adım 2: PLANLA — Fix Planını Sun

Kullanıcıya kısa ve net bir plan sun:

```
🔍 Kök Neden: [1 cümle]
🎯 Çözüm: [1-2 cümle]
📁 Değişecek dosyalar: [liste]
⚠️ Riskler: [yan etkiler varsa]
```

## Adım 3: KARAR — Teknik Fix Senin İşin

- Kök neden + çözüm planı netleştikten sonra **direkt uygula** — kullanıcıyı teknik plana onaylatma.
- Sadece şu durumlarda dur ve sor: (a) fix'in kullanıcıya görünür bir davranış değişikliği yaratıyor (ton, dil, akış), (b) geri-dönüşü zor + dış-dünyaya görünür (deploy/mesaj/silme), (c) ürünsel bir tercih gerekiyor (hangi model/servis).
- Tek bir teknik yaklaşım yerine birden fazla ürünsel okuma çıkıyorsa hangisini tercih ettiğini sor; teknik tercihi (kütüphane/refactor/dosya yapısı) sen seç.

## Adım 4: UYGULA — Minimal Müdahale

- **Sadece kırılan yeri düzelt**, dosyayı baştan yazma
- Değiştirilen satır sayısı mümkün olduğunca az olmalı
- 5 satırlık fix için 200 satır değiştirme

## Adım 5: DOĞRULA — Fix Doğrulaması

1. **Syntax kontrolü:** `python3 -m py_compile dosya.py`
2. **Import testi:** `python3 -c "import dosya"`
3. **Platform checklist:** `_knowledge/platform-checklists/railway.md` kontrol et
4. **Push + deploy** (gerekiyorsa)
5. **Log kontrolü:** 60 sn bekle, Railway loglarında fatal error ara

## Adım 6: KAYDET — Bilgi Bankasını Güncelle

Eğer bu yeni bir hata pattern'iyse:
```
_knowledge/hatalar-ve-cozumler.md → yeni entry ekle
```

Format:
```markdown
### [Hata Başlığı] — [Tarih]
**Semptom:** [Kullanıcının gördüğü hata]
**Kök neden:** [Gerçek sebep]
**Çözüm:** [Uygulanan fix]
**Etkilenen projeler:** [Liste]
**Önlem:** [Gelecekte nasıl önlenir]
```
