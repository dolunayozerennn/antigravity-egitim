---
description: Paylaşım — Skill, proje veya tüm Antigravity starter kit'ini başkalarının kullanabileceği formata dönüştür
---

> **🤖 Agent:** Bu workflow `_agents/yayinla-paylas/AGENT.md` agent'ının bir parçasıdır.
> Agent üzerinden veya bağımsız olarak `/proje-paylas` komutuyla çalıştırılabilir.

# 📦 Paylaşım (Export)

Skill'leri, projeleri veya bütün Antigravity yapısını başkalarının alıp kullanabileceği formata çevirir. 
API anahtarlarını temizler, bağımlılıkları çözer, kurulum rehberi üretir.

## Gerekli Skill
`_skills/folder-paylasim/SKILL.md` → ÖNCE OKU

## Kullanım

Bu workflow 3 modda çalışır. Kullanıcı ne paylaşmak istediğini belirtir:

### Mod 1: Skill Paylaşımı
```
/proje-paylas skill [skill-adi]
```
Örnek: `/proje-paylas skill kie-ai-video-production`

### Mod 2: Proje Paylaşımı
```
/proje-paylas proje [proje-adi]
```
Örnek: `/proje-paylas proje B2B_Outreach`

### Mod 3: Starter Kit (Tam Antigravity)
```
/proje-paylas starter-kit
```

---

## Adımlar (Tüm Modlar İçin Genel Akış)

1. **Skill'i Oku**
   - `_skills/folder-paylasim/SKILL.md` dosyasını oku
   - İlgili mod bölümündeki adımları takip et

2. **Otomatik Güvenlik Taraması (Zorunlu)**
   - Paylaşılacak proje klasörünü belirle.
   - Sızıntıları engellemek için **ZORUNLU** olarak şu komutu çalıştır:
     ```bash
     python _skills/folder-paylasim/scripts/security_scanner.py --target [HEDEF_KLASOR_YOLU_BURAYA]
     ```
   - Çıktı kırmızı (HATA) dönerse: Taramanın gösterdiği sorunlu dosyalardaki tüm sızıntıları temizle ve komutu tekrar çalıştır.
   - Tarama YEŞİL (✅) dönene kadar paylaşım işlemini ilerletme.

3. **Bağımlılık Kontrolü**
   - `_skills/folder-paylasim/checklists/bagimlilik-kontrol.md` dosyasını referans al
   - Proje dışı import'ları tespit et ve çöz
   - Skill bağımlılıklarını tespit et ve belirle
   - requirements.txt oluştur/güncelle

4. **Belgeleme**
   - İlgili şablonu `_skills/folder-paylasim/templates/` altından al
   - Skill export → `GEREKSINIMLER_SKILL.md` şablonundan `GEREKSINIMLER.md` oluştur
   - Proje export → `KURULUM_REHBERI_PROJE.md` şablonundan `KURULUM_REHBERI.md` oluştur
   - Starter Kit → `BASLANGIÇ_REHBERI.md` şablonundan oluştur
   - Profil şablonu → `profil-sablon.md`
   - API anahtarları şablonu → `api-anahtarlari-sablon.md`

5. **Sonuç Raporlama**
   - Temizlenen key'leri listele
   - Silinen/hariç tutulan dosyaları listele
   - Tespit edilen bağımlılıkları listele
   - Hedef klasör yolunu bildir
