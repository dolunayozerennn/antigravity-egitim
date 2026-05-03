from datetime import datetime
from notion_client import fetch_published_videos, fetch_payment_amounts
from database import get_pending_notifications
from email_client import send_email_notification
from ops_logger import get_ops_logger

ops = get_ops_logger("Isbirligi_Tahsilat_Takip", "Pipeline")

BRACKETS = [
    ("yellow", "🟡 Sarı (14-29 gün)", "#faad14", "#fffbe6"),
    ("red",    "🔴 Kırmızı (30-59 gün)", "#ff4d4f", "#fff1f0"),
    ("black",  "⚫ Siyah (60+ gün)", "#1f1f1f", "#ececec"),
]


def _fmt_amount(amount):
    if amount is None:
        return "—"
    if float(amount).is_integer():
        return f"{int(amount):,} TL".replace(",", ".")
    return f"{amount:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")


def _render_table(items, color):
    rows = "".join(
        f"""
        <tr>
            <td style="padding:8px 10px;border-bottom:1px solid #eee;">{it['title']}</td>
            <td style="padding:8px 10px;border-bottom:1px solid #eee;">{it['db_type']}</td>
            <td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:center;">{it['published_date']}</td>
            <td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:center;"><strong>{it['days_passed']}</strong></td>
            <td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{_fmt_amount(it['amount'])}</td>
            <td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:center;"><a href="{it['notion_url']}">aç</a></td>
        </tr>
        """
        for it in items
    )
    return f"""
    <table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:14px;">
        <thead>
            <tr style="background:{color};color:#fff;">
                <th style="padding:10px;text-align:left;">Marka / Video</th>
                <th style="padding:10px;text-align:left;">Tür</th>
                <th style="padding:10px;text-align:center;">Yayın</th>
                <th style="padding:10px;text-align:center;">Geçen Gün</th>
                <th style="padding:10px;text-align:right;">Tutar</th>
                <th style="padding:10px;text-align:center;">Notion</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """


def _build_email(pending):
    grouped = {key: [] for key, *_ in BRACKETS}
    for item in pending:
        grouped[item["bracket"]].append(item)

    counts = {k: len(v) for k, v in grouped.items()}

    total_known_amount = sum(it["amount"] or 0 for it in pending)
    has_unknown = any(it["amount"] is None for it in pending)
    total_label = _fmt_amount(total_known_amount)
    if has_unknown:
        total_label += " (+ bilinmeyen)"

    sections = ""
    for key, label, color, _bg in BRACKETS:
        items = grouped[key]
        if not items:
            continue
        sections += f"""
        <h3 style="margin:24px 0 4px 0;color:{color};">{label} — {len(items)} kayıt</h3>
        {_render_table(items, color)}
        """

    subject = (
        f"Tahsilat Özeti — {len(pending)} bekleyen "
        f"({counts['yellow']} sarı / {counts['red']} kırmızı / {counts['black']} siyah)"
    )

    html = f"""
    <html>
    <body style="font-family:Arial,Helvetica,sans-serif;color:#222;line-height:1.5;">
        <h2 style="margin-bottom:4px;">💰 Tahsilat Özeti</h2>
        <p style="margin-top:0;color:#666;">{datetime.now().strftime('%Y-%m-%d')} — toplam <strong>{len(pending)}</strong> bekleyen işbirliği,
        bilinen tutar toplamı: <strong>{total_label}</strong>.</p>
        {sections}
        <p style="margin-top:24px;color:#888;font-size:12px;">
            Tahsilat alındığında Notion'da ilgili kaydın <strong>Check</strong> kutusunu işaretle — bir sonraki tarama dışı bırakır.
        </p>
    </body>
    </html>
    """
    return subject, html


def check_for_alerts():
    print(f"[{datetime.now()}] Notion veritabanları kontrol ediliyor...")

    try:
        videos = fetch_published_videos()
    except Exception as e:
        print(f"Notion video çekme hatası: {e}")
        ops.error("Notion veri çekme hatası", exception=e)
        return

    if not videos:
        print("İncelenecek 'Yayınlandı' kayıt yok.")
        return

    try:
        amounts = fetch_payment_amounts()
    except Exception as e:
        print(f"Tahsilat Takip okuma hatası (devam ediliyor, tutarlar boş): {e}")
        amounts = {}

    print(f"Toplam {len(videos)} yayınlanmış video, {len(amounts)} tahsilat eşlemesi bulundu.")

    pending = get_pending_notifications(videos, amounts=amounts)

    if not pending:
        print("Uyarı gerektiren tahsilat yok — mail atılmayacak.")
        ops.success("Tahsilat özeti", "Bekleyen yok, mail atlandı")
        return

    print(f"{len(pending)} bekleyen kayıt → tek toplu mail hazırlanıyor.")

    subject, html_body = _build_email(pending)
    success = send_email_notification(subject, html_body)

    if success:
        print(f"Toplu özet maili gönderildi: {len(pending)} kayıt.")
        ops.success("Tahsilat özeti gönderildi", f"{len(pending)} bekleyen")
    else:
        print("Toplu özet maili gönderilemedi.")
        ops.warning("Tahsilat özeti gönderilemedi", f"{len(pending)} bekleyen")


def main():
    print("Isbirligi_Tahsilat_Takip baslatildi. (Cron Modu)")
    print(f"[{datetime.now()}] Zamanlanmis gorev basliyor...")
    check_for_alerts()
    print(f"[{datetime.now()}] Zamanlanmis gorev bitti.")
    ops.wait_for_logs()
    print("İşlem tamamlandı, çıkılıyor.")
    import sys
    sys.exit(0)


if __name__ == "__main__":
    main()
