"""
Web Scraper Service — Ürün Fotoğrafı Çekme
=============================================
Verilen URL'den ürün fotoğraflarını çeker.
OG/meta görselleri öncelikli, sonra büyük img tag'leri.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from logger import get_logger

log = get_logger("web_scraper")

# Atlanacak pattern'ler (logo, ikon, izleme pikseli vb.)
SKIP_PATTERNS = [
    "logo", "icon", "favicon", "sprite", "banner",
    "pixel", ".svg", "tracking", "spacer", "1x1",
    "avatar", "badge", "rating", "star", "arrow",
    "cart", "search", "menu", "close", "share",
    "facebook", "twitter", "instagram", "youtube",
    "linkedin", "pinterest", "tiktok", "whatsapp",
]

# OpenAI Vision API tarafından desteklenmeyen görsel formatları
# Bu formatlardaki URL'ler scrape sonuçlarından filtrelenir
UNSUPPORTED_IMAGE_FORMATS = {".avif", ".svg", ".bmp", ".tiff", ".tif", ".ico", ".heic", ".heif"}

REQUEST_TIMEOUT = 15


class WebScraperService:
    """Ürün fotoğrafı scraper — e-ticaret sayfalarından görsel çeker."""

    def __init__(self, timeout: int = REQUEST_TIMEOUT):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
        }

    def scrape_product_data(self, url: str, max_images: int = 5) -> dict:
        """
        URL'den ürün fotoğraflarını ve sayfa metnini çeker.

        Returns:
            dict: {
                "images": list[dict] (url, alt, source),
                "page_text": str (Title, description ve içerik özetleri)
            }
        """
        try:
            resp = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException:
            log.error(f"URL fetch hatası: {url}", exc_info=True)
            return {"images": [], "page_text": ""}

        soup = BeautifulSoup(resp.text, "html.parser")
        
        # ── 0. Sayfa Metnini Çıkar (Title, Meta, Content) ──
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta_desc = (self._get_meta_content(soup, "og:description") or 
                     (soup.find("meta", attrs={"name": "description"}).get("content", "") if soup.find("meta", attrs={"name": "description"}) else ""))
        
        paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
        content_ps = [p for p in paragraphs if len(p) > 40]  # Çok kısa metinleri atla
        main_content = "\n".join(content_ps[:10])  # İlk 10 anlamlı paragrafı al
        
        page_text = f"Title: {title}\nDescription: {meta_desc}\n\nContent:\n{main_content}"
        
        images = []
        seen_urls = set()

        # ── 1. Open Graph image (en güvenilir) ──
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            img_url = self._normalize_url(og_image["content"], url)
            if img_url and img_url not in seen_urls:
                images.append({
                    "url": img_url,
                    "alt": self._get_meta_content(soup, "og:title") or "Ana ürün görseli",
                    "source": "og",
                })
                seen_urls.add(img_url)

        # ── 2. Twitter card image ──
        tc_image = soup.find("meta", attrs={"name": "twitter:image"})
        if not tc_image:
            tc_image = soup.find("meta", attrs={"property": "twitter:image"})
        if tc_image and tc_image.get("content"):
            img_url = self._normalize_url(tc_image["content"], url)
            if img_url and img_url not in seen_urls:
                images.append({
                    "url": img_url,
                    "alt": "Twitter card görseli",
                    "source": "meta",
                })
                seen_urls.add(img_url)

        # ── 3. JSON-LD schema.org product image ──
        import json
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                ld_data = json.loads(script.string or "")
                # Handle arrays
                if isinstance(ld_data, list):
                    for item in ld_data:
                        self._extract_jsonld_images(item, url, images, seen_urls)
                else:
                    self._extract_jsonld_images(ld_data, url, images, seen_urls)
            except (json.JSONDecodeError, TypeError):
                continue

        # ── 4. Content img tags (filtrelenmiş) ──
        for img in soup.find_all("img"):
            src = (
                img.get("src")
                or img.get("data-src")
                or img.get("data-lazy-src")
                or img.get("data-original")
            )
            if not src:
                continue

            img_url = self._normalize_url(src, url)
            if not img_url or img_url in seen_urls:
                continue

            # Skip küçük görseller (ikonlar, badge'ler)
            width = self._parse_dimension(img.get("width"))
            height = self._parse_dimension(img.get("height"))
            if width and width < 150:
                continue
            if height and height < 150:
                continue

            # Skip non-product pattern'ler
            lower_url = img_url.lower()
            if any(p in lower_url for p in SKIP_PATTERNS):
                continue

            alt = img.get("alt", "").strip()
            images.append({
                "url": img_url,
                "alt": alt or "Sayfa görseli",
                "source": "content",
            })
            seen_urls.add(img_url)

        # ── Desteklenmeyen görsel formatlarını filtrele ──
        filtered = []
        for img in images:
            img_path = img["url"].lower().split("?")[0]  # Query parametrelerini kaldır
            if any(img_path.endswith(fmt) for fmt in UNSUPPORTED_IMAGE_FORMATS):
                log.info(f"Desteklenmeyen format filtrelendi: {img['url'][:80]}")
                continue
            filtered.append(img)

        result = filtered[:max_images]
        log.info(f"URL'den {len(result)} ürün fotoğrafı ve metin çıkarıldi. ({len(images) - len(filtered)} filtrelendi): {url[:80]}")
        return {
            "images": result,
            "page_text": page_text
        }

    def scrape_product_images(self, url: str, max_images: int = 5) -> list[dict]:
        """Geriye dönük uyumluluk için sadece images listesi döner."""
        data = self.scrape_product_data(url, max_images)
        return data.get("images", [])

    def _extract_jsonld_images(
        self, data: dict, base_url: str, images: list, seen: set
    ):
        """JSON-LD schema.org verisinden ürün görsellerini çıkar."""
        if not isinstance(data, dict):
            return

        # Product type
        if data.get("@type") in ("Product", "IndividualProduct"):
            img = data.get("image")
            if isinstance(img, str):
                img_list = [img]
            elif isinstance(img, list):
                img_list = [i if isinstance(i, str) else i.get("url", "") for i in img]
            elif isinstance(img, dict):
                img_list = [img.get("url", "")]
            else:
                img_list = []

            for raw_url in img_list:
                norm = self._normalize_url(raw_url, base_url)
                if norm and norm not in seen:
                    images.append({
                        "url": norm,
                        "alt": data.get("name", "Ürün görseli"),
                        "source": "schema",
                    })
                    seen.add(norm)

    @staticmethod
    def _normalize_url(src: str, base_url: str) -> str | None:
        """Relative URL'leri absolute'a çevirir, data URL'leri eler."""
        if not src or src.startswith("data:"):
            return None
        src = src.strip()
        if src.startswith("//"):
            src = "https:" + src
        elif not src.startswith("http"):
            src = urljoin(base_url, src)
        return src

    @staticmethod
    def _parse_dimension(value) -> int | None:
        """Width/height attribute'unu int'e çevirir."""
        if not value:
            return None
        try:
            return int(str(value).replace("px", "").replace("%", "").strip())
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _get_meta_content(soup, property_name: str) -> str:
        """Meta tag'den content çeker."""
        tag = soup.find("meta", property=property_name)
        if tag:
            return tag.get("content", "")
        return ""
