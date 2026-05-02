"""Token bucket rate limiter — thread-safe, minimal.

Kullanım:
    bucket = TokenBucket(rate_per_sec=3, capacity=5)
    bucket.acquire()  # 1 token tüketir, gerekirse bekler
"""

from __future__ import annotations

import threading
import time


class TokenBucket:
    """Klasik token bucket: saniyede `rate_per_sec` token üretir,
    `capacity` kadarını biriktirir.

    `acquire(n)` istenen tokenları alır, yetmezse uykuya yatar.
    Birden fazla thread'den güvenle çağrılabilir.
    """

    def __init__(self, rate_per_sec: float, capacity: float | None = None):
        if rate_per_sec <= 0:
            raise ValueError("rate_per_sec must be > 0")
        self.rate = float(rate_per_sec)
        self.capacity = float(capacity if capacity is not None else max(1.0, rate_per_sec))
        self._tokens = self.capacity
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def _refill_locked(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._last = now

    def acquire(self, tokens: float = 1.0) -> None:
        if tokens > self.capacity:
            raise ValueError("requested tokens exceed bucket capacity")
        while True:
            with self._lock:
                self._refill_locked()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                deficit = tokens - self._tokens
                wait = deficit / self.rate
            time.sleep(wait)


# ── Servis-bazlı paylaşımlı bucket'lar ────────────────────────────────────
# Notion: resmi limit ~3 req/s; biraz emniyetli kalalım.
notion_bucket = TokenBucket(rate_per_sec=2.5, capacity=5)
# Gmail send: günlük 500 quota; pratik bir burst koruması için saniyede 1.
gmail_bucket = TokenBucket(rate_per_sec=1.0, capacity=2)
