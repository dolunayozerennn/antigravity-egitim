"""
Lead Pipeline — Birleşik Konfigürasyon Modülü
Tele Satış CRM + Lead Notifier Bot ayarlarını tek dosyada toplar.
"""
import os
import json
import logging

logger = logging.getLogger(__name__)


class Config:
    """Environment variable tabanlı birleşik konfigürasyon."""

    # ── GOOGLE SHEETS (CRM Kaynak) ──────────────────────────────────
    CRM_SPREADSHEET_ID = os.environ.get(
        "CRM_SPREADSHEET_ID",
        "10uTCr65VlIBng0Sxlmz7h1Q2y5AWBp1qDQHTeqI7mGU"
    )

    _crm_tabs_env = os.environ.get("CRM_SHEET_TABS", "")
    if _crm_tabs_env:
        CRM_SHEET_TABS = [
            {"name": name.strip()} for name in _crm_tabs_env.split(",") if name.strip()
        ]
    else:
        CRM_SHEET_TABS = [
            {"name": "Mart-2026-Saat Bazlı-v2"},
        ]

    # ── GOOGLE SHEETS (Notifier Kaynak) ─────────────────────────────
    NOTIFIER_SPREADSHEET_ID = os.environ.get(
        "NOTIFIER_SPREADSHEET_ID",
        "1DUxt0W6b-Sa5StDdGMnyVm4WFy-PB3FZIlCH30_9sh4"
    )

    _notifier_tabs_env = os.environ.get("NOTIFIER_SHEET_TABS", "")
    if _notifier_tabs_env:
        NOTIFIER_SHEET_TABS = [
            {"name": name.strip()} for name in _notifier_tabs_env.split(",") if name.strip()
        ]
    else:
        NOTIFIER_SHEET_TABS = [
            {"name": "Sayfa1"}
        ]

    # ── NOTION (CRM Hedef) ──────────────────────────────────────────
    NOTION_API_TOKEN = os.environ.get("NOTION_API_TOKEN", "")
    NOTION_DATABASE_ID = os.environ.get(
        "NOTION_DATABASE_ID",
        "31226924bb82800e9adad6f16399eba0"
    )
    NOTION_RATE_LIMIT_DELAY = float(os.environ.get("NOTION_RATE_LIMIT_DELAY", "0.35"))
    NOTION_MAX_RETRIES = int(os.environ.get("NOTION_MAX_RETRIES", "3"))
    DEDUP_WINDOW_DAYS = int(os.environ.get("DEDUP_WINDOW_DAYS", "7"))
    VALID_BUDGETS = ["$0 - $20", "$20 - $50", "$50 - $150", "$150+"]

    # ── BİLDİRİM (Notifier) ────────────────────────────────────────
    NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "savasgocgen@gmail.com")
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "ozerendolunay@gmail.com")
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

    # ── HATA BİLDİRİM (CRM) ────────────────────────────────────────
    ERROR_NOTIFY_EMAIL = os.environ.get("ERROR_NOTIFY_EMAIL", "ozerendolunay@gmail.com")
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_APP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD", "")

    # ── GOOGLE AUTH ─────────────────────────────────────────────────
    GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

    @classmethod
    def validate(cls):
        """Zorunlu konfigürasyon değerlerini kontrol eder."""
        errors = []

        if not cls.NOTION_API_TOKEN:
            errors.append("NOTION_API_TOKEN env variable'ı tanımlı değil")

        if not cls.TELEGRAM_BOT_TOKEN:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN tanımlı değil — Telegram bildirimleri kapalı")

        if not cls.GOOGLE_SERVICE_ACCOUNT_JSON:
            creds_path = os.path.join(os.path.dirname(__file__), "credentials.json")
            if not os.path.exists(creds_path):
                errors.append(
                    "GOOGLE_SERVICE_ACCOUNT_JSON env variable'ı veya credentials.json dosyası bulunamadı"
                )

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
