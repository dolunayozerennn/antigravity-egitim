---
description: Bot Test — Tüm Telegram botlarını otomatik test et, sağlık durumunu raporla (quick/full modlu)
---

# /bot-test — Telegram Bot Otomatik Test Workflow'u

> Tüm Telegram botlarını (YouTube, eCom, Shorts, Supplement) otomatik test et, sonuçları raporla.
> **Quick mod:** Health Check + Import + Railway (~15s)
> **Full mod:** Quick + Conversation + Stres Test + Derin Test (~3dk)

---

## Ön Koşullar

- `_skills/bot-test/SKILL.md` dosyasını oku (test protokolü)
- `_knowledge/credentials/master.env` env variable'ları yüklenmiş olmalı

---

## Adım 0: Env Yükle + SKILL.md Oku

```
view_file → _skills/bot-test/SKILL.md
```

**Env yükleme:** Persistent terminal aç ve master.env'den tüm token'ları yükle:

// turbo
```bash
cd ~/Desktop/Antigravity && python3 -c "
from pathlib import Path; import os
p = Path('_knowledge/credentials/master.env')
if p.exists():
    loaded = 0
    for line in p.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, _, v = line.partition('=')
            k, v = k.strip(), v.strip()
            if k:
                os.environ[k] = v
                loaded += 1
    print(f'✅ {loaded} env değişkeni yüklendi')
else:
    print('❌ master.env bulunamadı!')
"
```

> **NOT:** Bu terminal persistent olarak kullanılacak. Sonraki tüm komutlar aynı terminal'de çalışmalı.

---

## Adım 1: Health Check (Katman 1) — ~10 saniye

Tüm botların (YouTube, eCom, Shorts, Supplement) canlılığını kontrol et.

// turbo
```bash
cd ~/Desktop/Antigravity && python3 _skills/bot-test/health_check.py
```

**Beklenen:** 4 bot ✅ (Telegram + Railway)
**Hata varsa:** Railway loglarını incele, kullanıcıya bildir. Hata → Düzeltme Haritası'nı kullan.

> **Quick mod burada bitiyor.** Kullanıcı sadece "bot test" veya "hızlı kontrol" dediyse → Adım 6'ya atla.
> "Full test", "derin test", "kapsamlı test" dediyse → devam et.

---

## Adım 2: YouTube Conversation Test (Katman 2A) — ~15 saniye

// turbo
```bash
cd ~/Desktop/Antigravity/Projeler/YouTube_Otomasyonu && python3 test_conversation.py
```

**Beklenen:** 5/5 senaryo ✅
**Hata varsa:** İlgili dosyayı aç, hatayı analiz et, düzeltme öner.

---

## Adım 3: eCom Import + Conversation Test (Katman 2B) — ~30 saniye

// turbo
```bash
cd ~/Desktop/Antigravity/Projeler/eCom_Reklam_Otomasyonu && python3 test_bot.py --test imports
```

**Beklenen:** 12/12 modül import ✅
**Hata varsa:** Eksik modül veya config hatası — `requirements.txt` veya `config.py` kontrol et.

// turbo
```bash
cd ~/Desktop/Antigravity/Projeler/eCom_Reklam_Otomasyonu && python3 test_bot.py --test conversation
```

**Beklenen:** State geçişleri ve LLM bilgi çıkarma ✅
**Hata varsa:** `conversation_manager.py` veya OpenAI API kontrolü.

---

## Adım 4: YouTube Stres Test (Katman 2.5 — Opsiyonel)

> **Sadece** kullanıcı "derin test", "stres test" veya "full test" dediğinde çalıştır.
> ~60 saniye sürer, API kredi harcar (~$0.10).

// turbo
```bash
cd ~/Desktop/Antigravity/Projeler/YouTube_Otomasyonu && python3 test_stress.py
```

**Beklenen:** 10 kategoride 60+ test, %90+ başarı oranı
**Kontrol edilenler:**
- Saçma girişler (emoji, keyboard smash)
- Prompt injection / jailbreak denemeleri
- Kararsız kullanıcı senaryoları
- Rapid fire (eşzamanlı mesajlar)
- Tehlikeli içerik talepleri
- Farklı diller
- State tutarlılığı
- Gerçekçi kullanıcı yolculukları

---

## Adım 5: Derin Test — Servis + Pipeline (Katman 3 — Opsiyonel)

> Sadece kullanıcı "derin test" veya deploy sonrası istediğinde çalıştır.
> API kredi harcar!

```bash
cd ~/Desktop/Antigravity/Projeler/eCom_Reklam_Otomasyonu && python3 test_bot.py --test services
cd ~/Desktop/Antigravity/Projeler/eCom_Reklam_Otomasyonu && python3 test_bot.py --test pipeline
```

**Kontrol edilenler:** OpenAI, Perplexity, Kie AI bakiye, ElevenLabs ses listesi, Pipeline DRY-RUN

---

## Adım 6: Sonuç Raporu

Tüm test sonuçlarını aşağıdaki formatta kullanıcıya sun. Çalıştırılmayan katmanları "⏭️ Atlandı" ile işaretle:

