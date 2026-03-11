#!/usr/bin/env python3
"""
4_takip_guncelle.py — Adım 4
Takip_Listesi.csv'yi manuel güncellemek veya yanıt durumunu işlemek için.

Kullanım:
  python3 4_takip_guncelle.py                    # Özet raporu göster
  python3 4_takip_guncelle.py --yanit @username  # Yanıt geldi olarak işaretle
  python3 4_takip_guncelle.py --not @username "notlar..."  # Not ekle
"""

import csv
import sys
import os
from datetime import datetime
from config import TAKIP_CSV


def load_csv():
    if not os.path.exists(TAKIP_CSV):
        print(f"⚠️  {TAKIP_CSV} bulunamadı.")
        return []
    with open(TAKIP_CSV, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_csv(rows: list):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(TAKIP_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ozet_goster(rows: list):
    """Takip durumu özeti."""
    toplam    = len(rows)
    gonderilen = sum(1 for r in rows if r.get("gonderildi_mi") == "Evet")
    yanit     = sum(1 for r in rows if r.get("yanit") and r["yanit"].strip())
    bekleyen  = gonderilen - yanit

    print(f"\n{'='*55}")
    print(f"📊 TAKİP LİSTESİ ÖZETİ — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")
    print(f"  📋 Toplam kayıt    : {toplam}")
    print(f"  📧 Gönderildi      : {gonderilen}")
    print(f"  ✅ Yanıt geldi     : {yanit}")
    print(f"  ⏳ Yanıt bekliyor  : {bekleyen}")
    print(f"  📭 E-posta yok     : {toplam - gonderilen}")
    print(f"{'='*55}")

    if yanit > 0:
        print(f"\n✅ YANIT GELENLER:")
        for r in rows:
            if r.get("yanit") and r["yanit"].strip():
                print(f"  → @{r.get('isim', '?'):20s} | {r.get('email', ''):30s} | {r.get('yanit', '')}")

    print(f"\n⏳ YANIT BEKLENİYOR (İlk 10):")
    bekleyenler = [r for r in rows if r.get("gonderildi_mi") == "Evet" and not r.get("yanit")]
    for r in bekleyenler[:10]:
        gon_tarihi = r.get("gonderim_tarihi", "-")
        print(f"  → @{r.get('isim', '?'):20s} | {r.get('email', ''):30s} | {gon_tarihi}")

    if len(bekleyenler) > 10:
        print(f"  ... ve {len(bekleyenler) - 10} tane daha")
    print()


def isaretle_yanit(rows: list, username: str, yanit_notu: str = "Evet"):
    """Belirtilen kullanıcı için yanıt alanını işaretle."""
    found = False
    for r in rows:
        isim = r.get("isim", "").lower().lstrip("@")
        if isim == username.lower().lstrip("@"):
            r["yanit"] = yanit_notu
            found = True
            break
    if found:
        print(f"✅ @{username} için yanıt işaretlendi: {yanit_notu}")
    else:
        print(f"⚠️  @{username} takip listesinde bulunamadı.")
    return rows


def not_ekle(rows: list, username: str, notlar: str):
    """Belirtilen kullanıcı için not ekle."""
    found = False
    for r in rows:
        isim = r.get("isim", "").lower().lstrip("@")
        if isim == username.lower().lstrip("@"):
            r["notlar"] = notlar
            found = True
            break
    if found:
        print(f"📝 @{username} için not eklendi.")
    else:
        print(f"⚠️  @{username} takip listesinde bulunamadı.")
    return rows


def main():
    rows = load_csv()

    if "--yanit" in sys.argv:
        idx = sys.argv.index("--yanit")
        if idx + 1 < len(sys.argv):
            username = sys.argv[idx + 1]
            yanit_notu = sys.argv[idx + 2] if idx + 2 < len(sys.argv) else "Evet"
            rows = isaretle_yanit(rows, username, yanit_notu)
            save_csv(rows)

    elif "--not" in sys.argv:
        idx = sys.argv.index("--not")
        if idx + 2 < len(sys.argv):
            username = sys.argv[idx + 1]
            notlar = sys.argv[idx + 2]
            rows = not_ekle(rows, username, notlar)
            save_csv(rows)

    # Her durumda özeti göster
    ozet_goster(rows)
    print(f"📁 Takip dosyası: {TAKIP_CSV}")


if __name__ == "__main__":
    main()
