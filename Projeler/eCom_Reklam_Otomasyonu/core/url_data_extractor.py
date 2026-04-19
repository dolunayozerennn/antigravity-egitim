from __future__ import annotations

"""
URL Data Extractor — Deterministik Ürün Veri Çıkarma
======================================================
E-ticaret URL'sinden tek seferde tam ürün verisi çıkarır.

Pipeline:
1. Firecrawl ile URL scrape (birincil)
2. Firecrawl başarısızsa → WebScraperService fallback
3. LLM (GPT-4.1 Mini) ile structured data extraction
4. LLM Vision ile en iyi 1-3 ürün görseli seçimi

Kullanıcıya SIFIR soru sorulur — her şey otomatik çıkarılır.
"""

import re

from logger import get_logger

log = get_logger("url_data_extractor")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LLM PROMPT — Ürün Verisi Çıkarma
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXTRACTION_PROMPT = """Sen bir e-ticaret ürün analiz uzmanısın. Aşağıdaki web sayfası verisinden şu bilgileri JSON formatında çıkar.

## Kurallar:
- Sayfada açıkça bulamadığın bilgileri makul şekilde çıkar (örn: marka adı domain'den anlaşılabilir)
- ad_concept alanı için ürüne uygun, kısa ve etkileyici bir Türkçe reklam konsepti üret
- target_audience alanı için ürünün doğal hedef kitlesini belirle
- Yanıtın SADECE JSON olmalı, başka hiçbir metin ekleme

## Çıkarılacak JSON formatı:
{{
    "brand_name": "Marka adı",
    "product_name": "Ürün adı (kısa ve net)",
    "product_description": "Ürünün 2-3 cümlelik açıklaması",
    "ad_concept": "Kısa, etkileyici Türkçe reklam konsepti (1-2 cümle, sinematik ve dinamik)",
    "target_audience": "Hedef kitle tanımı (1 cümle)",
    "product_category": "Ürün kategorisi (örn: Elektronik, Giyim, Kozmetik, Mobilya)"
}}

## Sayfa Verisi:
---
{page_content}
---"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LLM PROMPT — En İyi Görsel Seçimi
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMAGE_SELECTION_PROMPT = """Aşağıdaki ürün görsellerini incele. Bir e-ticaret video reklamı üretmek için EN UYGUN 1-3 fotoğrafı seç.

## Seçim Kriterleri (öncelik sırasına göre):
1. Ürünü en net ve yüksek kalitede gösteren
2. Reklam için en etkileyici açıya sahip
3. Arka planı temiz veya profesyonel
4. Ürünün tamamını gösteren (kırpılmamış)

## Kurallar:
- En az 1, en fazla 3 görsel seç
- Seçtiğin görsellerin indeks numaralarını JSON array olarak döndür
- SADECE JSON döndür: {{"selected_indices": [0, 2, 4]}}
- Logo, ikon, lifestyle (ürün olmayan) ve düşük çözünürlüklü görselleri ASLA SEÇME

