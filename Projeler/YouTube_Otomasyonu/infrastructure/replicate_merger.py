"""
Replicate Video Merger — Çoklu klipleri birleştirir.
Birincil: Replicate lucataco/video-merge API
Fallback: FFmpeg local birleştirme
"""
import os
import json
import asyncio
import tempfile
import logging
import shutil
import httpx
from config import settings

log = logging.getLogger("ReplicateMerger")

# FFmpeg absolute path — Nixpacks PATH kaybı sorununu önler
_FFMPEG_BIN = shutil.which("ffmpeg") or "ffmpeg"


async def merge_videos(video_urls: list[str], keep_audio: bool = True) -> str:
    """
    Video URL'lerini birleştirir.
    Önce Replicate API, başarısız olursa FFmpeg fallback.

    Args:
        video_urls: CDN video URL'leri listesi (en az 2)
        keep_audio: Sesi koru

    Returns:
        str: Birleşmiş video URL'si (veya lokal dosya yolu)
    """
    if len(video_urls) < 2:
        log.info("📎 Tek video — birleştirme gereksiz.")
        return video_urls[0]

    if settings.IS_DRY_RUN:
        log.info(f"🧪 DRY-RUN: {len(video_urls)} video birleştirme simülasyonu...")
        await asyncio.sleep(2)
        return "https://cdn.example.com/dry-run-merged.mp4"

    log.info(f"🎞️ {len(video_urls)} video birleştiriliyor (Replicate)...")

    try:
        merged_url = await _merge_via_replicate(video_urls, keep_audio)
        log.info(f"✅ Replicate merge başarılı: {merged_url[:80]}...")
        return merged_url
    except Exception as e:
        log.warning(f"⚠️ Replicate merge başarısız: {e}. FFmpeg fallback deneniyor...")

    try:
        merged_path = await _merge_via_ffmpeg(video_urls)
        log.info(f"✅ FFmpeg merge başarılı: {merged_path}")
        return merged_path
    except Exception as e:
        log.error(f"❌ FFmpeg merge de başarısız: {e}", exc_info=True)
        raise RuntimeError(f"Video birleştirme tamamen başarısız. Replicate ve FFmpeg ikisi de hata verdi.")


async def _merge_via_replicate(video_urls: list[str], keep_audio: bool) -> str:
    """Replicate lucataco/video-merge API ile birleştirme."""
    api_url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Bearer {settings.REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "version": settings.REPLICATE_MERGE_VERSION,
        "input": {
            "video_files": video_urls,
            "keep_audio": keep_audio,
        },
    }

    # ── Task oluştur ──
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(api_url, json=payload, headers=headers)

    if response.status_code != 201:
        raise RuntimeError(f"Replicate task oluşturma hatası: {response.status_code} — {response.text[:200]}")

    prediction = response.json()
    prediction_id = prediction.get("id")
    poll_url = prediction.get("urls", {}).get("get", f"{api_url}/{prediction_id}")

    log.info(f"📋 Replicate prediction oluşturuldu: {prediction_id}")

    # ── Polling ──
    for attempt in range(1, 61):
        await asyncio.sleep(10)

        async with httpx.AsyncClient(timeout=30) as client:
            poll_resp = await client.get(poll_url, headers=headers)

        poll_data = poll_resp.json()
        status = poll_data.get("status", "unknown")

        if status == "succeeded":
            output = poll_data.get("output")
            if isinstance(output, str):
                return output
            elif isinstance(output, list) and output:
                return output[0]
            else:
                raise RuntimeError(f"Replicate output formatı beklenmiyor: {output}")

        elif status == "failed":
            error = poll_data.get("error", "Bilinmeyen hata")
            raise RuntimeError(f"Replicate merge başarısız: {error}")

        elif status == "canceled":
            raise RuntimeError("Replicate merge iptal edildi")

        else:
            log.info(f"   [{attempt}/60] Replicate durum: {status}...")

    raise RuntimeError("Replicate merge zaman aşımı (60 deneme)")


async def _merge_via_ffmpeg(video_urls: list[str]) -> str:
    """FFmpeg ile lokal birleştirme — Replicate başarısız olursa fallback."""
    import time

    # Videoları indir
    temp_files = []
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            for i, url in enumerate(video_urls):
                log.info(f"   📥 Video {i+1}/{len(video_urls)} indiriliyor (streaming)...")

                temp_path = os.path.join(tempfile.gettempdir(), f"merge_input_{i}_{int(time.time())}.mp4")
                async with client.stream("GET", url) as resp:
                    resp.raise_for_status()
                    with open(temp_path, "wb") as f:
                        async for chunk in resp.aiter_bytes(chunk_size=65536):
                            f.write(chunk)
                temp_files.append(temp_path)

        # concat file oluştur
        concat_path = os.path.join(tempfile.gettempdir(), f"concat_{int(time.time())}.txt")
        with open(concat_path, "w") as f:
            for path in temp_files:
                f.write(f"file '{path}'\n")

        # FFmpeg ile birleştir
        output_path = os.path.join(tempfile.gettempdir(), f"merged_{int(time.time())}.mp4")

        cmd = f'{_FFMPEG_BIN} -f concat -safe 0 -i "{concat_path}" -c copy -y "{output_path}"'
        log.info(f"   🎞️ FFmpeg çalıştırılıyor: {_FFMPEG_BIN}")

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg hatası (rc={proc.returncode}): {stderr.decode()[:500]}")

        # concat dosyasını temizle
        if os.path.exists(concat_path):
            os.remove(concat_path)

        return output_path

    finally:
        # Temp input dosyalarını temizle
        for path in temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
