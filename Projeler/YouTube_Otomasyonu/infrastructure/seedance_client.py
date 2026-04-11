"""
[DEPRECATED] Bu dosya V2 mimarisinde kullanılmıyor.
Yerine infrastructure/kie_client.py kullanılıyor.
Seedance 2.0 + Veo 3.1 her ikisi de kie_client.py üzerinden yönetilir.
"""
# Geriye uyumluluk için eski import'u yönlendir
from infrastructure.kie_client import KieClient

_client = KieClient()


def create_video(prompt: str) -> str:
    """[DEPRECATED] Geriye uyumluluk wrapper'ı. Yeni kodda KieClient kullanın."""
    import asyncio
    from config import settings
    return asyncio.run(_client.create_video(
        model="seedance-2",
        prompt=prompt,
        orientation="portrait",
        duration=settings.DEFAULT_DURATION,
        audio=settings.DEFAULT_AUDIO,
    ))
