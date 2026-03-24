"""
Google Sheets Okuma Modülü
Yeni satırları okur ve son okunan durumu kaydeder.
"""
import os
import sys
import json
import time
import logging
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import Config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
_TRANSIENT_KEYWORDS = ["eof", "ssl", "broken pipe", "connection reset", "timeout", "connection aborted", "timed out"]
_MAX_RETRIES = 3
_STATE_FILE = os.path.join(os.path.dirname(__file__), ".last_row_counts.json")

class SheetsReader:
    def __init__(self):
        self.service = None
        self._last_row_counts: dict[str, int] = self._load_state()
        self._pending_counts: dict[str, int] = {}

    @staticmethod
    def _load_state() -> dict[str, int]:
        """Disk'teki persist dosyasından _last_row_counts'u yükler."""
        try:
            if os.path.exists(_STATE_FILE):
                with open(_STATE_FILE, "r") as f:
                    data = json.load(f)
                logger.info(f"📂 Önceki satır sayıları yüklendi: {data}")
                return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"⚠️ State dosyası okunamadı, sıfırdan başlanıyor: {e}")
        return {}

    def _save_state(self):
        """_last_row_counts'u diske kaydeder."""
        try:
            with open(_STATE_FILE, "w") as f:
                json.dump(self._last_row_counts, f)
        except OSError as e:
            logger.warning(f"⚠️ State dosyası yazılamadı: {e}")

    @staticmethod
    def _is_transient(err: Exception) -> bool:
        msg = str(err).lower()
        return any(kw in msg for kw in _TRANSIENT_KEYWORDS)

    def authenticate(self):
        """Google Sheets API'ye bağlanır."""
        creds = None
        sa_info = Config.get_google_credentials_info()
        
        if sa_info:
            logger.info("🔑 Service Account ile authentication yapılıyor...")
            creds = service_account.Credentials.from_service_account_info(
                sa_info, scopes=SCOPES
            )
        else:
            logger.info("🔑 Merkezi google_auth ile authentication yapılıyor (Lokal)...")
            _antigravity_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            sys.path.insert(0, os.path.join(_antigravity_root, "_knowledge", "credentials", "oauth"))
            from google_auth import get_sheets_service
            self.service = get_sheets_service("outreach")
            logger.info("✅ Google Sheets API bağlantısı kuruldu (merkezi auth)")
            return

        self.service = build("sheets", "v4", credentials=creds)
        logger.info("✅ Google Sheets API bağlantısı kuruldu")

    def get_all_rows(self, tab_name: str) -> list[dict]:
        """Belirtilen tab'daki tüm satırları header'larla birlikte döner."""
        if not self.service:
            self.authenticate()

        last_err = None
        for attempt in range(_MAX_RETRIES):
            if attempt > 0:
                wait = 2 ** attempt
                logger.warning(
                    f"⚠️ '{tab_name}' geçici ağ hatası, {wait}s sonra "
                    f"yeniden bağlanılıyor (deneme {attempt + 1}/{_MAX_RETRIES})..."
                )
                time.sleep(wait)
                self.service = None
                self.authenticate()

            try:
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

            except Exception as e:
                if self._is_transient(e) and attempt < _MAX_RETRIES - 1:
                    last_err = e
                    continue
                raise

        raise last_err

    def get_new_rows(self, tab_name: str) -> list[dict]:
        """Sadece eklenen yeni satırları döner."""
        all_rows = self.get_all_rows(tab_name)
        total = len(all_rows)
        last_count = self._last_row_counts.get(tab_name, 0)

        if last_count == 0:
            # İlk çalıştırma -> Hepsini bildirmemek için toplamı kaydet ve boş dön
            self._pending_counts[tab_name] = total
            logger.info(
                f"📊 '{tab_name}': İlk çalıştırma — Mevcut {total} satır atlanıyor. "
                "Bundan sonraki yeni satırlar bildirilecek."
            )
            return []

        if total > last_count:
            new_rows = all_rows[last_count:]
            self._pending_counts[tab_name] = total
            logger.info(f"📊 '{tab_name}': {len(new_rows)} yeni satır bulundu (toplam: {total})")
            return new_rows

        if total < last_count:
            # Satır silinmiş
            logger.warning(f"⚠️ '{tab_name}': Satır sayısı azaldı ({last_count} → {total}). Counter sıfırlandı.")
            self._pending_counts[tab_name] = total
            return []

        # Değişiklik yok
        self._pending_counts[tab_name] = total
        return []

    def confirm_processed(self):
        """Lead'ler başarıyla işlendikten sonra pending counts kalıcı olur."""
        if self._pending_counts:
            self._last_row_counts.update(self._pending_counts)
            self._pending_counts.clear()
            self._save_state()
            logger.debug("✅ Satır sayıları onaylandı ve kaydedildi")

    def rollback_pending(self):
        if self._pending_counts:
            logger.info(f"↩️ Pending counts geri alındı: {self._pending_counts}")
            self._pending_counts.clear()

    def poll_all_tabs(self) -> list[dict]:
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
