"""
Lead Notifier Bot — Konfigürasyon Modülü
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
        "1DUxt0W6b-Sa5StDdGMnyVm4WFy-PB3FZIlCH30_9sh4"
    )

    # Tab isimleri — SHEET_TABS env var ile ayarlanabilir
    _sheet_tabs_env = os.environ.get("SHEET_TABS", "")
    if _sheet_tabs_env:
        SHEET_TABS = [
            {"name": name.strip()} for name in _sheet_tabs_env.split(",") if name.strip()
        ]
    else:
        # Default: "Sayfa1" (Genelde ilk tab)
        SHEET_TABS = [
            {"name": "Sayfa1"}
        ]

    # Polling (dakika olarak değil, saniye olarak)
    POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "300")) # 5 Dakika

    # Bildirim E-posta Ayarları
    NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "BILDIRIM_EMAIL_BURAYA@email.com")
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "EMAIL_ADRESI_BURAYA")

    # Telegram Bot Ayarları
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN_BURAYA")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

    # Google Auth — Production: Service Account, Lokal: OAuth2
    GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

    @classmethod
    def validate(cls):
        """Zorunlu konfigürasyon değerlerini kontrol eder."""
        errors = []

        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN tanımlı değil")
            
        if not cls.TELEGRAM_CHAT_ID:
            logger.warning("TELEGRAM_CHAT_ID tanımlı değil. /get_chat_id.py kullanarak CHAT_ID'nizi alın ve .env dosyasına ekleyin.")
            # Hata fırlatma, çünkü belki sadece email gitmesi istenir

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
