#!/usr/bin/env python3
"""
outreach_gonder.py — Kişiselleştirilmiş E-posta Gönderim Scripti

Gmail API ile lead'lere kişiselleştirilmiş outreach e-postası gönderir.
YAML config dosyasından parametreleri okur.

Kullanım:
  python3 outreach_gonder.py --config config/bugra-influencer.yaml --dry-run
  python3 outreach_gonder.py --config config/bugra-influencer.yaml
  python3 outreach_gonder.py --config config/sweatcoin-outreach.yaml --limit 10
  python3 outreach_gonder.py --config config/bugra-influencer.yaml --auth-only

Kaynak: Projeler/Bugra_Influencer_Kampanya/3_outreach_gonder.py → Parametrik hale getirildi
Referans: _agents/musteri-kazanim/AGENT.md
"""

import argparse
import base64
import csv
import json
import os
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yaml

# ═══════════════════════════════════════════════════
# ⚙️ CONFIG & API
# ═══════════════════════════════════════════════════

def config_yukle(config_yolu: str) -> dict:
    """YAML config dosyasını yükler."""
    with open(config_yolu, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def credentials_yollarini_bul() -> tuple[str, str]:
    """
    DEPRECATED: Bu fonksiyon artık kullanılmıyor.
    Merkezi google_auth modülü kullanılır.
    Geriye uyumluluk için bırakılmıştır.
    """
    return "", ""


# ═══════════════════════════════════════════════════
# 🔐 GMAIL KİMLİK DOĞRULAMA
# ═══════════════════════════════════════════════════

# Merkezi Google Auth modülünü import et
_antigravity_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(_antigravity_root, "_knowledge", "credentials", "oauth"))
from google_auth import get_gmail_service as _get_gmail_service


def authenticate(cred_file: str = "", token_file: str = ""):
    """Gmail API OAuth2 kimlik doğrulaması — Merkezi token sistemi."""
    # cred_file ve token_file parametreleri geriye uyumluluk için bırakılmıştır
    # Artık merkezi google_auth kullanılır
    return _get_gmail_service("outreach")


# ═══════════════════════════════════════════════════
# 📧 E-POSTA OLUŞTURMA & GÖNDERME
# ═══════════════════════════════════════════════════

def mesaj_olustur(to: str, subject: str, body: str) -> dict:
    """MIME e-posta mesajı oluşturur."""
    message = MIMEMultipart("alternative")
    message["to"] = to
    message["subject"] = subject
    text_part = MIMEText(body, "plain", "utf-8")
    message.attach(text_part)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"raw": raw}


def email_gonder(service, to: str, subject: str, body: str) -> str:
    """E-posta gönderir ve message ID döndürür."""
    msg = mesaj_olustur(to, subject, body)
    result = service.users().messages().send(userId="me", body=msg).execute()
    return result.get("id", "")


# ═══════════════════════════════════════════════════
# ✏️ KİŞİSELLEŞTİRME
# ═══════════════════════════════════════════════════

# Varsayılan şablonlar (config'de sablon_dosyasi yoksa kullanılır)
VARSAYILAN_SABLONLAR = {
    "TR": {
        "konu": "İş birliği teklifi — {ad}",
        "govde": """Merhaba {ad},

{platform}'daki içeriklerini takip ediyorum ve {nis} alanındaki paylaşımların dikkatimi çekti.

{deger_onerisi}

{cta}

Saygılarımla,
{gonderici_adi}""",
    },
    "EN": {
        "konu": "Collaboration opportunity — {ad}",
        "govde": """Hi {ad},

I've been following your content on {platform} and your posts about {nis} really caught my attention.

{deger_onerisi}

{cta}

Best regards,
{gonderici_adi}""",
    },
}


