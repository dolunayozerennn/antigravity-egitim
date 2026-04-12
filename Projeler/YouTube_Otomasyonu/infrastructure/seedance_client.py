"""
[DEPRECATED] Bu dosya V2 mimarisinde kullanılmıyor.
Yerine infrastructure/kie_client.py kullanılıyor.
Seedance 2.0 + Veo 3.1 her ikisi de kie_client.py üzerinden yönetilir.
"""
import warnings

warnings.warn(
    "seedance_client.py DEPRECATED. Yerine infrastructure/kie_client.py kullanın.",
    DeprecationWarning,
    stacklevel=2,
)

# Geriye uyumluluk — sadece import yönlendirmesi
from infrastructure.kie_client import KieClient  # noqa: F401
