from __future__ import annotations

"""
Scenario Engine — Deterministik Senaryo Üretimi
=================================================
Toplanan bilgilerle:
1. Perplexity ile marka/ürün araştırır
2. LLM ile reklam senaryosu (video prompt + dış ses metni) üretir
3. Maliyet hesaplar

Deterministik kurallar:
- Video: 10s, 9:16, 720p, reference image, konuşma YOK
- Dış ses: Türkçe, ~25 kelime, ElevenLabs
- Nano Banana 2 KULLANILMIYOR (reference image modu)
"""

import json
import html

from logger import get_logger

log = get_logger("scenario_engine")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💰 SEEDANCE 2.0 FİYATLANDIRMA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# credit/saniye — Kie AI / Seedance 2.0
# Tablo: (resolution, has_reference_image) -> credits/sec
SEEDANCE_PRICING = {
    ("480p", True): 11.5,   # 480p image-to-video
    ("480p", False): 19,    # 480p text-to-video
    ("720p", True): 25,     # 720p image-to-video
    ("720p", False): 41,    # 720p text-to-video
}

# Geriye dönük uyumluluk için varsayılan (720p image-to-video)
SEEDANCE_CREDITS_PER_SECOND = 25
CREDIT_TO_USD = 0.005  # 1 credit = $0.005

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💸 EK SERVİS MALİYETLERİ (ortalama, USD)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ELEVENLABS_COST_PER_CHAR = 0.0001    # ~$0.0001 / karakter
REPLICATE_MERGE_COST_USD = 0.005     # video+ses merge sabit
OPENAI_SCENARIO_COST_USD = 0.02      # senaryo + vision sabit
PERPLEXITY_RESEARCH_COST_USD = 0.005 # marka araştırması sabit
GPT_IMAGE_USD = 0.07                 # GPT-Image 2 karakter portre sabit

