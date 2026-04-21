"""
Ceren_Marka_Takip — Hatırlatma State Yönetimi
================================================
Aynı thread için 2 iş günü arayla tekrar hatırlatma göndermeyi sağlar.
Duplicate hatırlatmaları engeller.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# State dosyası yolu
STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
STATE_FILE = os.path.join(STATE_DIR, "reminder_history.json")

# Railway'de kalıcı disk yok — env variable ile state yönetimi
STATE_ENV_VAR = "REMINDER_HISTORY_JSON"

# Hatırlatma cooldown süresi (iş günü)
COOLDOWN_DAYS = 2


def _load_state() -> Dict[str, Any]:
    """
    State'i yükle.
    Öncelik: 1) Lokal dosya, 2) Environment variable, 3) Boş state
    """
    # 1) Lokal dosya
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"State dosyası okunamadı: {e}")

    # 2) Env variable (Railway)
    env_state = os.environ.get(STATE_ENV_VAR)
    if env_state:
        try:
            return json.loads(env_state)
        except json.JSONDecodeError as e:
            logger.warning(f"State env variable parse edilemedi: {e}")

    # 3) Boş state
    return {"reminders": {}, "last_run": None, "stats": {"total_runs": 0, "total_reminders": 0}}


def _save_state(state: Dict[str, Any]):
    """State'i kaydet (lokal dosya)."""
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)
    logger.debug(f"State kaydedildi: {STATE_FILE}")


def filter_already_notified(thread_results: List[Dict], cooldown_days: int = COOLDOWN_DAYS) -> List[Dict]:
    """
    Son cooldown_days iş günü içinde hatırlatma gönderilmiş thread'leri filtrele.
    
    Args:
        thread_results: Analiz edilmiş thread listesi
        cooldown_days: Kaç iş günü arayla tekrar hatırlatma gönderilsin
    
    Returns:
        Sadece hatırlatma gönderilmesi gereken thread'ler
    """
    state = _load_state()
    reminders = state.get("reminders", {})
    now = datetime.utcnow()
    cooldown_td = timedelta(days=cooldown_days)

    to_notify = []
    for thread in thread_results:
        thread_id = thread.get("thread_id", "")
        last_reminded = reminders.get(thread_id)
        
        if last_reminded:
            last_reminded_dt = datetime.fromisoformat(last_reminded)
            if (now - last_reminded_dt) < cooldown_td:
                logger.debug(f"Thread {thread_id} zaten bildirilmiş, cooldown aktif")
                continue

        to_notify.append(thread)

    logger.info(f"Filtre sonucu: {len(thread_results)} → {len(to_notify)} thread bildirilecek")
    return to_notify


def update_state(notified_threads: List[Dict]):
    """Gönderilen hatırlatmaları state'e kaydet."""
    state = _load_state()
    now = datetime.utcnow().isoformat()

    for thread in notified_threads:
        thread_id = thread.get("thread_id", "")
        state["reminders"][thread_id] = now

    state["last_run"] = now
    state["stats"]["total_runs"] = state["stats"].get("total_runs", 0) + 1
    state["stats"]["total_reminders"] = state["stats"].get("total_reminders", 0) + len(notified_threads)

    # 30 günden eski hatırlatmaları temizle
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    state["reminders"] = {
        tid: ts for tid, ts in state["reminders"].items() if ts > cutoff
    }

    _save_state(state)
    logger.info(f"State güncellendi: {len(notified_threads)} yeni hatırlatma kaydedildi")


def get_run_stats() -> Dict[str, Any]:
    """Son çalışma istatistiklerini döndür."""
    state = _load_state()
    return {
        "last_run": state.get("last_run"),
        "total_runs": state["stats"].get("total_runs", 0),
        "total_reminders": state["stats"].get("total_reminders", 0),
        "active_threads": len(state.get("reminders", {})),
    }
