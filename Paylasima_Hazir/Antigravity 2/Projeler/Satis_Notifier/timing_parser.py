"""
Tele Satış Notifier — Zamanlama Tercihi Tespit Modülü
Google Sheets'ten gelen lead verisindeki zamanlama tercihini parse eder.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Sheets → Normalize zamanlama mapping (büyük/küçük harf toleranslı)
TIMING_MAP = {
    "akşam 6'dan sonra":    "aksam_6",
    "gün içinde":           "gun_icinde",
    "haftasonu":            "haftasonu",
    "aramayın mesaj atın":  "mesaj",  # Bu durumda mail atılmaz
    "aramayın, mesaj atın": "mesaj",
}


def detect_timing_preference(raw_data: dict) -> str:
    """
    Lead verisindeki zamanlama tercihini tespit eder.
    
    Sheets'teki sütun isimleri şu keyword'lerden biriyle eşleşir:
      - "zaman" veya "ulaşalım" içeren sütun
    
    Returns:
        "gun_icinde" | "aksam_6" | "haftasonu" | "mesaj" | "bilinmiyor"
    """
    # Zamanlama sütununu bul
    timing_key = None
    for key in raw_data:
        k_lower = key.lower()
        if "zaman" in k_lower or "ulaşalım" in k_lower:
            timing_key = key
            break
    
    if not timing_key:
        logger.warning(f"⚠️ Zamanlama sütunu bulunamadı. Mevcut sütunlar: {list(raw_data.keys())}")
        return "bilinmiyor"
    
    raw_value = str(raw_data.get(timing_key, "")).strip()
    if not raw_value:
        return "bilinmiyor"
    
    # Alt çizgileri ve virgülleri temizle, küçük harfe çevir
    normalized = raw_value.replace("_", " ").replace(",", "").lower().strip()
    
    if normalized in TIMING_MAP:
        result = TIMING_MAP[normalized]
        logger.info(f"⏰ Zamanlama tercihi: '{raw_value}' → {result}")
        return result
    
    # Virgüllü hâliyle de dene
    normalized_with_comma = raw_value.replace("_", " ").lower().strip()
    if normalized_with_comma in TIMING_MAP:
        result = TIMING_MAP[normalized_with_comma]
        logger.info(f"⏰ Zamanlama tercihi: '{raw_value}' → {result}")
        return result
    
    logger.warning(f"⚠️ Bilinmeyen zamanlama tercihi: '{raw_value}'")
    return "bilinmiyor"


def extract_lead_info(raw_data: dict) -> dict:
    """
    Lead verisinden temel bilgileri çıkarır.
    
    Returns:
        {
            "name": str,
            "phone": str,
            "email": str,
            "budget": str,
            "timing": str,
            "source_tab": str,
            "raw": dict,
        }
    """
    # Bütçe sütununu bul
    budget_key = None
    for key in raw_data:
        k_lower = key.lower()
        if "bütçe" in k_lower or "yatırım" in k_lower or "otomatik" in k_lower:
            budget_key = key
    
    return {
        "name": str(raw_data.get("full_name", "")).strip().title(),
        "phone": str(raw_data.get("phone_number", "")).strip(),
        "email": str(raw_data.get("email", "")).strip().lower(),
        "budget": str(raw_data.get(budget_key, "")).strip() if budget_key else "",
        "timing": detect_timing_preference(raw_data),
        "source_tab": raw_data.get("_source_tab", "Bilinmiyor"),
        "raw": raw_data,
    }
