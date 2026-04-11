from ops_logger import get_ops_logger
ops = get_ops_logger("LinkedIn_Video_Paylasim", "VideoProcessor")
import subprocess
import os
import shutil

from config import settings

# Resolve ffmpeg binary path once at module load.
# On Railway/Nixpacks, ffmpeg lives under /root/.nix-profile/bin/ which may
# not be inherited by subprocess child processes. Using the absolute path
# prevents FileNotFoundError at runtime.
_FFMPEG_BIN = shutil.which("ffmpeg") or "ffmpeg"


class VideoProcessor:
    def strip_metadata(self, input_path: str) -> str:
        """
        Takes an MP4 file and uses FFmpeg to strip all metadata.
        Re-encodes the video completely (libx264) to ensure a clean file.
        Returns the path to the stripped file.
        """
        if not input_path or not os.path.exists(input_path):
            ops.error(f"Cannot strip metadata from missing file: {input_path}")
            return None

        dir_name = os.path.dirname(input_path)
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(dir_name, f"{name}_clean{ext}")

        # FFmpeg command using resolved absolute path:
        # -map_metadata -1 : removes global metadata
        # -fflags +bitexact : removes encoder-specific metadata
        # scale=trunc(iw/2)*2:1080 : ensure 1080p output with even-pixel width
        #   (using trunc instead of -2 to avoid errors with odd-dimension sources)
        # Re-encoding with libx264 to strip all TikTok fingerprinting
        ops.info(f"Using ffmpeg binary: {_FFMPEG_BIN}")
        cmd = [
            _FFMPEG_BIN,
            "-y",
            "-i", input_path,
            "-map_metadata", "-1",
            "-fflags", "+bitexact",
            "-vf", "scale=trunc(iw/2)*2:1080",
            "-c:v", "libx264",
            "-crf", "23",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]

        try:
            ops.info(f"Stripping metadata and ensuring 1080p output...")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0 and os.path.exists(output_path):
                file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                ops.info(f"Metadata stripping successful -> {output_path} ({file_size_mb:.1f} MB)")
                return output_path
            else:
                ops.error(f"FFmpeg failed with exit code {result.returncode}.\nSTDERR: {result.stderr[:500]}")
                return None
        except Exception as e:
            ops.error(f"Failed to execute FFmpeg command: {e}", exception=e)
            return None
