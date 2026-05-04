"""Typefully Draft Publisher (text + image draft).

X (Twitter) için Typefully'ye **draft** olarak post oluşturur — otomatik yayınlamaz.
Dolunay Typefully UI'da inceleyip onaylar.

Akış:
  - Tek tweet:   POST /v2/social-sets/{ss}/drafts  (publish_at YOK → draft)
  - Thread:      Aynı endpoint, posts: [tweet1, tweet2, ...]
  - Görselli:    Önce /media/upload → S3 PUT → polling, sonra draft create
"""

import os
import time
import mimetypes
from pathlib import Path

import requests

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "TypefullyPublisher")

BASE = "https://api.typefully.com/v2"


class TypefullyDraftError(Exception):
    pass


class TypefullyDraftPublisher:
    def __init__(self):
        self.api_key = settings.TYPEFULLY_API_KEY
        self.social_set_id = settings.TYPEFULLY_SOCIAL_SET_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _ss_url(self, suffix: str) -> str:
        return f"{BASE}/social-sets/{self.social_set_id}{suffix}"

    def create_single_draft(self, text: str) -> dict:
        """Tek tweet draft'ı. Returns {draft_id, share_url} on success, raises on failure."""
        return self._create_draft([{"text": text}])

    def create_thread_draft(self, tweets: list[str]) -> dict:
        """Thread draft'ı (5-7 tweet). Returns {draft_id, share_url}."""
        if not tweets:
            raise TypefullyDraftError("Boş thread")
        posts = [{"text": t} for t in tweets if t and t.strip()]
        return self._create_draft(posts)

    def create_single_draft_with_image(self, text: str, image_path: str) -> dict:
        """Görselli tek tweet draft'ı. Görsel yoksa text-only fallback."""
        if not image_path or not os.path.exists(image_path):
            ops.warning("Görsel bulunamadı, text-only draft'a dönülüyor")
            return self.create_single_draft(text)
        media_id = self._upload_image(image_path)
        if not media_id:
            ops.warning("Görsel upload başarısız, text-only draft'a dönülüyor")
            return self.create_single_draft(text)
        return self._create_draft([{"text": text, "media_ids": [media_id]}])

    def _upload_image(self, image_path: str) -> str:
        """JPG/PNG upload → media_id (Twitter_Video_Paylasim publisher patternı)."""
        if settings.IS_DRY_RUN:
            ops.info("[DRY-RUN] Görsel upload atlandı")
            return "dry-run-media"

        ext = Path(image_path).suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png"):
            ops.error(f"Desteklenmeyen görsel uzantısı: {ext}")
            return ""
        safe_stem = "".join(c if (c.isalnum() or c in "_.()-") else "_"
                            for c in Path(image_path).stem)[:200]
        file_name = f"{safe_stem}{ext}"
        try:
            r = requests.post(self._ss_url("/media/upload"), headers=self.headers,
                              json={"file_name": file_name}, timeout=20)
            if r.status_code != 201:
                ops.error(f"media/upload {r.status_code}: {r.text[:300]}")
                return ""
            data = r.json()
            media_id = data["media_id"]
            upload_url = data["upload_url"]
        except Exception as e:
            ops.error("media/upload exception", exception=e)
            return ""

        try:
            with open(image_path, "rb") as f:
                put = requests.put(upload_url, data=f, timeout=120)
            if put.status_code not in (200, 204):
                ops.error(f"S3 PUT {put.status_code}: {put.text[:300]}")
                return ""
        except Exception as e:
            ops.error("S3 PUT exception", exception=e)
            return ""

        # Polling
        poll = self._ss_url(f"/media/{media_id}")
        deadline = time.time() + 120
        while time.time() < deadline:
            try:
                pr = requests.get(poll, headers=self.headers, timeout=15)
                pr.raise_for_status()
                pd = pr.json()
                status = pd.get("status", "")
                if status == "ready":
                    return media_id
                if status == "failed":
                    ops.error(f"media processing failed: {pd.get('error_reason','?')}")
                    return ""
            except Exception as e:
                ops.warning(f"media polling: {e}")
            time.sleep(3)
        ops.error("media ready olmadı (120s)")
        return ""

    def _create_draft(self, posts: list[dict]) -> dict:
        if settings.IS_DRY_RUN:
            ops.info("[DRY-RUN] Draft create atlandı", f"{len(posts)} post(s)")
            return {"draft_id": "dry-run", "share_url": "https://typefully.com/dry-run"}

        payload = {
            "platforms": {
                "x": {
                    "enabled": True,
                    "posts": posts,
                }
            },
            # publish_at GİRİLMİYOR → Typefully draft olarak tutuyor
        }
        try:
            r = requests.post(
                self._ss_url("/drafts"),
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            if r.status_code == 429:
                raise TypefullyDraftError(f"Rate limit; reset={r.headers.get('x-ratelimit-user-reset','?')}")
            if r.status_code not in (200, 201):
                raise TypefullyDraftError(f"draft create {r.status_code}: {r.text[:500]}")
            data = r.json()
            draft_id = data.get("id")
            share_url = data.get("share_url") or data.get("private_url") or f"typefully://draft/{draft_id}"
            ops.info("Draft oluşturuldu", f"id={draft_id}, posts={len(posts)}, url={share_url}")
            return {"draft_id": draft_id, "share_url": share_url}
        except TypefullyDraftError:
            raise
        except Exception as e:
            ops.error("draft create exception", exception=e)
            raise TypefullyDraftError(str(e))
