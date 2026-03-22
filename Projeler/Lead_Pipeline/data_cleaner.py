"""
Lead Pipeline — Veri Temizleme Modülü
Tele Satış CRM'den aynen taşındı. Telefon, isim, e-posta, bütçe ve zamanlama temizliği.
"""
import re
import logging
import difflib

from config import Config

logger = logging.getLogger(__name__)


def clean_phone(raw_phone: str) -> str:
    """Türkiye telefon numarasını uluslararası formata çevirir."""
    phone = str(raw_phone or "")
    phone = re.sub(r"^p:\+?", "", phone)
    phone = re.sub(r"[^\d]", "", phone)

    if not phone:
        return ""

    if phone.startswith("090") and len(phone) == 13:
        phone = phone[1:]
    if phone.startswith("0") and len(phone) == 11:
        phone = "90" + phone[1:]
    if phone.startswith("5") and len(phone) == 10:
        phone = "90" + phone

    if phone.startswith("90") and len(phone) == 12:
        return f"+{phone[:2]} {phone[2:5]} {phone[5:8]} {phone[8:]}"

    return f"+{phone}" if phone else ""


def clean_name(raw_name: str) -> str:
    """İsmin baş harflerini büyük yapar."""
    name = str(raw_name or "").strip()
    if not name:
        return ""
    return " ".join(word.capitalize() if word else "" for word in name.split())


def clean_email(raw_email: str) -> str:
    """Email'i lowercase yapar ve trim eder."""
    return str(raw_email or "").strip().lower()


def clean_budget(raw_budget: str) -> str:
    """Bütçe değerini select seçenekleriyle eşleştirir."""
    budget = str(raw_budget or "").replace("_", " ")
    if budget in Config.VALID_BUDGETS:
        return budget
    return ""


def clean_timing(raw_timing: str) -> str:
    """Ulaşım zamanı tercihini temizler."""
    timing = str(raw_timing or "").strip().replace("_", " ")
    timing_no_comma = timing.replace(",", "")

    TIMING_MAP = {
        "akşam 6'dan sonra":    "Akşam 6'dan sonra",
        "gün içinde":           "Gün içinde",
        "haftasonu":            "Haftasonu",
        "aramayın mesaj atın":  "Aramayın mesaj atın",
        "aramayın, mesaj atın": "Aramayın mesaj atın",
    }

    key = timing_no_comma.lower()
    if key in TIMING_MAP:
        return TIMING_MAP[key]

    key_with_comma = timing.lower()
    if key_with_comma in TIMING_MAP:
        return TIMING_MAP[key_with_comma]

    matches = difflib.get_close_matches(key_with_comma, TIMING_MAP.keys(), n=1, cutoff=0.7)
    if matches:
        return TIMING_MAP[matches[0]]

    return ""


def clean_lead(raw_data: dict) -> dict:
    """Tüm lead verisini temizler (CRM pipeline)."""
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
