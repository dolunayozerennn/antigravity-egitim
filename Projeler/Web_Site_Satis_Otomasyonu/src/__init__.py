# Web Site Satış Otomasyonu — src package
import sys
import os

# Mono-repo kökünü sys.path'e ekle → _skills.providers import'u için
_mono_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _mono_root not in sys.path:
    sys.path.insert(0, _mono_root)
