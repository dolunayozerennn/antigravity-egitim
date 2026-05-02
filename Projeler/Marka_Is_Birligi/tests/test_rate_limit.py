import time

import pytest

from src.utils.rate_limit import TokenBucket


def test_capacity_allows_burst():
    b = TokenBucket(rate_per_sec=1, capacity=3)
    start = time.monotonic()
    for _ in range(3):
        b.acquire()
    elapsed = time.monotonic() - start
    # Üç token zaten dolu — neredeyse anlık.
    assert elapsed < 0.05


def test_blocks_when_empty():
    b = TokenBucket(rate_per_sec=10, capacity=1)
    b.acquire()  # token tüketildi
    start = time.monotonic()
    b.acquire()
    elapsed = time.monotonic() - start
    # 10/s rate → ikinci token ~0.1s sonra hazır.
    assert 0.05 < elapsed < 0.25


def test_invalid_rate():
    with pytest.raises(ValueError):
        TokenBucket(rate_per_sec=0)


def test_request_exceeding_capacity():
    b = TokenBucket(rate_per_sec=1, capacity=2)
    with pytest.raises(ValueError):
        b.acquire(tokens=5)
