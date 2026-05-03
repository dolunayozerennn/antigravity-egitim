"""
database.py — Tahsilat Bildirim Filtresi (state-less)

Doğruluk kaynağı:
  - Marka tahsilat etti mi? → Tahsilat Takip > "Tahsil Tarihi" alanı dolu mu
  - "Ceren Ödeme" video DB'sindeki Ceren komisyonu için, marka tahsilatı DEĞİL.

Atlama kuralları (uyarı GÖNDERİLMEZ):
  1. Ceren Ödeme = "Ödeme Yok"  → işbirliği değil, baştan elenir
  2. Tahsilat Takip kaydı VAR ve Tahsil Tarihi DOLU → markadan alınmış
  3. Check = True → manuel "tahsil edildi" işareti

Tahsilat Takip kaydı YOK ise: kayıp olabileceği için atlamayız, uyarıya dahil ederiz.
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


def get_pending_notifications(videos, payment_status=None):
    payment_status = payment_status or {}
    pending = []
    now = datetime.now()

    for video in videos:
        # 1. İşbirliği değil
        if video.get("ceren_odeme", "") == "Ödeme Yok":
            continue

        page_id = video["id"]
        ps = payment_status.get(page_id) or {}

        # 2. Markadan tahsilat alınmış
        if ps.get("paid"):
            continue

        # 3. Manuel check işareti
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

        pending.append({
            "id": page_id,
            "title": video["title"],
            "published_date": pub_date.strftime("%Y-%m-%d"),
            "days_passed": days_passed,
            "bracket": bracket,
            "amount": ps.get("amount"),
            "notion_url": video.get("notion_url", "https://www.notion.so")
        })

    pending.sort(key=lambda x: x["days_passed"], reverse=True)
    return pending
