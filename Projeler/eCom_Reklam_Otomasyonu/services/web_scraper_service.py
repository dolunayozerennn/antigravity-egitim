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

    def scrape_product_images(self, url: str, max_images: int = 5) -> list[dict]:
        """
        URL'den ürün fotoğraflarını çeker.

        Öncelik sırası:
        1. OG (Open Graph) görseli
        2. Twitter card görseli
        3. JSON-LD schema.org product image
        4. İçerikteki büyük img tag'leri

        Args:
            url: Ürün sayfası URL'i
            max_images: Maximum döndürülecek görsel sayısı

        Returns:
            list[dict]: [{"url": "...", "alt": "...", "source": "og|meta|content"}]
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
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
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

        result = images[:max_images]
        log.info(f"URL'den {len(result)} ürün fotoğrafı bulundu: {url[:80]}")
        return result

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
