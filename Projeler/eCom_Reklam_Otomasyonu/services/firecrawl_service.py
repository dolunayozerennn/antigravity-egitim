from __future__ import annotations

"""
Firecrawl Service — AI-Powered Web Scraping
=============================================
E-ticaret ürün sayfalarından yapısal veri çekmek için Firecrawl v2 REST API.
SDK kullanmıyoruz — sadece /scrape endpoint'i ile doğrudan requests çağrısı.

Kredi yönetimi:
- Ücretsiz plan: 500 sayfa (one-time)
- 1 kredi/sayfa (/scrape with markdown)
- JSON extraction KULLANILMIYOR (5-9x kredi çarpanından kaçınmak için)
- LLM analizi kendi GPT çağrımızla yapılır
"""

import requests

from logger import get_logger
from utils.retry import RateLimitError, retry_api_call

log = get_logger("firecrawl_service")

FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"
REQUEST_TIMEOUT = 45  # JS-rendered sayfalar biraz daha uzun sürebilir


class FirecrawlService:
    """Firecrawl v2 REST API ile web scraping."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    @retry_api_call(max_retries=2, base_delay=3.0, operation_name="Firecrawl Scrape")
    def scrape(self, url: str) -> dict:
        """
        URL'yi Firecrawl ile scrape eder.

        Markdown + metadata döner. JSON extraction kullanılmaz
        (kredi tasarrufu — analiz kendi LLM'imizle yapılır).

        Args:
            url: Scrape edilecek sayfa URL'i

        Returns:
            dict: {
                "success": bool,
                "markdown": str,        # Sayfa içeriği markdown formatında
                "metadata": dict,       # title, description, sourceURL, vb.
                "error": str | None,    # Hata mesajı (başarısızsa)
            }

        Raises:
            Exception: API hatası (retry sonrası)
        """
        payload = {
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True,
            "timeout": 30000,  # ms — Firecrawl tarafı
        }

        response = requests.post(
            f"{FIRECRAWL_BASE_URL}/scrape",
            headers=self.headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        # Rate limit veya beklenmedik hata
        if response.status_code == 429:
            # Retry-After header parse — saniye veya HTTP-date olabilir, sayı dene
            retry_after_raw = response.headers.get("Retry-After")
            retry_after_seconds: float | None = None
            if retry_after_raw:
                try:
                    retry_after_seconds = float(retry_after_raw)
                except ValueError:
                    log.warning(f"Firecrawl Retry-After parse edilemedi: {retry_after_raw}")
            log.warning(
                f"Firecrawl rate limit — retry edilecek "
                f"(retry_after={retry_after_seconds}s)"
            )
            raise RateLimitError(
                "Firecrawl rate limit aşıldı",
                retry_after=retry_after_seconds,
            )

        if response.status_code == 402:
            log.error("Firecrawl kredi limiti dolmuş (402 Payment Required)")
            return {
                "success": False,
                "markdown": "",
                "metadata": {},
                "error": "Firecrawl kredi limiti dolmuş. Fallback scraper kullanılacak.",
            }

        response.raise_for_status()
        data = response.json()

        if not data.get("success", False):
            error_msg = data.get("error", "Bilinmeyen Firecrawl hatası")
            log.warning(f"Firecrawl scrape başarısız: {url} — {error_msg}")
            return {
                "success": False,
                "markdown": "",
                "metadata": {},
                "error": error_msg,
            }

        # Başarılı yanıt
        fc_data = data.get("data", {})
        markdown = fc_data.get("markdown", "")
        metadata = fc_data.get("metadata", {})

        log.info(
            f"Firecrawl scrape tamamlandı: {url[:60]}... — "
            f"{len(markdown)} karakter markdown, "
            f"title='{metadata.get('title', 'N/A')[:40]}'"
        )

        return {
            "success": True,
            "markdown": markdown,
            "metadata": metadata,
            "error": None,
        }

    def extract_images_from_markdown(self, markdown: str) -> list[str]:
        """
        Firecrawl markdown çıktısından görsel URL'lerini çıkarır.

        Markdown formatındaki görseller: ![alt](url)
        Ayrıca metadata'daki og:image vb. tag'ler de dahil edilir.

        Args:
            markdown: Firecrawl'dan gelen markdown içerik

        Returns:
            list[str]: Bulunan görsel URL'leri (filtrelenmiş)
        """
        import re
        from urllib.parse import urlparse

        # Markdown görselleri: ![...](url)
        pattern = r'!\[.*?\]\((https?://[^\s\)]+)\)'
        raw_urls = re.findall(pattern, markdown)

        # Filtreleme — logo, ikon, placeholder gibi gereksiz görselleri çıkar
        filtered = []
        skip_patterns = [
            "logo", "icon", "favicon", "sprite", "banner", "badge",
            "avatar", "placeholder", "loading", "spinner", "arrow",
            "btn", "button", "social", "payment", "flag", "star",
            "rating", "wishlist", "cart", "search", "menu", "close",
            "1x1", "pixel", "tracking", "analytics",
        ]
        skip_extensions = {".svg", ".ico", ".gif"}

        for url in raw_urls:
            url_lower = url.lower()
            parsed = urlparse(url_lower)
            path = parsed.path

            # Uzantı kontrolü
            if any(path.endswith(ext) for ext in skip_extensions):
                continue

            # Pattern kontrolü
            if any(pattern in url_lower for pattern in skip_patterns):
                continue

            # Çok küçük görselleri atla (URL'de boyut bilgisi varsa)
            if re.search(r'[/_-](16|20|24|32|48)x\1', url_lower):
                continue

            filtered.append(url)

        log.info(f"Markdown'dan {len(raw_urls)} görsel bulundu, "
                 f"{len(filtered)} tanesi filtreden geçti")
        return filtered
