"""Retry & backoff utilities — Apify/Hunter/Gmail/Notion çağrıları için.

`with_retry(...)` decorator'ı geçici hatalar (network, rate limit, 5xx) için
exponential backoff uygular. Custom exception tipleri kalıcı hataları net
şekilde işaretler — pipeline bunları yakalayıp Telegram alert atabilir.
"""

from __future__ import annotations

import functools
import logging
import random
import time
from typing import Callable, Iterable, Type

import requests

logger = logging.getLogger(__name__)


# ── Custom exception types ────────────────────────────────────────────────


class PipelineError(Exception):
    """Pipeline-wide base exception."""


class ApifyQuotaError(PipelineError):
    """Tüm Apify token'ları quota/rate limit yedi."""


class HunterRateLimitError(PipelineError):
    """Hunter.io rate limit (429)."""


class GmailQuotaError(PipelineError):
    """Gmail API daily quota aşıldı / auth invalid."""


class NotionUnavailableError(PipelineError):
    """Notion API erişilemez (5xx, network)."""


# ── Decorator ─────────────────────────────────────────────────────────────

# Geçici sayılan HTTP statü kodları
TRANSIENT_STATUS = {408, 425, 429, 500, 502, 503, 504}


def _is_transient(exc: BaseException) -> bool:
    """Exception geçici (yeniden denenebilir) mi?"""
    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return True
    if isinstance(exc, requests.HTTPError):
        resp = getattr(exc, "response", None)
        if resp is not None and resp.status_code in TRANSIENT_STATUS:
            return True
    return False


def with_retry(
    *,
    attempts: int = 4,
    base_delay: float = 1.5,
    max_delay: float = 30.0,
    transient_excs: Iterable[Type[BaseException]] = (),
):
    """Exponential backoff decorator.

    Args:
        attempts: toplam deneme sayısı (ilk deneme dahil).
        base_delay: ilk bekleme (saniye).
        max_delay: bekleme tavanı.
        transient_excs: geçici sayılacak ek exception sınıfları.

    Yalnızca `_is_transient` veya `transient_excs` ile eşleşen hatalar
    yeniden denenir; diğer hatalar olduğu gibi yükseltilir.
    """

    def deco(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: BaseException | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    transient = _is_transient(e) or isinstance(e, tuple(transient_excs))
                    if not transient or attempt == attempts:
                        raise
                    delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
                    delay += random.uniform(0, delay * 0.25)  # jitter
                    logger.warning(
                        "[retry] %s attempt %d/%d failed (%s); sleeping %.1fs",
                        func.__name__, attempt, attempts, e, delay,
                    )
                    time.sleep(delay)
            assert last_exc is not None
            raise last_exc

        return wrapper

    return deco
