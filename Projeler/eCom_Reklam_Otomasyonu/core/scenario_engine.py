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
  "title": "Senaryo başlığı (Türkçe)",
  "summary": "1-2 cümlelik Türkçe özet",
  "hook_pattern": "Sürpriz reveal | Before/After | POV | Problem-Solution | ASMR | Unexpected analogy",
  "voice_name": "Ahu",
  "character_gender": "kadın",
  "scene_count": 3,
  "duration": 15,
  "character_visual_prompt": "GPT-Image 2 için TEK karakter portresi İngilizce promptu",
  "scenes": [
    {
      "scene_name": "Sahne adı (İngilizce, kısa)",
      "video_prompt": "Seedance 2.0 için DETAYLI İngilizce video promptu"
    }
  ],
  "voiceover_text": "Türkçe dış ses metni (audio tag'lerle)",
  "technical_notes": "Teknik notlar"
}
```

### Ses Seçimi (voice_name) — KATI KURAL
Voiceover sesi **bu Türkçe Professional Voice Clone kataloğundan birini seç** ve
seçimini ürünün havasına/karakterine göre yap. Karakter cinsiyeti (`character_gender`)
**MUTLAKA seçtiğin sesin cinsiyetiyle aynı olmalı**, ve **video promptlarındaki
karakter de aynı cinsiyette tanımlanmalı**. Erkek ses + kadın model olamaz.

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

Şablon (İNGİLİZCE, tek string, ~60-90 kelime):
```
Single [age] [gender] [ethnicity hint matching brand vibe], [hair description],
[outfit fitting brand identity and product category], natural skin texture with
subtle imperfections, casual three-quarter shot, neutral plain studio background
or soft window-lit interior, soft natural light, photorealistic iPhone selfie
aesthetic, candid expression, no text, no logos, no watermarks, 9:16 vertical
```

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

### Sahne Yapısı ve Süre (MULTI-SCENE VARSAYILAN):
1. **duration**: 15-25 saniye arası seç. Daha kısa video = daha az sahne = daha sıkıcı.
2. **scene_count kuralı (KATIDIR — MULTI-SCENE TERCİH EDİLİR)**:
   - **DEFAULT: 3 sahne** (15s video, her sahne 5s)
   - **DİNAMİK PROFESYONEL: 4-5 sahne** (20-25s video) → REKLAM HİSSİ İÇİN İDEAL
   - **Tek sahne**: SADECE çok minimal/sinematik bir konsept varsa (nadir).
   - Seedance her sahneyi 5s üretir → toplam = scene_count × 5s.
3. Her sahne Seedance 2.0'da ayrı üretilip birleştirilir — her sahne kendi içinde TAM olmalı.
4. **HER SAHNE FARKLI OLMALI — TEKRARDAN KESİNLİKLE KAÇIN**:
   - **Farklı KAMERA AÇISI**: close-up macro / wide establishing shot / POV first-person / overhead top-down / tracking side / dutch angle / over-the-shoulder — her sahne farklı bir açı.
   - **Farklı ORTAM/MEKAN**: yatak odası → sokak → kafe → spor salonu → araba içi → banyo → park gibi.
   - **Farklı KOMPOZİSYON**: ürün ön planda / model ön planda / detay zoom / context wide.
   Tek bir mekanda tek bir karakter yürüyen 15s video = BAŞARISIZLIK.

### Video Prompt (İngilizce — UGC CREATOR-FIRST YAPISI ZORUNLU):
1. Her zaman İNGİLİZCE yaz.
2. Her sahne prompt'u ŞU SIRAYLA yazılacak — sıralama kritiktir, başa cinematic
   detay yazma; başa CREATOR IDENTITY yaz:

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
1. TÜRKÇE yaz. Türkçe ses olan İrem ile okunacak.
2. **TON**: Bir arkadaşın seninle samimi konuşuyor — reklam spikeri DEĞİL.
   - ✅ "Kızlar, bunu yıllardır kullanıyorum cidden..."
   - ✅ "Tamam söylüyorum, AirPods Pro'suz dışarı çıkmıyorum artık."
   - ❌ "X marka süper bir ürün sunuyor"
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
5. **Süre**: doğal akıcı 2-3 cümle. Video duration sonradan ses süresine eşitlenecek —
   kelime sayma, akıcılığı koru. Net ama samimi.
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
