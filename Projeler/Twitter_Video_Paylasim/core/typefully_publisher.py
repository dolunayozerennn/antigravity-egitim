"""Typefully üzerinden X (Twitter) video paylaşımı.

Akış:
  1) POST /media/upload → media_id + presigned S3 URL
  2) PUT video binary'sini upload_url'e
  3) Polling: GET /media/{id} → status='ready'
  4) POST /drafts (publish_at='now') → Typefully X paylaşımını tetikler
  5) Polling: GET /drafts/{id} → status='published' → X URL

Free Typefully + Free X API desteklenir; video yükleme limiti Typefully'nin
arka uç X entegrasyonu üzerinden gider.
"""

import os
import time
import mimetypes
from pathlib import Path

import requests

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Video_Paylasim", "TypefullyPublisher")

BASE = "https://api.typefully.com/v2"


class TypefullyError(Exception):
    """Typefully veya S3 upload hatası — pipeline'ı durdurur, sonraki cron'a bırakır.
    Bu hatalar genellikle rate limit, presigned URL süresi, veya geçici servis hatası;
    sıradaki videoyu denemek bandwidth/kota israfıdır.
    """
    pass


class TypefullyRateLimited(TypefullyError):
    """Raised when Typefully API returns 429."""
    pass


class TypefullyPublisher:
    def __init__(self):
        self.api_key = settings.TYPEFULLY_API_KEY
        self.social_set_id = settings.TYPEFULLY_SOCIAL_SET_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _ss_url(self, suffix: str) -> str:
        return f"{BASE}/social-sets/{self.social_set_id}{suffix}"

    def upload_video(self, video_path: str) -> str:
        """Returns media_id (UUID) when ready, empty string on failure."""
        if not video_path or not os.path.exists(video_path):
            ops.error(f"Video bulunamadı: {video_path}")
            return ""

        if settings.IS_DRY_RUN:
            ops.info(f"[DRY-RUN] Typefully media upload atlandı: {video_path}")
            return "dry-run-media-id"

        # Typefully filename pattern: ^[a-zA-Z0-9_.()\-]+\.(jpg|...|mp4|mov|pdf)$
        original = Path(video_path).name
        ext = Path(video_path).suffix.lower()
        if ext not in (".mp4", ".mov"):
            ops.error(f"Desteklenmeyen video uzantısı: {ext}")
            return ""
        # Sanitize file_name to satisfy Typefully regex
        safe_stem = "".join(c if (c.isalnum() or c in "_.()-") else "_" for c in Path(video_path).stem)[:200]
        file_name = f"{safe_stem}{ext}"

        try:
            r = requests.post(
                self._ss_url("/media/upload"),
                headers=self.headers,
                json={"file_name": file_name},
                timeout=20,
            )
            if r.status_code == 429:
                reset = r.headers.get("x-ratelimit-user-reset", "?")
                raise TypefullyRateLimited(f"media/upload rate limit; reset={reset}")
            if r.status_code != 201:
                raise TypefullyError(f"media/upload {r.status_code}: {r.text[:300]}")
            data = r.json()
            media_id = data["media_id"]
            upload_url = data["upload_url"]
        except TypefullyError:
            raise
        except Exception as e:
            raise TypefullyError(f"media/upload exception: {e}") from e

        # PUT raw bytes to S3 presigned URL.
        # Content-Type GÖNDERME — Typefully presigned URL'i Content-Type olmadan imzalıyor;
        # header eklersek SignatureDoesNotMatch alırız.
        try:
            with open(video_path, "rb") as f:
                put = requests.put(upload_url, data=f, timeout=600)
            if put.status_code not in (200, 204):
                raise TypefullyError(f"S3 PUT {put.status_code}: {put.text[:400]}")
            ops.info(f"S3 upload tamam ({Path(video_path).stat().st_size/1024/1024:.1f}MB) media_id={media_id[:8]}…")
        except TypefullyError:
            raise
        except Exception as e:
            raise TypefullyError(f"S3 PUT exception: {e}") from e

        if not self._wait_media_ready(media_id, label="media"):
            raise TypefullyError(f"media {media_id[:8]}… ready olmadı")
        return media_id

    def _wait_media_ready(self, media_id: str, label: str = "media", max_wait: int = 300) -> bool:
        url = self._ss_url(f"/media/{media_id}")
        deadline = time.time() + max_wait
        last_status = ""
        while time.time() < deadline:
            try:
                r = requests.get(url, headers=self.headers, timeout=15)
                r.raise_for_status()
                data = r.json()
                status = data.get("status", "")
                if status != last_status:
                    ops.info(f"{label} status: {status}")
                    last_status = status
                if status == "ready":
                    return True
                if status == "failed":
                    ops.error(f"{label} processing failed: {data.get('error_reason','?')}")
                    return False
            except Exception as e:
                ops.warning(f"{label} polling hatası: {e}")
            time.sleep(5)
        ops.error(f"{label} hazır olmadı ({max_wait}s timeout)")
        return False

    def post_tweet(self, text: str, media_id: str) -> str:
        """Tweet'i Typefully → X kuyruğuna 'şimdi yayınla' olarak gönder.
        Returns tweet permalink URL on success, empty string on failure.
        """
        if settings.IS_DRY_RUN:
            ops.info(f"[DRY-RUN] Typefully draft → 'now' publish: '{text[:80]}…' media={media_id}")
            return "https://x.com/dolunayozeren/status/dry-run"

        payload = {
            "platforms": {
                "x": {
                    "enabled": True,
                    "posts": [{"text": text, "media_ids": [media_id] if media_id else []}],
                }
            },
            "publish_at": "now",
        }
        try:
            r = requests.post(self._ss_url("/drafts"), headers=self.headers, json=payload, timeout=30)
            if r.status_code == 429:
                reset = r.headers.get("x-ratelimit-user-reset", "?")
                raise TypefullyRateLimited(f"draft create rate limit; reset={reset}")
            if r.status_code not in (200, 201):
                raise TypefullyError(f"draft create {r.status_code}: {r.text[:500]}")
            data = r.json()
            draft_id = data.get("id")
            ops.info(f"Draft oluşturuldu (id={draft_id}); 'now' publish bekleniyor")
        except TypefullyError:
            raise
        except Exception as e:
            raise TypefullyError(f"draft create exception: {e}") from e

        # Poll draft until published or error
        return self._wait_draft_published(draft_id) or ""

    def _wait_draft_published(self, draft_id, max_wait: int = 180) -> str:
        url = self._ss_url(f"/drafts/{draft_id}")
        deadline = time.time() + max_wait
        last_status = ""
        while time.time() < deadline:
            try:
                r = requests.get(url, headers=self.headers, timeout=15)
                r.raise_for_status()
                data = r.json()
                # Detect status — schema differs by version; check share_url + scheduled state
                status = (data.get("status") or "").lower()
                # Some draft responses use 'state' or include published flag; try common fields
                if not status:
                    if data.get("published_at"):
                        status = "published"
                    elif data.get("scheduled_date"):
                        status = "scheduled"
                if status != last_status:
                    ops.info(f"draft {draft_id} status: {status or 'unknown'}")
                    last_status = status
                if status == "published":
                    # Typefully draft response top-level: x_published_url
                    x_url = data.get("x_published_url")
                    if x_url:
                        return x_url
                    # fallback: share/private URL
                    return data.get("share_url") or data.get("private_url") or f"typefully://draft/{draft_id}"
                if status in ("error", "failed"):
                    ops.error(f"Draft publish başarısız: {data}")
                    return ""
            except Exception as e:
                ops.warning(f"draft polling hatası: {e}")
            time.sleep(5)
        ops.warning(f"Draft yayınlanma timeout ({max_wait}s) — Typefully arka planda devam edebilir")
        # Don't fail loud — return draft URL as soft success
        return f"typefully://draft/{draft_id}"
