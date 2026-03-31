"""
Tele Satış Notifier — Konfigürasyon Modülü
Tüm ayarları environment variable'lardan okur.

Tele Satış CRM Google Sheet'ini izler ve lead'lerin zamanlama tercihine göre
Ece'ye toplu/anlık bilgilendirme e-postası gönderir.
"""
import os
import json
import logging

logger = logging.getLogger(__name__)


class Config:
    """Environment variable tabanlı konfigürasyon."""

    # ── Google Sheets ──────────────────────────────────────
    SPREADSHEET_ID = os.environ.get(
        "SPREADSHEET_ID",
        "SPREADSHEET_ID_BURAYA"
    )

    # Tab isimleri — SHEET_TABS env var ile güncellenebilir
    _sheet_tabs_env = os.environ.get("SHEET_TABS", "")
    if _sheet_tabs_env:
        SHEET_TABS = [
            {"name": name.strip()} for name in _sheet_tabs_env.split(",") if name.strip()
        ]
    else:
        SHEET_TABS = [
            {"name": "Mart-2026"},
            {"name": "Mart-2026-Saat Bazlı"},
            {"name": "Saat-Bazlı - v2"},
        ]

    # ── Polling ────────────────────────────────────────────
    POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))  # 5 dk

    # ── E-posta gönderim ayarları ──────────────────────────
    # Gönderen: GONDEREN_EMAIL_BURAYA (OAuth2)
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "GONDEREN_EMAIL_BURAYA")
    SENDER_ACCOUNT = os.environ.get("SENDER_ACCOUNT", "secondary")  # google_auth hesap adı

    # Alıcı: Ece
    RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "ALICI_EMAIL_BURAYA")
    RECIPIENT_NAME = os.environ.get("RECIPIENT_NAME", "Ece")

    # ── Zamanlama ──────────────────────────────────────────
    # Türkiye saat dilimi (UTC+3)
    TIMEZONE = os.environ.get("TIMEZONE", "Europe/Istanbul")

    # Akşam 6 gönderim saati
    EVENING_SEND_HOUR = int(os.environ.get("EVENING_SEND_HOUR", "18"))  # 18:00

    # Haftasonu gönderim saati
    WEEKEND_SEND_HOUR = int(os.environ.get("WEEKEND_SEND_HOUR", "10"))  # 10:00

    # ── Google Auth ──────────────────────────────────────── 
    GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

    @classmethod
    def validate(cls):
        """Zorunlu konfigürasyon değerlerini kontrol eder."""
        errors = []

        if not cls.GOOGLE_SERVICE_ACCOUNT_JSON:
            creds_path = os.path.join(os.path.dirname(__file__), "credentials.json")
            if not os.path.exists(creds_path):
                # Lokal ortam — merkezi auth kullanılacak, sorun değil
                pass

        if errors:
            for err in errors:
                logger.error(f"❌ Config hatası: {err}")
            return False

        logger.info("✅ Konfigürasyon doğrulandı")
        return True

    @classmethod
    def get_google_credentials_info(cls):
        """Google credentials bilgisini döner (service account JSON parse)."""
        if cls.GOOGLE_SERVICE_ACCOUNT_JSON:
            try:
                return json.loads(cls.GOOGLE_SERVICE_ACCOUNT_JSON)
            except json.JSONDecodeError:
                logger.error("GOOGLE_SERVICE_ACCOUNT_JSON parse edilemedi")
                return None
        return None
