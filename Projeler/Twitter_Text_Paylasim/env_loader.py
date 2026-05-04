#!/usr/bin/env python3
"""env_loader: master.env (lokal) + Railway env vars."""

import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
ANTIGRAVITY_ROOT = SCRIPT_DIR.parent.parent
MASTER_ENV_PATH = ANTIGRAVITY_ROOT / "_knowledge" / "credentials" / "master.env"

_env_cache: dict = {}


def _load_master_env() -> dict:
    try:
        if not MASTER_ENV_PATH.exists():
            return {}
    except PermissionError:
        return {}
    env = {}
    with open(MASTER_ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                v = v.strip()
                # Inline yorumu kırp (tırnak içindeki # değil ama burada tırnaklı değer
                # beklemiyoruz; basit tutuyoruz)
                if " #" in v:
                    v = v.split(" #", 1)[0].strip()
                env[k.strip()] = v
    return env


def get_env(key: str, default: str = "") -> str:
    global _env_cache
    val = os.environ.get(key)
    if val:
        return val
    if not _env_cache:
        _env_cache = _load_master_env()
    return _env_cache.get(key, default)
