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
        # Default: "Sheet1" (Genelde ilk tab)
        SHEET_TABS = [
            {"name": "Sheet1"}
        ]

    # Polling (dakika olarak değil, saniye olarak)
    POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "300")) # 5 Dakika

    # Bildirim E-posta Ayarları
    NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "savasgocgen@gmail.com")
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "ozerendolunay@gmail.com")
    SMTP_USER = os.environ.get("SMTP_USER", "ozerendolunay@gmail.com")
    SMTP_APP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD", "")

    # Telegram Bot Ayarları
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "847006455")

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

        # GOOGLE_SERVICE_ACCOUNT_JSON opsiyonel, sheets_reader merkezi oath kullanabilir veya
        # /_knowledge/credentials/google-service-account.json okuyabiliriz.
        
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
                
        # Eğer env variable'da yoksa, merkezi dosyadan oku (Railway/Lokal uyumluluğu için)
        sa_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "_knowledge", "credentials", "google-service-account.json"))
        if os.path.exists(sa_path):
            try:
                with open(sa_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Merkezi Service Account dosyası okunamadı: {e}")
                
        return None