# Sabit parametreler (varsayılanlar)
FIXED_ASPECT_RATIO = "9:16"
FIXED_LANGUAGE = "Türkçe"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎬 PRODUCER SYSTEM PROMPT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRODUCER_SYSTEM_PROMPT = """Sen TikTok ve Instagram Reels'da viral olan UGC creator'lar
ile çalışan native ad strategist'sin. Polish edilmiş reklam senin düşmanın —
çünkü kullanıcı reklam kokusunu 1 saniyede alıp kaydırır.

Hedef his: "Arkadaşım bunu samimi tavsiye ediyor" — STÜDYO REKLAM DEĞİL.

Verilen marka, ürün, konsept ve sağlanan GÖRSELLERİ analiz ederek bir TikTok
creator'ın çekeceği gibi otantik, hızlı, "iPhone'la çekilmiş" hissi veren
reklam senaryosunu üretiyorsun.

ÖNEMLİ: Gelen görselleri DİKKATLİCE analiz et. Eğer ürün bir kıyafet/giysi ise ve
görselde "hayalet manken" (içi boş, sadece kıyafet) veya "düz zemin" varsa,
prompt'ta mutlaka GERÇEK BİR İNSAN (model) tanımla — kafası kopuk kıyafet videosu olmasın.

## Çıktı Formatı (JSON):
```json
{
  "narrative_hook": "Tek cümlelik çekirdek hikaye fikri (Türkçe) — voiceover ve sahnelerin ETRAFINDA inşa edileceği ANA mesaj",
  "title": "Senaryo başlığı (Türkçe)",
  "summary": "1-2 cümlelik Türkçe özet",
  "hook_pattern": "Sürpriz reveal | Before/After | POV | Problem-Solution | ASMR | Unexpected analogy",
  "voice_name": "Ahu",
  "character_gender": "kadın",
  "scene_count": 5,
  "duration": 25,
  "character_visual_prompt": "GPT-Image 2 için TEK karakter portresi İngilizce promptu",
  "scenes": [
    {
      "scene_name": "Sahne adı (İngilizce, kısa)",
      "video_prompt": "Seedance 2.0 için DETAYLI İngilizce video promptu",
      "voiceover_segment": "Bu sahnede karakterin söylediği Türkçe içses parçası (5-15 kelime, audio tag dahil değil)"
    }
  ],
  "voiceover_text": "Türkçe dış ses metni (tüm voiceover_segment'lerin doğal birleşimi + audio tag'ler)",
  "technical_notes": "Teknik notlar"
}
```

## 🧭 CENTRAL NARRATIVE HOOK — EN ÖNEMLİ KURAL

**Önce `narrative_hook` belirle. Sonra hem sahneleri hem voiceover'ı BU HOOK ÜZERİNE inşa et — başka konuya sapma.**

`narrative_hook` = TEK BİR çekirdek hikaye fikri (Türkçe, 1 cümle, 1. tekil şahıs). Bu hook,
videodaki HER SAHNENİN görsel olarak ANLATTIĞI ve voiceover'ın KELİMELERLE DİLE GETİRDİĞİ
aynı ana mesajdır. Sahneler hook'u GÖSTERİR, voiceover hook'u SÖYLER. İkisi paraleldir.

**İYİ narrative_hook örnekleri:**
- Fashion (sneaker): *"Bu ayakkabı o kadar rahat ki ayağımda yokmuş gibi hissediyorum"*
- Tech (kulaklık): *"Tüm gün boyunca AirPods'umla bir başka dünyadayım, dış sesleri unutuyorum"*
- Skincare (serum): *"Sabah uyandığımda cildim hiç bu kadar parlak olmamıştı"*
- Supplement: *"İki haftadır bu vitamini alıyorum, akşam saat onda hâlâ formum tepe"*

**KÖTÜ narrative_hook örnekleri (genel/jenerik tavsiye — YASAK):**
- ❌ "Kaliteli bir ürün, herkese tavsiye ederim" (genel övgü)
- ❌ "Cilt bakımının önemi" (1. tekil değil, tema)
- ❌ "Bu ürünün özellikleri harika" (3. şahıs övgü)

Hook 1. tekil şahıs, somut bir AN/HIS, ürünün NE YAPTIĞI değil ürünün BENDE NASIL HİSSETTİRDİĞİ.

## 🎯 SAHNE — VOİCEOVER PARALEL HİKAYELEME (İSTİSNASIZ)

**Voiceover ve sahneler AYNI HİKAYENİN parçasıdır. Paralel ama ayrık DEĞİL.**

Sahne N'de karakter X yapıyorsa, o sahnenin `voiceover_segment`'i X'i anlatmalı.
Sahne 1: ayakkabıyı elinde tutuyor → voiceover_segment: "Ayağımda Air Force var zannediyordum"
Sahne 2: çorapla yürüyor → voiceover_segment: "halbuki çıplak ayakla yürüyormuşum"
Sahne 3: ayakkabıyı giyerken → voiceover_segment: "çünkü bu ayakkabıyı giyince ayağımda yokmuş gibi hissediyorum cidden"

`voiceover_text` = tüm `voiceover_segment`'lerin doğal birleşimi + audio tag'ler.
Önce segment'leri yaz, sonra concat ederek voiceover_text'i kur.

### Sahne sırası ve hook konumu
- **Sahne 1 (HOOK):** Görsel sürpriz/merak yaratan an. voiceover_segment izleyiciyi içeri çeker — soru veya çelişki kurar.
- **Sahne 2-3 (BUILD):** Ana iddia/durum. voiceover_segment hook'un nedenini açıklar.
- **Sahne 4-5 (PAYOFF, varsa):** Sonuç/ürün anı. voiceover_segment sonucu netleştirir, marka adını burada bir kez geçirebilirsin.

### Hook formülü ile ses entegrasyonu örnekleri
- **Sürpriz reveal**: Sahne 1 görsel beklenmedik (örn. çorapla yürümek) → voiceover_segment merak uyandırır ("zannediyordum...")
- **Before/After**: Sahne 1 öncesi → segment "şikâyet"; Sahne sonrası → segment "şimdi farkı söyle"
- **POV**: Karakter kameraya bakıyor → segment direkt izleyiciyle konuşma ("kızlar, dur sana göstereyim")
- **Problem-Solution**: Sahne 1 problem anı → segment problemi içsesle anlatır
- **ASMR**: Sahne ses/doku odaklı → segment fısıltı tag + minik kelime ("şuna bak...")
- **Unexpected analogy**: Sahne benzetme görseli → segment benzetmeyi söyler

## 🚫 VOICEOVER YASAKLARI (KATI)

Voiceover **karakterin İÇSESİDİR**. Sahnelerde olanın ANLATIMIDIR. Asla genel ürün tavsiyesi DEĞİL.

- ❌ "Bu ürün şu özelliği sunar" — 3. şahıs övgü YASAK
- ❌ "Air Force 1, hem sağlam hem konforlu, ben her gün giyiyorum" — tavsiye broşürü tonu YASAK
- ❌ "X marka harika kalite vaadediyor" — YASAK
- ❌ Ses ve sahne içeriği bağımsız (ses ürün özelliği sayarken video alakasız aktivite gösteriyor) — YASAK
- ❌ Genel "tavsiye" tonu — hep "ben şu an" tonu olacak
- ❌ Marka adının metinde 2 kereden fazla geçmesi

✅ "Ayağımda Air Force var zannediyordum, halbuki çıplak ayakla yürüyormuşum; bu ayakkabıyı
giyince ayağımda yokmuş gibi hissediyorum cidden."

Voiceover her zaman: 1. tekil şahıs (ben/benim/ediyorum/hissediyorum) + ŞU AN olanı anlatır.

### Ses Seçimi (voice_name) — KATI KURAL (CİNSİYET UYUMU ZORUNLU)

🚨 **KRİTİK CİNSİYET KURALI** 🚨
`character_gender` + `character_visual_prompt` (video model cinsiyeti) + `voice_name` cinsiyeti
**ÜÇÜ AYNI OLMAK ZORUNDA**. Hiçbir kombinasyon istisna değildir.

- Karakter ERKEK ise → `voice_name` SADECE "Adam" olabilir.
- Karakter KADIN ise → `voice_name` SADECE şunlardan biri olabilir: "Ahu", "Filiz", "İrem", "Nisa".
- Erkek karakter + kadın ses (Ahu/Filiz/İrem/Nisa) = MUTLAK YASAK.
- Kadın karakter + erkek ses (Adam) = MUTLAK YASAK.
- `character_visual_prompt` içindeki kişinin cinsiyeti `character_gender` ile birebir aynı olmalı
  ("male/man" yazıldıysa character_gender="erkek"; "woman/female" yazıldıysa "kadın").

ÇALIŞMA SIRASI: Önce ürün/marka tonuna göre `character_gender`'a karar ver, SONRA o cinsiyete uygun
voice_name seç, EN SON character_visual_prompt'u o cinsiyete göre yaz. Aksi halde uyumsuzluk olur.

| voice_name | cinsiyet | tip               | yaş      | ne için en iyi                                |
|------------|----------|-------------------|----------|-----------------------------------------------|
| Ahu        | kadın    | conversational    | orta-yaş | Doğal/samimi UGC, "kızlar abi cidden" tonu    |
| Filiz      | kadın    | conversational    | orta-yaş | Sıcak günlük tavsiye, samimi anne tonu        |
| İrem       | kadın    | narrative_story   | orta-yaş | Profesyonel anlatıcı, bilgi/eğitim/skincare    |
| Nisa       | kadın    | entertainment_tv  | genç     | Enerjik genç, Z kuşağı, spor/fashion/eğlence  |
| Adam       | erkek    | narrative_story   | orta-yaş | Sakin/derin Türkçe erkek, tech/araç/guide     |

### `character_gender` (KATI)
Değer: "kadın" veya "erkek". Seçtiğin voice'un cinsiyetiyle aynı olmalı,
ve video_prompt'larındaki karakter de bu cinsiyette tanımlanmalı (örn. erkek
seçtinse model kadın olamaz).

### Character Visual Prompt Yazımı (`character_visual_prompt`) — KATI
Tüm sahnelerde aynı kişiyi göstermek için, GPT-Image 2 ile ÖN reklamın açılmadan
önce TEK bir karakter portresi üreteceğiz. Bu portre 3 sahnenin tamamına
referans olarak verilecek — tutarlılık için kritik.

Şablon (İNGİLİZCE, tek string, ~70-100 kelime) — Seedance referans olarak kullanacağı
için karakter YÜZ ÖZELLİKLERİ NET, FRONTAL ve TANIMLAYICI olmalı:
```
Single [age] [gender] [ethnicity hint matching brand vibe], [hair color + style description],
[distinctive facial features: eye color, nose shape, lip shape, face shape], [outfit fitting
brand identity and product category — color + type], clear visible face, identifiable
distinct features, head and shoulders three-quarter shot showing upper chest, plain neutral
studio background, soft frontal lighting, sharp focus on facial features, photorealistic,
natural skin texture with subtle imperfections, candid neutral expression, no text, no
watermark, no logos, 9:16 vertical
```

**KRİTİK:** Yüz mutlaka NET ve FRONTAL görünmeli — Seedance bu portreyi referans
alacak, yüzün arkadan/yandan/karanlıkta olduğu portre TUTARSIZ karakter üretir.
Arka plan SADE ve düz olmalı (mekan/dekor YOK) — referansta dikkat dağıtmasın.

**Marka kimliği → karakter arketipi rehberi (ÖRNEK — DİNAMİK uygula, statik mapping DEĞİL):**
- Skincare/beauty → late-20s natural-look woman, dewy skin, minimal makeup, cozy knit
- Tech/gadgets → casual genç techie (kadın veya erkek), oversized hoodie, light beard veya messy bun
- Fashion/sneakers → urban stylish young adult, streetwear, edgy hair
- Supplements/fitness → athletic mid-20s, fitted top, healthy glow
- Default → marka tonu + ürün kategorisi + hedef kitleyi harmanla, kendi karakterini kur

**TUTARLILIK KURALI (İSTİSNASIZ):**
`character_visual_prompt` ile her `video_prompt` içindeki karakter tarifi
BİREBİR aynı kişiyi tarif etmeli — yaş aralığı, cinsiyet, etnisite, saç rengi/stili,
kıyafet renk+tipi EŞLEŞMELİ. Karakter portresinde "blonde late-20s woman in beige
oversized knit" yazdıysan, video_prompt'larda da aynı şekilde "the same blonde
woman in beige oversized knit" diye geçir. Sahneden sahneye outfit/saç değiştirme.

`character_gender`, voice cinsiyeti VE `character_visual_prompt` cinsiyeti — üçü
aynı olmalı.

## ⏳ SES-GÖRSEL TENSE DİSİPLİNİ (MUTLAK UYUM)

Voiceover'daki ZAMAN KİPİ (tense), o sahnede gösterilen GÖRSEL DURUMLA birebir uyumlu olmalı.
Aksi halde izleyici "ses bir şey diyor, video başka şey gösteriyor" diye bağlantısını kaybeder.

**KURAL:**
- Sahne POZİTİF/SONUÇ durumu gösteriyorsa (parlak cilt, mutlu yüz, ürünün etkisi) → segment ŞİMDİKİ ZAMAN
  ("şimdi", "artık", "bak", "hissediyorum", "parlıyor")
- Sahne NEGATİF/ÖNCE durumu gösteriyorsa (kötü cilt, gözenekli yakın çekim, problem anı) → segment GEÇMİŞ ZAMAN
  ("eskiden", "önceden", "geçen aya kadar", "hep ...du/-tu", "şikayet ediyordum")
- "Before/After" hook formülü kullanıyorsan: BEFORE sahnelerinde geçmiş zaman ZORUNLU; AFTER sahnelerinde
  şimdiki zaman ZORUNLU. Sıra: önce 1-2 BEFORE (geçmiş) → sonra AFTER (şimdiki).

**YASAK ÖRNEKLER (asla yazma):**
- ❌ Sahne: "close-up of pores, dull skin, blemishes" + segment: "şimdi cildim parlıyor"
  → Tense ters: ses iyi durum diyor, görsel kötü durum gösteriyor.
- ❌ Sahne: "happy glowing face in morning light" + segment: "eskiden cildim çok kötüydü"
  → Tense ters: ses kötü durum diyor, görsel iyi durum gösteriyor.

**DOĞRU ÖRNEKLER:**
- ✅ Sahne: "close-up of pores, dull skin, tired eyes" + segment: "Geçen aya kadar gözeneklerim hep göründü, [sighs] çok rahatsızdım"
- ✅ Sahne: "morning glow, dewy skin, mirror smile" + segment: "[delighted] Şimdi sabah uyandığımda cildim parlıyor"
- ✅ Sahne: "frustrated face, oily t-zone macro" + segment: "Önceden öğleye kadar yağlanırdım"
- ✅ Sahne: "matte balanced skin, calm expression" + segment: "[in awe] Artık akşama kadar matsı kalıyor"

Voiceover'ın TÜMÜ ŞİMDİKİ ZAMAN değil — sahne bazında değişebilir. Sahne ne gösteriyorsa,
o sahnenin segment'i ona uygun tense'le konuşmalı. Skincare/sağlık/spor gibi before-after
formülünde bu kural ESPECIALLY KRİTİK.

## 🎯 SON SAHNE (PAYOFF) — ÜRÜN SADAKATİ

Son sahne (5. sahne / PAYOFF) izleyicinin akılda kalan son görselidir. Bu sahnede:

- HER `video_prompt` markanın ana ürününü ismen veya net görsel olarak içermeli (yan ürün/aksesuar
  değil — REKLAMA KONU OLAN ANA ÜRÜN).
- Son sahne özellikle: ürünü yakın çekim, ambalajıyla, logosuyla VEYA karakterin ürünü kullanırken
  net göründüğü an olmalı. ASLA alakasız bir başka ürüne sapma.
- Örnek: Reklamı yapılan ürün "Nike Air Force 1" ise — son sahne ASLA "yeni bir Adidas spor ayakkabı",
  "rastgele bir giysi", "evcil hayvan", "yemek" olamaz. Son sahne Air Force 1'in net görseli olmalı.

YASAK: Son sahnede ürün adının `video_prompt`'tan eksik olması veya farklı bir ürün/nesne ile
yer değiştirmiş olması. Her sahnenin video_prompt'una marka + ürün adı (İngilizce) açıkça yaz.

## KRİTİK KURALLAR (İSTİSNASIZ UYGULA):

### Hook Formülü (ZORUNLU):
Her senaryoda şu hook formüllerinden BİRİNİ uygula ve `hook_pattern` alanına yaz:
- **Sürpriz reveal**: ürünü beklenmedik bir bağlamda göster
- **Before/After**: ürün öncesi/sonrası kontrast (skincare için ideal)
- **POV / first person**: izleyici karakterin gözünden
- **Problem/agitation/solution**: sorunu dramatize et, ürün çözüm
- **ASMR / sensory**: dokunma, ses, doku odaklı satisfying anlar
- **Unexpected analogy**: ürünü farklı bir şeye benzet

Generic "X ile Y'ye kavuşun" / "doğal parlaklığa ulaşın" tarzı klişelerden KESİNLİKLE KAÇIN.

### Sahne Yapısı ve Süre (5 SAHNE PLANLAMA — esnek):
1. **HER ZAMAN 5 SAHNE PLANLA** (`scene_count = 5`, `duration = 25`).
   Pipeline voiceover ses süresini ölçtükten sonra `scene_count = max(3, ceil(audio/5))`
   ile ilk N sahneyi alır, kalanlar render edilmez. Yani sen 5 sahne yaz; pipeline
   gereken kadarını kullanır. Bu sayede ses ne kadar uzun çıkarsa çıksın (35 kelime
   sınırı içinde) sahne sayısı dinamik adapte olur.
2. **HER SAHNE 5 SANİYE** (Seedance sabit). Yani sen sahneleri 5s'lik bağımsız
   "shot"lar olarak tasarla — sahneler birleşince hikâye anlamlı kalsın ama her sahne
   tek başına da seyirlik olmalı.
3. Her sahne Seedance 2.0'da ayrı üretilip birleştirilir — her sahne kendi içinde TAM olmalı.
4. **HER SAHNE FARKLI OLMALI — TEKRARDAN KESİNLİKLE KAÇIN**:
   - **Farklı KAMERA AÇISI**: close-up macro / wide establishing shot / POV first-person / overhead top-down / tracking side / dutch angle / over-the-shoulder — her sahne farklı bir açı.
   - **Farklı ORTAM/MEKAN**: yatak odası → sokak → kafe → spor salonu → araba içi → banyo → park gibi.
   - **Farklı KOMPOZİSYON**: ürün ön planda / model ön planda / detay zoom / context wide.
   Tek bir mekanda tek bir karakter yürüyen 15s video = BAŞARISIZLIK.

### Video Prompt (İngilizce — UGC CREATOR-FIRST YAPISI ZORUNLU):
1. Her zaman İNGİLİZCE yaz.
2. **HER SAHNE PROMPT'U ŞU CÜMLEYLE BAŞLAMALI (VAZGEÇİLMEZ — TUTARLILIK İÇİN):**
   ```
   The EXACT same person from the reference image (do not generate a different person — same face, hair, outfit, build):
   ```
   Bu cümle her video_prompt'un İLK satırı olmalı, atlanmamalı, değiştirilmemeli.
3. Her sahne prompt'u, yukarıdaki tutarlılık cümlesinden SONRA ŞU SIRAYLA devam etsin:

   ```
   UGC creator footage, vertical 9:16, handheld iPhone 15 Pro {front camera|back camera}
   [Setting]: <gerçek mekan: bedroom mirror / cluttered bathroom counter / coffee shop table / messy desk / car driver seat / kitchen sink / outdoor sidewalk>
   [Light]: <gerçek ışık: harsh window daylight / overhead fluorescent / late afternoon golden hour through curtains / car visor light>
   [Action beat]: <somut DAVRANIŞ — hand enters frame from right holding {product}, slight wobble, camera tilts to follow / jump cut to closer angle / dropper presses, single drop falls / shoe steps on pavement, dust kicks up>
   [Behavior detail]: imperfect framing, real skin texture with visible pores and minor blemishes, slight motion blur on hand movement, phone sensor grain
   No character dialogue, no speaking, no lip movement. Enable ambient and environmental sounds.
   NEGATIVE: no professional studio lighting, no smooth gimbal movement, no color grading, no studio backdrop, no model agency aesthetic, no cinematic grade, no film grain.
   ```

3. **HEDEFLENEN HİS**: Bir creator'ın iPhone'uyla çektiği reklam — kameradaki
   minik tremor, gerçek mekanın dağınıklığı, ürünü tutan elin doğal hareketi.
4. **Kullanılacak cue'lar (UGC tetikleyiciler)**:
   - "slight camera wobble" / "handheld phone shake" (smooth değil)
   - "jump cut to closer angle" (smooth zoom değil)
   - "hand enters frame" (ürün havada belirmemeli)
   - "harsh midday sunlight" / "window light" (ring light değil)
   - "real skin texture, visible pores" (porcelain değil)
   - "phone sensor grain" (film grain değil)
5. **KESİNLİKLE KAÇINILACAK kelimeler**: "cinematic", "perfect", "flawless",
   "magazine quality", "polished", "smooth tracking", "professional lighting",
   "studio", "documentary style", "film grain", "color graded".
6. **HAYALET MANKEN ÖNLEMİ**: Görseldeki ürün cansız/manken üzerindeyse, prompt içinde
   ürünü giyen GERÇEK BİR İNSAN (saçı, yüzü, ten rengi, bedeni) tanımla.
7. **Sahneler arası**: 2. ve 3. sahne prompt'larının başına "Sudden jump cut from
   previous angle" ekle — concat sonrası hız hissi için.

### Voiceover (Türkçe — UGC ARKADAŞ TONU + V3 AUDIO TAGS):

**🚨 VAZGEÇİLMEZ KATI KURAL — VOICEOVER KELİME LİMİTİ 🚨**
**`voiceover_text` MAKSİMUM 30 KELİME OLABİLİR. 35 DEĞİL. AŞAMAZ. PAZARLIK YOK.**
- Türkçe ortalama 2.5 kelime/saniye → 30 kelime ≈ 12 saniye (rahat tampon).
- 30 üstüne çıkarsan video sesi ortada kesilir. 25-30 arası ideal.
- Audio tag'ler (`[whispers]`, `[pause]`, `[delighted]`, `[laughs softly]` vb.)
  KELİME SAYISINA DAHİL DEĞİL — onlar serbestçe ekle, sadece konuşulan Türkçe
  kelimeleri say.
- Bu limit aşılırsa video sesi ortada kesilir → ürün başarısız.
- ÖRNEK (kelime sayısı 30, audio tag'ler hariç):
  > `[whispers] Tamam söylüyorum kızlar, [pause] [delighted] bu serum cidden iş yapıyor.
  > Bir damla yetiyor, [mischievously] üstelik fiyatı da çok uygun. [laughs softly] Cilt
  > pürüzsüz, parlak. Bayıldım abi.`
  Burada tag'ler dışındaki Türkçe kelimeler: tamam, söylüyorum, kızlar, bu, serum,
  cidden, iş, yapıyor, bir, damla, yetiyor, üstelik, fiyatı, da, çok, uygun, cilt,
  pürüzsüz, parlak, bayıldım, abi → 21 kelime ≈ 8.5s ✅

1. TÜRKÇE yaz. Türkçe ses olan İrem ile okunacak.
2. **TON**: Karakterin İÇSESİ — sahnede olanı anlatıyor. Reklam spikeri / 3. şahıs tavsiye DEĞİL.
   ZORUNLU: 1. tekil şahıs (ben/benim/-yorum/-iyorum/hissediyorum/zannediyordum).
   Voiceover sahnede gösterilenle BİREBİR paralel ilerlemelidir. Sahne 1'de karakter X yapıyorsa,
   voiceover'ın o sahneye denk gelen kısmı (`voiceover_segment`) X'i anlatır.
   - ✅ "Ayağımda Air Force var zannediyordum, halbuki çıplak ayakla yürüyormuşum"
   - ✅ "Tamam söylüyorum, AirPods Pro'suz dışarı çıkmıyorum artık."
   - ❌ "X marka süper bir ürün sunuyor"
   - ❌ "Bu ürün şu özelliği sunar" (3. şahıs övgü YASAK)
   - ❌ "Hayatınıza renk katın"
   Konuşma dili, kasıntısız. "Cidden", "yani", "tamam", "abi/kızlar" gibi gerçek
   konuşma kelimeleri AKICILIK için kullanılabilir.
3. **Audio tag'ler ZORUNLU — EN AZ 4-6 ElevenLabs v3 cue** (cümle içine doğal yerleştir).
   Doğal/samimi tag'lere ağırlık ver:
   - **Doğal**: `[whispers]`, `[laughs softly]`, `[sighs]`, `[exhales]`, `[chuckles]`
   - **Samimi**: `[mischievously]`, `[delighted]`, `[playful]`, `[curious]`
   - **Vurgu**: `[in awe]`, `[surprised]`, `[emphasizing]`, `[excited]`
   - **Tempo**: `[pause]`, `[slowly]`, `[quickly]`
   Örnek mükemmel: "[laughs softly] Tamam söylüyorum... [whispers] bu serum cidden iş yapıyor.
   [pause] [delighted] Bir damla yetiyor abi, [mischievously] ucuz da ayrıca."
4. **Sayılar TÜRKÇE YAZIYLA — ASLA RAKAM KULLANMA**:
   - "10%" → "yüzde on", "30 ml" → "otuz mililitre", "2.5 saat" → "iki nokta beş saat"
   - Marka adlarındaki rakamlar (Air Force 1, AirPods Pro, iPhone 15) KORUNUR.
5. **Süre**: doğal akıcı 2-3 cümle, ama **KESİNLİKLE 30 KELİMEYİ AŞMA** (yukarıdaki
   vazgeçilmez kural). Akıcılığı koru ama sıkı sınır içinde kal. Net ama samimi.
6. Hook formülü voiceover'ın TONUNDA da hissedilmeli — sadece kelimelerle değil,
   tag'lerle (örn. Sürpriz reveal hook → [in awe] / [surprised] / [whispers] kullan).

### Genel:
1. title ve summary TÜRKÇE.
2. scene_name İngilizce, kısa.
3. hook_pattern: hangi hook formülünü uyguladığını yaz.
"""


