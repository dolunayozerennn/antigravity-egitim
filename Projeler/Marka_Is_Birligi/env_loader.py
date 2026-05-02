"""env_loader.py — Merkezi credential loader.

Öncelik:
  1. os.environ (Railway env vars)
  2. master.env dosyası (lokal geliştirme,
     `_knowledge/credentials/master.env`)

Bu modül, eski `_knowledge/api-anahtarlari.md` markdown regex fallback'inin
yerini alır — markdown formatı parse hatalarına ve sızıntı riskine açıktı.
master.env tek kaynak gerçek olarak kullanılır.
"""

from __future__ import annotations

import os
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
_MASTER_ENV = _BASE_DIR.parent.parent / "_knowledge" / "credentials" / "master.env"

_cache: dict[str, str] | None = None


def _load_master_env() -> dict[str, str]:
    if not _MASTER_ENV.exists():
        return {}
    env: dict[str, str] = {}
    try:
        with _MASTER_ENV.open("r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        return {}
    return env


def get_env(key: str, default: str = "") -> str:
    """`key`'i önce os.environ'dan, yoksa master.env'den döndür."""
    val = os.environ.get(key)
    if val:
        return val
    global _cache
    if _cache is None:
        _cache = _load_master_env()
    return _cache.get(key, default)
