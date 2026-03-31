"""
Tele Satış CRM — Notion Yazma Modülü
Duplikasyon kontrolü + Lead oluşturma.
Doğrudan Notion API kullanır (MCP yok — Railway'de çalışacak).
"""
import re
import time
import logging

import requests
from requests.exceptions import ConnectionError, Timeout

from config import Config

logger = logging.getLogger(__name__)

NOTION_API_URL = "https://api.notion.com/v1"
WHATSAPP_BASE = "https://wa.me/"
NOTION_VERSION = "2022-06-28"

# Geçici API hataları — retry ile kurtarabileceğimiz HTTP status kodları
_RETRYABLE_STATUS_CODES = {429, 502, 503, 504}


class NotionWriter:
    """Notion CRM veritabanına lead ekler."""

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {Config.NOTION_API_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }
        self.database_id = Config.NOTION_DATABASE_ID
        self._rate_limit_delay = Config.NOTION_RATE_LIMIT_DELAY
        self._max_retries = Config.NOTION_MAX_RETRIES

    @staticmethod
    def _build_whatsapp_link(phone: str) -> str:
        """
        Telefon numarasından WhatsApp linki üretir.
        Boşluk, +, -, (, ) gibi karakterleri temizler.
        Örnek: '+90 532 123 4567' → 'https://wa.me/905321234567'
        """
        if not phone:
            return ""
        digits = re.sub(r"[^\d]", "", phone)
        return f"{WHATSAPP_BASE}{digits}" if digits else ""

    def _api_call(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Notion API çağrısı yapar.
        - Rate limit delay uygular (429 önleme)
        - Geçici hatalarda (429, 502, 503, timeout) otomatik retry yapar
        """
        last_err = None
        for attempt in range(self._max_retries):
            try:
                if attempt > 0:
                    wait = 2 ** attempt
                    logger.warning(
                        f"⚠️ Notion API geçici hata, {wait}s sonra tekrar "
                        f"deneniyor (deneme {attempt + 1}/{self._max_retries})..."
                    )
                    time.sleep(wait)

                resp = getattr(requests, method)(url, headers=self.headers, **kwargs)

                # Rate limit aşıldı veya geçici sunucu hatası
                if resp.status_code in _RETRYABLE_STATUS_CODES:
                    retry_after = float(resp.headers.get("Retry-After", 2 ** attempt))
                    logger.warning(
                        f"⚠️ Notion {resp.status_code}, {retry_after}s bekleniyor..."
                    )
                    time.sleep(retry_after)
                    last_err = requests.HTTPError(response=resp)
                    continue

                resp.raise_for_status()

                # Başarılı çağrıdan sonra rate limit delay
                time.sleep(self._rate_limit_delay)
                return resp

            except (ConnectionError, Timeout) as e:
                last_err = e
                if attempt < self._max_retries - 1:
                    continue
                raise

        # Tüm denemeler başarısız
        if isinstance(last_err, requests.HTTPError):
            raise last_err
        raise last_err  # type: ignore

    def _query_by_phone(self, phone: str) -> list[dict]:
        """Notion'da telefon numarasına göre lead arar."""
        url = f"{NOTION_API_URL}/databases/{self.database_id}/query"
        payload = {
            "filter": {
                "property": "Phone",
                "phone_number": {"equals": phone},
            },
            "page_size": 1,
        }
        resp = self._api_call("post", url, json=payload)
        return resp.json().get("results", [])

    def _query_by_email(self, email: str) -> list[dict]:
        """Notion'da email adresine göre lead arar."""
        url = f"{NOTION_API_URL}/databases/{self.database_id}/query"
        payload = {
            "filter": {
                "property": "email",
                "email": {"equals": email},
            },
            "page_size": 1,
        }
        resp = self._api_call("post", url, json=payload)
        return resp.json().get("results", [])

    def _query_by_name(self, name: str) -> list[dict]:
        """Notion'da isime göre lead arar (email+telefon yoksa fallback)."""
        url = f"{NOTION_API_URL}/databases/{self.database_id}/query"
        payload = {
            "filter": {
                "property": "İsim",
                "title": {"equals": name},
            },
            "page_size": 1,
        }
        resp = self._api_call("post", url, json=payload)
        return resp.json().get("results", [])

    def bulk_check_duplicates(self, leads: list[dict]) -> tuple[set, set, set]:
        """
        Notion üzerinde toplu (bulk) duplikasyon kontrolü yapar.
        Belirtilen lead'lerin telefon, email veya isimlerini OR filtresi ile tek/az sayıda sorguda kontrol eder.
        
        Returns:
            (existing_phones, existing_emails, existing_names)
        """
        existing_phones = set()
        existing_emails = set()
        existing_names = set()
        
        if not leads:
            return existing_phones, existing_emails, existing_names
            
        # Notion API OR filter 100 condition ile sınırlı. Batch başı 30 lead alıroruz (30 leads * 3 durum = mx 90 conditions).
        batch_size = 30
        for i in range(0, len(leads), batch_size):
            batch = leads[i:i+batch_size]
            or_conditions = []
            
            for lead in batch:
                if lead["clean_phone"]:
                    or_conditions.append({
                        "property": "Phone",
                        "phone_number": {"equals": lead["clean_phone"]}
                    })
                if lead["clean_email"]:
                    or_conditions.append({
                        "property": "email",
                        "email": {"equals": lead["clean_email"]}
                    })
                # Sadece telefonu ve emaili olmayan yetim isimleri kontrole sok
                if not lead["clean_phone"] and not lead["clean_email"] and lead["clean_name"]:
                    or_conditions.append({
                        "property": "İsim",
                        "title": {"equals": lead["clean_name"]}
                    })
            
            if not or_conditions:
                continue
                
            payload = {
                "filter": {"or": or_conditions},
                "page_size": 100
            }
            url = f"{NOTION_API_URL}/databases/{self.database_id}/query"
            
            has_more = True
            next_cursor = None
            
            while has_more:
                if next_cursor:
                    payload["start_cursor"] = next_cursor
                    
                resp = self._api_call("post", url, json=payload)
                data = resp.json()
                results = data.get("results", [])
                
                for page in results:
                    props = page.get("properties", {})
                    
                    # Extract phone
                    phone_prop = props.get("Phone", {})
                    if phone_prop.get("phone_number"):
                        existing_phones.add(phone_prop["phone_number"])
                        
                    # Extract email
                    email_prop = props.get("email", {})
                    if email_prop.get("email"):
                        existing_emails.add(email_prop["email"])
                        
                    # Extract name
                    name_prop = props.get("İsim", {})
                    title_arr = name_prop.get("title", [])
                    if title_arr and title_arr[0].get("text", {}).get("content"):
                        existing_names.add(title_arr[0]["text"]["content"])
                        
                has_more = data.get("has_more", False)
                next_cursor = data.get("next_cursor")
                
        return existing_phones, existing_emails, existing_names

    def check_duplicate(self, clean_email: str, clean_phone: str,
                        clean_name: str = "") -> tuple[bool, str]:
        """
        Notion API filtresi ile duplikasyon kontrolü yapar.
        Telefon veya email ile doğrudan sorgular — tarih penceresi yok.

        Returns:
            (is_duplicate, match_reason)
        """
        # 1) Telefon ile kontrol
        if clean_phone:
            results = self._query_by_phone(clean_phone)
            if results:
                logger.info(f"🔁 Duplike tespit: Telefon eşleşti ({clean_phone})")
                return True, f"Telefon eşleşti ({clean_phone})"

        # 2) Email ile kontrol
        if clean_email:
            results = self._query_by_email(clean_email)
            if results:
                logger.info(f"🔁 Duplike tespit: Email eşleşti ({clean_email})")
                return True, f"Email eşleşti ({clean_email})"

        # 3) Ne email ne telefon varsa, isim ile fallback
        if not clean_phone and not clean_email and clean_name:
            results = self._query_by_name(clean_name)
            if results:
                logger.info(f"🔁 Duplike tespit: İsim eşleşti ({clean_name})")
                return True, f"İsim eşleşti ({clean_name})"

        return False, ""

    def create_lead(self, cleaned_data: dict) -> dict:
        """
        Yeni lead'i Notion veritabanına ekler.
        
        Args:
            cleaned_data: clean_lead() fonksiyonundan dönen temizlenmiş veri
            
        Returns:
            Notion API response
        """
        url = f"{NOTION_API_URL}/pages"

        # Properties oluştur
        properties = {
            "İsim": {
                "title": [
                    {
                        "text": {
                            "content": cleaned_data["clean_name"] or "İsimsiz Lead"
                        }
                    }
                ]
            },
            "Durum": {
                "status": {"name": "Aranacak"}
            },
            "Komisyon": {
                "select": {"name": "Ödenmedi"}
            },
        }

        # Email (boş olmayabilir)
        if cleaned_data["clean_email"]:
            properties["email"] = {"email": cleaned_data["clean_email"]}

        # Telefon + WhatsApp Link
        if cleaned_data["clean_phone"]:
            properties["Phone"] = {
                "phone_number": cleaned_data["clean_phone"]
            }
            # WhatsApp linkini Python'da hesapla (Notion formula yerine)
            wa_link = self._build_whatsapp_link(cleaned_data["clean_phone"])
            if wa_link:
                properties["WhatsApp Link"] = {"url": wa_link}

        # Bütçe (boş olabilir — select alanı)
        if cleaned_data["clean_budget"]:
            properties["Bütçe"] = {
                "select": {"name": cleaned_data["clean_budget"]}
            }

        # Ulaşım Zamanı
        if cleaned_data.get("clean_timing"):
            properties["Ne zaman ulaşalım?"] = {
                "select": {"name": cleaned_data["clean_timing"]}
            }

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
        }

        resp = self._api_call("post", url, json=payload)

        result = resp.json()
        logger.info(
            f"✅ Lead oluşturuldu: {cleaned_data['clean_name']} "
            f"(ID: {result.get('id', 'bilinmiyor')})"
        )
        return result

    def process_lead(self, cleaned_data: dict, skip_duplicate_check: bool = False) -> dict:
        """
        Tek bir lead'i işler: duplikasyon kontrolü + oluşturma.
        
        Args:
            cleaned_data: data_cleaner'dan geçen temizli veri
            skip_duplicate_check: true ise Notion API ile duplicate kontrolünü atlar (bulk kontrol yapıldıysa)
            
        Returns:
            {"action": "created"|"skipped"|"error", ...}
        """
        name = cleaned_data["clean_name"]
        email = cleaned_data["clean_email"]
        phone = cleaned_data["clean_phone"]

        try:
            # Duplikasyon kontrolü
            if not skip_duplicate_check:
                is_dup, reason = self.check_duplicate(email, phone, name)
    
                if is_dup:
                    return {
                        "action": "skipped",
                        "name": name,
                        "reason": reason,
                    }

            # Yeni lead — Notion'a ekle
            result = self.create_lead(cleaned_data)
            return {
                "action": "created",
                "name": name,
                "notion_id": result.get("id"),
            }

        except (ConnectionError, Timeout) as e:
            # Geçici ağ hatası — bu lead'i atlamak yerine yukarı fırlat,
            # böylece döngü durur ve sonraki polling'de tekrar denenir
            logger.error(f"❌ Geçici ağ hatası ({name}): {e}")
            raise

        except requests.HTTPError as e:
            error_msg = str(e)
            try:
                error_body = e.response.json()
                error_msg = error_body.get("message", str(e))
            except Exception:
                pass

            logger.error(f"❌ Lead işlenirken hata: {name} — {error_msg}")
            return {
                "action": "error",
                "name": name,
                "error": error_msg,
            }
        except Exception as e:
            logger.error(f"❌ Beklenmeyen hata: {name} — {e}")
            return {
                "action": "error",
                "name": name,
                "error": str(e),
            }
