"""Master kaliteyi koru: default-OFF reencode; sadece faststart remux (kayıpsız)."""

import os
import shutil
import subprocess
from pathlib import Path

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Video_Paylasim", "VideoProcessor")

_FFMPEG_BIN = shutil.which("ffmpeg") or "ffmpeg"


class VideoProcessor:
    def prepare_for_upload(self, input_path: str) -> str:
        if not input_path or not os.path.exists(input_path):
            ops.error(f"Dosya bulunamadı: {input_path}")
            return ""

        size_bytes = os.path.getsize(input_path)
        size_mb = size_bytes / (1024 * 1024)

        if settings.REENCODE_OVER_BYTES and size_bytes > settings.REENCODE_OVER_BYTES:
            ops.warning(f"Dosya {size_mb:.0f}MB > eşik — minimal compress")
            compressed = self._compress(input_path)
            return compressed or input_path

        remuxed = self._faststart_remux(input_path)
        return remuxed or input_path

    def _faststart_remux(self, input_path: str) -> str:
        p = Path(input_path)
        out = p.with_name(f"{p.stem}_fs{p.suffix}")
        cmd = [_FFMPEG_BIN, "-y", "-i", input_path, "-c", "copy", "-movflags", "+faststart", str(out)]
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if r.returncode == 0 and out.exists() and out.stat().st_size > 0:
                ops.info(f"Faststart remux tamam: {out.name}")
                return str(out)
            ops.warning(f"Faststart remux başarısız (code={r.returncode}); orijinal kullanılacak")
        except Exception as e:
            ops.warning(f"Faststart remux exception: {e}; orijinal kullanılacak")
        return ""

    def _compress(self, input_path: str) -> str:
        p = Path(input_path)
        out = p.with_name(f"{p.stem}_compressed{p.suffix}")
        cmd = [
            _FFMPEG_BIN, "-y", "-i", input_path,
            "-c:v", "libx264", "-crf", "20", "-preset", "slow",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(out),
        ]
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if r.returncode == 0 and out.exists() and out.stat().st_size > 0:
                ops.info(f"Compress tamam: {out.name} ({out.stat().st_size/1024/1024:.1f}MB)")
                return str(out)
            ops.error(f"Compress başarısız: {r.stderr[:500]}")
        except Exception as e:
            ops.error(f"Compress exception: {e}", exception=e)
        return ""
