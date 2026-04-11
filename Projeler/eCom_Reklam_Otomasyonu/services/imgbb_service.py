"""
ImgBB Service — Görsel Hosting
================================
Telegram'dan gelen görselleri ImgBB'ye yükler.
Kie AI ve diğer servislerin erişebileceği public URL döndürür.
"""

import base64

import requests

from logger import get_logger

log = get_logger("imgbb_service")

IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"
REQUEST_TIMEOUT = 30


class ImgBBService:
    """ImgBB görsel hosting servisi."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def upload_image_bytes(self, image_bytes: bytes, name: str = "product") -> dict:
        """
        Ham image bytes'ı ImgBB'ye yükler.

        Args:
            image_bytes: Raw image data
            name: Görsel adı (opsiyonel)

        Returns:
            dict: {"url": "https://...", "delete_url": "https://...", "size": 123456}

        Raises:
            Exception: Yükleme başarısız olursa
        """
        try:
            b64 = base64.b64encode(image_bytes).decode("utf-8")

            payload = {
                "key": self.api_key,
                "image": b64,
                "name": name,
            }

            response = requests.post(
                IMGBB_UPLOAD_URL,
                data=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()
            if not data.get("success"):
                raise ValueError(f"ImgBB upload failed: {data}")

            result = {
                "url": data["data"]["url"],
                "display_url": data["data"]["display_url"],
                "delete_url": data["data"]["delete_url"],
                "size": data["data"]["size"],
            }

            log.info(f"ImgBB upload başarılı: {result['url']} ({result['size']} bytes)")
            return result

        except requests.exceptions.Timeout:
            log.error("ImgBB upload timeout")
            raise
        except Exception:
            log.error("ImgBB upload hatası", exc_info=True)
            raise

    def upload_image_url(self, image_url: str, name: str = "product") -> dict:
        """
        URL'deki görseli ImgBB'ye yükler.

        Args:
            image_url: Kaynak görsel URL'i
            name: Görsel adı

        Returns:
            dict: {"url": "...", "display_url": "...", "delete_url": "...", "size": ...}
        """
        try:
            payload = {
                "key": self.api_key,
                "image": image_url,
                "name": name,
            }

            response = requests.post(
                IMGBB_UPLOAD_URL,
                data=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()
            if not data.get("success"):
                raise ValueError(f"ImgBB URL upload failed: {data}")

            result = {
                "url": data["data"]["url"],
                "display_url": data["data"]["display_url"],
                "delete_url": data["data"]["delete_url"],
                "size": data["data"]["size"],
            }

            log.info(f"ImgBB URL upload başarılı: {result['url']}")
            return result

        except Exception:
            log.error("ImgBB URL upload hatası", exc_info=True)
            raise
