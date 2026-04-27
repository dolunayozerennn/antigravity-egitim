"""
LinkedIn API ile metin + görsel post paylaşma.
n8n'deki "Create a post" node'unun birebir karşılığı.
Görsel paylaşım için Images API (registerUpload + upload + post) kullanır.
"""
from ops_logger import get_ops_logger
ops = get_ops_logger("LinkedIn_Text_Paylasim", "LinkedinPublisher")
import requests
import os

from config import settings


class LinkedInPublisher:
    """LinkedIn'e metin + görsel post paylaşır."""

    API_BASE = "https://api.linkedin.com"

    def __init__(self):
        self.access_token = settings.LINKEDIN_ACCESS_TOKEN
        self.person_urn = settings.LINKEDIN_PERSON_URN
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": "202503",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def create_text_image_post(self, text: str, image_path: str = None) -> str:
        """
        LinkedIn'e metin + görsel post atar.
        n8n'de shareMediaCategory: "IMAGE" olarak ayarlanmış.

        Args:
            text: Post metni
            image_path: Görsel dosya yolu (None ise sadece metin post)

        Returns: Post URN veya None
        """
        if settings.IS_DRY_RUN:
            ops.info(f"[DRY-RUN] LinkedIn post atlanıyor: '{text[:80]}...'")
            return "urn:li:share:mock_post_dry_run"

        # Görsel varsa önce yükle
        image_urn = None
        if image_path and os.path.exists(image_path):
            image_urn = self._upload_image(image_path)
            if not image_urn:
                ops.warning("Görsel yüklenemedi, sadece metin post atılacak.")

        # Post oluştur
        return self._create_post(text, image_urn)

    def _upload_image(self, image_path: str) -> str:
        """
        Görseli LinkedIn'e yükler ve image URN döndürür.
        Yeni LinkedIn Images API (initializeUpload + binary upload).
        Dönen URN formatı: urn:li:image:... (rest/posts API ile uyumlu).
        """
        try:
            # Step 1: Initialize Upload (yeni Images API)
            init_url = f"{self.API_BASE}/rest/images?action=initializeUpload"
            init_payload = {
                "initializeUploadRequest": {
                    "owner": self.person_urn
                }
            }

            resp = requests.post(init_url, headers=self.headers, json=init_payload, timeout=30)
            if resp.status_code not in (200, 201):
                ops.error("Görsel Upload Init Hatası", message=f"HTTP {resp.status_code} — {resp.text[:500]}")
                return None

            data = resp.json()
            upload_url = data["value"]["uploadUrl"]
            image_urn = data["value"]["image"]

            ops.info("Görsel Upload Init", f"Image URN: {image_urn}")

            # Step 2: Upload binary
            upload_headers = {
                "Authorization": f"Bearer {self.access_token}",
            }

            with open(image_path, "rb") as f:
                image_data = f.read()

            resp = requests.put(upload_url, headers=upload_headers, data=image_data, timeout=60)
            if resp.status_code not in (200, 201):
                ops.error("Görsel Yükleme Hatası", message=f"HTTP {resp.status_code} — {resp.text[:500]}")
                return None

            ops.info("Görsel Yüklendi", f"{image_urn} ({len(image_data)} bytes)")
            return image_urn

        except Exception as e:
            ops.error("LinkedIn Görsel Yükleme Hatası", exception=e, message=str(e)[:500])
            return None

    def _create_post(self, text: str, image_urn: str = None) -> str:
        """
        LinkedIn post oluşturur (metin veya metin+görsel).
        rest/posts API — image_urn formatı: urn:li:image:... (yeni Images API'den).
        """
        url = f"{self.API_BASE}/rest/posts"

        payload = {
            "author": self.person_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }

        # Görsel varsa content ekle (urn:li:image:... formatı)
        if image_urn:
            payload["content"] = {
                "media": {
                    "id": image_urn,
                }
            }

        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
            if resp.status_code in (200, 201):
                post_urn = resp.headers.get("x-restli-id", "")
                if not post_urn:
                    data = resp.json() if resp.text else {}
                    post_urn = data.get("id", "unknown")

                ops.info("LinkedIn Post Başarılı", f"URN: {post_urn} | Görsel: {'var' if image_urn else 'yok'}")
                return post_urn
            else:
                # Detaylı hata logla — HTTP kodu + tam yanıt body'si
                error_body = resp.text[:800] if resp.text else "(boş yanıt)"
                ops.error(
                    "LinkedIn Post Oluşturma Hatası",
                    message=f"HTTP {resp.status_code} | Author: {self.person_urn} | Image: {image_urn or 'yok'} | Body: {error_body}"
                )
                return None
        except Exception as e:
            ops.error("LinkedIn Post Hatası", exception=e, message=str(e)[:500])
            return None
