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


import urllib.request

def _get_notion_token():
    return os.environ.get("NOTION_SOCIAL_TOKEN") or os.environ.get("NOTION_API_TOKEN")

def _get_notion_db():
    return os.environ.get("NOTION_DB_OPS_LOG", "33095514-0a32-81b4-858a-ff81a77b6d48")

def _query_notion_state() -> Dict[str, str]:
    """Notion DB üzerinden son X gündeki hatırlatılan thread'leri çeker."""
    token = _get_notion_token()
    db_id = _get_notion_db()
    if not token:
        return {}
    
    cutoff = (datetime.utcnow() - timedelta(days=COOLDOWN_DAYS)).isoformat() + "Z"
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    payload = {
        "filter": {
            "and": [
                {"property": "Project", "select": {"equals": "Ceren_Marka_Takip"}},
                {"property": "Component", "select": {"equals": "Notifier_State"}},
                {"timestamp": "created_time", "created_time": {"on_or_after": cutoff}}
            ]
        },
        "page_size": 100
    }
    
    req = urllib.request.Request(url, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Notion-Version", "2022-06-28")
    req.add_header("Content-Type", "application/json")
    
    reminders = {}
    try:
        data = json.dumps(payload).encode("utf-8")
        with urllib.request.urlopen(req, data=data, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            for page in result.get("results", []):
                props = page.get("properties", {})
                title_prop = props.get("Title", {}).get("title", [])
                if title_prop:
                    thread_id = title_prop[0].get("text", {}).get("content", "")
                    created_time = page.get("created_time")
                    if thread_id:
                        reminders[thread_id] = created_time
    except Exception as e:
        logger.error(f"Notion state sorgulaması başarısız: {e}")
        
    return reminders

def _push_notion_state(thread_id: str):
    """Hatırlatma bilgisini Notion'a kaydeder."""
    token = _get_notion_token()
    db_id = _get_notion_db()
    if not token:
        return

    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": db_id},
        "properties": {
            "Title": {"title": [{"text": {"content": thread_id}}]},
            "Message": {"rich_text": [{"text": {"content": "Hatırlatma gönderildi"}}]},
            "Level": {"select": {"name": "INFO"}},
            "Component": {"select": {"name": "Notifier_State"}},
            "Project": {"select": {"name": "Ceren_Marka_Takip"}}
        }
    }
    
    req = urllib.request.Request(url, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Notion-Version", "2022-06-28")
    req.add_header("Content-Type", "application/json")
    
    try:
        data = json.dumps(payload).encode("utf-8")
        with urllib.request.urlopen(req, data=data, timeout=15) as _:
            pass
    except Exception as e:
        logger.error(f"Notion state kaydı başarısız ({thread_id}): {e}")

def _load_state() -> Dict[str, Any]:
    """
    Kalıcı durumu yükler.
    Artık öncelik Notion altyapısındadır. Not available ise lokal dosyayı kullanır.
    """
    notion_reminders = _query_notion_state()
    
    state = {"reminders": {}, "last_run": None, "stats": {"total_runs": 0, "total_reminders": 0}}
    
    # Lokal dosya fallback (eski yapı için)
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                local_state = json.load(f)
                state = local_state
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"State dosyası okunamadı: {e}")

    # En son geçerli olan Notion verileriyle lokal verileri birleştir
    for t_id, ts in notion_reminders.items():
        state["reminders"][t_id] = ts
        
    return state

def _save_state(state: Dict[str, Any]):
    """Sadece bağımsız lokal istatistikleri korur."""
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)
    logger.debug(f"State lokal olarak kaydedildi: {STATE_FILE}")

def filter_already_notified(thread_results: List[Dict], cooldown_days: int = COOLDOWN_DAYS) -> List[Dict]:
    """Son cooldown_days iş günü içinde hatırlatma gönderilmiş thread'leri filtrele."""
    state = _load_state()
    reminders = state.get("reminders", {})
    now = datetime.utcnow()
    cooldown_td = timedelta(days=cooldown_days)

    to_notify = []
    for thread in thread_results:
        thread_id = thread.get("thread_id", "")
        last_reminded = reminders.get(thread_id)
        
        if last_reminded:
            # Datetime string parse
            clean_ts = last_reminded.replace("Z", "+00:00")
            try:
                last_reminded_dt = datetime.fromisoformat(clean_ts).replace(tzinfo=None)
                if (now - last_reminded_dt) < cooldown_td:
                    logger.debug(f"Thread {thread_id} zaten bildirilmiş, cooldown aktif")
                    continue
            except ValueError:
                pass

        to_notify.append(thread)

    logger.info(f"Filtre sonucu: {len(thread_results)} → {len(to_notify)} thread bildirilecek")
    return to_notify

def update_state(notified_threads: List[Dict]):
    """Gönderilen hatırlatmaları anında Notion Ops Logger'a iterek kalıcı kaydeder."""
    state = _load_state()
    now = datetime.utcnow().isoformat()

    for thread in notified_threads:
        thread_id = thread.get("thread_id", "")
        if not thread_id:
            continue
            
        state["reminders"][thread_id] = now
        _push_notion_state(thread_id)

    state["last_run"] = now
    state["stats"]["total_runs"] = state["stats"].get("total_runs", 0) + 1
    state["stats"]["total_reminders"] = state["stats"].get("total_reminders", 0) + len(notified_threads)

    _save_state(state)
    logger.info(f"State güncellendi: {len(notified_threads)} yeni hatırlatma Notion/Lokal'e kaydedildi")

def get_run_stats() -> Dict[str, Any]:
    """Son çalışma istatistiklerini döndür."""
    state = _load_state()
    return {
        "last_run": state.get("last_run"),
        "total_runs": state.get("stats", {}).get("total_runs", 0),
        "total_reminders": state.get("stats", {}).get("total_reminders", 0),
        "active_threads": len(state.get("reminders", {})),
    }
