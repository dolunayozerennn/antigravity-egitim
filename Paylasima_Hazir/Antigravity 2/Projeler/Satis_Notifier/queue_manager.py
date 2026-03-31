"""
Tele Satış Notifier — Kuyruk Yönetim Modülü (Google Sheets Tabanlı)
Bekleyen lead'leri Google Sheets'te kalıcı olarak saklar.
Akşam 6 ve haftasonu kuyruklarını yönetir.

Railway'de her deploy/restart'ta veri kaybolmaz.
Aynı spreadsheet'e "Kuyruk" tab'ı eklenir.
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import Config

logger = logging.getLogger(__name__)

# Kuyruk sheet ayarları
_QUEUE_TAB = "Kuyruk"
_HEADERS = ["name", "phone", "email", "budget", "timing", "source_tab",
            "queue_type", "target_date", "added_date", "status"]

# Retry ayarları
_MAX_RETRIES = 3


class QueueManager:
    """Zamanlama kuyruğunu Google Sheets üzerinde yönetir."""

    def __init__(self, sheets_service=None):
        """
        Args:
            sheets_service: Mevcut Google Sheets API service nesnesi.
                           None ise kendi auth'unu yapar.
        """
        self.service = sheets_service
        self._ensure_queue_tab()

    # ── AUTHENTICATION ───────────────────────────────────

    def _authenticate(self):
        """SheetsReader ile aynı auth mekanizması."""
        import sys

        # 1. GONDEREN_EMAIL_BURAYA OAuth token (Railway - birincil)
        env_token = os.environ.get("GOOGLE_SECONDARY_TOKEN_JSON", "")
        if env_token:
            try:
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request

                token_data = json.loads(env_token)
                scopes = ["https://www.googleapis.com/auth/spreadsheets"]
                creds = Credentials.from_authorized_user_info(token_data, scopes)
                if not creds.valid:
                    if creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        raise RuntimeError("OAuth token geçersiz ve yenilenemiyor")
                self.service = build("sheets", "v4", credentials=creds)
                logger.info("✅ QueueManager: Sheets API bağlantısı kuruldu (OAuth2)")
                return
            except Exception as e:
                logger.warning(f"⚠️ QueueManager OAuth auth başarısız: {e}")

        # 2. Service Account (Railway fallback)
        sa_info = Config.get_google_credentials_info()
        if sa_info:
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            creds = service_account.Credentials.from_service_account_info(
                sa_info, scopes=scopes
            )
            self.service = build("sheets", "v4", credentials=creds)
            logger.info("✅ QueueManager: Sheets API bağlantısı kuruldu (Service Account)")
            return

        # 3. Lokal: merkezi google_auth
        _antigravity_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        sys.path.insert(0, os.path.join(
            _antigravity_root, "_knowledge", "credentials", "oauth"
        ))
        from google_auth import get_sheets_service
        self.service = get_sheets_service("outreach")
        logger.info("✅ QueueManager: Sheets API bağlantısı kuruldu (merkezi auth)")

    # ── RETRY WRAPPER ────────────────────────────────────

    @staticmethod
    def _is_transient(err: Exception) -> bool:
        """Gerçek Exception sınıfları ile geçici ağ ve sunucu hatalarını tespit eder."""
        import ssl
        import socket
        from urllib.error import URLError
        from requests.exceptions import RequestException

        if isinstance(err, (ssl.SSLError, socket.timeout, socket.error, URLError, RequestException)):
            return True
            
        if isinstance(err, HttpError):
            status = err.resp.status if hasattr(err, 'resp') else 0
            if status in (429, 500, 502, 503, 504):
                return True
        return False

    def _retry_call(self, func, *args, **kwargs):
        """API çağrısını retry ile yapar."""
        last_err = None
        for attempt in range(_MAX_RETRIES):
            if attempt > 0:
                wait = min(2 ** attempt, 30)
                logger.warning(f"⚠️ Kuyruk API retry {attempt + 1}/{_MAX_RETRIES}, {wait}s bekleniyor...")
                time.sleep(wait)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_err = e
                if self._is_transient(e) and attempt < _MAX_RETRIES - 1:
                    continue
                raise
        raise last_err

    # ── SHEET KURULUM ────────────────────────────────────

    def _ensure_queue_tab(self):
        """'Kuyruk' tab'ını kontrol eder, yoksa oluşturur ve header ekler."""
        if not self.service:
            self._authenticate()

        try:
            # Spreadsheet metadata'sını al
            spreadsheet = self._retry_call(
                self.service.spreadsheets().get(
                    spreadsheetId=Config.SPREADSHEET_ID,
                    fields="sheets.properties.title"
                ).execute
            )

            existing_tabs = [
                s["properties"]["title"]
                for s in spreadsheet.get("sheets", [])
            ]

            if _QUEUE_TAB in existing_tabs:
                logger.info(f"📂 '{_QUEUE_TAB}' tab'ı mevcut")
                # Header'ları kontrol et
                self._ensure_headers()
                return

            # Tab'ı oluştur
            logger.info(f"📝 '{_QUEUE_TAB}' tab'ı oluşturuluyor...")
            body = {
                "requests": [{
                    "addSheet": {
                        "properties": {
                            "title": _QUEUE_TAB,
                            "gridProperties": {
                                "rowCount": 1000,
                                "columnCount": len(_HEADERS)
                            }
                        }
                    }
                }]
            }
            self._retry_call(
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=Config.SPREADSHEET_ID,
                    body=body
                ).execute
            )

            # Header'ları yaz
            self._retry_call(
                self.service.spreadsheets().values().update(
                    spreadsheetId=Config.SPREADSHEET_ID,
                    range=f"'{_QUEUE_TAB}'!A1:{chr(64 + len(_HEADERS))}1",
                    valueInputOption="RAW",
                    body={"values": [_HEADERS]}
                ).execute
            )

            logger.info(f"✅ '{_QUEUE_TAB}' tab'ı oluşturuldu ve header'lar eklendi")

        except Exception as e:
            logger.error(f"❌ Kuyruk tab'ı oluşturulamadı: {e}")
            raise

    def _ensure_headers(self):
        """Header'ların doğru olup olmadığını kontrol eder, yoksa yazar."""
        try:
            result = self._retry_call(
                self.service.spreadsheets().values().get(
                    spreadsheetId=Config.SPREADSHEET_ID,
                    range=f"'{_QUEUE_TAB}'!A1:{chr(64 + len(_HEADERS))}1"
                ).execute
            )
            values = result.get("values", [])
            if not values or values[0] != _HEADERS:
                logger.info("📝 Kuyruk header'ları güncelleniyor...")
                self._retry_call(
                    self.service.spreadsheets().values().update(
                        spreadsheetId=Config.SPREADSHEET_ID,
                        range=f"'{_QUEUE_TAB}'!A1:{chr(64 + len(_HEADERS))}1",
                        valueInputOption="RAW",
                        body={"values": [_HEADERS]}
                    ).execute
                )
        except Exception as e:
            logger.warning(f"⚠️ Header kontrolü başarısız: {e}")

    # ── VERİ OKUMA ───────────────────────────────────────

    def _read_all_queue_rows(self) -> list[dict]:
        """Kuyruk tab'ındaki tüm satırları dict olarak döner."""
        try:
            # Header'ları oku (1. satır)
            result = self._retry_call(
                self.service.spreadsheets().values().get(
                    spreadsheetId=Config.SPREADSHEET_ID,
                    range=f"'{_QUEUE_TAB}'!A:J"
                ).execute
            )
            values = result.get("values", [])
            if not values or len(values) < 2:
                return []

            headers = values[0]
            rows = []
            for i, row_values in enumerate(values[1:], start=2):
                row_dict = {"_row_index": i}  # Sheets satır numarası (Update için tutuyoruz)
                for j, header in enumerate(headers):
                    row_dict[header] = row_values[j] if j < len(row_values) else ""
                rows.append(row_dict)
            return rows

        except Exception as e:
            logger.error(f"❌ Kuyruk okunamadı: {e}")
            return []

    # ── AKŞAM 6 KUYRUĞU ─────────────────────────────────

    def add_to_evening_queue(self, lead_info: dict, target_date: str):
        """
        Akşam 6 kuyruğuna lead ekler (Sheets'e satır yazar).

        Args:
            lead_info: extract_lead_info() çıktısı
            target_date: YYYY-MM-DD formatında hedef gün
        """
        row = [
            lead_info.get("name", ""),
            lead_info.get("phone", ""),
            lead_info.get("email", ""),
            lead_info.get("budget", ""),
            lead_info.get("timing", ""),
            lead_info.get("source_tab", ""),
            "aksam_6",
            target_date,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bekliyor" # Status
        ]

        try:
            self._retry_call(
                self.service.spreadsheets().values().append(
                    spreadsheetId=Config.SPREADSHEET_ID,
                    range=f"'{_QUEUE_TAB}'!A:J",
                    valueInputOption="RAW",
                    insertDataOption="INSERT_ROWS",
                    body={"values": [row]}
                ).execute
            )
            logger.info(
                f"📥 Akşam 6 kuyruğuna eklendi (Sheets): {lead_info['name']} "
                f"(hedef: {target_date} 18:00)"
            )
        except Exception as e:
            logger.error(f"❌ Akşam 6 kuyruğuna eklenemedi: {e}")
            raise

    def get_evening_leads(self, target_date: str) -> list[dict]:
        """Belirli bir gün için akşam 6 kuyruğundaki lead'leri döner."""
        all_rows = self._read_all_queue_rows()
        leads = []
        for row in all_rows:
            if row.get("queue_type") == "aksam_6" and row.get("target_date") == target_date and row.get("status") != "gonderildi":
                leads.append(self._row_to_lead(row))
        return leads

    def clear_evening_queue(self, target_date: str):
        """Belirli bir günün akşam 6 kuyruğunu temizler (Status'u 'gonderildi' yapar)."""
        all_rows = self._read_all_queue_rows()
        rows_to_update = [
            row["_row_index"]
            for row in all_rows
            if row.get("queue_type") == "aksam_6" and row.get("target_date") == target_date and row.get("status") != "gonderildi"
        ]

        if rows_to_update:
            self._mark_rows_as_sent(rows_to_update)
            logger.info(f"🗑️ Akşam 6 kuyruğu gönderildi olarak işaretlendi ({target_date}): {len(rows_to_update)} lead")
        else:
            logger.info(f"📭 Akşam 6 kuyruğunda işaretlenecek satır yok ({target_date})")

    # ── HAFTASONU KUYRUĞU ────────────────────────────────

    def add_to_weekend_queue(self, lead_info: dict):
        """Haftasonu kuyruğuna lead ekler (Sheets'e satır yazar)."""
        row = [
            lead_info.get("name", ""),
            lead_info.get("phone", ""),
            lead_info.get("email", ""),
            lead_info.get("budget", ""),
            lead_info.get("timing", ""),
            lead_info.get("source_tab", ""),
            "haftasonu",
            "",  # target_date yok, haftasonu gelince gönderilir
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bekliyor" # Status
        ]

        try:
            self._retry_call(
                self.service.spreadsheets().values().append(
                    spreadsheetId=Config.SPREADSHEET_ID,
                    range=f"'{_QUEUE_TAB}'!A:J",
                    valueInputOption="RAW",
                    insertDataOption="INSERT_ROWS",
                    body={"values": [row]}
                ).execute
            )
            logger.info(
                f"📥 Haftasonu kuyruğuna eklendi (Sheets): {lead_info['name']} "
                f"(Cumartesi 10:00'da gönderilecek)"
            )
        except Exception as e:
            logger.error(f"❌ Haftasonu kuyruğuna eklenemedi: {e}")
            raise

    def get_weekend_leads(self) -> list[dict]:
        """Haftasonu kuyruğundaki tüm lead'leri döner."""
        all_rows = self._read_all_queue_rows()
        leads = []
        for row in all_rows:
            if row.get("queue_type") == "haftasonu" and row.get("status") != "gonderildi":
                leads.append(self._row_to_lead(row))
        return leads

    def clear_weekend_queue(self):
        """Haftasonu kuyruğunu tamamen temizler (Status'u 'gonderildi' yapar)."""
        all_rows = self._read_all_queue_rows()
        rows_to_update = [
            row["_row_index"]
            for row in all_rows
            if row.get("queue_type") == "haftasonu" and row.get("status") != "gonderildi"
        ]

        if rows_to_update:
            self._mark_rows_as_sent(rows_to_update)
            logger.info(f"🗑️ Haftasonu kuyruğu gönderildi olarak işaretlendi: {len(rows_to_update)} lead")
        else:
            logger.info("📭 Haftasonu kuyruğunda işaretlenecek satır yok")

    # ── YARDIMCI METODLAR ────────────────────────────────

    @staticmethod
    def _row_to_lead(row: dict) -> dict:
        """Sheets satırını lead_info dict'ine dönüştürür."""
        return {
            "name": row.get("name", ""),
            "phone": row.get("phone", ""),
            "email": row.get("email", ""),
            "budget": row.get("budget", ""),
            "timing": row.get("timing", ""),
            "source_tab": row.get("source_tab", ""),
        }

    def _mark_rows_as_sent(self, row_indices: list[int]):
        """Belirtilen satır numaralarının 'status' (J) sütununu 'gonderildi' olarak günceller."""
        try:
            data = []
            for row_idx in row_indices:
                data.append({
                    "range": f"'{_QUEUE_TAB}'!J{row_idx}",
                    "values": [["gonderildi"]]
                })
            
            if data:
                self._retry_call(
                    self.service.spreadsheets().values().batchUpdate(
                        spreadsheetId=Config.SPREADSHEET_ID,
                        body={
                            "valueInputOption": "RAW",
                            "data": data
                        }
                    ).execute
                )
        except Exception as e:
            logger.error(f"❌ Satır durumunu güncelleme hatası: {e}")
            raise

    # ── DURUM BİLGİSİ ────────────────────────────────────

    @property
    def evening_count(self) -> int:
        all_rows = self._read_all_queue_rows()
        return sum(1 for r in all_rows if r.get("queue_type") == "aksam_6")

    @property
    def weekend_count(self) -> int:
        all_rows = self._read_all_queue_rows()
        return sum(1 for r in all_rows if r.get("queue_type") == "haftasonu")

    def get_status(self) -> dict:
        """Kuyruk durumunu döner (sadece bekleyenler)."""
        all_rows = self._read_all_queue_rows()
        aksam = sum(1 for r in all_rows if r.get("queue_type") == "aksam_6" and r.get("status") != "gonderildi")
        haftsonu = sum(1 for r in all_rows if r.get("queue_type") == "haftasonu" and r.get("status") != "gonderildi")
        return {
            "aksam_6": aksam,
            "haftasonu": haftsonu,
        }