def kisisellestir(sablon_konu: str, sablon_govde: str, lead: dict, config: dict) -> tuple[str, str]:
    """Şablondaki değişkenleri lead verisiyle doldurur."""
    outreach = config.get("outreach", {})
    icp = config.get("icp", {})

    degiskenler = {
        "ad": lead.get("tam_ad") or lead.get("kullanici_adi", ""),
        "first_name": lead.get("tam_ad", "").split()[0] if lead.get("tam_ad") else lead.get("kullanici_adi", ""),
        "platform": lead.get("platform", ""),
        "nis": ", ".join(icp.get("nis", [])) or "your niche",
        "niche": ", ".join(icp.get("nis", [])) or "your niche",
        "deger_onerisi": outreach.get("deger_onerisi", ""),
        "value_prop": outreach.get("deger_onerisi", ""),
        "cta": outreach.get("cta", ""),
        "gonderici_adi": outreach.get("gonderici_adi", ""),
        "sender_name": outreach.get("gonderici_adi", ""),
        "ekstra_bilgi": outreach.get("ekstra_bilgi", ""),
        "brand_name": lead.get("tam_ad") or lead.get("kullanici_adi", ""),
        "sirket": lead.get("tam_ad") or "",
        "pozisyon": "",
        "position": "",
        "kanca": "",
        "hook": "",
    }

    konu = sablon_konu
    govde = sablon_govde

    for key, val in degiskenler.items():
        konu = konu.replace(f"{{{key}}}", str(val))
        govde = govde.replace(f"{{{key}}}", str(val))

    return konu, govde


# ═══════════════════════════════════════════════════
# 📊 TAKİP CSV GÜNCELLEME
# ═══════════════════════════════════════════════════

def takip_csv_guncelle(csv_path: str, kayitlar: list):
    """Takip CSV dosyasını günceller."""
    mevcut = []
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            mevcut = list(reader)

    fieldnames = [
        "lead_id", "ad", "platform", "profil_url", "takipci", "email",
        "email_kaynagi", "outreach_status", "outreach_date",
        "sequence_adim", "acildi_mi", "cevaplandi_mi", "cevap_tipi",
        "konu", "notlar",
    ]

    mevcut_emailler = {r.get("email", "") for r in mevcut}
    yeni = [r for r in kayitlar if r.get("email") not in mevcut_emailler]
    mevcut.extend(yeni)

    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(mevcut)

    print(f"📊 Takip listesi güncellendi: {csv_path} ({len(yeni)} yeni kayıt)")


