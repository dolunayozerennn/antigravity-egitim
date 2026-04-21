"""
Ceren_Marka_Takip — Stale Thread Tespit
==========================================
48+ iş saati sessiz olan thread'leri filtreler.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

from utils.business_hours import is_stale, count_business_hours_since, business_days_since

logger = logging.getLogger(__name__)

# Varsayılan eşik: 48 iş saati
DEFAULT_THRESHOLD_HOURS = 48.0


def filter_stale(threads: List[Dict[str, Any]], 
                 threshold_hours: float = DEFAULT_THRESHOLD_HOURS) -> List[Dict[str, Any]]:
    """
    Stale (eşik aşılmış) thread'leri filtrele.
    
    Args:
        threads: gmail_scanner'dan gelen thread listesi
        threshold_hours: İş saati eşiği (varsayılan: 48)
    
    Returns:
        Sadece stale olan thread'ler
    """
    now = datetime.utcnow()
    stale_threads = []

    for thread in threads:
        last_date = thread.get("last_message_date")
        if not last_date:
            logger.debug(f"Thread {thread['thread_id']}: tarih yok, atlanıyor")
            continue

        if isinstance(last_date, str):
            try:
                last_date = datetime.fromisoformat(last_date)
            except ValueError:
                logger.warning(f"Thread {thread['thread_id']}: tarih parse edilemedi: {last_date}")
                continue

        if is_stale(last_date, threshold_hours, now):
            hours = count_business_hours_since(last_date, now)
            days = business_days_since(last_date, now)
            thread["stale_hours"] = round(hours, 1)
            thread["stale_business_days"] = days
            stale_threads.append(thread)
            logger.debug(
                f"STALE: '{thread['subject'][:40]}' — {hours:.0f} iş saati sessiz"
            )

    logger.info(
        f"Stale filtre: {len(threads)} thread → {len(stale_threads)} stale "
        f"({threshold_hours}+ iş saati)"
    )
    return stale_threads
