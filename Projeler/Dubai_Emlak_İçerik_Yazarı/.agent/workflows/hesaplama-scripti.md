---
description: Hesaplama içerikli yatırım scripti üret — daire fiyatı, mortgage, kira geliri hesapları ile
---

# /hesaplama-scripti Workflow

Yatırım hesaplama gerektiren video scriptleri için bu workflow'u kullan.

## Adımlar

### 1. Skill ve referans dosyaları oku
// turbo
`skills/icerik-yazari/SKILL.md` ve `reference-scripts/yatirim_hesaplama_scriptleri.md` dosyalarını oku.

### 2. Yatırım parametrelerini topla
Kullanıcıdan şu bilgileri al (verilmezse varsayılanları kullan):

| Parametre | Varsayılan | Açıklama |
|-----------|-----------|----------|
| Daire fiyatı | — | Zorunlu (USD) |
| Peşinat % | %20 | Opsiyonel |
| İnşaat süresi | 3 yıl | Opsiyonel |
| İnşaat ödeme % | %40 | Opsiyonel (peşinat hariç) |
| Başlangıç yılı | 2025 | Opsiyonel |
| Mortgage faizi | %4.5 | Opsiyonel |
| Mortgage vadesi | 20 yıl | Opsiyonel |

**Sabit metrikler (değiştirilemez):**
- Değer artışı: İlk 3 yıl %8, sonrası %7
- ROI: %7

### 3. Hesaplamayı çalıştır
// turbo
```bash
cd "/Users/dolunayozeren/Desktop/Antigravity/Dubai Emlak İçerik Yazarı"
python3 tools/calculator.py <daire_fiyatı> <peşinat_%> <inşaat_yılı> <başlangıç_yılı>
```

Veya Python'da doğrudan:
```python
from tools.calculator import investment_scenario, format_payment_table, format_summary
scenario = investment_scenario(property_price=540000, downpayment_pct=0.20, ...)
print(format_payment_table(scenario))
```

### 4. Sonuçları doğrula
Hesaplama çıktısını kontrol et:
- Mortgage taksidi mantıklı mı?
- Kira geliri piyasa ile uyumlu mu?
- Değer artışı tutarlı mı?

### 5. Scripti oluştur
Referans formata sadık kalarak scripti yaz:
- **Hook:** Hedef kitleye doğrudan hitap eden soru (ör: "Ayda X dolar pasif gelir istiyorum")
- **Script:** Adım adım hesaplama anlatımı
- **Tablo:** `calculator.py` çıktısını doğrudan kullan
- **TL karşılığı:** Güncel kur ile TL'ye çevir

### 6. Script formatında çıktı ver
Çıktı formatı:
```markdown
### Script #XXX
#### Hook
(...)

#### Script
# Başlık
(Hesaplama adımları ve anlatım)

| Yıl | Ödeme Tipi | Tutar (USD) | ... |
| --- | --- | --- | ... |

#### Script ve Notlar
*Yıllık değer artışı %8/%7, ROI %7 olarak hesaplanmıştır*
```
