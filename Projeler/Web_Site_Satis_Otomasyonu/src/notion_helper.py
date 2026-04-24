"""
Notion yardımcı fonksiyonları — DB oluşturma ve lead yazma.
Raw Notion API kullanır (requests).
"""
from __future__ import annotations
import requests
from src import config

NOTION_API = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {config.NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# ---------------------------------------------------------------------------
# Lead Onay DB şeması
# ---------------------------------------------------------------------------
LEAD_DB_SCHEMA = {
    "İşletme Adı": {"title": {}},
    "Kategori": {"select": {}},
    "Adres": {"rich_text": {}},
    "Şehir": {"select": {}},
    "Telefon": {"phone_number": {}},
    "Website": {"url": {}},
    "Email": {"email": {}},
    "Instagram": {"url": {}},
    "Yıldız": {"number": {"format": "number"}},
    "Yorum Sayısı": {"number": {"format": "number"}},
    "Fiyat Skalası": {"select": {}},
    "Lead Skor": {"number": {"format": "number"}},
    "Öncelik": {
        "select": {
            "options": [
                {"name": "Yüksek", "color": "green"},
                {"name": "Düşük", "color": "yellow"},
            ]
        }
    },
    "Durum": {
        "select": {
            "options": [
                {"name": "Onay Bekliyor", "color": "orange"},
                {"name": "Üret", "color": "green"},
                {"name": "Elendi", "color": "red"},
                {"name": "Manuel İletişim Bekliyor", "color": "purple"},
            ]
        }
    },
    "Place ID": {"rich_text": {}},
    "Google Maps URL": {"url": {}},
}


def create_lead_db(parent_page_id: str) -> str:
    """
    Notion'da Lead Onay DB'yi oluşturur.
    Zaten varsa hata verir — idempotency config'de DB ID ile sağlanır.
    Returns: database_id
    """
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "Lead Onay DB"}}],
        "is_inline": True,
        "properties": LEAD_DB_SCHEMA,
    }

    resp = requests.post(f"{NOTION_API}/databases", headers=HEADERS, json=payload)
    resp.raise_for_status()
    db_id = resp.json()["id"]
    config.logger.info("Notion Lead Onay DB oluşturuldu: %s", db_id)
    return db_id


def check_place_exists(db_id: str, place_id: str) -> bool:
    """place_id'nin DB'de zaten olup olmadığını kontrol et (idempotency)."""
    payload = {
        "filter": {
            "property": "Place ID",
            "rich_text": {"equals": place_id},
        }
    }
    resp = requests.post(
        f"{NOTION_API}/databases/{db_id}/query", headers=HEADERS, json=payload
    )
    resp.raise_for_status()
    return len(resp.json().get("results", [])) > 0


def write_lead(db_id: str, lead: dict) -> str | None:
    """
    Tek bir lead'i Notion DB'ye yazar.
    Duplicate kontrolü yapar (place_id).
    Returns: page_id veya None (duplicate ise)
    """
    place_id = lead.get("place_id", "")

    # Idempotency kontrolü
    if check_place_exists(db_id, place_id):
        config.logger.info("SKIP (zaten var): %s — %s", lead.get("name"), place_id)
        return None

    # Fiyat skalası güvenli çekim
    price_scale = lead.get("price_scale")
    if price_scale and not isinstance(price_scale, str):
        price_scale = str(price_scale)

    # Öncelik hesapla
    score = lead.get("score", 0)
    if score >= config.SCORE_THRESHOLD_HIGH:
        priority = "Yüksek"
    else:
        priority = "Düşük"

    # İletişim durumuna göre statü
    has_email = bool(lead.get("email"))
    has_phone = bool(lead.get("phone"))
    if has_email:
        status = "Onay Bekliyor"
    elif has_phone:
        status = "Manuel İletişim Bekliyor"
    else:
        status = "Onay Bekliyor"  # en azından IG varsa

    properties = {
        "İşletme Adı": {"title": [{"text": {"content": lead.get("name", "N/A")}}]},
        "Kategori": {"select": {"name": lead.get("category", "Genel")}},
        "Adres": {"rich_text": [{"text": {"content": lead.get("address", "")}}]},
        "Şehir": {"select": {"name": lead.get("city", "Bilinmiyor")}},
        "Yıldız": {"number": lead.get("stars", 0)},
        "Yorum Sayısı": {"number": lead.get("reviews_count", 0)},
        "Lead Skor": {"number": round(score, 1)},
        "Öncelik": {"select": {"name": priority}},
        "Durum": {"select": {"name": status}},
        "Place ID": {"rich_text": [{"text": {"content": place_id}}]},
    }

    # Opsiyonel alanlar (None ise Notion'a gönderme)
    if lead.get("phone"):
        properties["Telefon"] = {"phone_number": lead["phone"]}
    if lead.get("website"):
        properties["Website"] = {"url": lead["website"]}
    if lead.get("email"):
        properties["Email"] = {"email": lead["email"]}
    if lead.get("instagram"):
        properties["Instagram"] = {"url": lead["instagram"]}
    if price_scale:
        properties["Fiyat Skalası"] = {"select": {"name": price_scale}}
    if lead.get("google_maps_url"):
        properties["Google Maps URL"] = {"url": lead["google_maps_url"]}

    payload = {
        "parent": {"database_id": db_id},
        "properties": properties,
    }

    resp = requests.post(f"{NOTION_API}/pages", headers=HEADERS, json=payload)
    resp.raise_for_status()
    page_id = resp.json()["id"]
    config.logger.info(
        "Lead yazıldı: %s (skor: %.1f, öncelik: %s)",
        lead.get("name"),
        score,
        priority,
    )
    return page_id
