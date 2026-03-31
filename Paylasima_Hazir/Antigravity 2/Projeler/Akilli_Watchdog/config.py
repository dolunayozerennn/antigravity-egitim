"""
Akıllı Watchdog — Konfigürasyon Modülü
LLM-destekli pipeline sağlık kontrolü.

İzlenen projeler:
  1. Tele Satış CRM (Sheets → Notion)
  2. Lead Notifier Bot (Sheets → Telegram/Email)
  3. Tele Satış Notifier (Sheets → Email zamanlı)
"""
import os
import json
import logging

logger = logging.getLogger(__name__)


def _parse_tabs(csv_str: str) -> list[str]:
    """Virgülle ayrılmış tab isimlerini parse eder."""
    return [t.strip() for t in csv_str.split(",") if t.strip()]


class Config:
    """Environment variable tabanlı konfigürasyon."""

    # ── Groq LLM ──────────────────────────────────────────
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_BASE_URL = os.environ.get(
        "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
    )
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    # ── Alarm ─────────────────────────────────────────────
    ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "EMAIL_ADRESI_BURAYA")

    # Gmail API OAuth2 (SMTP yerine — Railway port engellemesi nedeniyle)
    # Railway: GOOGLE_OUTREACH_TOKEN_JSON env variable
    # Lokal: Merkezi google_auth modülü otomatik kullanılır

    # ── Notion ─────────────────────────────────────────────
    NOTION_API_TOKEN = os.environ.get("NOTION_API_TOKEN", "")
    NOTION_DATABASE_ID = os.environ.get(
        "NOTION_DATABASE_ID", "NOTION_DATABASE_ID_BURAYA"
    )

    # ── Google Auth (Production: Service Account) ─────────
    GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

    # ── İzlenen Projeler ──────────────────────────────────
    MONITORED_PROJECTS = [
        {
            "name": "Tele Satış CRM",
            "spreadsheet_id": os.environ.get(
                "CRM_SPREADSHEET_ID",
                "SPREADSHEET_ID_BURAYA",
            ),
            "sheet_tabs": _parse_tabs(os.environ.get(
                "CRM_SHEET_TABS",
                "Mart-2026,Mart-2026-Saat Bazlı,Saat-Bazlı - v2",
            )),
            "expected_columns": [
                "full_name", "phone_number", "email",
            ],
            "expected_column_keywords": [
                "bütçe|yatırım|otomatik",
                "zaman|ulaşalım",
            ],
            "pipeline": "sheets_to_notion",
            "notion_db_id": os.environ.get(
                "CRM_NOTION_DB_ID",
                "NOTION_DATABASE_ID_BURAYA",
            ),
            "notion_properties": ["İsim", "Phone", "email", "Durum", "Bütçe"],
        },
        {
            "name": "Lead Notifier Bot",
            "spreadsheet_id": os.environ.get(
                "NOTIFIER_SPREADSHEET_ID",
                "1DUxt0W6b-Sa5StDdGMnyVm4WFy-PB3FZIlCH30_9sh4",
            ),
            "sheet_tabs": _parse_tabs(os.environ.get(
                "NOTIFIER_SHEET_TABS", "Sayfa1",
            )),
            "expected_columns": [
                "full_name", "phone_number", "email",
            ],
            "expected_column_keywords": [],
            "pipeline": "sheets_to_notification",
        },
        {
            "name": "Tele Satış Notifier",
            "spreadsheet_id": os.environ.get(
                "ZAMANLAYICI_SPREADSHEET_ID",
                "SPREADSHEET_ID_BURAYA",
            ),
            "sheet_tabs": _parse_tabs(os.environ.get(
                "ZAMANLAYICI_SHEET_TABS",
                "Mart-2026,Mart-2026-Saat Bazlı,Saat-Bazlı - v2",
            )),
            "expected_columns": [
                "full_name", "phone_number", "email",
            ],
            "expected_column_keywords": [
                "bütçe|yatırım|otomatik",
                "zaman|ulaşalım",
            ],
            "pipeline": "sheets_to_email",
        },
    ]

    # ── Zamanlama ────────────────────────────────────────
    CHECK_INTERVAL_HOURS = int(os.environ.get("CHECK_INTERVAL_HOURS", "24"))

    @classmethod
    def validate(cls) -> bool:
        """Zorunlu konfigürasyon değerlerini kontrol eder."""
        errors = []

        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY tanımlı değil")

        if errors:
            for err in errors:
                logger.error(f"❌ Config hatası: {err}")
            return False

        logger.info("✅ Konfigürasyon doğrulandı")
        return True

    @classmethod
    def get_google_credentials_info(cls):
        """Google credentials bilgisini döner."""
        if cls.GOOGLE_SERVICE_ACCOUNT_JSON:
            try:
                return json.loads(cls.GOOGLE_SERVICE_ACCOUNT_JSON)
            except json.JSONDecodeError:
                logger.error("GOOGLE_SERVICE_ACCOUNT_JSON parse edilemedi")
                return None
        return None
