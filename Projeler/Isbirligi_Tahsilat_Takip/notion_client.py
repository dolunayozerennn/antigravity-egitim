import requests
from config import NOTION_API_TOKEN, COLLAB_DB_ID, COLLAB_PARENT_SLUG

NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

# Tahsilat Takip DB (Gelir sayfası altında) — SADECE OKUMA.
TAHSILAT_TAKIP_DB_ID = "2cb955140a3282708ada810e72dbd0d2"


def _build_notion_url(page_id):
    """Yan-panel açılışlı deep link: parent page + ?p=childId&pm=s"""
    clean = page_id.replace("-", "")
    return f"https://www.notion.so/{COLLAB_PARENT_SLUG}?p={clean}&pm=s"


def fetch_published_videos():
    """
    Birleşik Reels+YouTube DB'sinden 'Yayınlandı' kayıtları çeker.

    Her kayıt: id, title, status, check, ceren_odeme, published_date, notion_url.
    Filtre/atlama mantığı (Ödeme Yok vs.) database.py'da uygulanır.
    """
    url = f"https://api.notion.com/v1/databases/{COLLAB_DB_ID}/query"
    payload = {
        "filter": {
            "property": "Status",
            "select": {"equals": "Yayınlandı"}
        }
    }

    videos = []
    has_more = True
    next_cursor = None

    while has_more:
        if next_cursor:
            payload["start_cursor"] = next_cursor

        resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        if resp.status_code != 200:
            print(f"[Collab DB] Hata: {resp.status_code} - {resp.text}")
            break

        data = resp.json()
        for item in data.get("results", []):
            props = item.get("properties", {})

            title_arr = props.get("Name", {}).get("title", [])
            title = "".join([t.get("plain_text", "") for t in title_arr]).strip() if title_arr else ""
            if not title:
                continue

            status = (props.get("Status", {}).get("select") or {}).get("name", "")
            check = props.get("Check", {}).get("checkbox", False)
            ceren_odeme = (props.get("Ceren Ödeme", {}).get("select") or {}).get("name", "")

            published_date = None
            date_prop = props.get("Paylaşım Tarihi", {}).get("date")
            if date_prop and date_prop.get("start"):
                published_date = date_prop["start"]
            if not published_date:
                published_date = item.get("created_time", "")

            videos.append({
                "id": item["id"],
                "title": title,
                "status": status,
                "check": check,
                "ceren_odeme": ceren_odeme,
                "published_date": published_date,
                "notion_url": _build_notion_url(item["id"])
            })

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor", None)

    return videos


def fetch_payment_status():
    """
    Tahsilat Takip DB'sini SADECE OKUR ve {video_page_id: {"amount": x, "paid": bool}} döner.

    paid = True   → markadan tahsilat alınmış (Tahsil Tarihi dolu en az bir satır var)
    paid = False  → tahsilat satırı var ama Tahsil Tarihi boş (markadan henüz alınmadı)
    Hiç eşleşme yoksa → dict'te yer almaz (kayıp tahsilat satırı = atlanmaz, uyarı verilir).

    Bir video birden fazla satıra bağlıysa: amount toplanır, paid = (en az biri ödenmiş).
    Bu DB üzerinde hiçbir yazma çağrısı yoktur.
    """
    url = f"https://api.notion.com/v1/databases/{TAHSILAT_TAKIP_DB_ID}/query"
    status = {}
    has_more = True
    next_cursor = None
    payload = {}

    while has_more:
        if next_cursor:
            payload["start_cursor"] = next_cursor

        resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        if resp.status_code != 200:
            print(f"[Tahsilat Takip] Okuma hatası: {resp.status_code} - {resp.text}")
            break

        data = resp.json()
        for row in data.get("results", []):
            props = row.get("properties", {})

            tutar = props.get("Tutar", {}).get("number")
            tahsil_tarihi = (props.get("Tahsil Tarihi", {}).get("date") or {}).get("start")
            row_paid = bool(tahsil_tarihi)

            relation = props.get("Dolunay Reels", {}).get("relation", []) or []
            for ref in relation:
                video_id = ref.get("id")
                if not video_id:
                    continue
                cur = status.setdefault(video_id, {"amount": 0, "paid": False})
                if tutar is not None:
                    cur["amount"] = (cur["amount"] or 0) + tutar
                if row_paid:
                    cur["paid"] = True

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor", None)

    # amount'u 0'dan None'a çevir (gösterimde "—" olur)
    for v in status.values():
        if v["amount"] == 0:
            v["amount"] = None
    return status
