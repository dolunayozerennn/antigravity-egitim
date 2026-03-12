"""
Tele Satış CRM — Veri Temizleme Modülü
n8n'deki "Veri Temizleme" node'unun Python karşılığı.
"""
import re
import logging

from config import Config

logger = logging.getLogger(__name__)


def clean_phone(raw_phone: str) -> str:
    """
    Telefon numarasını temizler ve formatlar.
    Türk numarası: +90 5XX XXX XXXX
    """
    phone = str(raw_phone or "")
    # p:+ prefix'ini kaldır
    phone = re.sub(r"^p:\+?", "", phone)
    # Tüm boşluk, +, -, (, ) karakterlerini kaldır
    phone = re.sub(r"[\s+\-()]", "", phone)

    # Türk numarası formatla
    if phone.startswith("90") and len(phone) == 12:
        return f"+{phone[:2]} {phone[2:5]} {phone[5:8]} {phone[8:]}"

    return f"+{phone}" if phone else ""


def clean_name(raw_name: str) -> str:
    """İsmin baş harflerini büyük yapar."""
    name = str(raw_name or "").strip()
    if not name:
        return ""
    return " ".join(
        word.capitalize() if word else "" for word in name.split()
    )


def clean_email(raw_email: str) -> str:
    """Email'i lowercase yapar ve trim eder."""
    return str(raw_email or "").strip().lower()


def clean_budget(raw_budget: str) -> str:
    """
    Bütçe değerini temizler ve Notion select seçenekleriyle eşleştirir.
    Alt çizgileri boşluğa çevirir, geçerli değilse boş döner.
    """
    budget = str(raw_budget or "").replace("_", " ")
    if budget in Config.VALID_BUDGETS:
        return budget
    return ""


def clean_timing(raw_timing: str) -> str:
    """
    Ulaşım zamanı tercihini temizler.
    Toleranslı eşleşme sağlar veya direkt string döner.
    """
    timing = str(raw_timing or "").strip()
    valid_options = ["Akşam 6'dan sonra", "Gün içinde", "Haftasonu", "Aramayın, mesaj atın"]
    for opt in valid_options:
        if opt.lower() == timing.lower():
            return opt
    return timing if timing else ""


def clean_lead(raw_data: dict) -> dict:
    """
    Tüm lead verisini temizler.
    
    Args:
        raw_data: Google Sheet'ten gelen ham satır verisi
        
    Returns:
        Temizlenmiş lead verisi
    """
    # Bütçe sütun adı (Sheet'teki uzun sütun ismi)
    budget_key = None
    timing_key = None
    for key in raw_data:
        k_lower = key.lower()
        if "bütçe" in k_lower or "yatırım" in k_lower or "otomatik" in k_lower:
            budget_key = key
        if "zaman" in k_lower or "ulaşalım" in k_lower:
            timing_key = key

    budget_value = raw_data.get(budget_key, "") if budget_key else ""
    timing_value = raw_data.get(timing_key, "") if timing_key else ""

    cleaned = {
        "clean_name": clean_name(raw_data.get("full_name", "")),
        "clean_phone": clean_phone(raw_data.get("phone_number", "")),
        "clean_email": clean_email(raw_data.get("email", "")),
        "clean_budget": clean_budget(budget_value),
        "clean_timing": clean_timing(timing_value),
        "raw": raw_data,
    }

    logger.debug(
        f"Temizlendi: {cleaned['clean_name']} | "
        f"{cleaned['clean_phone']} | "
        f"{cleaned['clean_email']} | "
        f"Bütçe: {cleaned['clean_budget']}"
    )

    return cleaned
