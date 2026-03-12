"""
Tele Satış CRM — Google Sheets Okuma Modülü
Google Sheets API v4 ile her iki tab'dan yeni satırları okur.
Production'da Service Account, lokalde merkezi google_auth kullanır.
"""
import os
import sys
import json
import logging
from typing import Optional

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config import Config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class SheetsReader:
    """Google Sheets'ten yeni lead'leri okur."""

    def __init__(self):
        self.service = None
        # Her tab için en son okunan satır sayısını takip eder
        self._last_row_counts: dict[str, int] = {}

    def authenticate(self):
        """Google Sheets API'ye bağlanır."""
        creds = None

        # 1) Service Account (Production — Railway)
        sa_info = Config.get_google_credentials_info()
        if sa_info:
            logger.info("🔑 Service Account ile authentication yapılıyor...")
            creds = service_account.Credentials.from_service_account_info(
                sa_info, scopes=SCOPES
            )
        else:
            # 2) Merkezi Google Auth (Lokal Geliştirme)
            logger.info("🔑 Merkezi google_auth ile authentication yapılıyor...")
            _antigravity_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            sys.path.insert(0, os.path.join(_antigravity_root, "_knowledge", "credentials", "oauth"))
            from google_auth import get_sheets_service
            self.service = get_sheets_service("outreach")
            logger.info("✅ Google Sheets API bağlantısı kuruldu (merkezi auth)")
            return

        self.service = build("sheets", "v4", credentials=creds)
        logger.info("✅ Google Sheets API bağlantısı kuruldu")

    def get_all_rows(self, tab_name: str) -> list[dict]:
        """
        Belirtilen tab'daki tüm satırları header'larla birlikte dict olarak döner.
        """
        if not self.service:
            self.authenticate()

        result = (
            self.service.spreadsheets()
            .values()
            .get(
                spreadsheetId=Config.SPREADSHEET_ID,
                range=f"'{tab_name}'!A:Z",
            )
            .execute()
        )

        values = result.get("values", [])
        if not values or len(values) < 2:
            return []

        headers = values[0]
        rows = []
        for row_values in values[1:]:
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header] = row_values[i] if i < len(row_values) else ""
            rows.append(row_dict)

        return rows

    def get_new_rows(self, tab_name: str) -> list[dict]:
        """
        Sadece son okumadan beri eklenen yeni satırları döner.
        İlk çalıştırmada tüm satırları döner (mevcut kayıtlar Notion'da
        zaten var olduğundan duplikasyon kontrolü onları atlayacak).
        """
        all_rows = self.get_all_rows(tab_name)
        total = len(all_rows)

        last_count = self._last_row_counts.get(tab_name, 0)

        if last_count == 0:
            # İlk çalıştırma — Mevcut satır sayısını kaydet, ancak verileri DÖNME.
            # Yoksa sunucu her baştan başladığında eski yüzlerce veriyi Notion'a baştan yazar.
            self._last_row_counts[tab_name] = total
            logger.info(
                f"📊 '{tab_name}': İlk okuma — toplam {total} satır mevcut. Eski kayıtlar atlanıyor."
            )
            return []

        if total > last_count:
            new_rows = all_rows[last_count:]
            self._last_row_counts[tab_name] = total
            logger.info(
                f"📊 '{tab_name}': {len(new_rows)} yeni satır bulundu "
                f"(toplam: {total})"
            )
            return new_rows

        # Değişiklik yok
        self._last_row_counts[tab_name] = total
        return []

    def poll_all_tabs(self) -> list[dict]:
        """
        Tüm tab'lardan yeni satırları toplar.
        Her satıra kaynak tab bilgisi ekler.
        """
        all_new = []
        for tab_info in Config.SHEET_TABS:
            tab_name = tab_info["name"]
            try:
                new_rows = self.get_new_rows(tab_name)
                for row in new_rows:
                    row["_source_tab"] = tab_name
                all_new.extend(new_rows)
            except Exception as e:
                logger.error(f"❌ '{tab_name}' okunamadı: {e}")
                raise

        return all_new
