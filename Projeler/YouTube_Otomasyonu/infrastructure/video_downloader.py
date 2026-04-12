"""
Video İndirici — Kie AI CDN'den videoyu indirir ve geçici dosyaya kaydeder.
"""
import os
import time
import tempfile
import requests
from config import settings
from logger import get_logger

log = get_logger("VideoDownloader")


def download_video(video_url: str) -> str:
    """
    Video URL'sini indirir ve geçici dosyaya kaydeder.
    
    Args:
        video_url: İndirilecek videonun URL'si veya lokal dosya yolu
                   (FFmpeg merge sonucu lokal yol gelebilir)
        
    Returns:
        str: İndirilen dosyanın yerel yolu
        
    Raises:
        RuntimeError: İndirme başarısız olduğunda
    """
    # FFmpeg fallback'ten lokal dosya yolu gelmiş olabilir — direkt döndür
    if video_url and not video_url.startswith("http") and os.path.exists(video_url):
        log.info(f"📂 Lokal dosya yolu tespit edildi, indirme atlanıyor: {video_url}")
        return video_url

    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: Mock video dosyası oluşturuluyor...")
        # Gerçekçi bir dosya yolu döndür (ama dosya oluşturma)
        mock_path = os.path.join(tempfile.gettempdir(), f"yt_mock_{int(time.time())}.mp4")
        # Boş bir dosya oluştur (test için)
        with open(mock_path, "wb") as f:
            f.write(b"MOCK_VIDEO_DATA")
        log.info(f"   Mock dosya: {mock_path}")
        return mock_path

    timestamp = int(time.time())
    filename = f"yt_automation_{timestamp}.mp4"
    filepath = os.path.join(tempfile.gettempdir(), filename)

    log.info(f"📥 Video indiriliyor: {video_url[:80]}...")

    max_attempts = 3
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(video_url, stream=True, timeout=(10, 120))
            response.raise_for_status()

            # Content-Type doğrulama — HTML error page veya JSON hata body'si olabilir
            content_type = response.headers.get("Content-Type", "")
            if content_type and "video" not in content_type and "octet-stream" not in content_type:
                raise RuntimeError(
                    f"Beklenmeyen Content-Type: {content_type}. "
                    f"Video yerine hata sayfası dönmüş olabilir."
                )

            total_size = 0
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)

            size_mb = total_size / (1024 * 1024)
            log.info(f"✅ Video indirildi: {filepath} ({size_mb:.1f} MB)")

            # Dosya bütünlük kontrolü — 100KB'dan küçükse muhtemelen hatalı
            if total_size < 100_000:
                if os.path.exists(filepath):
                    os.remove(filepath)
                raise RuntimeError(
                    f"İndirilen dosya çok küçük ({total_size} bytes / {size_mb:.2f} MB). "
                    f"Bozuk video veya hata yanıtı olabilir."
                )

            return filepath

        except (requests.RequestException, RuntimeError) as e:
            last_error = e
            # Yarım kalmış dosyayı temizle
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass

            if attempt < max_attempts:
                wait = 2 ** attempt  # 2s, 4s
                log.warning(f"⚠️ Video indirme hatası (deneme {attempt}/{max_attempts}): {e}. {wait}s sonra tekrar...")
                time.sleep(wait)
            else:
                log.error(f"❌ Video indirme başarısız ({max_attempts} deneme): {e}", exc_info=True)

    raise RuntimeError(f"Video indirilemedi ({max_attempts} deneme): {last_error}")


def cleanup_video(filepath: str):
    """İndirilen geçici video dosyasını temizler."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            log.info(f"🗑️ Geçici dosya temizlendi: {filepath}")
    except OSError as e:
        log.warning(f"⚠️ Dosya temizleme hatası: {e}")
