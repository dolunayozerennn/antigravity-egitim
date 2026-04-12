from __future__ import annotations

"""
Scenario Engine — Senaryo Üretimi + Maliyet Hesaplama
=======================================================
Toplanan bilgilerle:
1. Perplexity ile marka/ürün araştırır
2. GPT-5 Mini Vision ile ürün görselini analiz eder
3. LLM ile reklam senaryosu (shot listesi + dış ses metni) üretir
4. Maliyet hesaplar
"""

import json
import math

from logger import get_logger

log = get_logger("scenario_engine")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💰 SEEDANCE 2.0 FİYATLANDIRMA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# credit/saniye — Kie AI üzerinden
PRICING = {
    "480p": {"with_image": 11.5, "without_image": 19},
    "720p": {"with_image": 25, "without_image": 41},
}

CREDIT_TO_USD = 0.005  # 1 credit = $0.005


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎬 SENARYO SYSTEM PROMPT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCENARIO_SYSTEM_PROMPT = """Sen profesyonel bir reklam film yönetmenisin. Verilen marka, ürün ve konsept bilgilerine göre bir video reklam senaryosu üretiyorsun.

## Girdi:
- Marka bilgileri ve araştırma sonuçları
- Ürün görseli analizi
- Kullanıcının istediği konsept, süre, format ve dil

## Çıktı Formatı (JSON):
```json
{
  "title": "Senaryo başlığı",
  "summary": "1-2 cümlelik özet",
  "video_prompt": "Seedance 2.0 için detaylı İngilizce video promptu. Kamera hareketleri, ışık, renk paleti, atmosfer dahil. 'no dialogue, ambient sounds only' ifadesini ekle eğer Türkçe dış ses varsa.",
  "voiceover_text": "Türkçe dış ses metni (video süresine uygun: ~2.5 kelime/saniye). Dil İngilizce ise boş bırak.",
  "image_prompt": "Nano Banana 2 için İngilizce giriş karesı promptu. Ürünün/markanın tanıtıldığı sinematik ilk kare.",
  "resolution": "720p",
  "technical_notes": "Teknik notlar ve öneriler"
}
```

## Kurallar:
1. Video prompt'u İNGİLİZCE olmalı — Seedance 2.0 İngilizce en iyi sonucu verir
2. Dış ses metni belirtilen dilde olmalı (Türkçe veya İngilizce)
3. Dış ses metni uzunluğu video süresine göre ayarla: ~2.5 kelime/saniye
   - 10 saniyelik video → ~25 kelime dış ses
   - 15 saniyelik video → ~37 kelime dış ses
4. Dil "Türkçe" ise video prompt'una "no dialogue, ambient sounds only" ekle
5. Dil "İngilizce" ise voiceover_text boş string ("") olmalı
6. Image prompt sinematik, ürüne odaklı, ilgi çekici olmalı
7. Konsept/hikaye markanın tonuna uygun olmalı (araştırma sonuçlarını kullan)
8. Resolution varsayılan olarak "720p" kullan, kullanıcı 480p isterse onu yaz
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
        Marka/ürün araştırması ve görsel analizi yapar.

        Args:
            collected_data: ConversationManager'dan toplanan veriler

        Returns:
            dict: {
                "brand_research": str,
                "image_analysis": str,
            }
        """
        brand = collected_data.get("brand_name", "")
        product = collected_data.get("product_name", "")
        image_url = collected_data.get("product_image", "")
        language = collected_data.get("language", "Türkçe")

        # 1. Perplexity marka araştırması
        lang_code = "tr" if language == "Türkçe" else "en"
        log.info(f"Marka araştırması başlıyor: {brand} — {product}")
        brand_research = self.perplexity.research_brand(brand, product, lang_code)

        # 2. GPT-5 Mini Vision — ürün görseli analizi
        image_analysis = ""
        if image_url:
            log.info(f"Ürün görseli analiz ediliyor: {image_url[:60]}...")
            image_analysis = self.openai.analyze_image(
                image_url=image_url,
                prompt=(
                    "Bu ürün fotoğrafını analiz et. Şunları belirt:\n"
                    "1. Ürün türü ve renkleri\n"
                    "2. Ürünün dikkat çeken özellikleri\n"
                    "3. Reklam videosu için önerilen görsel tema\n"
                    "4. Arka plan ve ışık önerileri\n"
                    "Kısa ve öz yanıt ver."
                ),
            )

        log.info(
            f"Araştırma tamamlandı: brand_research={len(brand_research)} chars, "
            f"image_analysis={len(image_analysis)} chars"
        )

        return {
            "brand_research": brand_research,
            "image_analysis": image_analysis,
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🎬 SENARYO ÜRETİMİ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def generate_scenario(self, collected_data: dict, research_data: dict) -> dict:
        """
        Araştırma sonuçlarıyla video senaryosu üretir.

        Args:
            collected_data: Kullanıcıdan toplanan veriler
            research_data: research() çıktısı

        Returns:
            dict: Senaryo bilgileri + maliyet
        """
        brand = collected_data.get("brand_name", "")
        product = collected_data.get("product_name", "")
        concept = collected_data.get("ad_concept", "")
        duration = collected_data.get("video_duration", 10)
        aspect_ratio = collected_data.get("aspect_ratio", "9:16")
        resolution = collected_data.get("resolution", "720p")
        language = collected_data.get("language", "Türkçe")
        has_image = bool(collected_data.get("product_image"))

        # Resolution doğrulama
        if resolution not in ("480p", "720p"):
            resolution = "720p"

        user_brief = (
            f"## Proje Bilgileri:\n"
            f"- Marka: {brand}\n"
            f"- Ürün: {product}\n"
            f"- Konsept: {concept}\n"
            f"- Video Süresi: {duration} saniye\n"
            f"- Format: {aspect_ratio}\n"
            f"- Çözünürlük: {resolution}\n"
            f"- Dil: {language}\n"
            f"- Ürün Fotoğrafı: {'Var (image-to-video kullanılacak)' if has_image else 'Yok (text-to-video)'}\n\n"
            f"## Marka Araştırması:\n{research_data.get('brand_research', 'N/A')}\n\n"
            f"## Ürün Görseli Analizi:\n{research_data.get('image_analysis', 'N/A')}\n"
        )

        messages = [
            {"role": "system", "content": SCENARIO_SYSTEM_PROMPT},
            {"role": "user", "content": user_brief},
        ]

        log.info(f"Senaryo üretimi başlıyor: {brand} — {product} ({duration}s, {aspect_ratio})")

        try:
            scenario = self.openai.chat_json(messages, temperature=0.8, max_tokens=2500)
        except Exception:
            log.error("Senaryo üretimi hatası", exc_info=True)
            raise

        # Kullanıcının seçtiği resolution'ı kullan (senaryodaki override edilir)
        # Maliyet hesapla
        cost = self.calculate_cost(duration, resolution, has_image)

        # Senaryo sonucunu zenginleştir
        scenario["duration"] = duration
        scenario["aspect_ratio"] = aspect_ratio
        scenario["language"] = language
        scenario["resolution"] = resolution
        scenario["has_product_image"] = has_image
        scenario["cost"] = cost

        log.info(
            f"Senaryo üretildi: '{scenario.get('title', '?')}' — "
            f"${cost['total_usd']:.3f}, {cost['total_credits']} credits"
        )

        return scenario

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 💰 MALİYET HESAPLAMA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def calculate_cost(duration: int, resolution: str = "720p",
                       has_image: bool = True) -> dict:
        """
        Seedance 2.0 maliyet hesaplama.

        Args:
            duration: Video süresi (saniye)
            resolution: "480p" veya "720p"
            has_image: Image-to-video mi (True) yoksa text-to-video mu (False)

        Returns:
            dict: {
                "credits_per_second": float,
                "total_credits": float,
                "total_usd": float,
                "breakdown": str,
            }
        """
        pricing_tier = PRICING.get(resolution, PRICING["720p"])
        mode = "with_image" if has_image else "without_image"
        credits_per_sec = pricing_tier[mode]

        total_credits = credits_per_sec * duration
        total_usd = total_credits * CREDIT_TO_USD

        mode_label = "image-to-video" if has_image else "text-to-video"

        return {
            "credits_per_second": credits_per_sec,
            "total_credits": total_credits,
            "total_usd": round(total_usd, 3),
            "breakdown": (
                f"{duration}s × {credits_per_sec} credit/s = "
                f"{total_credits} credits (${total_usd:.3f}) "
                f"[{resolution}, {mode_label}]"
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
        cost = scenario.get("cost", {})

        summary = (
            f"🎬 **Senaryo Hazır!**\n\n"
            f"**{scenario.get('title', 'Reklam Videosu')}**\n"
            f"_{scenario.get('summary', '')}_\n\n"
            f"📐 **Format:** {scenario.get('aspect_ratio', '9:16')} "
            f"| {scenario.get('resolution', '720p')}\n"
            f"⏱ **Süre:** {scenario.get('duration', 10)} saniye\n"
            f"🌍 **Dil:** {scenario.get('language', 'Türkçe')}\n"
        )

        # Dış ses varsa göster
        voiceover = scenario.get("voiceover_text", "")
        if voiceover:
            # İlk 100 karakter + ...
            preview = voiceover[:100] + ("..." if len(voiceover) > 100 else "")
            summary += f"🎙 **Dış Ses:** _{preview}_\n"

        # Maliyet
        summary += (
            f"\n💰 **Tahmini Maliyet:** ${cost.get('total_usd', 0):.2f}\n"
            f"📊 {cost.get('breakdown', '')}\n"
        )

        summary += (
            f"\n✅ **Onayla** → Üretim başlar\n"
            f"✏️ **Düzelt** → Değişiklik yap\n"
            f"❌ **İptal** → Vazgeç"
        )

        return summary
