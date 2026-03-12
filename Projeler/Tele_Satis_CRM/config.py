"""
Tele Satış CRM — Konfigürasyon Modülü
Tüm ayarları environment variable'lardan okur.
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
        "10uTCr65VlIBng0Sxlmz7h1Q2y5AWBp1qDQHTeqI7mGU"
    )
    SHEET_TABS = [
        {"name": "Mart-2026", "gid": 0},
        {"name": "Mart-2026-Saat Bazlı", "gid": 76091790},
        {"name": "Saat-Bazlı - v2", "gid": 0},
    ]

    # Notion
    NOTION_API_TOKEN = os.environ.get("NOTION_API_TOKEN", "")
    NOTION_DATABASE_ID = os.environ.get(
        "NOTION_DATABASE_ID",
        "31226924bb82800e9adad6f16399eba0"
    )

    # Polling
    POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))

    # Hata Bildirimi
    ERROR_NOTIFY_EMAIL = os.environ.get("ERROR_NOTIFY_EMAIL", "ozerendolunay@gmail.com")
    SMTP_USER = os.environ.get("SMTP_USER", "")  # Gmail adresi
    SMTP_APP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD", "")  # Gmail App Password

    # Google Auth — Production: Service Account, Lokal: OAuth2
    GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

    # Duplikasyon Kuralı
    DEDUP_WINDOW_DAYS = int(os.environ.get("DEDUP_WINDOW_DAYS", "7"))

    # Bütçe Seçenekleri (Notion select alanıyla eşleşmeli)
    VALID_BUDGETS = ["$0 - $20", "$20 - $50", "$50 - $150", "$150+"]

    @classmethod
    def validate(cls):
        """Zorunlu konfigürasyon değerlerini kontrol eder."""
        errors = []

        if not cls.NOTION_API_TOKEN:
            errors.append("NOTION_API_TOKEN env variable'ı tanımlı değil")

        if not cls.GOOGLE_SERVICE_ACCOUNT_JSON:
            # Lokal geliştirmede credentials.json olabilir
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
