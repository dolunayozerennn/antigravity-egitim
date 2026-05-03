"""
Türkçe TTS için sayı/yüzde/birim normalizasyonu.

ElevenLabs voiceover'ından önce çağrılır — "10%" → "yüzde on", "30 ml" → "otuz mililitre".
LLM'in senaryo prompt'undaki "rakam yazma" kuralını ihlal ettiği durumlar için safety net.

Marka adı whitelist: bilinen ürün isimlerinde rakam korunur (Air Force 1, AirPods Pro, iPhone 15).
Bu marka isimleri zaten İngilizce/orijinal okunduğu için TTS doğru telaffuz eder.
"""

from __future__ import annotations

import re
from num2words import num2words


_BRAND_PROTECTED_PATTERNS = [
    r"Air\s*Force\s*\d+",
    r"AirPods\s*\w*",
    r"iPhone\s*\d+\s*\w*",
    r"PlayStation\s*\d+",
    r"Galaxy\s*S\d+",
    r"MacBook\s*\w*",
]

_UNIT_MAP = {
    "ml": "mililitre",
    "ML": "mililitre",
    "Ml": "mililitre",
    "g": "gram",
    "gr": "gram",
    "kg": "kilogram",
    "L": "litre",
    "l": "litre",
    "cm": "santimetre",
    "mm": "milimetre",
    "m": "metre",
    "saat": "saat",
    "dk": "dakika",
    "sn": "saniye",
}


def _tr_number(n: int) -> str:
    """Tam sayıyı Türkçe yazıyla döndür."""
    return num2words(n, lang="tr")


def _tr_decimal(s: str) -> str:
    """'2.5' veya '2,5' → 'iki nokta beş'."""
    s = s.replace(",", ".")
    if "." in s:
        whole, frac = s.split(".", 1)
        return f"{_tr_number(int(whole))} nokta {_tr_number(int(frac))}"
    return _tr_number(int(s))


def _protect_brands(text: str) -> tuple[str, list[str]]:
    """Marka pattern'lerini placeholder ile değiştirip listede sakla."""
    protected = []
    for pat in _BRAND_PROTECTED_PATTERNS:
        for m in re.finditer(pat, text):
            placeholder = f"__BRAND_{len(protected)}__"
            protected.append(m.group(0))
            text = text.replace(m.group(0), placeholder, 1)
    return text, protected


def _restore_brands(text: str, protected: list[str]) -> str:
    for i, original in enumerate(protected):
        text = text.replace(f"__BRAND_{i}__", original)
    return text


def normalize_for_tts(text: str) -> str:
    """
    Voiceover metnindeki rakam/yüzde/birim kombinasyonlarını Türkçe okumaya çevir.

    Örnekler:
        "%10 indirim" → "yüzde on indirim"
        "10%" → "yüzde on"
        "30 ml serum" → "otuz mililitre serum"
        "2.5 saat şarj" → "iki nokta beş saat şarj"
        "Air Force 1 ile" → "Air Force 1 ile" (marka korunur)
    """
    if not text:
        return text

    text, protected = _protect_brands(text)

    # Yüzde: "%10" veya "10%"
    text = re.sub(
        r"%\s*(\d+(?:[.,]\d+)?)",
        lambda m: f"yüzde {_tr_decimal(m.group(1))}",
        text,
    )
    text = re.sub(
        r"(\d+(?:[.,]\d+)?)\s*%",
        lambda m: f"yüzde {_tr_decimal(m.group(1))}",
        text,
    )

    # Sayı + birim: "30 ml", "2.5 saat"
    unit_pattern = "|".join(re.escape(u) for u in _UNIT_MAP.keys())
    text = re.sub(
        rf"(\d+(?:[.,]\d+)?)\s*({unit_pattern})\b",
        lambda m: f"{_tr_decimal(m.group(1))} {_UNIT_MAP[m.group(2)]}",
        text,
    )

    # Geriye kalan çıplak sayılar (1-9999): yalnızca rakam yazılmışsa
    text = re.sub(
        r"\b(\d+(?:[.,]\d+)?)\b",
        lambda m: _tr_decimal(m.group(1)),
        text,
    )

    text = _restore_brands(text, protected)
    return text