```
🧪 BOT TEST RAPORU — [tarih saat]
⏱️  Toplam süre: X saniye
🔧 Mod: Quick / Full / Derin

📺 YouTube Otomasyonu (V2.5 — Deploy: [tarih])
  [✅/❌] Health Check: Bot aktif (@username) / Bot yanıt vermiyor
  [✅/❌/⏭️] Conversation: X/Y senaryo geçti / Atlandı (quick mod)
  [✅/❌/⏭️] Stres Test: X/Y geçti (%Z başarı) / Atlandı
  [✅/❌] Railway: Deploy SUCCESS — Fatal hata YOK / CRASHED

🛒 eCom Reklam Otomasyonu (V2.4 — Deploy: [tarih])
  [✅/❌] Health Check: Bot aktif / Bot yanıt vermiyor
  [✅/❌/⏭️] Import: X/Y modül import edildi / Atlandı
  [✅/❌/⏭️] Conversation: X/Y test geçti / Atlandı
  [✅/❌/⏭️] Derin Test: X/Y servis + pipeline / Atlandı
  [✅/❌] Railway: Deploy SUCCESS / CRASHED

🎬 Shorts Demo Botu (Deploy: [tarih])
  [✅/❌] Health Check: Bot aktif / Bot yanıt vermiyor
  [✅/❌] Railway: Deploy SUCCESS / CRASHED

💊 Supplement Analyzer (Deploy: [tarih])
  [✅/❌] Health Check: Bot aktif / Bot yanıt vermiyor
  [✅/❌] Railway: Deploy SUCCESS / CRASHED

📊 Genel Durum: ✅ SAĞLIKLI / ⚠️ DİKKAT / ❌ KRİTİK
   Kontrol: X/Y geçti
```

---

## Ne Zaman Hangi Mod?

| Tetikleyici | Mod | Katmanlar |
|-------------|-----|-----------|
| `/bot-test` komutu (varsayılan) | Quick | Katman 1 (Health + Railway) |
| "Full test" veya "kapsamlı test" | Full | Katman 1 + 2A + 2B |
| "Derin test" veya "stres test" | Derin | Katman 1 + 2A + 2B + 2.5 + 3 |
| Deploy sonrası (`/canli-yayina-al` tamamlandığında) | Full | Katman 1 + 2A + 2B |
| 48-saat izleme kontrolü | Quick | Katman 1 (Sadece Health Check) |

---

## Hata → Düzeltme Haritası

| Hata Paterni | İlgili Dosya | İlk Aksiyon |
|---|---|---|
| `ImportError: No module named 'X'` | `requirements.txt` | Eksik paketi bul → `pip install X==version` → requirements güncelle |
| OpenAI API error / boş yanıt | `services/openai_service.py` + `config.py` | Model adını kontrol et (gpt-4.1-mini) |
| `AttributeError` ConversationManager | `core/conversation_manager.py` | Session/state yapısı değişmiş mi kontrol et |
| `TimeoutError` Kie AI / Replicate | `core/production_pipeline.py` | Timeout süresini artır, retry mekanizmasını kontrol et |
| Railway `CRASHED` status | Railway logları | `deploymentLogs` çek → kök neden analizi → `/hata-duzeltme` |
| Telegram `401 Unauthorized` | `master.env` → token | Token geçersiz → yeni token oluştur |
| Telegram `409 Conflict` | Birden fazla polling instance | Railway'de eski deploy'lar hâlâ polling yapıyor olabilir |
| `SyntaxError` | İlgili .py dosyası | `python3 -m py_compile <dosya>` ile bul |
| `NameError` / `UnboundLocalError` | İlgili .py dosyası | Değişken tanımsız — son commit'i kontrol et |
| Stres test %90 altı | Robustness sorunu | test_stress.py çıktısını oku, categories of fail analiz et |

---

## Hata Durumunda Yönlendirme

1. **Health Check FAIL:** Railway loglarını incele → kök neden analizi → `/hata-duzeltme` workflow'una yönlendir
2. **Conversation Test FAIL:** İlgili modülü aç → hatayı analiz et → düzeltme öner → kullanıcı onayı al
3. **Stres Test FAIL (<%90):** Başarısız test kategori(ler)ini raporla → edge case fix öner
4. **Railway CRASHED:** `deploy-registry.md`'den proje bilgilerini al → son deploy'u kontrol et → gerekirse `/canli-yayina-al`
5. **Import FAIL:** `requirements.txt` vs lokal `pip list` farkını bul → eksik paket ekle → push

---

## 48-Saat İzleme Entegrasyonu

Test sonuçlarını `_knowledge/bekleyen-gorevler.md`'deki aktif izleme kayıtlarıyla eşleştir:
- İzleme altındaki bir bot'un testi geçtiyse → ilgili kontrol satırını ✅ olarak güncelle
- Test başarısız olduysa → izleme kaydına ❌ ve hata detayı ekle
- 2 temiz kontrol geçen izlemeler → "arşive taşı" öner
