import pytest
import requests

from src.utils.retry import with_retry, ApifyQuotaError, _is_transient


class _FakeResp:
    def __init__(self, status_code):
        self.status_code = status_code


def _make_http_error(status):
    err = requests.HTTPError(f"HTTP {status}")
    err.response = _FakeResp(status)
    return err


def test_is_transient_429():
    assert _is_transient(_make_http_error(429))


def test_is_transient_404_not():
    assert not _is_transient(_make_http_error(404))


def test_is_transient_connection_error():
    assert _is_transient(requests.ConnectionError("boom"))


def test_with_retry_recovers_after_transient(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)  # hızlandır
    calls = {"n": 0}

    @with_retry(attempts=3, base_delay=0.01)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise _make_http_error(503)
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3


def test_with_retry_reraises_non_transient(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)

    @with_retry(attempts=3, base_delay=0.01)
    def bad():
        raise ValueError("permanent")

    with pytest.raises(ValueError):
        bad()


def test_with_retry_custom_transient(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)
    calls = {"n": 0}

    @with_retry(attempts=2, base_delay=0.01, transient_excs=(ApifyQuotaError,))
    def quota():
        calls["n"] += 1
        raise ApifyQuotaError("limit")

    with pytest.raises(ApifyQuotaError):
        quota()
    assert calls["n"] == 2  # retry edildi, sonra fırlattı
