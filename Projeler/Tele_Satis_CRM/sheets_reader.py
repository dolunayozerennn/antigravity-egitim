"""
Tele Satış CRM — Google Sheets Okuma Modülü
Google Sheets API v4 ile her iki tab'dan yeni satırları okur.
Production'da Service Account, lokalde merkezi google_auth kullanır.
"""
import os
import sys
import json
import time
import logging
from typing import Optional

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config import Config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Geçici ağ hataları — retry ile kurtarılabilir
_TRANSIENT_KEYWORDS = ["eof", "ssl", "broken pipe", "connection reset",
                       "timeout", "connection aborted", "timed out"]

_MAX_RETRIES = 3

# Persist dosyası — restart'larda _last_row_counts'u korur
_STATE_FILE = os.path.join(os.path.dirname(__file__), ".last_row_counts.json")


class SheetsReader:
    """Google Sheets'ten yeni lead'leri okur."""

    def __init__(self):
        self.service = None
        # Her tab için en son okunan satır sayısını takip eder
        self._last_row_counts: dict[str, int] = self._load_state()

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
        """_last_row_counts'u diske kaydeder (restart koruması)."""
        try:
            with open(_STATE_FILE, "w") as f:
                json.dump(self._last_row_counts, f)
        except OSError as e:
            logger.warning(f"⚠️ State dosyası yazılamadı: {e}")

    @staticmethod
    def _is_transient(err: Exception) -> bool:
        """Geçici ağ hatası mı kontrolü."""
        msg = str(err).lower()
        return any(kw in msg for kw in _TRANSIENT_KEYWORDS)

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
        Geçici ağ hatalarında (SSL EOF, timeout vb.) yeniden bağlanıp tekrar dener.
        """
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
        """
        Sadece son okumadan beri eklenen yeni satırları döner.

        İlk çalıştırmada (crash/restart sonrası): son 48 saatin lead'lerini
        döner. Bunlar Notion'daki duplikasyon kontrolünden geçecek — zaten
        kayıtlı olanlar atlanır, crash sırasında kaçanlar eklenir.
        """
        all_rows = self.get_all_rows(tab_name)
        total = len(all_rows)

        last_count = self._last_row_counts.get(tab_name, 0)

        if last_count == 0:
            # İlk çalıştırma (state dosyası yoksa) —
            # Son 48 saatin satırlarını döndür.
            # Duplikasyon kontrolü zaten var olanları atlayacak,
            # ama crash sırasında kaçanları kurtaracak.
            self._last_row_counts[tab_name] = total
            self._save_state()

            recent_rows = self._filter_recent_rows(all_rows, hours=48)
            if recent_rows:
                logger.info(
                    f"📊 '{tab_name}': İlk çalıştırma — son 48 saatte "
                    f"{len(recent_rows)} satır var, duplikasyon kontrolünden "
                    f"geçirilecek (toplam: {total})"
                )
                return recent_rows

            # created_time sütunu yoksa veya parse edilemezse
            # güvenli fallback: son 50 satırı döndür
            if total > 0:
                fallback_count = min(50, total)
                logger.info(
                    f"📊 '{tab_name}': İlk çalıştırma — created_time yok, "
                    f"son {fallback_count} satır duplikasyon kontrolünden "
                    f"geçirilecek (toplam: {total})"
                )
                return all_rows[-fallback_count:]

            logger.info(
                f"📊 '{tab_name}': İlk okuma — toplam {total} satır mevcut. "
                f"Tabloda kayıt yok."
            )
            return []

        if total > last_count:
            new_rows = all_rows[last_count:]
            self._last_row_counts[tab_name] = total
            self._save_state()
            logger.info(
                f"📊 '{tab_name}': {len(new_rows)} yeni satır bulundu "
                f"(toplam: {total})"
            )
            return new_rows

        if total < last_count:
            # Google Sheet'te satır silinmiş — count sıfırla ve
            # sonraki polling'de doğru yere devam et
            logger.warning(
                f"⚠️ '{tab_name}': Satır sayısı azaldı "
                f"({last_count} → {total}). Sheets'te satır silinmiş olabilir. "
                f"Counter sıfırlandı."
            )
            self._last_row_counts[tab_name] = total
            self._save_state()
            return []

        # Değişiklik yok
        self._last_row_counts[tab_name] = total
        self._save_state()
        return []

    @staticmethod
    def _filter_recent_rows(rows: list[dict], hours: int = 48) -> list[dict]:
        """
        created_time sütununa göre son N saat içindeki satırları filtreler.
        created_time yoksa veya parse edilemezse satır dahil edilmez.
        """
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent = []

        for row in rows:
            raw_time = row.get("created_time", "")
            if not raw_time:
                continue
            try:
                # ISO 8601 formatı: 2026-03-14T00:27:21-05:00
                dt = datetime.fromisoformat(raw_time)
                # timezone-naive ise UTC varsay
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt >= cutoff:
                    recent.append(row)
            except (ValueError, TypeError):
                continue

        return recent

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
