"""
database.py — Tahsilat Bildirim Filtresi (state-less)

Tek tahsilat sinyali: video DB'deki 'Check' kutusu.
  - Check = True  → tahsilat alınmış, atla
  - Check = False → tahsilat bekleniyor

Atlama kuralları (uyarı GÖNDERİLMEZ):
  1. Ceren Ödeme = "Ödeme Yok"  → işbirliği değil, baştan elenir
  2. Check = True               → tahsilat tamam
"""

from datetime import datetime


def _bracket(days_passed):
    if days_passed >= 60:
        return "black"
    if days_passed >= 30:
        return "red"
    if days_passed >= 14:
        return "yellow"
    return None


def get_pending_notifications(videos, amounts=None):
    amounts = amounts or {}
    pending = []
    now = datetime.now()

    for video in videos:
        if video.get("ceren_odeme", "") == "Ödeme Yok":
            continue
        if video.get("check", False):
            continue

        published_date_str = video.get("published_date", "")
        if not published_date_str:
            continue

        try:
            pub_date_clean = published_date_str.split("T")[0]
            pub_date = datetime.strptime(pub_date_clean, "%Y-%m-%d")
            days_passed = (now - pub_date).days
        except Exception as e:
            print(f"Tarih parse hatası: {e} — video: {video.get('title', 'Unknown')}")
            continue

        bracket = _bracket(days_passed)
        if bracket is None:
            continue

        page_id = video["id"]
        pending.append({
            "id": page_id,
            "title": video["title"],
            "published_date": pub_date.strftime("%Y-%m-%d"),
            "days_passed": days_passed,
            "bracket": bracket,
            "amount": amounts.get(page_id),
            "notion_url": video.get("notion_url", "https://www.notion.so")
        })

    pending.sort(key=lambda x: x["days_passed"], reverse=True)
    return pending
