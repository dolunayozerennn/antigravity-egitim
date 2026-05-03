"""
database.py — Tahsilat Bildirim Filtresi (state-less)

Günde 1 tek toplu özet mail atıldığı için kalıcı state takibine gerek yok.
Notion'a hiçbir şey yazılmaz; comment okuma/yazma kaldırıldı.
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
    """
    'Yayınlandı' + 'Check kapalı' + 14+ gün geçmiş videoları döner.

    Her item: id, title, db_type, published_date, days_passed, bracket, amount, notion_url
    """
    amounts = amounts or {}
    pending = []
    now = datetime.now()

    for video in videos:
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
            "db_type": video["database_type"],
            "published_date": pub_date.strftime("%Y-%m-%d"),
            "days_passed": days_passed,
            "bracket": bracket,
            "amount": amounts.get(page_id),
            "notion_url": video.get("notion_url", "https://www.notion.so")
        })

    pending.sort(key=lambda x: x["days_passed"], reverse=True)
    return pending
