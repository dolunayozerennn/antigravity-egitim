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

from logger import get_logger

log = get_logger("scenario_engine")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💰 SEEDANCE 2.0 FİYATLANDIRMA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# credit/saniye — Kie AI / Seedance 2.0 (reference image modu)
SEEDANCE_CREDITS_PER_SECOND = 25  # 720p + with_image
CREDIT_TO_USD = 0.005  # 1 credit = $0.005

# Sabit parametreler (varsayılanlar)
FIXED_ASPECT_RATIO = "9:16"
FIXED_LANGUAGE = "Türkçe"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎬 PRODUCER SYSTEM PROMPT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRODUCER_SYSTEM_PROMPT = """Sen yaratıcı bir e-ticaret reklam yapımcısı ve yönetmenisin (Producer). Verilen marka, ürün, konsept bilgilerini ve sağlanan GÖRSELLERİ analiz ederek en etkili reklam senaryosunu üretiyorsun.

ÖNEMLİ: Gelen görselleri DİKKATLİCE analiz et. Eğer ürün bir kıyafet/giysi ise ve görselde "hayalet manken" (içi boş, sadece kıyafet) veya "düz zemin" varsa, bunu fark etmeli ve Seedance promptunda mutlaka GERÇEK BİR İNSAN (model) tanımlamalısın ki yapay zeka kafası kopuk bir kıyafet videosu üretmesin!

## Çıktı Formatı (JSON):
```json
{
  "title": "Senaryo başlığı (Türkçe)",
  "summary": "1-2 cümlelik Türkçe özet",
  "scene_count": 1, // veya 2, veya 3 (Kurguya göre dinamik karar ver)
  "duration": 10, // Toplam saniye: 5 ile 15 arasında (Kurguya göre dinamik karar ver)
  "scenes": [
    {
      "scene_name": "Sahne adı (İngilizce, kısa)",
      "video_prompt": "Seedance 2.0 için DETAYLI İngilizce video promptu"
    }
  ],
  "voiceover_text": "Türkçe dış ses metni",
  "technical_notes": "Teknik notlar"
}
```

## KRİTİK KURALLAR (İSTİSNASIZ UYGULA):

### Sahne Yapısı ve Süre (Dinamik):
1. **Süre (duration):** Ürüne ve mesaja göre videonun toplam süresine sen karar ver (min 5s, max 15s).
2. **Sahne Sayısı (scene_count):** 1, 2 veya 3 sahne seçebilirsin.
   - Sinematik, tek odaklı bir ürünse: 1 sahne.
   - UGC, dinamik veya birden fazla açı gösterilecekse: 2 veya 3 sahne.
3. Her sahne Seedance 2.0'da ayrı ayrı üretilip sonradan birleştirilecektir. Bu yüzden her sahnenin promptu KENDİ İÇİNDE BAĞIMSIZ VE TAM OLMALIDIR.

### Video Prompt (İngilizce — HER SAHNE İÇİN AYRI):
1. Her zaman İNGİLİZCE yaz — Seedance 2.0 İngilizce'de en iyi sonucu verir.
2. Prompt'un SONUNA mutlaka şu cümleyi ekle: "No character dialogue, no speaking, no lip movement. Enable ambient and environmental sounds, natural atmosphere."
3. Kamera hareketlerini, ışığı, rengi ve atmosferi net tanımla (smooth zoom in, soft cinematic lighting vb.).
4. **HAYALET MANKEN ÖNLEMİ:** Görseldeki ürün cansız/manken üzerindeyse, prompt içinde ürünü giyen, hareket eden GERÇEK BİR İNSAN (modelin saçı, yüzü, bedeni) detaylıca tanımla.
5. Seedance 2.0'ın image-to-video altyapısını kullandığımız için prompt görselle uyumlu, görseldeki ürünü canlandıran yapıda olmalıdır.

### Dış Ses (Türkçe — TÜM VİDEO İÇİN TEK):
1. Her zaman TÜRKÇE yaz.
2. Dış ses uzunluğunu, belirlediğin toplam `duration` değerine tam uyumlu olacak şekilde ayarla. Ortalama olarak saniyede 1.6 - 2.0 kelime okunur. (Örn: 10 saniye için ~16-20 kelime). Konuşma hızlandırılmamalıdır!
3. Metnin başı videonun başına, sonu videonun sonuna denk gelecek şekilde kurgula.

### Genel:
1. title ve summary her zaman TÜRKÇE olmalı.
2. scene_name İngilizce, kısa ve açıklayıcı olmalı.
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

        # Maliyet hesapla
        cost = self.calculate_cost(duration, has_images, scene_count=scene_count)

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
                       scene_count: int = 1) -> dict:
        """
        Seedance 2.0 maliyet hesaplama.

        Args:
            duration: Video süresi (saniye) — TOPLAM SÜRE
            has_reference_image: Reference image var mı
            scene_count: Sahne sayısı (multi-scene için 2+)

        Returns:
            dict: Maliyet bilgileri
        """
        credits_per_sec = SEEDANCE_CREDITS_PER_SECOND
        
        # Toplam maliyet credit/s * duration
        total_credits = credits_per_sec * duration
        total_usd = total_credits * CREDIT_TO_USD

        mode_label = "reference-image" if has_reference_image else "text-to-video"
        scene_label = f"{scene_count} sahne" if scene_count > 1 else "tek sahne"

        return {
            "credits_per_second": credits_per_sec,
            "total_credits": total_credits,
            "total_usd": round(total_usd, 3),
            "scene_count": scene_count,
            "breakdown": (
                f"{duration}s toplam × {credits_per_sec} credit/s = "
                f"{total_credits} credits (${total_usd:.3f}) "
                f"[720p, {mode_label}, {scene_label}]"
            ),
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📝 KULLANICIYA ÖZET
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def format_scenario_summary(scenario: dict) -> str:
        """
        Senaryoyu kullanıcıya gösterilecek özet formata çevirir.
        Telegram'da güzel görünsün diye markdown.

        Returns:
            str: Telegram markdown mesajı
        """
        def safe_md(text):
            if not text:
                return ""
            # Markdown parse hatalarını önlemek için _, *, [, ] gibi karakterleri güvenli hale getir
            return str(text).replace("_", "-").replace("*", "").replace("[", "(").replace("]", ")")

        cost = scenario.get("cost", {})

        title = safe_md(scenario.get('title', 'Reklam Videosu'))
        summary_text = safe_md(scenario.get('summary', ''))
        
        duration = scenario.get("duration", 10)
        scene_count = scenario.get("scene_count", 1)

        summary = (
            f"🎬 **Senaryo Hazır!**\n\n"
            f"**{title}**\n"
            f"_{summary_text}_\n\n"
            f"📐 **Format:** {scenario.get('aspect_ratio', FIXED_ASPECT_RATIO)} | 720p\n"
            f"⏱ **Süre:** {duration} saniye (Dinamik)\n"
            f"🌍 **Dil:** {scenario.get('language', FIXED_LANGUAGE)}\n"
            f"🖼 **Referans Görsel:** {'Var (Vision Analizli)' if scenario.get('has_reference_images') else 'Yok'}\n"
        )

        # Multi-scene bilgisi
        if scenario.get("scenes"):
            scenes = scenario["scenes"]
            summary += f"🎬 **Kurgu:** {len(scenes)} Sahne\n"
            for i, scene in enumerate(scenes, 1):
                scene_name = safe_md(scene.get("scene_name", f"Sahne {i}"))
                summary += f"   {i}. {scene_name}\n"
            summary += "\n"

        # Dış ses (her zaman var)
        voiceover = safe_md(scenario.get("voiceover_text", ""))
        if voiceover:
            word_count = len(voiceover.split())
            wps = word_count / max(1, duration)
            summary += f"🎙 **Dış Ses ({word_count} kelime, {wps:.1f} kelime/sn):** _{voiceover}_\n"

        # Maliyet
        summary += (
            f"\n💰 **Tahmini Maliyet:** ${cost.get('total_usd', 0):.2f}\n"
            f"📊 {cost.get('breakdown', '')}\n"
        )

        summary += (
            f"\n✅ **Onayla** → Üretim başlar\n"
            f"❌ **İptal** → Vazgeç"
        )

        return summary
