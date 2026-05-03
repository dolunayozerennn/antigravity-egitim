import requests
from config import NOTION_API_TOKEN, YOUTUBE_DB_ID, REELS_DB_ID

NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

# Tahsilat Takip DB (Gelir sayfası altında) — SADECE OKUMA.
# Kritik veri içerir; bu modülden hiçbir yazma çağrısı yapılmaz.
TAHSILAT_TAKIP_DB_ID = "2cb955140a3282708ada810e72dbd0d2"


def query_database(db_id, title_prop_name, status_prop_name, checkbox_prop_name, db_type_label, date_prop_name=None):
    """
    Notion veritabanından 'Yayınlandı' durumundaki kayıtları çeker.
    """
    url = f"https://api.notion.com/v1/databases/{db_id}/query"

    payload = {
        "filter": {
            "property": status_prop_name,
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
            print(f"[{db_type_label}] Hata oluştu: {resp.status_code} - {resp.text}")
            break

        data = resp.json()
        results = data.get("results", [])

        for item in results:
            props = item.get("properties", {})

            title_prop = props.get(title_prop_name, {})
            title_arr = title_prop.get("title", [])
            title = "".join([t.get("plain_text", "") for t in title_arr]).strip() if title_arr else ""

            if not title:
                continue

            status_prop = props.get(status_prop_name, {})
            status = status_prop.get("select", {}).get("name", "") if status_prop.get("select") else ""

            check_prop = props.get(checkbox_prop_name, {})
            is_checked = check_prop.get("checkbox", False)

            published_date = None
            if date_prop_name:
                date_prop = props.get(date_prop_name, {})
                if date_prop.get("date") and date_prop["date"].get("start"):
                    published_date = date_prop["date"]["start"]

            if not published_date:
                published_date = item.get("created_time", "")

            page_id_clean = item["id"].replace("-", "")
            notion_url = f"https://www.notion.so/{page_id_clean}"

            videos.append({
                "id": item["id"],
                "title": title,
                "status": status,
                "check": is_checked,
                "database_type": db_type_label,
                "published_date": published_date,
                "notion_url": notion_url
            })

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor", None)

    return videos


def fetch_published_videos():
    """Tüm (YouTube ve Reels) yayımlanmış videoları çeker."""
    youtube_videos = query_database(
        db_id=YOUTUBE_DB_ID,
        title_prop_name="Video Adı",
        status_prop_name="Durum",
        checkbox_prop_name="Check",
        db_type_label="YouTube İşbirliği",
        date_prop_name=None
    )

    reels_videos = query_database(
        db_id=REELS_DB_ID,
        title_prop_name="Name",
        status_prop_name="Status",
        checkbox_prop_name="Check",
        db_type_label="Reels İşbirliği",
        date_prop_name="Paylaşım Tarihi"
    )

    return youtube_videos + reels_videos


def fetch_payment_amounts():
    """
    Tahsilat Takip DB'sini SADECE OKUR ve {video_page_id: tutar} sözlüğü döner.

    Tahsilat Takip'teki her satırın 'Dolunay Reels' relation alanı,
    Reels DB'sindeki video kaydına işaret eder. Bir video birden fazla
    Tahsilat satırına bağlıysa tutarlar toplanır.

    Bu DB kritik veri içerir — bu fonksiyon yalnızca query (POST /query)
    yapar, hiçbir page/comment yazımı yoktur.
    """
    url = f"https://api.notion.com/v1/databases/{TAHSILAT_TAKIP_DB_ID}/query"
    amounts = {}
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
            if tutar is None:
                continue

            relation = props.get("Dolunay Reels", {}).get("relation", []) or []
            for ref in relation:
                video_id = ref.get("id")
                if not video_id:
                    continue
                amounts[video_id] = amounts.get(video_id, 0) + tutar

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor", None)

    return amounts
