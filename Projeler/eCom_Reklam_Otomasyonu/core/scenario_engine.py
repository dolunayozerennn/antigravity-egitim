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

# Sabit parametreler (deterministik)
FIXED_DURATION = 10       # saniye
FIXED_ASPECT_RATIO = "9:16"
FIXED_LANGUAGE = "Türkçe"
TARGET_WORD_COUNT = 25    # ~2.5 kelime/saniye × 10s


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎬 SENARYO SYSTEM PROMPT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCENARIO_SYSTEM_PROMPT = """Sen profesyonel bir reklam film yönetmenisin. Verilen marka, ürün ve konsept bilgilerine göre 10 saniyelik bir video reklam senaryosu üretiyorsun.

## Çıktı Formatı (JSON):
```json
{
  "title": "Senaryo başlığı (Türkçe)",
  "summary": "1-2 cümlelik Türkçe özet",
  "video_prompt": "Seedance 2.0 için DETAYLI İngilizce video promptu",
  "voiceover_text": "Türkçe dış ses metni (tam 25 kelime ±3)",
  "technical_notes": "Teknik notlar"
}
```

## KRİTİK KURALLAR (İSTİSNASIZ UYGULA):

### Video Prompt (İngilizce):
1. Her zaman İNGİLİZCE yaz — Seedance 2.0 İngilizce'de en iyi sonucu verir
2. Prompt'un SONUNA mutlaka şu cümleyi ekle: "No character dialogue, no speaking, no lip movement. Enable ambient and environmental sounds, natural atmosphere."
3. Kamera hareketlerini detaylı belirt (smooth zoom in, slow pan, cinematic tracking shot)
4. Işık, renk paleti ve atmosferi net tanımla (soft cinematic lighting, depth of field)
5. Ürün referans görseli otomatik verilecek — prompt içinde görselin etrafında nasıl hareket ve sahne oluşturulacağını 3D sinematik hissiyatla belirt
6. Durağan veya basit kalıplardan KAÇIN — her sahne dinamik ve sinematik olmalı
7. Video tam 10 saniye — tek sahne veya max 2 sahne ile kurgula

### Dış Ses (Türkçe):
1. Her zaman TÜRKÇE yaz
2. Tam 25 kelime (±3 kelime tolerans) — 10 saniyelik video = 2.5 kelime/saniye
3. Metnin başı videonun başına, sonu videonun sonuna denk gelecek şekilde kurgula
4. Etkileyici, akılda kalıcı ve ürünün faydalarını vurgulayan bir dış ses yaz
5. Sosyal medya reklamına uygun ton: enerjik ama samimi

### Genel:
1. Konsept/hikaye markanın tonuna uygun olmalı (araştırma sonuçlarını kullan)
2. title ve summary her zaman TÜRKÇE olmalı
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

    def generate_scenario(self, collected_data: dict, research_data: dict) -> dict:
        """
        Araştırma sonuçlarıyla deterministik video senaryosu üretir.

        Sabit parametreler: 10s, 9:16, 720p, Türkçe dış ses, reference image.

        Args:
            collected_data: URLDataExtractor'dan gelen veriler
            research_data: research() çıktısı

        Returns:
            dict: Senaryo bilgileri + maliyet
        """
        brand = collected_data.get("brand_name", "")
        product = collected_data.get("product_name", "")
        concept = collected_data.get("ad_concept", "")
        description = collected_data.get("product_description", "")
        target_audience = collected_data.get("target_audience", "")
        has_images = bool(collected_data.get("best_image_urls"))

        user_brief = (
            f"## Proje Bilgileri:\n"
            f"- Marka: {brand}\n"
            f"- Ürün: {product}\n"
            f"- Ürün Açıklaması: {description}\n"
            f"- Reklam Konsepti: {concept}\n"
            f"- Hedef Kitle: {target_audience}\n"
            f"- Video Süresi: {FIXED_DURATION} saniye (SABİT)\n"
            f"- Format: {FIXED_ASPECT_RATIO} (SABİT)\n"
            f"- Dil: {FIXED_LANGUAGE} (SABİT)\n"
            f"- Ürün Referans Görseli: {'Var (reference image modu)' if has_images else 'Yok (text-to-video)'}\n\n"
            f"## Marka Araştırması:\n{research_data.get('brand_research', 'N/A')}\n"
        )

        messages = [
            {"role": "system", "content": SCENARIO_SYSTEM_PROMPT},
            {"role": "user", "content": user_brief},
        ]

        log.info(f"Senaryo üretimi başlıyor: {brand} — {product} "
                 f"({FIXED_DURATION}s, {FIXED_ASPECT_RATIO})")

        try:
            scenario = self.openai.chat_json(messages, temperature=0.8, max_tokens=2500)
        except Exception:
            log.error("Senaryo üretimi hatası", exc_info=True)
            raise

        # Maliyet hesapla (tek tier: 720p + reference image)
        cost = self.calculate_cost(FIXED_DURATION, has_images)

        # Senaryo sonucunu deterministik parametrelerle zenginleştir
        scenario["duration"] = FIXED_DURATION
        scenario["aspect_ratio"] = FIXED_ASPECT_RATIO
        scenario["language"] = FIXED_LANGUAGE
        scenario["has_reference_images"] = has_images
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
    def calculate_cost(duration: int = FIXED_DURATION,
                       has_reference_image: bool = True) -> dict:
        """
        Seedance 2.0 maliyet hesaplama (tek tier: 720p + reference image).

        Args:
            duration: Video süresi (saniye)
            has_reference_image: Reference image var mı

        Returns:
            dict: Maliyet bilgileri
        """
        credits_per_sec = SEEDANCE_CREDITS_PER_SECOND
        total_credits = credits_per_sec * duration
        total_usd = total_credits * CREDIT_TO_USD

        mode_label = "reference-image" if has_reference_image else "text-to-video"

        return {
            "credits_per_second": credits_per_sec,
            "total_credits": total_credits,
            "total_usd": round(total_usd, 3),
            "breakdown": (
                f"{duration}s × {credits_per_sec} credit/s = "
                f"{total_credits} credits (${total_usd:.3f}) "
                f"[720p, {mode_label}]"
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
            f"📐 **Format:** {scenario.get('aspect_ratio', FIXED_ASPECT_RATIO)} | 720p\n"
            f"⏱ **Süre:** {scenario.get('duration', FIXED_DURATION)} saniye\n"
            f"🌍 **Dil:** {scenario.get('language', FIXED_LANGUAGE)}\n"
            f"🖼 **Referans Görsel:** {'Var' if scenario.get('has_reference_images') else 'Yok'}\n"
        )

        # Dış ses (her zaman var)
        voiceover = scenario.get("voiceover_text", "")
        if voiceover:
            word_count = len(voiceover.split())
            summary += f"🎙 **Dış Ses ({word_count} kelime):** _{voiceover}_\n"

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
