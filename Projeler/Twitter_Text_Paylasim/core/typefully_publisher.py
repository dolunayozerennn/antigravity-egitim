"""Typefully Draft Publisher (text-only).

X (Twitter) için Typefully'ye **draft** olarak post oluşturur — otomatik yayınlamaz.
Dolunay Typefully UI'da inceleyip onaylar.

Pro plan ileride aktif olunca aynı endpoint çalışır; draft mode için Pro şart değil
(Free Typefully de draft oluşturur, sadece zamanlanmış otomatik yayın için Pro lazım).

Akış:
  - Tek tweet:   POST /v2/social-sets/{ss}/drafts  (publish_at YOK → draft)
  - Thread:      Aynı endpoint, posts: [tweet1, tweet2, ...] olarak gönderilir
"""

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