## Görsel URL Listesi:
{image_list}"""


class URLDataExtractor:
    """
    URL → Structured Data pipeline.

    Firecrawl (birincil) + WebScraperService (fallback) ile
    URL'den tam ürün verisi çıkarır. Kullanıcıya soru sormaz.
    """

    def __init__(
        self,
        openai_service,
        firecrawl_service,
        web_scraper_fallback=None,
    ):
        """
        Args:
            openai_service: OpenAIService instance (chat_json + vision)
            firecrawl_service: FirecrawlService instance (birincil scraper)
            web_scraper_fallback: WebScraperService instance (fallback, opsiyonel)
        """
        self.openai = openai_service
        self.firecrawl = firecrawl_service
        self.web_scraper = web_scraper_fallback

    async def extract(self, url: str) -> dict:
        """
        URL'den tam ürün verisi çıkarır.

        Pipeline:
        1. Firecrawl scrape → markdown + metadata
        2. Fallback: WebScraperService
        3. LLM structured extraction
        4. Vision ile en iyi görselleri seç

        Args:
            url: E-ticaret ürün sayfası URL'i

        Returns:
            dict: {
                "brand_name": str,
                "product_name": str,
                "product_description": str,
                "ad_concept": str,
                "target_audience": str,
                "product_category": str,
                "best_image_urls": list[str],   # 1-3 en iyi ürün görseli
                "all_image_urls": list[str],     # Tüm bulunan görseller
                "page_content": str,             # Ham içerik (loglama)
                "extraction_source": str,        # "firecrawl" | "scraper"
            }

        Raises:
            ValueError: Hiçbir veri çıkarılamadıysa
        """
        import asyncio

        log.info(f"URL veri çıkarma başlatılıyor: {url}")

        # ── ADIM 1: Web scraping ──
        page_content, image_urls, metadata, source = await asyncio.to_thread(
            self._scrape_url, url
        )

        if not page_content and not image_urls:
            raise ValueError(
                f"URL'den hiçbir veri çıkarılamadı: {url}\n"
                "Lütfen farklı bir ürün linki deneyin."
            )

        # ── ADIM 2: LLM ile structured data extraction ──
        extracted = await asyncio.to_thread(
            self._extract_structured_data, page_content, metadata
        )

        # ── ADIM 3: En iyi görselleri seç ──
        best_images = await asyncio.to_thread(
            self._select_best_images, image_urls
        )

        result = {
            **extracted,
            "best_image_urls": best_images,
            "all_image_urls": image_urls,
            "page_content": page_content[:2000],  # Loglama için kırp
            "extraction_source": source,
        }

        log.info(
            f"URL veri çıkarma tamamlandı: "
            f"marka='{result.get('brand_name', 'N/A')}', "
            f"ürün='{result.get('product_name', 'N/A')}', "
            f"{len(best_images)} referans görsel, "
            f"kaynak={source}"
        )

        return result

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # INTERNAL METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _scrape_url(self, url: str) -> tuple[str, list[str], dict, str]:
        """
        URL'yi scrape eder — Firecrawl birincil, WebScraperService fallback.

        Returns:
            tuple: (page_content, image_urls, metadata, source)
        """
        # ── Firecrawl (birincil) ──
        try:
            result = self.firecrawl.scrape(url)

            if result["success"] and result["markdown"]:
                markdown = result["markdown"]
                metadata = result.get("metadata", {})
                image_urls = self.firecrawl.extract_images_from_markdown(markdown)

                # Metadata'dan ek görseller (og:image vb.)
                og_image = metadata.get("ogImage")
                if og_image and og_image not in image_urls:
                    image_urls.insert(0, og_image)

                log.info(f"Firecrawl başarılı: {len(markdown)} char, "
                         f"{len(image_urls)} görsel")
                return markdown, image_urls, metadata, "firecrawl"

            log.warning(f"Firecrawl başarısız: {result.get('error')} — "
                        f"fallback scraper deneniyor")

        except Exception:
            log.warning("Firecrawl hatası — fallback scraper deneniyor",
                        exc_info=True)

        # ── WebScraperService (fallback) ──
        if self.web_scraper:
            try:
                scrape_result = self.web_scraper.scrape_product_page(url)
                page_text = scrape_result.get("page_text", "")
                images = scrape_result.get("images", [])

                if page_text or images:
                    log.info(f"Fallback scraper başarılı: {len(page_text)} char, "
                             f"{len(images)} görsel")
                    return page_text, images, {}, "scraper"

                log.warning("Fallback scraper de veri döndüremedi")

            except Exception:
                log.warning("Fallback scraper hatası", exc_info=True)

        # Her ikisi de başarısız
        log.error(f"Tüm scraping yöntemleri başarısız: {url}")
        return "", [], {}, "none"

    def _extract_structured_data(self, page_content: str, metadata: dict) -> dict:
        """
        LLM ile sayfa içeriğinden structured ürün verisi çıkarır.

        Args:
            page_content: Markdown veya düz metin sayfa içeriği
            metadata: Firecrawl metadata (title, description vb.)

        Returns:
            dict: Çıkarılan structured veri
        """
        # İçeriği zenginleştir — metadata varsa ekle
        enriched_content = ""
        if metadata:
            if metadata.get("title"):
                enriched_content += f"Sayfa Başlığı: {metadata['title']}\n"
            if metadata.get("description"):
                enriched_content += f"Meta Açıklama: {metadata['description']}\n"
            if metadata.get("sourceURL"):
                enriched_content += f"Kaynak URL: {metadata['sourceURL']}\n"
            enriched_content += "---\n"

        # Sayfa içeriğini kırp (token limiti)
        max_content_length = 6000
        enriched_content += page_content[:max_content_length]

        prompt = EXTRACTION_PROMPT.format(page_content=enriched_content)

        try:
            messages = [
                {"role": "system", "content": "Sen bir JSON çıktı üreten asistansın. Her zaman geçerli JSON döndür."},
                {"role": "user", "content": prompt},
            ]

            result = self.openai.chat_json(messages, max_tokens=1000)

            # Zorunlu alanları doğrula
            required_fields = ["brand_name", "product_name", "ad_concept"]
            for field in required_fields:
                if not result.get(field):
                    log.warning(f"LLM çıkarma: '{field}' alanı boş, "
                                f"metadata'dan doldurulmaya çalışılıyor")
                    if field == "brand_name" and metadata.get("sourceURL"):
                        # Domain'den marka adı çıkar
                        from urllib.parse import urlparse
                        domain = urlparse(metadata["sourceURL"]).netloc
                        domain = domain.replace("www.", "").split(".")[0]
                        result[field] = domain.capitalize()
                    elif field == "product_name" and metadata.get("title"):
                        result[field] = metadata["title"][:50]

            log.info(
                f"LLM structured extraction tamamlandı: "
                f"marka='{result.get('brand_name')}', "
                f"ürün='{result.get('product_name')}'"
            )
            return result

        except Exception:
            log.error("LLM structured extraction hatası", exc_info=True)
            # Minimal fallback — en azından metadata'dan bir şeyler çıkar
            return {
                "brand_name": metadata.get("title", "Bilinmeyen Marka"),
                "product_name": metadata.get("title", "Bilinmeyen Ürün"),
                "product_description": metadata.get("description", ""),
                "ad_concept": "Ürünü keşfet, farkı hisset.",
                "target_audience": "Genel tüketici",
                "product_category": "Genel",
            }

    def _select_best_images(self, image_urls: list[str]) -> list[str]:
        """
        LLM Vision ile en iyi 1-3 ürün görselini seçer.

        Args:
            image_urls: Tüm bulunan görsel URL'leri

        Returns:
            list[str]: Seçilen en iyi 1-3 görsel URL'i
        """
        if not image_urls:
            log.warning("Görsel URL'si bulunamadı — boş liste dönüyor")
            return []

        # URL validasyonu — desteklenmeyen formatları filtrele
        valid_urls = [
            url for url in image_urls
            if self.openai._validate_image_url(url)
        ]

        if not valid_urls:
            log.warning("Geçerli görsel URL'si bulunamadı (format filtresi sonrası)")
            return []

        if len(valid_urls) <= 3:
            log.info(f"3 veya daha az görsel var ({len(valid_urls)}) — hepsi seçildi")
            return valid_urls

        # LLM Vision ile seçim yap (max 10 görsel gönder)
        candidates = valid_urls[:10]

        try:
            # Görsel listesini formatla
            image_list = "\n".join(
                f"[{i}] {url}" for i, url in enumerate(candidates)
            )
            prompt = IMAGE_SELECTION_PROMPT.format(image_list=image_list)

            # Vision API ile görselleri gönder
            content_list = [{"type": "text", "text": prompt}]
            for url in candidates:
                content_list.append({
                    "type": "image_url",
                    "image_url": {"url": url, "detail": "low"},
                })

            messages = [{"role": "user", "content": content_list}]

            response = self.openai.client.chat.completions.create(
                model=self.openai.model,
                messages=messages,
                max_completion_tokens=200,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                log.warning("Vision API boş yanıt döndürdü — ilk 3 görsel kullanılıyor")
                return candidates[:3]

            import json
            result = json.loads(content)
            selected_indices = result.get("selected_indices", [0])

            # İndeksleri doğrula
            selected_urls = []
            for idx in selected_indices:
                if isinstance(idx, int) and 0 <= idx < len(candidates):
                    selected_urls.append(candidates[idx])

            if not selected_urls:
                log.warning("Vision geçersiz indeksler döndürdü — ilk görsel kullanılıyor")
                return [candidates[0]]

            log.info(f"Vision {len(candidates)} görsel arasından "
                     f"{len(selected_urls)} tanesini seçti: "
                     f"indeksler={selected_indices}")
            return selected_urls

        except Exception:
            log.warning("Vision görsel seçim hatası — ilk 3 görsel kullanılıyor",
                        exc_info=True)
            return candidates[:3]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # YARDIMCI METODLAR
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def extract_url_from_text(text: str) -> str | None:
        """
        Metin içinden URL çıkarır.

        Args:
            text: Kullanıcı mesajı

        Returns:
            str | None: Bulunan ilk URL veya None
        """
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        match = re.search(url_pattern, text)
        if match:
            url = match.group(0)
            # Sonundaki noktalama işaretlerini temizle
            url = url.rstrip(".,;:!?)")
            return url
        return None
