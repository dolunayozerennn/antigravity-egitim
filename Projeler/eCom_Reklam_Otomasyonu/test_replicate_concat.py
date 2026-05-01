"""
Replicate concat_videos format testi.

Ne test eder: video_files parametresinin array (list) olarak gönderildiğini doğrular.
Neden: Replicate API "Expected: array, given: string" 422 hatası geçmişte iki kez
patladı — pipe-joined string gönderilince. Bu test o regression'ı yakalar.

Çalıştırma: python test_replicate_concat.py
"""

import asyncio
import sys
from unittest.mock import MagicMock, patch


FAKE_URLS = [
    "https://example.com/video1.mp4",
    "https://example.com/video2.mp4",
]
FAKE_OUTPUT_URL = "https://replicate.delivery/merged.mp4"


def _make_mock_prediction(output=FAKE_OUTPUT_URL):
    pred = MagicMock()
    pred.id = "test-prediction-id"
    pred.status = "succeeded"
    pred.output = output
    pred.reload = MagicMock()
    return pred


def test_sync_concat_sends_array():
    from services.replicate_service import ReplicateService

    mock_pred = _make_mock_prediction()
    with patch("replicate.Client") as MockClient:
        MockClient.return_value.predictions.create.return_value = mock_pred
        svc = ReplicateService(api_token="fake_token")
        result = svc.concat_videos(FAKE_URLS)

    call_kwargs = MockClient.return_value.predictions.create.call_args
    video_files_arg = call_kwargs.kwargs["input"]["video_files"]

    assert isinstance(video_files_arg, list), (
        f"video_files array olmalı, ama {type(video_files_arg).__name__} geldi: {video_files_arg!r}"
    )
    assert video_files_arg == FAKE_URLS, f"URL listesi yanlış: {video_files_arg}"
    assert result == FAKE_OUTPUT_URL
    print("PASS — sync concat_videos video_files=array ✓")


async def _run_async_concat():
    from services.replicate_service import ReplicateService

    mock_pred = _make_mock_prediction()
    with patch("replicate.Client") as MockClient:
        MockClient.return_value.predictions.create.return_value = mock_pred
        svc = ReplicateService(api_token="fake_token")
        result = await svc.async_concat_videos(FAKE_URLS)
        call_kwargs = MockClient.return_value.predictions.create.call_args

    return result, call_kwargs


def test_async_concat_sends_array():
    result, call_kwargs = asyncio.run(_run_async_concat())

    video_files_arg = call_kwargs.kwargs["input"]["video_files"]

    assert isinstance(video_files_arg, list), (
        f"video_files array olmalı, ama {type(video_files_arg).__name__} geldi: {video_files_arg!r}"
    )
    assert video_files_arg == FAKE_URLS, f"URL listesi yanlış: {video_files_arg}"
    assert result == FAKE_OUTPUT_URL
    print("PASS — async_concat_videos video_files=array ✓")


def test_pipe_string_would_fail():
    """Pipe-joined string'in neden hatalı olduğunu belgeliyen negatif test."""
    pipe_str = "|".join(FAKE_URLS)
    assert isinstance(pipe_str, str), "Beklenen: string"
    assert not isinstance(pipe_str, list), "String, list değil"
    print("PASS — pipe-joined string list DEĞİL (eski hatalı format belgelendi) ✓")


if __name__ == "__main__":
    failed = []
    for test_fn in [test_sync_concat_sends_array, test_async_concat_sends_array, test_pipe_string_would_fail]:
        try:
            test_fn()
        except Exception as e:
            print(f"FAIL — {test_fn.__name__}: {e}")
            failed.append(test_fn.__name__)

    print()
    if failed:
        print(f"❌ {len(failed)} test başarısız: {failed}")
        sys.exit(1)
    else:
        print("✅ Tüm testler geçti.")
