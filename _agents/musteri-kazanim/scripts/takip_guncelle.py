#!/usr/bin/env python3
"""
takip_guncelle.py — Kampanya Takip ve Sequence Yönetim Scripti

Takip CSV dosyasını yönetir: özet rapor gösterir, yanıt işaretler,
not ekler ve sequence durumunu günceller.

Kullanım:
  python3 takip_guncelle.py --config config/bugra-influencer.yaml
  python3 takip_guncelle.py --config config/bugra-influencer.yaml --yanit @username
  python3 takip_guncelle.py --config config/bugra-influencer.yaml --yanit @username "Olumlu — görüşme planlandı"
  python3 takip_guncelle.py --config config/bugra-influencer.yaml --not @username "Tekrar denenecek"
  python3 takip_guncelle.py --config config/bugra-influencer.yaml --durum @username "Sent"

Kaynak: Projeler/Bugra_Influencer_Kampanya/4_takip_guncelle.py → Parametrik hale getirildi
Referans: _agents/musteri-kazanim/AGENT.md
"""

import argparse
import csv
import os
import sys
from datetime import datetime

import yaml


# ═══════════════════════════════════════════════════
# ⚙️ CONFIG YÜKLEMErun
# ═══════════════════════════════════════════════════

def config_yukle(config_yolu: str) -> dict:
    """YAML config dosyasını yükler."""
    with open(config_yolu, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ═══════════════════════════════════════════════════
# 📊 CSV İŞLEMLERİ
# ═══════════════════════════════════════════════════

FIELDNAMES = [
    "lead_id", "ad", "platform", "profil_url", "takipci", "email",
    "email_kaynagi", "outreach_status", "outreach_date",
    "sequence_adim", "acildi_mi", "cevaplandi_mi", "cevap_tipi",
    "konu", "notlar",
]


def csv_yukle(csv_path: str) -> list:
    """Takip CSV dosyasını yükler."""
    if not os.path.exists(csv_path):
        print(f"⚠️  {csv_path} bulunamadı.")
        return []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def csv_kaydet(csv_path: str, rows: list):
    """Takip CSV dosyasını kaydeder."""
    if not rows:
        return
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ═══════════════════════════════════════════════════
# 📋 ÖZET RAPOR
# ═══════════════════════════════════════════════════

def ozet_goster(rows: list, kampanya_adi: str):
    """Kampanya takip durumu özeti."""
    toplam = len(rows)
    gonderilen = sum(1 for r in rows if r.get("outreach_status") == "Sent")
    basarisiz = sum(1 for r in rows if r.get("outreach_status") == "Failed")
    bekleyen = sum(1 for r in rows if r.get("outreach_status") in ("Pending", ""))
    cevaplanan = sum(1 for r in rows if r.get("cevaplandi_mi") in ("Evet", "True", "true", "1"))
    acilan = sum(1 for r in rows if r.get("acildi_mi") in ("Evet", "True", "true", "1"))

    # Cevap tipi dağılımı
    cevap_dagilimi = {}
    for r in rows:
        tip = r.get("cevap_tipi", "").strip()
        if tip:
            cevap_dagilimi[tip] = cevap_dagilimi.get(tip, 0) + 1

    # Email kaynağı dağılımı
    kaynak_dagilimi = {}
    for r in rows:
        kaynak = r.get("email_kaynagi", "bilinmeyen").strip()
        if kaynak:
            kaynak_dagilimi[kaynak] = kaynak_dagilimi.get(kaynak, 0) + 1

    print(f"\n{'='*60}")
    print(f"📊 KAMPANYA TAKİP ÖZETİ — {kampanya_adi}")
    print(f"   Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    print(f"  📋 Toplam lead      : {toplam}")
    print(f"  📧 Gönderildi       : {gonderilen}")
    print(f"  ❌ Başarısız        : {basarisiz}")
    print(f"  ⏳ Bekleyen         : {bekleyen}")
    print(f"  👁️  Açıldı           : {acilan}")
    print(f"  ✅ Cevaplandı       : {cevaplanan}")
    print(f"  📭 Cevap bekliyor   : {gonderilen - cevaplanan}")
    print(f"{'='*60}")

    # Oranlar
    if gonderilen > 0:
        print(f"\n📈 ORANLAR:")
        print(f"  Açılma oranı   : {acilan/gonderilen*100:.1f}%")
        print(f"  Cevap oranı    : {cevaplanan/gonderilen*100:.1f}%")

    # Cevap tipi dağılımı
    if cevap_dagilimi:
        print(f"\n📬 CEVAP TİPLERİ:")
        for tip, sayi in sorted(cevap_dagilimi.items()):
            ikon = {
                "Olumlu": "✅", "olumlu": "✅",
                "Olumsuz": "❌", "olumsuz": "❌",
                "Soru": "❓", "soru": "❓",
                "OOO": "🏖️", "ooo": "🏖️",
                "Bounce": "🔴", "bounce": "🔴",
            }.get(tip, "📩")
            print(f"  {ikon} {tip}: {sayi}")

    # Email kaynağı dağılımı
    if kaynak_dagilimi:
        print(f"\n📮 EMAIL KAYNAK DAĞILIMI:")
        for kaynak, sayi in sorted(kaynak_dagilimi.items(), key=lambda x: -x[1]):
            print(f"  → {kaynak}: {sayi}")

    # Cevaplananlar
    cevaplananlar = [r for r in rows if r.get("cevaplandi_mi") in ("Evet", "True", "true", "1")]
    if cevaplananlar:
        print(f"\n✅ CEVAP GELENLER:")
        for r in cevaplananlar:
            tip = r.get("cevap_tipi", "-")
            print(f"  → {r.get('ad', '?'):20s} | {r.get('email', ''):30s} | {tip}")

    # Cevap bekleyenler (ilk 10)
    bekleyenler = [r for r in rows if r.get("outreach_status") == "Sent"
                   and r.get("cevaplandi_mi") not in ("Evet", "True", "true", "1")]
    if bekleyenler:
        print(f"\n⏳ CEVAP BEKLENİYOR (İlk 10):")
        for r in bekleyenler[:10]:
            gon = r.get("outreach_date", "-")
            print(f"  → {r.get('ad', '?'):20s} | {r.get('email', ''):30s} | {gon}")
        if len(bekleyenler) > 10:
            print(f"  ... ve {len(bekleyenler) - 10} tane daha")

    print()


# ═══════════════════════════════════════════════════
# ✏️ GÜNCELLEME FONKSİYONLARI
# ═══════════════════════════════════════════════════

def lead_bul(rows: list, arama: str) -> int | None:
    """Lead'i ad veya email ile arar, index döndürür."""
    arama_temiz = arama.lower().lstrip("@")
    for i, r in enumerate(rows):
        ad = (r.get("ad", "") or r.get("lead_id", "")).lower().lstrip("@")
        email = r.get("email", "").lower()
        if arama_temiz in ad or arama_temiz == email or arama_temiz in r.get("lead_id", "").lower():
            return i
    return None


def isaretle_yanit(rows: list, username: str, yanit_notu: str = "Evet") -> list:
    """Belirtilen lead için yanıt alanını işaretler."""
    idx = lead_bul(rows, username)
    if idx is not None:
        rows[idx]["cevaplandi_mi"] = "Evet"
        rows[idx]["cevap_tipi"] = yanit_notu
        print(f"✅ @{username} için yanıt işaretlendi: {yanit_notu}")
    else:
        print(f"⚠️  @{username} takip listesinde bulunamadı.")
    return rows


def not_ekle(rows: list, username: str, notlar: str) -> list:
    """Belirtilen lead için not ekler."""
    idx = lead_bul(rows, username)
    if idx is not None:
        mevcut = rows[idx].get("notlar", "") or ""
        yeni = f"{mevcut} | {notlar}" if mevcut else notlar
        rows[idx]["notlar"] = yeni
        print(f"📝 @{username} için not eklendi.")
    else:
        print(f"⚠️  @{username} takip listesinde bulunamadı.")
    return rows


def durum_guncelle(rows: list, username: str, yeni_durum: str) -> list:
    """Belirtilen lead için outreach_status günceller."""
    idx = lead_bul(rows, username)
    if idx is not None:
        eski = rows[idx].get("outreach_status", "")
        rows[idx]["outreach_status"] = yeni_durum
        print(f"🔄 @{username}: {eski} → {yeni_durum}")
    else:
        print(f"⚠️  @{username} takip listesinde bulunamadı.")
    return rows


def toplu_export(rows: list, kampanya_adi: str, filtre: str = None):
    """Filtrelenmiş lead'leri ayrı CSV dosyasına export eder."""
    if filtre:
        filtreli = [r for r in rows if r.get("cevap_tipi", "").lower() == filtre.lower()]
    else:
        filtreli = rows

    export_path = f"data/{kampanya_adi}_{filtre or 'all'}_export.csv"
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    export_full = os.path.join(data_dir, f"{kampanya_adi}_{filtre or 'all'}_export.csv")

    os.makedirs(data_dir, exist_ok=True)
    with open(export_full, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(filtreli)

    print(f"📁 Export edildi: {export_full} ({len(filtreli)} kayıt)")


# ═══════════════════════════════════════════════════
# 🏁 MAIN
# ═══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Kampanya Takip Güncelleme — Sequence Yönetimi"
    )
    parser.add_argument(
        "--config", required=True,
        help="Kampanya config YAML dosyası"
    )
    parser.add_argument(
        "--yanit", nargs="+",
        help="Yanıt işaretle: --yanit @username [yanıt notu]"
    )
    parser.add_argument(
        "--not", nargs=2, dest="not_ekle",
        metavar=("USERNAME", "NOT"),
        help="Not ekle: --not @username 'not metni'"
    )
    parser.add_argument(
        "--durum", nargs=2,
        metavar=("USERNAME", "DURUM"),
        help="Durum güncelle: --durum @username Sent"
    )
    parser.add_argument(
        "--export", nargs="?", const="all",
        help="CSV export: --export [filtre] (ör: --export olumlu)"
    )
    args = parser.parse_args()

    # Config yükle
    config = config_yukle(args.config)
    kampanya_adi = config.get("kampanya_adi", "bilinmeyen")

    # Takip CSV yolunu belirle
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    csv_path = os.path.join(data_dir, f"{kampanya_adi}_takip.csv")

    # CSV yükle
    rows = csv_yukle(csv_path)

    # Komutları işle
    if args.yanit:
        username = args.yanit[0]
        yanit_notu = args.yanit[1] if len(args.yanit) > 1 else "Evet"
        rows = isaretle_yanit(rows, username, yanit_notu)
        csv_kaydet(csv_path, rows)

    elif args.not_ekle:
        username, notlar = args.not_ekle
        rows = not_ekle(rows, username, notlar)
        csv_kaydet(csv_path, rows)

    elif args.durum:
        username, yeni_durum = args.durum
        rows = durum_guncelle(rows, username, yeni_durum)
        csv_kaydet(csv_path, rows)

    elif args.export:
        filtre = args.export if args.export != "all" else None
        toplu_export(rows, kampanya_adi, filtre)

    # Her durumda özeti göster
    ozet_goster(rows, kampanya_adi)
    print(f"📁 Takip dosyası: {csv_path}")


if __name__ == "__main__":
    main()
