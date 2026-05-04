#!/usr/bin/env python3
"""env_loader: master.env (lokal) + GOOGLE_SERVICE_ACCOUNT_JSON base64 (Railway)."""

import os
import json
import base64
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
ANTIGRAVITY_ROOT = SCRIPT_DIR.parent.parent
MASTER_ENV_PATH = ANTIGRAVITY_ROOT / "_knowledge" / "credentials" / "master.env"
SA_JSON_PATH = ANTIGRAVITY_ROOT / "_knowledge" / "credentials" / "google-service-account.json"

_env_cache: dict = {}
_sa_temp_path: str = ""


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
                env[k.strip()] = v.strip()
    return env


def get_env(key: str, default: str = "") -> str:
    global _env_cache
    val = os.environ.get(key)
    if val:
        return val
    if not _env_cache:
        _env_cache = _load_master_env()
    return _env_cache.get(key, default)


def get_sa_json_path() -> str:
    global _sa_temp_path
    if _sa_temp_path and os.path.exists(_sa_temp_path):
        return _sa_temp_path

    sa_b64 = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if sa_b64:
        try:
            sa_json = base64.b64decode(sa_b64).decode("utf-8")
            json.loads(sa_json)
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", prefix="sa_", delete=False)
            tmp.write(sa_json)
            tmp.close()
            _sa_temp_path = tmp.name
            return _sa_temp_path
        except Exception as e:
            print(f"GOOGLE_SERVICE_ACCOUNT_JSON decode error: {e}")

    try:
        if SA_JSON_PATH.exists():
            return str(SA_JSON_PATH)
    except PermissionError:
        pass

    return ""
