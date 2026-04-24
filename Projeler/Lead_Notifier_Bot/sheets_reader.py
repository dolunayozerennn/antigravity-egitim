"""
Google Sheets Okuyucu — v3 (Tamamen Stateless)

ESKİ SORUN: Yerel dosya (seen_ids) veya RAM tabanlı state, Railway gibi geçici dosya sistemlerinde restart anında "cold start amnesia" veya "spam" yaratıyordu.
YENİ ÇÖZÜM: Single Source of Truth = Google Sheets. Bot sadece `lead_status == "CREATED"` satırlarını alır.
Bildirim başarılı olunca o hücre `NOTIFIED` olarak güncellenir. Eğer bot çökerse bile veri Google Sheets'te "CREATED" kalacağı için hiçbir bildirim kaçırılmaz.
"""
import os
import sys
import time
import logging
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import Config

logger = logging.getLogger(__name__)

# Yazma yetkisi eklendi (.readonly kaldırıldı)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_TRANSIENT_KEYWORDS = [
    "eof", "ssl", "broken pipe", "connection reset", "timeout",
    "connection aborted", "timed out", "502", "503", "429",
    "rate limit", "quota", "internal error", "backend error",
    "service unavailable", "bad gateway"
]
_MAX_RETRIES = 5


def get_column_letter(col_idx: int) -> str:
    """0-based index'i Excel sütun harfine çevirir (0=A, 25=Z, 26=AA)"""
    letters = ""
    col_idx += 1
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


class SheetsReader:
    def __init__(self):
        self.service = None
        self._creds = None
        self._consecutive_errors = 0
        self._status_col_letter = None

    # ── HATA TESPİTİ ────────────────────────────────────────

    @staticmethod
    def _is_transient(err: Exception) -> bool:
        """Geçici (tekrar denenebilir) hata mı?"""
        msg = str(err).lower()
        if any(kw in msg for kw in _TRANSIENT_KEYWORDS):
            return True
        if isinstance(err, HttpError):
            status = err.resp.status if hasattr(err, 'resp') else 0
            if status in (429, 500, 502, 503):
                return True
        return False

    # ── AUTHENTICATION ───────────────────────────────────────

    def authenticate(self):
        """Google Sheets API bağlantısı kurar."""
        sa_info = Config.get_google_credentials_info()

        if sa_info:
            logger.info("🔑 Service Account ile auth...")
            self._creds = service_account.Credentials.from_service_account_info(
                sa_info, scopes=SCOPES
            )
            self.service = build("sheets", "v4", credentials=self._creds)
        else:
            logger.info("🔑 Merkezi google_auth ile auth (lokal)...")
            _root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..")
            )
            sys.path.insert(0, os.path.join(
                _root, "_knowledge", "credentials", "oauth"
            ))
            from google_auth import get_sheets_service
            self.service = get_sheets_service("outreach")

        logger.info("✅ Google Sheets API bağlantısı kuruldu")

    def _reconnect(self):
        """API bağlantısını yenile."""
        logger.info("🔄 Sheets API yeniden bağlanılıyor...")
        self.service = None
        self.authenticate()

    # ── VERİ OKUMA ───────────────────────────────────────────

    def _fetch_all_rows(self) -> list[dict]:
        """Sheet'ten tüm satırları header'larla birlikte oku.
        Sütun isimlerinden `lead_status` sütununu bulup harfini _status_col_letter olarak kaydeder.
        Transient hatalar için exponential backoff ile retry yapar.
        """
        if not self.service:
            self.authenticate()

        last_err = None
        for attempt in range(_MAX_RETRIES):
            if attempt > 0:
                wait = min(2 ** attempt, 60)
                logger.warning(
                    f"⚠️ Retry {attempt + 1}/{_MAX_RETRIES}, "
                    f"{wait}s bekleniyor..."
                )
                time.sleep(wait)
                try:
                    self._reconnect()
                except Exception:
                    continue

            try:
                result = (
                    self.service.spreadsheets()
                    .values()
                    .get(
                        spreadsheetId=Config.SPREADSHEET_ID,
                        range=f"'{Config.SHEET_TAB}'!A:Z",
                    )
                    .execute()
                )

                values = result.get("values", [])
                if not values or len(values) < 2:
                    return []

                headers = [h.strip().lower() for h in values[0]]
                
                # Sütun harfini dinamik olarak tespit et
                if "lead_status" in headers:
                    status_col_idx = headers.index("lead_status")
                    self._status_col_letter = get_column_letter(status_col_idx)
                else:
                    self._status_col_letter = None

                rows = []
                # Header satırı 1 kabul edilir, veri 2. satırdan başlar.
                for idx, row_values in enumerate(values[1:], start=2):
                    row_dict = {"__row_index__": idx}
                    for i, header in enumerate(headers):
                        row_dict[header] = row_values[i] if i < len(row_values) else ""
                    rows.append(row_dict)

                self._consecutive_errors = 0
                return rows

            except Exception as e:
                last_err = e
                if self._is_transient(e) and attempt < _MAX_RETRIES - 1:
                    continue
                self._consecutive_errors += 1
                raise

        raise last_err

    # ── YENİ LEAD TESPİTİ ───────────────────────────────────

    def get_new_leads(self) -> list[dict]:
        """
        Yeni lead'leri tespit eder.
        
        Mantık:
        1. Tüm satırları oku
        2. lead_status == "CREATED" olanları filtrele (Google Sheets'te manuel "CREATED" yazılmış veya webhook ile gelmiş)
        """
        all_rows = self._fetch_all_rows()

        if not all_rows:
            logger.info("📭 Sheet boş veya okunamadı")
            return []

        # lead_status == "CREATED" filtresi
        new_leads = [
            row for row in all_rows
            if row.get("lead_status", "").strip().upper() == "CREATED"
        ]

        if new_leads:
            logger.info(f"📥 {len(new_leads)} yeni CREATED lead bulundu (Stateless Mod)")

        return new_leads

    # ── GOOGLE SHEETS GÜNCELLEME ─────────────────────────────

    def mark_as_notified(self, row_indices: list[int]):
        """Google Sheets'te ilgili satırların lead_status değerlerini 'NOTIFIED' yapar."""
        if not self.service:
            logger.error("❌ API bağlı değil.")
            return

        if not getattr(self, "_status_col_letter", None):
            logger.error("❌ 'lead_status' sütunu bulunamadı! Güncelleme yapılamıyor.")
            return

        data = []
        for r_idx in row_indices:
            range_name = f"'{Config.SHEET_TAB}'!{self._status_col_letter}{r_idx}"
            data.append({
                "range": range_name,
                "values": [["NOTIFIED"]]
            })

        body = {
            "valueInputOption": "USER_ENTERED",
            "data": data
        }

        try:
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=Config.SPREADSHEET_ID,
                body=body
            ).execute()
            logger.info(f"✅ {len(row_indices)} lead Google Sheets üzerinde 'NOTIFIED' olarak güncellendi.")
        except Exception as e:
            logger.error(f"❌ Google Sheets update hatası: {e}", exc_info=True)
            self._consecutive_errors += 1

    @property
    def is_healthy(self) -> bool:
        """Ardışık hata sayısına dayalı sağlık durumu."""
        return self._consecutive_errors < 3
