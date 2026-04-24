"""
Google Sheets Okuyucu — v3 (ID Tabanlı State)

ESKİ SORUN: Satır sayısına dayalı state → satır silinince tüm lead'ler tekrar bildiriliyordu
YENİ ÇÖZÜM: Her lead'in benzersiz ID'sini takip et → tekrar bildirim imkansız

Ek filtre: Sadece lead_status == "CREATED" olan lead'ler bildirilir.
"""
import os
import sys
import json
import time
import logging
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import Config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

_TRANSIENT_KEYWORDS = [
    "eof", "ssl", "broken pipe", "connection reset", "timeout",
    "connection aborted", "timed out", "502", "503", "429",
    "rate limit", "quota", "internal error", "backend error",
    "service unavailable", "bad gateway"
]
_MAX_RETRIES = 5
_STATE_FILE = os.path.join(os.path.dirname(__file__), ".seen_lead_ids.json")
_STATE_ENV_KEY = "LEAD_NOTIFIER_SEEN_IDS"


class SheetsReader:
    def __init__(self):
        self.service = None
        self._creds = None
        self._seen_ids: set = self._load_state()
        self._pending_ids: set = set()
        self._consecutive_errors = 0

    # ── STATE YÖNETİMİ ──────────────────────────────────────

    @staticmethod
    def _load_state() -> set:
        """Disk veya env'den seen ID'leri yükler."""
        # 1. Diskten dene
        try:
            if os.path.exists(_STATE_FILE):
                with open(_STATE_FILE, "r") as f:
                    data = json.load(f)
                ids = set(data.get("seen_ids", []))
                logger.info(f"📂 Önceki state yüklendi (disk): {len(ids)} ID")
                return ids
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"⚠️ State dosyası okunamadı: {e}")

        # 2. Env'den dene (Railway restart sonrası)
        env_state = os.environ.get(_STATE_ENV_KEY, "")
        if env_state:
            try:
                data = json.loads(env_state)
                ids = set(data.get("seen_ids", []))
                logger.info(f"📂 Önceki state yüklendi (env): {len(ids)} ID")
                return ids
            except json.JSONDecodeError:
                logger.warning("⚠️ Env state parse edilemedi")

        return set()

    def _save_state(self):
        """State'i hem diske hem env'ye kaydeder."""
        state_data = {
            "seen_ids": list(self._seen_ids),
            "last_updated": datetime.now().isoformat()
        }

        try:
            with open(_STATE_FILE, "w") as f:
                json.dump(state_data, f)
        except OSError as e:
            logger.warning(f"⚠️ State dosyası yazılamadı (ephemeral FS?): {e}")

        os.environ[_STATE_ENV_KEY] = json.dumps(state_data)

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
                rows = []
                for row_values in values[1:]:
                    row_dict = {}
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
        2. lead_status == "CREATED" olanları filtrele
        3. ID'si seen_ids'de olmayanları yeni kabul et
        4. İlk çalıştırmada tüm mevcut ID'leri kaydet (bildirim yapma)
        """
        all_rows = self._fetch_all_rows()

        if not all_rows:
            logger.info("📭 Sheet boş veya okunamadı")
            return []

        # lead_status == "CREATED" filtresi
        created_rows = [
            row for row in all_rows
            if row.get("lead_status", "").strip().upper() == "CREATED"
        ]

        logger.debug(
            f"📊 Toplam: {len(all_rows)}, "
            f"CREATED: {len(created_rows)}, "
            f"Seen: {len(self._seen_ids)}"
        )

        # İlk çalıştırma — tüm mevcut lead'leri "görüldü" olarak kaydet
        if not self._seen_ids:
            all_ids = {
                row.get("id", "").strip()
                for row in created_rows
                if row.get("id", "").strip()
            }
            if all_ids:
                self._seen_ids = all_ids
                self._save_state()
                logger.info(
                    f"📊 İlk çalıştırma — Mevcut {len(all_ids)} CREATED lead "
                    "atlanıyor. Bundan sonraki yeni lead'ler bildirilecek."
                )
            return []

        # Yeni lead tespiti
        new_leads = []
        for row in created_rows:
            lead_id = row.get("id", "").strip()
            if not lead_id:
                continue
            if lead_id not in self._seen_ids:
                new_leads.append(row)
                self._pending_ids.add(lead_id)

        if new_leads:
            logger.info(f"📥 {len(new_leads)} yeni CREATED lead bulundu")

        return new_leads

    # ── STATE ONAY / GERİ ALMA ──────────────────────────────

    def confirm_processed(self):
        """Başarılı bildirim sonrası pending ID'leri seen'e taşı."""
        if self._pending_ids:
            self._seen_ids.update(self._pending_ids)
            self._pending_ids.clear()
            self._save_state()
            logger.debug("✅ Yeni ID'ler kaydedildi")

    def rollback_pending(self):
        """Hata durumunda pending'i geri al — sonraki döngüde tekrar denensin."""
        if self._pending_ids:
            logger.info(f"↩️ {len(self._pending_ids)} pending ID geri alındı")
            self._pending_ids.clear()

    @property
    def is_healthy(self) -> bool:
        """Ardışık hata sayısına dayalı sağlık durumu."""
        return self._consecutive_errors < 3
