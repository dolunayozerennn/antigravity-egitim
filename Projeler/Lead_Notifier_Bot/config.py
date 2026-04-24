"""
Lead Notifier Bot v3 — Konfigürasyon
Tüm ayarlar environment variable'lardan okunur.
Hardcoded değer SIFIR.
"""
import os
import json
import logging

logger = logging.getLogger(__name__)


class Config:
    """Environment variable tabanlı konfigürasyon."""

    # Google Sheets
    SPREADSHEET_ID = os.environ.get(
        "SPREADSHEET_ID",
        "1DdrIZzWpdksuOQMnlxfffyW8ewAN4WsNVt_pdDZojm4"
    )
    SHEET_TAB = os.environ.get("SHEET_TAB", "0426-Yeni")

    # Polling (saniye)
    POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))

    # Telegram
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

    # Email
    NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "savasgocgen@gmail.com")
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "ozerendolunay@gmail.com")

    # Google Auth — Production: Service Account, Lokal: OAuth2
    GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

    # Gmail API — Railway: OAuth token JSON, Lokal: merkezi google_auth
    GOOGLE_OUTREACH_TOKEN_JSON = os.environ.get("GOOGLE_OUTREACH_TOKEN_JSON", "")

    # Güvenlik — tek döngüde max bildirim sayısı (spam koruması)
    MAX_BATCH_SIZE = int(os.environ.get("MAX_BATCH_SIZE", "10"))

    @classmethod
    def validate(cls):
        """Zorunlu değerleri kontrol eder. Eksikse EnvironmentError fırlatır."""
        errors = []

        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN")
        if not cls.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID")

        if not cls.GOOGLE_SERVICE_ACCOUNT_JSON:
            creds_path = os.path.join(os.path.dirname(__file__), "credentials.json")
            if not os.path.exists(creds_path):
                errors.append("GOOGLE_SERVICE_ACCOUNT_JSON veya credentials.json")

        if errors:
            raise EnvironmentError(
                f"Eksik zorunlu env variable(lar): {', '.join(errors)}"
            )

        logger.info("✅ Konfigürasyon doğrulandı")

    @classmethod
    def get_google_credentials_info(cls):
        """Service Account JSON'ını parse eder."""
        if cls.GOOGLE_SERVICE_ACCOUNT_JSON:
            try:
                return json.loads(cls.GOOGLE_SERVICE_ACCOUNT_JSON)
            except json.JSONDecodeError:
                logger.error("GOOGLE_SERVICE_ACCOUNT_JSON parse edilemedi")
                return None
        return None