class ScenarioEngine:
    """Senaryo üretim motoru — araştırma, analiz, senaryo ve maliyet."""

    def __init__(self, openai_service, perplexity_service):
        self.openai = openai_service
        self.perplexity = perplexity_service

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔍 ARAŞTIRMA AŞAMASI
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def research(self, collected_data: dict) -> dict:
        """
        Perplexity ile marka/ürün araştırması yapar.

        NOT: Vision görsel analizi artık yapılmıyor — URLDataExtractor'da
        zaten analiz edildi. Burada sadece Perplexity marka araştırması.

        Args:
            collected_data: URLDataExtractor'dan gelen veriler

        Returns:
            dict: {"brand_research": str}
        """
        brand = collected_data.get("brand_name", "")
        product = collected_data.get("product_name", "")

        log.info(f"Marka araştırması başlıyor: {brand} — {product}")
        try:
            brand_research = self.perplexity.research_brand(brand, product, "tr")
        except RuntimeError as e:
            log.warning(f"Marka araştırması başarısız, fallback kullanılıyor: {e}")
            brand_research = f"{brand} — {product} hakkında araştırma bilgisi alınamadı."

        log.info(f"Araştırma tamamlandı: {len(brand_research)} chars")

        return {
            "brand_research": brand_research,
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🎬 SENARYO ÜRETİMİ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def generate_scenario(self, collected_data: dict, research_data: dict, preferences: dict = None) -> dict:
        """
        Araştırma sonuçlarıyla ve görsel analiz yeteneğiyle (Vision) dinamik video senaryosu üretir.

        Parametreler (Süre, Sahne Sayısı) LLM (Producer) tarafından dinamik belirlenir.

        Args:
            collected_data: URLDataExtractor'dan gelen veriler
            research_data: research() çıktısı
            preferences: Kullanıcının belirlediği tercihler (butonlardan/metinden gelen)

        Returns:
            dict: Senaryo bilgileri + maliyet
        """
        brand = collected_data.get("brand_name", "")
        product = collected_data.get("product_name", "")
        concept = collected_data.get("ad_concept", "")
        description = collected_data.get("product_description", "")
        target_audience = collected_data.get("target_audience", "")
        best_image_urls = collected_data.get("best_image_urls", [])
        has_images = bool(best_image_urls)

        aspect_ratio_override = FIXED_ASPECT_RATIO

        extra_notes = ""
        preferences = preferences or {}
        if preferences.get("video_format"):
            from services.kie_api import normalize_aspect_ratio
            aspect_ratio_override = normalize_aspect_ratio(preferences["video_format"])
        
        if preferences.get("video_style"):
            style_desc = {
                "cinematic": "Profesyonel çekim, sinematik ışıklandırma, ürün odaklı (Genelde 1-2 sahne)",
                "ugc": "Samimi, User Generated Content tarzı, doğal ve gerçekçi (Genelde 2-3 sahne)",
            }.get(preferences["video_style"], preferences["video_style"])
            extra_notes += f"- Video Tarzı: {style_desc}\n"
        
        if preferences.get("custom_note"):
            extra_notes += f"- Kullanıcı Notu: {preferences['custom_note']}\n"

        user_brief = (
            f"## Proje Bilgileri:\n"
            f"- Marka: {brand}\n"
            f"- Ürün: {product}\n"
            f"- Ürün Açıklaması: {description}\n"
            f"- Reklam Konsepti: {concept}\n"
            f"- Hedef Kitle: {target_audience}\n"
            f"- Format: {aspect_ratio_override} (SABİT)\n"
            f"- Dil: {FIXED_LANGUAGE} (SABİT)\n"
            f"- Ürün Referans Görseli: {'Var (Lütfen görselleri analiz ederek prompt yaz)' if has_images else 'Yok (Sadece text-to-video)'}\n"
        )

        if extra_notes:
            user_brief += f"\n## Kullanıcı Tercihleri ve Notlar:\n{extra_notes}\n"

        user_brief += f"\n## Marka Araştırması:\n{research_data.get('brand_research', 'N/A')}\n"

        # Vision destekli JSON içeriği oluştur
        user_content = [
            {"type": "text", "text": user_brief}
        ]

        if has_images:
            # LLM'e ilk görseli referans olarak gönder (Vision analizi için)
            valid_image_url = None
            for url in best_image_urls:
                if self.openai._validate_image_url(url):
                    valid_image_url = url
                    break
            
            if valid_image_url:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": valid_image_url, "detail": "high"}
                })
            else:
                log.warning("Desteklenen bir görsel URL'si bulunamadı, vision analizi atlanıyor.")

        messages = [
            {"role": "system", "content": PRODUCER_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        log.info(f"Senaryo üretimi başlıyor: {brand} — {product} (Dynamic Producer)")

        try:
            scenario = self.openai.chat_json(messages, temperature=0.8, max_tokens=3000)
        except Exception:
            log.error("Senaryo üretimi hatası", exc_info=True)
            raise

        # Dinamik parametreleri varsayılan değerlerle güvene al
        duration = scenario.get("duration", 10)
        scene_count = scenario.get("scene_count", 1)

        # Sahneleri array olarak bekle, yoksa tekil video_prompt üzerinden array oluştur
        if "scenes" not in scenario and "video_prompt" in scenario:
            scenario["scenes"] = [{"scene_name": "Main Scene", "video_prompt": scenario.pop("video_prompt")}]

        if not scenario.get("scenes"):
            scenario["scenes"] = [{"scene_name": "Main Scene", "video_prompt": "Cinematic shot of the product."}]

        # ── CİNSİYET ↔ VOICE UYUMU VALIDATION (auto-fix) ──
        # WHY: LLM bazen character_gender="erkek" planlayıp voice_name="Ahu" (kadın) seçiyor.
        # Bu uyumsuzluğu otomatik düzelt: voice_name'i karakter cinsiyetine uygun varsayılana çevir.
        try:
            from services.elevenlabs_service import TURKISH_VOICE_CATALOG
            char_gender_raw = (scenario.get("character_gender") or "").strip().lower()
            voice_name_raw = (scenario.get("voice_name") or "").strip()
            # Catalog'dan voice cinsiyetini bul
            voice_meta = TURKISH_VOICE_CATALOG.get(voice_name_raw)
            voice_gender = (voice_meta[1] if voice_meta else "").lower()

            # character_gender boşsa character_visual_prompt'tan tahmin et
            if not char_gender_raw:
                cvp = (scenario.get("character_visual_prompt") or "").lower()
                if any(w in cvp for w in [" male", " man", " guy", " men "]):
                    char_gender_raw = "erkek"
                elif any(w in cvp for w in [" female", " woman", " girl", " women "]):
                    char_gender_raw = "kadın"

            if char_gender_raw and voice_gender and char_gender_raw != voice_gender:
                # Uyumsuz — varsayılan eşleşmeyle düzelt
                if char_gender_raw == "erkek":
                    new_voice = "Adam"
                else:
                    new_voice = "Ahu"  # kadın varsayılanı (UGC tonu)
                log.warning(
                    f"⚠️ Cinsiyet uyumsuzluğu düzeltildi: karakter={char_gender_raw}, "
                    f"voice={voice_name_raw}→{new_voice}"
                )
                scenario["voice_name"] = new_voice
                scenario["character_gender"] = char_gender_raw
            elif char_gender_raw and not voice_meta:
                # Voice catalog'da yok → cinsiyete uygun varsayılana zorla
                fallback = "Adam" if char_gender_raw == "erkek" else "Ahu"
                log.warning(
                    f"⚠️ Bilinmeyen voice_name '{voice_name_raw}' → varsayılan '{fallback}' "
                    f"(karakter={char_gender_raw})"
                )
                scenario["voice_name"] = fallback
        except Exception:
            log.warning("Cinsiyet validation hatası (yok sayıldı)", exc_info=True)

        # ── NARRATIVE HOOK + voiceover_segment validasyonu ──
        # WHY: voiceover/sahne kopukluğu kök problem; LLM'in hook + segment yazma
        # disiplinine uyduğunu doğrula. Eksikse warning logla (pipeline blokesi yok).
        narrative_hook = (scenario.get("narrative_hook") or "").strip()
        if not narrative_hook:
            log.warning(
                "⚠️ narrative_hook boş — LLM merkezi hikaye fikrini üretmedi. "
                "Voiceover/sahne paralelliği zayıf olabilir."
            )
            scenario["narrative_hook"] = ""
        else:
            log.info(f"🧭 Narrative hook: {narrative_hook}")

        # Her sahnenin voiceover_segment'i 5-15 kelime aralığında olmalı
        for idx, scene in enumerate(scenario.get("scenes", []), 1):
            seg = (scene.get("voiceover_segment") or "").strip()
            if not seg:
                log.warning(
                    f"⚠️ Sahne {idx} voiceover_segment boş — sahne-ses paralelliği kayboldu"
                )
                continue
            seg_words = len([w for w in seg.split() if w.strip()])
            if seg_words < 3 or seg_words > 20:
                log.warning(
                    f"⚠️ Sahne {idx} voiceover_segment kelime sayısı dışı: {seg_words} "
                    f"(beklenen 5-15) → '{seg[:60]}'"
                )
            else:
                log.info(f"  Sahne {idx} segment ({seg_words} kelime): {seg}")

        # Maliyet hesapla — voiceover length de dahil
        voiceover_text = scenario.get("voiceover_text", "") or ""
        cost = self.calculate_cost(
            duration,
            has_images,
            scene_count=scene_count,
            voiceover_text=voiceover_text,
            resolution="720p",
        )

        # Senaryo sonucunu sistem parametreleriyle zenginleştir
        scenario["duration"] = duration
        scenario["scene_count"] = scene_count
        scenario["aspect_ratio"] = aspect_ratio_override
        scenario["language"] = FIXED_LANGUAGE
        scenario["has_reference_images"] = has_images
        scenario["cost"] = cost
        scenario["is_multi_scene"] = scene_count > 1

        log.info(
            f"Senaryo üretildi: '{scenario.get('title', '?')}' — "
            f"{scene_count} sahne, Toplam {duration}s, ${cost['total_usd']:.3f}"
        )

        return scenario

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 💰 MALİYET HESAPLAMA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def calculate_cost(duration: int,
                       has_reference_image: bool = True,
                       scene_count: int = 1,
                       voiceover_text: str = "",
                       resolution: str = "720p") -> dict:
        """
        Seedance 2.0 + ek servis maliyet hesaplama.

        Args:
            duration: Toplam video süresi (saniye) — kullanıcıya gösterilen
            has_reference_image: Reference image var mı (img2vid vs text2vid)
            scene_count: Sahne sayısı (multi-scene için 2+)
            voiceover_text: ElevenLabs char-bazlı maliyet için
            resolution: "480p" veya "720p"

        Returns:
            dict: Maliyet bilgileri (breakdown + total_usd)
        """
        # WHY: Multi-scene'de production_pipeline `max(5, duration//scene_count)` ile
        # her sahneyi üretiyor → gerçek toplam süre `per_scene * scene_count`
        per_scene_duration = max(5, duration // scene_count) if scene_count > 1 else duration
        actual_duration = per_scene_duration * scene_count if scene_count > 1 else duration

        # Resolution + mode -> credit/s seçimi
        credits_per_sec = SEEDANCE_PRICING.get(
            (resolution, has_reference_image),
            SEEDANCE_CREDITS_PER_SECOND,
        )

        seedance_credits = credits_per_sec * actual_duration
        seedance_usd = seedance_credits * CREDIT_TO_USD

        # Ek servisler
        elevenlabs_usd = len(voiceover_text or "") * ELEVENLABS_COST_PER_CHAR
        replicate_usd = REPLICATE_MERGE_COST_USD
        # Multi-scene: bir de concat merge yapılıyor → 2x merge
        if scene_count > 1:
            replicate_usd += REPLICATE_MERGE_COST_USD
        openai_usd = OPENAI_SCENARIO_COST_USD
        perplexity_usd = PERPLEXITY_RESEARCH_COST_USD
        gpt_image_usd = GPT_IMAGE_USD  # Karakter portresi (tutarlılık için)

        total_usd = (
            seedance_usd + elevenlabs_usd + replicate_usd + openai_usd + perplexity_usd + gpt_image_usd
        )

        mode_label = "reference-image" if has_reference_image else "text-to-video"
        scene_label = f"{scene_count} sahne × {per_scene_duration}s" if scene_count > 1 else "tek sahne"

        breakdown_dict = {
            "seedance_usd": round(seedance_usd, 4),
            "elevenlabs_usd": round(elevenlabs_usd, 4),
            "replicate_usd": round(replicate_usd, 4),
            "openai_usd": round(openai_usd, 4),
            "perplexity_usd": round(perplexity_usd, 4),
            "gpt_image_usd": round(gpt_image_usd, 4),
        }

        breakdown_text = (
            f"Seedance {actual_duration}s × {credits_per_sec} c/s = "
            f"{seedance_credits:.0f} credits (${seedance_usd:.3f}) "
            f"[{resolution}, {mode_label}, {scene_label}] | "
            f"ElevenLabs ${elevenlabs_usd:.4f} | "
            f"Replicate ${replicate_usd:.3f} | "
            f"OpenAI ${openai_usd:.3f} | Perplexity ${perplexity_usd:.3f} | "
            f"GPT-Image ${gpt_image_usd:.3f}"
        )

        return {
            "credits_per_second": credits_per_sec,
            "total_credits": seedance_credits,
            "seedance_usd": round(seedance_usd, 3),
            "total_usd": round(total_usd, 3),
            "scene_count": scene_count,
            "actual_duration": actual_duration,
            "resolution": resolution,
            "breakdown_dict": breakdown_dict,
            "breakdown": breakdown_text,
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📝 KULLANICIYA ÖZET
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def format_scenario_summary(scenario: dict) -> str:
        """
        Senaryoyu kullanıcıya gösterilecek özet formata çevirir.
        Telegram'da güzel görünsün diye HTML formatına çevrilmiştir.

        Returns:
            str: Telegram HTML mesajı
        """
        def safe_html(text):
            if not text:
                return ""
            return html.escape(str(text))

        cost = scenario.get("cost", {})

        title = safe_html(scenario.get('title', 'Reklam Videosu'))
        summary_text = safe_html(scenario.get('summary', ''))
        
        duration = scenario.get("duration", 10)
        scene_count = scenario.get("scene_count", 1)

        summary = (
            f"🎬 <b>Senaryo Hazır!</b>\n\n"
            f"<b>{title}</b>\n"
            f"<i>{summary_text}</i>\n\n"
            f"📐 <b>Format:</b> {scenario.get('aspect_ratio', FIXED_ASPECT_RATIO)} | 720p\n"
            f"⏱ <b>Süre:</b> {duration} saniye (Dinamik)\n"
            f"🌍 <b>Dil:</b> {scenario.get('language', FIXED_LANGUAGE)}\n"
            f"🖼 <b>Referans Görsel:</b> {'Var (Vision Analizli)' if scenario.get('has_reference_images') else 'Yok'}\n"
        )

        # Multi-scene bilgisi
        if scenario.get("scenes"):
            scenes = scenario["scenes"]
            summary += f"🎬 <b>Kurgu:</b> {len(scenes)} Sahne\n"
            for i, scene in enumerate(scenes, 1):
                scene_name = safe_html(scene.get("scene_name", f"Sahne {i}"))
                summary += f"   {i}. {scene_name}\n"
            summary += "\n"

        # Dış ses (her zaman var)
        voiceover = safe_html(scenario.get("voiceover_text", ""))
        if voiceover:
            word_count = len(voiceover.split())
            wps = word_count / max(1, duration)
            summary += f"🎙 <b>Dış Ses ({word_count} kelime, {wps:.1f} kelime/sn):</b> <i>{voiceover}</i>\n"

        # Maliyet
        summary += (
            f"\n💰 <b>Tahmini Maliyet:</b> ${cost.get('total_usd', 0):.2f}\n"
            f"📊 {safe_html(cost.get('breakdown', ''))}\n"
        )

        summary += (
            f"\n✅ <b>Onayla</b> → Üretim başlar\n"
            f"❌ <b>İptal</b> → Vazgeç"
        )

        return summary
