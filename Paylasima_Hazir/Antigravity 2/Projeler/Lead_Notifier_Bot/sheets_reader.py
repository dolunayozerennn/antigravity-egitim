"""
Google Sheets Okuma Modülü — v2 (Güçlendirilmiş)
Yeni satırları okur ve son okunan durumu kaydeder.

Güçlendirmeler:
  - Railway ephemeral dosya sistemi desteği (env fallback)
  - Google API rate limit (429) retry desteği  
  - HttpError ve ServerHttpError transient olarak işlenir
  - Service yeniden oluşturma mekanizması (uzun süreli kopmalar)
"""
import os
import sys
import json
import time
import logging
from typing import Optional

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
_STATE_FILE = os.path.join(os.path.dirname(__file__), ".last_row_counts.json")

# Railway'de dosya sistemi ephemeral — env variable ile de state tutabilmek lazım
_STATE_ENV_KEY = "LEAD_NOTIFIER_LAST_COUNTS"


class SheetsReader:
    def __init__(self):
        self.service = None
        self._creds = None
        self._last_row_counts: dict[str, int] = self._load_state()
        self._pending_counts: dict[str, int] = {}
        self._consecutive_errors = 0

    # ── STATE YÖNETİMİ ──────────────────────────────────────

    @staticmethod
    def _load_state() -> dict[str, int]:
        """Disk veya env variable'dan state yükler."""
        # 1. Disk'ten dene
        try:
            if os.path.exists(_STATE_FILE):
                with open(_STATE_FILE, "r") as f:
                    data = json.load(f)
                logger.info(f"📂 Önceki satır sayıları yüklendi (disk): {data}")
                return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"⚠️ State dosyası okunamadı: {e}")

        # 2. Env variable'dan dene (Railway restart sonrası)
        env_state = os.environ.get(_STATE_ENV_KEY, "")
        if env_state:
            try:
                data = json.loads(env_state)
                logger.info(f"📂 Önceki satır sayıları yüklendi (env): {data}")
                return data
            except json.JSONDecodeError:
                logger.warning("⚠️ Env state parse edilemedi")

        return {}

    def _save_state(self):
        """State'i hem diske hem memory'ye kaydeder."""
        try:
            with open(_STATE_FILE, "w") as f:
                json.dump(self._last_row_counts, f)
        except OSError as e:
            logger.warning(f"⚠️ State dosyası yazılamadı (ephemeral FS?): {e}")

        # Env variable'a da yaz ki Railway restart sonrası kaybolmasın
        os.environ[_STATE_ENV_KEY] = json.dumps(self._last_row_counts)

    # ── HATA TESPİTİ ────────────────────────────────────────

    @staticmethod
    def _is_transient(err: Exception) -> bool:
        """Geçici (tekrar denenebilir) hata mı kontrol eder."""
        msg = str(err).lower()
        if any(kw in msg for kw in _TRANSIENT_KEYWORDS):
            return True
        # HttpError 429, 500, 502, 503 kodları da transient
        if isinstance(err, HttpError):
            status = err.resp.status if hasattr(err, 'resp') else 0
            if status in (429, 500, 502, 503):
                return True
        return False

    # ── AUTHENTICATION ───────────────────────────────────────

    def authenticate(self):
        """Google Sheets API'ye bağlanır. Tekrar çağrılabilir (reconnect)."""
        sa_info = Config.get_google_credentials_info()

        if sa_info:
            logger.info("🔑 Service Account ile authentication yapılıyor...")
            self._creds = service_account.Credentials.from_service_account_info(
                sa_info, scopes=SCOPES
            )
        else:
            logger.info("🔑 Merkezi google_auth ile authentication yapılıyor (Lokal)...")
            _antigravity_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..")
            )
            sys.path.insert(0, os.path.join(
                _antigravity_root, "_knowledge", "credentials", "oauth"
            ))
            from google_auth import get_sheets_service
            self.service = get_sheets_service("outreach")
            logger.info("✅ Google Sheets API bağlantısı kuruldu (merkezi auth)")
            return

        self.service = build("sheets", "v4", credentials=self._creds)
        logger.info("✅ Google Sheets API bağlantısı kuruldu")

    def _reconnect(self):
        """API bağlantısını yeniden kurar (bağlantı kopmalarında)."""
        logger.info("🔄 Google Sheets API yeniden bağlanılıyor...")
        self.service = None
        try:
            self.authenticate()
        except Exception as e:
            logger.error(f"❌ Yeniden bağlanma başarısız: {e}")
            raise

    # ── VERİ OKUMA ───────────────────────────────────────────

    def get_all_rows(self, tab_name: str) -> list[dict]:
        """Belirtilen tab'daki tüm satırları header'larla birlikte döner.
        Transient hatalar için exponential backoff ile retry yapar.
        """
        if not self.service:
            self.authenticate()

        last_err = None
        for attempt in range(_MAX_RETRIES):
            if attempt > 0:
                # Exponential backoff: 2, 4, 8, 16, 32 saniye
                wait = min(2 ** attempt, 60)
                logger.warning(
                    f"⚠️ '{tab_name}' geçici hata, {wait}s sonra "
                    f"yeniden bağlanılıyor (deneme {attempt + 1}/{_MAX_RETRIES})..."
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

                # Başarılı okuma — hata sayacını sıfırla
                self._consecutive_errors = 0
                return rows

            except Exception as e:
                last_err = e
                if self._is_transient(e) and attempt < _MAX_RETRIES - 1:
                    continue
                # Son deneme veya kalıcı hata
                self._consecutive_errors += 1
                raise

        raise last_err

    # ── YENİ SATIR TESPİTİ ──────────────────────────────────

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
            logger.info(
                f"📊 '{tab_name}': {len(new_rows)} yeni satır bulundu (toplam: {total})"
            )
            return new_rows

        if total < last_count:
            # Satır silinmiş — counter'ı yeni total'e ayarla, kaybetme
            logger.warning(
                f"⚠️ '{tab_name}': Satır sayısı azaldı ({last_count} → {total}). "
                f"Counter güncellendi."
            )
            self._pending_counts[tab_name] = total
            return []

        # Değişiklik yok
        self._pending_counts[tab_name] = total
        return []

    # ── STATE ONAY / GERİ ALMA ──────────────────────────────

    def confirm_processed(self):
        """Lead'ler başarıyla işlendikten sonra pending counts kalıcı olur."""
        if self._pending_counts:
            self._last_row_counts.update(self._pending_counts)
            self._pending_counts.clear()
            self._save_state()
            logger.debug("✅ Satır sayıları onaylandı ve kaydedildi")

    def rollback_pending(self):
        """Hata durumunda pending'i geri al — sonraki döngüde tekrar denensin."""
        if self._pending_counts:
            logger.info(f"↩️ Pending counts geri alındı: {self._pending_counts}")
            self._pending_counts.clear()

    # ── POLL ORCHESTRATOR ────────────────────────────────────

    def poll_all_tabs(self) -> list[dict]:
        """Tüm tab'ları tarar, yeni satırları toplar.
        Tek tab hatası diğer tab'ları engellemez.
        """
        all_new = []
        had_error = False

        for tab_info in Config.SHEET_TABS:
            tab_name = tab_info["name"]
            try:
                new_rows = self.get_new_rows(tab_name)
                for row in new_rows:
                    row["_source_tab"] = tab_name
                all_new.extend(new_rows)
            except Exception as e:
                logger.error(f"❌ '{tab_name}' okunamadı: {e}")
                had_error = True
                # Tek tab hatası diğer tab'ları engellemesin, devam et
                continue

        if had_error and not all_new:
            # Tüm tab'lar hata verdiyse raise et ki main.py rollback yapsın
            raise RuntimeError("Tüm Google Sheets tab'ları okunamadı")

        return all_new

    @property
    def is_healthy(self) -> bool:
        """Ardışık hata sayısını kontrol eder — sağlık durumu."""
        return self._consecutive_errors < 3
