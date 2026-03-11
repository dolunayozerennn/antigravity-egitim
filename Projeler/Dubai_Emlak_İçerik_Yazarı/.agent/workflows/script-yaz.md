---
description: Video scripti üret — bölge analizi, gayrimenkul yatırımı veya hesaplama konseptlerinde
---

# /script-yaz Workflow

Çağrı Bozay için sosyal medya video scripti üretmek için bu workflow'u kullan.

## Adımlar

### 1. Skill dosyasını oku
// turbo
`view_file` ile `skills/icerik-yazari/SKILL.md` dosyasını oku. Üslup, format ve ton kurallarını yükle.

### 2. Konsepti belirle
Kullanıcıdan şu bilgiyi al:
- **Konsept:** Bölge analizi / Gayrimenkul yatırımı / Yatırım hesaplama
- **Konu:** Hangi bölge, hangi konu, hangi senaryo?
- **Ek bilgi:** Varsa spesifik veri veya rakamlar

### 3. Referans scriptleri oku
Konsepte göre ilgili referans dosyayı oku:
// turbo
- Bölge → `reference-scripts/bölgeler_scriptleri.md`
// turbo
- Gayrimenkul → `reference-scripts/gayrimenkul_yatirimi_scriptleri.md`
// turbo
- Hesaplama → `reference-scripts/yatirim_hesaplama_scriptleri.md`

En az 3 benzer scripti referans al.

### 4. Araştırma (gerekiyorsa)
Eğer güncel veri gerekiyorsa (fiyat, istatistik, bölge bilgisi):
- `search_web` ile **İngilizce** arama yap (ör: "Dubai JVC property prices 2025")
- `read_url_content` ile kaynağı oku
- Bilgiyi Türkçe scripte entegre et

### 5. Scripti yaz
Referans formata **sadık kalarak** scripti yaz. Kontrol listesi:
- [ ] Format doğru (Hook → Script → Tablo)
- [ ] Üslup tutarlı (samimi, profesyonel, abartısız)
- [ ] Hikaye payoff'u var
- [ ] CTA var (soru veya takip çağrısı)
- [ ] Kısa cümleler (video nefes hızında)

### 6. Çıktıyı ver
Scripti aynı referans dosyadaki format ile ver. Script numarasını bir sonraki olarak ata.
