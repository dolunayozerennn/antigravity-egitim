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
        video_url: İndirilecek videonun URL'si
        
    Returns:
        str: İndirilen dosyanın yerel yolu
        
    Raises:
        RuntimeError: İndirme başarısız olduğunda
    """
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

    try:
        response = requests.get(video_url, stream=True, timeout=120)
        response.raise_for_status()

        total_size = 0
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)

        size_mb = total_size / (1024 * 1024)
        log.info(f"✅ Video indirildi: {filepath} ({size_mb:.1f} MB)")

        # Dosya bütünlük kontrolü
        if total_size < 10000:  # 10KB'dan küçükse muhtemelen hatalı
            log.warning(f"⚠️ İndirilen dosya çok küçük ({total_size} bytes). Bozuk olabilir!")

        return filepath

    except requests.RequestException as e:
        log.error(f"❌ Video indirme hatası: {e}", exc_info=True)
        # Yarım kalmış dosyayı temizle
        if os.path.exists(filepath):
            os.remove(filepath)
        raise RuntimeError(f"Video indirilemedi: {e}")


def cleanup_video(filepath: str):
    """İndirilen geçici video dosyasını temizler."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            log.info(f"🗑️ Geçici dosya temizlendi: {filepath}")
    except OSError as e:
        log.warning(f"⚠️ Dosya temizleme hatası: {e}")
