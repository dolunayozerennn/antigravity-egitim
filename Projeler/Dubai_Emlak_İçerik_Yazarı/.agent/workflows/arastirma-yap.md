---
description: Dubai gayrimenkul piyasası hakkında internette araştırma yap
---

# /arastirma-yap Workflow

Güncel veri, istatistik veya bölge bilgisi gerektiğinde bu workflow'u kullan.

## Adımlar

### 1. Araştırma konusunu belirle
Kullanıcıdan öğren:
- Ne araştırılacak? (Bölge, fiyat, trend, yasal değişiklik, vb.)
- Ne için kullanılacak? (Script, veri doğrulama, genel bilgi)

### 2. İngilizce arama yap
**KRİTİK:** Araştırma her zaman **İngilizce** yapılır. Türkçe kaynak yetersizdir.

Örnek arama sorguları:
- `"Dubai [bölge] property prices 2025 2026"`
- `"Dubai real estate market trends Q1 2026"`
- `"[bölge] rental yield Dubai"`
- `"Dubai off-plan property investment risks"`
- `"RERA Dubai regulations [konu]"`

`search_web` aracını kullan:
```
search_web("Dubai JVC apartment prices 2026 rental yield")
```

### 3. Kaynakları oku
Güvenilir kaynakları tercih et:
- **Birincil:** Property Finder, Bayut, DLD (Dubai Land Department), RERA
- **İkincil:** Arabian Business, Gulf News, Khaleej Times
- **Veri:** Statista, Knight Frank, JLL, CBRE Dubai raporları

`read_url_content` ile kaynakları oku ve ilgili bilgileri çıkar.

### 4. Bilgiyi özetle
Araştırma sonuçlarını Türkçe olarak özetle:
- Rakamları USD cinsinden ver
- Kaynak belirt
- Tarihi belirt (veri ne kadar güncel?)
- Script'e nasıl entegre edileceğini öner

### 5. Çıktı formatı
```markdown
## Araştırma: [Konu]

**Tarih:** [Araştırma tarihi]
**Kaynaklar:** [URL listesi]

### Bulgular
- Bulgu 1
- Bulgu 2

### Script'e Entegrasyon Önerisi
(Bu bilgi nasıl kullanılabilir)
```
