"""
Ceren_Marka_Takip — İş Günü ve Saat Hesaplama
================================================
Hafta içi/dışı kontrolü ve iş saati bazlı süre hesaplama.
"""

from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def is_business_day(dt: datetime) -> bool:
    """Verilen tarih iş günü mü? (Pazartesi=0 ... Cuma=4)"""
    return dt.weekday() < 5  # 0-4 = Pazartesi-Cuma


def count_business_hours_since(last_message_time: datetime, now: Optional[datetime] = None) -> float:
    """
    Son mesajdan bu yana geçen iş saati sayısını hesaplar.
    
    Sadece iş günleri (Pazartesi-Cuma) sayılır.
    Hafta sonu günleri tamamen atlanır.
    
    Args:
        last_message_time: Thread'deki son mesajın zaman damgası (UTC)
        now: Şu anki zaman (test için override edilebilir)
    
    Returns:
        Geçen iş saati sayısı (float)
    """
    if now is None:
        now = datetime.utcnow()

    if last_message_time > now:
        return 0.0

    total_hours = 0.0
    current = last_message_time

    while current.date() < now.date():
        if is_business_day(current):
            # Bu günün gece yarısına kadar kalan saatleri
            next_midnight = (current + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            hours_remaining = (next_midnight - current).total_seconds() / 3600
            total_hours += hours_remaining
        # Sonraki günün başına geç
        current = (current + timedelta(days=1)).replace(hour=0, minute=0, second=0)

    # Son gün (bugün)
    if is_business_day(current) and current.date() == now.date():
        hours_today = (now - current).total_seconds() / 3600
        total_hours += hours_today

    return total_hours


def is_stale(last_message_time: datetime, threshold_hours: float = 48.0, 
             now: Optional[datetime] = None) -> bool:
    """
    Thread stale mi? (threshold_hours iş saati geçmiş mi?)
    
    Args:
        last_message_time: Son mesaj zamanı (UTC)
        threshold_hours: Eşik değeri (varsayılan: 48 iş saati)
        now: Şu anki zaman
    
    Returns:
        True = stale (eşik aşılmış)
    """
    hours = count_business_hours_since(last_message_time, now)
    return hours >= threshold_hours


def business_days_since(last_message_time: datetime, now: Optional[datetime] = None) -> int:
    """Kaç iş günü geçmiş? (İnsan-okunabilir rapor için)"""
    hours = count_business_hours_since(last_message_time, now)
    return int(hours / 24)  # Yaklaşık iş günü
