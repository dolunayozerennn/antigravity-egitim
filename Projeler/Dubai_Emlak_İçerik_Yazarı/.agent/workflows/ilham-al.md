---
description: Rakip emlakçıların videolarından ilham alarak Çağrı Bozay tarzında script üret
---

# /ilham-al Workflow

Rakip emlakçıların Instagram/TikTok videolarından ilham alarak, Çağrı Bozay'ın tarzına uygun video scripti üretmek için bu workflow'u kullan.

## Adımlar

### 1. Skill ve rakip listesini oku
// turbo
`skills/icerik-yazari/SKILL.md` ve `rakipler.md` dosyalarını oku.

### 2. Rakibi seç
Kullanıcıya rakip listesini göster ve hangi rakipten ilham almak istediğini sor.

### 3. Rakibin profilini incele
Browser subagent ile rakibin Instagram veya TikTok profilini ziyaret et:
- Son videoların başlıklarını/açıklamalarını oku
- Etkileşim oranlarına bak (beğeni, yorum sayısı)
- En popüler/ilginç videoları listele
- Kullanıcıya hangi videodan ilham almak istediğini sor

### 4. Transkript al
// turbo
Video URL'ine sahip olduğunda, Supadata API ile transkripti çıkar:
```bash
cd "/Users/dolunayozeren/Desktop/Antigravity/Dubai Emlak İçerik Yazarı"
python3 tools/transcript.py "<video_url>"
```

Eğer Supadata transkript bulamazsa:
- Browser subagent ile videoyu izle ve açıklamayı/altyazıyı oku
- `search_web` ile video hakkında bilgi ara

### 5. Transkripti analiz et
Transkripti oku ve şunları belirle:
- **Konu:** Ne anlatılıyor?
- **Hook:** Nasıl dikkat çekiyor?
- **Yapı:** Nasıl bir akış var?
- **Payoff:** İzleyici ne öğreniyor?
- **Rakamlar:** Hangi veriler kullanılmış?

### 6. İlham alarak script yaz
KRİTİK KURALLAR:
- ❌ Birebir kopyalama/çeviri YASAKTIR
- ✅ Sadece fikir ve yapıdan ilham al
- ✅ Çağrı Bozay'ın üslubunu koru (SKILL.md'deki kurallar)
- ✅ Verileri doğrula — rakibin rakamlarını körüce alma
- ✅ Türk yatırımcı perspektifinden yaz
- ✅ TL karşılıkları ekle (hesaplama scriptlerinde)

İlgili konsepte göre referans scripti oku ve formata sadık kal:
// turbo
- Bölge → `reference-scripts/bölgeler_scriptleri.md`
// turbo
- Gayrimenkul → `reference-scripts/gayrimenkul_yatirimi_scriptleri.md`
// turbo
- Hesaplama → `reference-scripts/yatirim_hesaplama_scriptleri.md`

### 7. Çıktıyı ver
Scripti referans formatında sun. Sonuna ilham kaynağını not olarak ekle:
```
> İlham kaynağı: @rakip_handle — [video konu özeti]
```
