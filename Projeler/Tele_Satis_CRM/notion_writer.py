"""
Tele Satış CRM — Notion Yazma Modülü
Duplikasyon kontrolü + Lead oluşturma.
Doğrudan Notion API kullanır (MCP yok — Railway'de çalışacak).
"""
import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

from config import Config

logger = logging.getLogger(__name__)

NOTION_API_URL = "https://api.notion.com/v1"
WHATSAPP_BASE = "https://wa.me/"
NOTION_VERSION = "2022-06-28"


class NotionWriter:
    """Notion CRM veritabanına lead ekler."""

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {Config.NOTION_API_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }
        self.database_id = Config.NOTION_DATABASE_ID

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

    def _query_recent_leads(self) -> list[dict]:
        """
        Son N gün içinde oluşturulan lead'leri Notion'dan çeker.
        Tüm DB'yi çekmek yerine tarih filtresi uygular → performans.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=Config.DEDUP_WINDOW_DAYS)
        cutoff_iso = cutoff.isoformat()

        url = f"{NOTION_API_URL}/databases/{self.database_id}/query"
        payload = {
            "filter": {
                "property": "Eklendi",
                "created_time": {
                    "on_or_after": cutoff_iso,
                },
            },
            "page_size": 100,
        }

        all_results = []
        has_more = True
        start_cursor = None

        while has_more:
            if start_cursor:
                payload["start_cursor"] = start_cursor

            resp = requests.post(url, headers=self.headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

            all_results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        logger.debug(
            f"📋 Son {Config.DEDUP_WINDOW_DAYS} günden {len(all_results)} kayıt çekildi"
        )
        return all_results

    def _extract_lead_info(self, page: dict) -> dict:
        """Notion page'inden email ve telefon bilgisini çıkarır."""
        props = page.get("properties", {})

        email = ""
        if "email" in props and props["email"].get("email"):
            email = props["email"]["email"].lower()

        phone = ""
        if "Phone" in props and props["Phone"].get("phone_number"):
            phone = re.sub(r"[\s+\-()p:]", "", props["Phone"]["phone_number"])

        created_time = page.get("created_time", "")

        return {
            "email": email,
            "phone": phone,
            "created_time": created_time,
        }

    def check_duplicate(self, clean_email: str, clean_phone: str) -> tuple[bool, str]:
        """
        7 gün kuralı ile duplikasyon kontrolü yapar.
        
        Returns:
            (is_duplicate, match_reason)
        """
        recent_leads = self._query_recent_leads()
        clean_phone_stripped = re.sub(r"[\s+\-()]", "", clean_phone)

        for page in recent_leads:
            info = self._extract_lead_info(page)

            matched_email = info["email"] and info["email"] == clean_email
            matched_phone = (
                info["phone"]
                and clean_phone_stripped
                and info["phone"] == clean_phone_stripped
            )

            if not matched_email and not matched_phone:
                continue

            # Eşleşme var — kaç gün önce oluşturulmuş?
            try:
                created = datetime.fromisoformat(
                    info["created_time"].replace("Z", "+00:00")
                )
                days_ago = (datetime.now(timezone.utc) - created).days
            except (ValueError, TypeError):
                days_ago = 0

            if matched_email and matched_phone:
                reason = f"Email + Telefon eşleşti ({days_ago} gün önce kayıt var)"
            elif matched_email:
                reason = f"Email eşleşti ({days_ago} gün önce kayıt var)"
            else:
                reason = f"Telefon eşleşti ({days_ago} gün önce kayıt var)"

            logger.info(f"🔁 Duplike tespit: {reason}")
            return True, reason

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

        resp = requests.post(url, headers=self.headers, json=payload)
        resp.raise_for_status()

        result = resp.json()
        logger.info(
            f"✅ Lead oluşturuldu: {cleaned_data['clean_name']} "
            f"(ID: {result.get('id', 'bilinmiyor')})"
        )
        return result

    def process_lead(self, cleaned_data: dict) -> dict:
        """
        Tek bir lead'i işler: duplikasyon kontrolü + oluşturma.
        
        Returns:
            {"action": "created"|"skipped"|"error", ...}
        """
        name = cleaned_data["clean_name"]
        email = cleaned_data["clean_email"]
        phone = cleaned_data["clean_phone"]

        try:
            # Duplikasyon kontrolü
            is_dup, reason = self.check_duplicate(email, phone)

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