# ═══════════════════════════════════════════════════
# 🏁 MAIN
# ═══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Outreach Gönderici — Gmail API ile Kişiselleştirilmiş E-posta"
    )
    parser.add_argument(
        "--config", required=True,
        help="Kampanya config YAML dosyası"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Göndermeden önizle"
    )
    parser.add_argument(
        "--auth-only", action="store_true",
        help="Sadece Gmail giriş yap"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Maksimum gönderilecek e-posta sayısı"
    )
    args = parser.parse_args()

    # Config yükle
    config = config_yukle(args.config)
    kampanya_adi = config.get("kampanya_adi", "bilinmeyen")
    outreach = config.get("outreach", {})
    sequence = config.get("sequence", {})
    dosyalar = config.get("dosyalar", {})

    print(f"\n{'='*60}")
    print(f"📧 OUTREACH GÖNDERİM: {kampanya_adi}")
    print(f"{'='*60}")

    # Gmail kimlik doğrulama
    service = authenticate()
    print("[INFO] ✅ Gmail API bağlantısı başarılı.")

    # Enriched listeyi yükle
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    enriched_path = os.path.join(data_dir, f"{kampanya_adi}_enriched.json")

    if not os.path.exists(enriched_path):
        print(f"❌ {enriched_path} bulunamadı. Önce: kampanya_baslat.py çalıştır.")
        return

    with open(enriched_path, "r", encoding="utf-8") as f:
        leads = json.load(f)

    # Limit belirle
    limit = args.limit or sequence.get("gunluk_gonderim_limiti", 50)

    # E-postası olan lead'leri filtrele
    gorecekler = [l for l in leads if l.get("email_final")][:limit]

    if not gorecekler:
        print("⚠️  E-posta adresi olan lead bulunamadı.")
        return

    # Şablon belirle
    sablon_dili = outreach.get("sablon_dili", "TR")
    sablon = VARSAYILAN_SABLONLAR.get(sablon_dili, VARSAYILAN_SABLONLAR["TR"])

    print(f"\n{'='*60}")
    print(f"📧 GÖNDERİLECEK E-POSTALAR ({len(gorecekler)} adet)")
    print(f"{'='*60}")
    for i, lead in enumerate(gorecekler, 1):
        print(f"  {i:2d}. @{lead['kullanici_adi']:25s} → {lead['email_final']}")
    print(f"{'='*60}")

    if args.dry_run:
        print("\n[DRY-RUN] E-postalar gönderilmedi.")
        print("\n🔎 İlk 2 mesaj önizlemesi:")
        for lead in gorecekler[:2]:
            konu, govde = kisisellestir(sablon["konu"], sablon["govde"], lead, config)
            print(f"\n{'─'*40}")
            print(f"Kime  : {lead['email_final']}")
            print(f"Konu  : {konu}")
            print(f"{'─'*40}")
            print(govde[:400])
        return

    # Onay
    print(f"\n⚠️  {len(gorecekler)} e-posta gönderilecek. Devam? (e/h): ", end="")
    cevap = input().strip().lower()
    if cevap not in ("e", "evet", "y", "yes"):
        print("[INFO] İptal edildi.")
        return

    # Gönderim
    yollanan = 0
    hatali = 0
    kayitlar = []

    for lead in gorecekler:
        email = lead["email_final"]
        konu, govde = kisisellestir(sablon["konu"], sablon["govde"], lead, config)

        try:
            msg_id = email_gonder(service, email, konu, govde)
            print(f"  ✅ @{lead['kullanici_adi']:25s} → {email} (ID: {msg_id})")
            status = "Sent"
            yollanan += 1
        except Exception as ex:
            print(f"  ❌ @{lead['kullanici_adi']:25s} → {email} HATA: {ex}")
            status = "Failed"
            hatali += 1

        kayitlar.append({
            "lead_id": lead.get("kullanici_adi", ""),
            "ad": lead.get("tam_ad") or lead.get("kullanici_adi", ""),
            "platform": lead.get("platform", ""),
            "profil_url": lead.get("profil_url", ""),
            "takipci": lead.get("takipci", 0),
            "email": email,
            "email_kaynagi": lead.get("email_kaynagi", ""),
            "outreach_status": status,
            "outreach_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "sequence_adim": 1,
            "acildi_mi": "",
            "cevaplandi_mi": "",
            "cevap_tipi": "",
            "konu": konu,
            "notlar": "",
        })

    # Takip CSV güncelle
    takip_path = os.path.join(data_dir, f"{kampanya_adi}_takip.csv")
    takip_csv_guncelle(takip_path, kayitlar)

    # Mesajları kaydet
    messages_path = os.path.join(data_dir, f"{kampanya_adi}_messages.json")
    mesajlar = {}
    for lead in gorecekler:
        konu, govde = kisisellestir(sablon["konu"], sablon["govde"], lead, config)
        mesajlar[lead["kullanici_adi"]] = {
            "ad": lead.get("tam_ad") or lead.get("kullanici_adi", ""),
            "email": lead["email_final"],
            "konu": konu,
            "govde": govde,
            "platform": lead.get("platform", ""),
        }
    with open(messages_path, "w", encoding="utf-8") as f:
        json.dump(mesajlar, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"📊 SONUÇ: {yollanan} gönderildi, {hatali} başarısız")
    print(f"{'='*60}")
    print(f"\n➡️  Sonraki adım: python3 scripts/takip_guncelle.py --config {args.config}")


if __name__ == "__main__":
    main()
