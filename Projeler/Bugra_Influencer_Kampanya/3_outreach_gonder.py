#!/usr/bin/env python3
"""
3_outreach_gonder.py — Adım 3
Gmail API ile influencerlara kişiselleştirilmiş outreach e-postası gönderir.

Kullanım:
  python3 3_outreach_gonder.py --dry-run    # Göndermeden önce önizle
  python3 3_outreach_gonder.py              # Gerçekten gönder
  python3 3_outreach_gonder.py --auth-only  # Sadece Gmail girişi yap
  python3 3_outreach_gonder.py --limit 10  # Maksimum 10 e-posta gönder
"""

import json
import sys
import base64
import os
import csv
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config import (
    CREDENTIALS_FILE,
    TOKEN_FILE,
    INPUT_EMAILS,
    OUTPUT_MESSAGES,
    TAKIP_CSV,
    GUNLUK_LIMIT,
    GONDEREN_EMAIL,
)

# ─────────────────────────────────────────────
# E-posta Şablonu — Buğra burayı kendi bilgileriyle dolduracak
# ─────────────────────────────────────────────

EMAIL_KONU_TR = "İş birliği teklifi — {isim}"

EMAIL_METIN_TR = """\
Merhaba {isim},

{platform}'daki içeriklerini takip ediyorum ve {niş} alanındaki paylaşımların dikkatimi çekti.

{etkinlik_adi} etkinlikleri kapsamında seninle iş birliği yapmak istiyoruz.

Detayları konuşmak için uygun musun?

Saygılarımla,
{gonderici_adi}
"""

# İngilizce şablon (niş bazlı kullanım için)
EMAIL_KONU_EN = "Collaboration Opportunity — {isim}"

EMAIL_METIN_EN = """\
Hi {isim},

I've been following your content on {platform} and loved your work on {niş}.

We're organizing events in Turkey and would love to collaborate with you.

Would you be open to discussing details?

Best regards,
{gonderici_adi}
"""

# ── Şablona eklenecek kişiselleştirme bilgileri ─────────────────────────────
# Buğra bu bilgileri kendi projesine göre doldurur:
KISISEL_BILGILER = {
    "gonderici_adi": "",       # ← Buğra'nın adı
    "etkinlik_adi": "",        # ← Etkinlik adı (örn. "İstanbul Müzik Festivali")
    "niş": "",                 # ← Influencer'ın ilgi alanı (genel şablon için)
}


# ─────────────────────────────────────────────
# Gmail Kimlik Doğrulama
# ─────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def authenticate():
    """Gmail API OAuth2 kimlik doğrulaması."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[INFO] Token yenileniyor...")
            creds.refresh(Request())
        else:
            print("[INFO] Tarayıcıda Google hesabınızla giriş yapın...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print("[INFO] ✅ Token kaydedildi.")

    return creds


# ─────────────────────────────────────────────
# E-posta Gönderme
# ─────────────────────────────────────────────

def olustur_mesaj(to: str, subject: str, body: str) -> dict:
    message = MIMEMultipart("alternative")
    message["to"] = to
    message["subject"] = subject
    text_part = MIMEText(body, "plain", "utf-8")
    message.attach(text_part)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"raw": raw}


def gonder_email(service, to: str, subject: str, body: str) -> str:
    """E-posta gönderir ve message ID döndürür."""
    msg = olustur_mesaj(to, subject, body)
    result = service.users().messages().send(userId="me", body=msg).execute()
    return result.get("id", "")


# ─────────────────────────────────────────────
# Takip CSV Güncelleme
# ─────────────────────────────────────────────

def takip_csv_guncelle(gonderilen_kayitlar: list):
    """Takip_Listesi.csv'ye gönderim kayıtlarını ekler."""
    mevcut = []
    if os.path.exists(TAKIP_CSV):
        with open(TAKIP_CSV, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            mevcut = list(reader)

    fieldnames = [
        "isim", "platform", "profil_url", "takipci", "email",
        "email_kaynagi", "gonderildi_mi", "gonderim_tarihi",
        "mesaj_turu", "konu", "yanit", "notlar"
    ]

    mevcut_emailler = {r.get("email", "") for r in mevcut}
    yeni = [r for r in gonderilen_kayitlar if r.get("email") not in mevcut_emailler]
    mevcut.extend(yeni)

    with open(TAKIP_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(mevcut)

    print(f"📊 Takip listesi güncellendi: {TAKIP_CSV} ({len(yeni)} yeni kayıt)")


# ─────────────────────────────────────────────
# Ana Fonksiyon
# ─────────────────────────────────────────────

def main():
    dry_run   = "--dry-run"   in sys.argv
    auth_only = "--auth-only" in sys.argv

    limit = GUNLUK_LIMIT
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            try:
                limit = int(sys.argv[i + 1])
            except ValueError:
                pass

    # Gmail kimlik doğrulama
    creds = authenticate()
    print("[INFO] ✅ Gmail API bağlantısı başarılı.")

    if auth_only:
        return

    service = build("gmail", "v1", credentials=creds)

    # Influencer listesini yükle
    try:
        with open(INPUT_EMAILS, "r", encoding="utf-8") as f:
            influencers = json.load(f)
    except FileNotFoundError:
        print(f"❌ {INPUT_EMAILS} bulunamadı. Önce: python3 2_email_topla.py")
        return

    # E-postası olan influencerları filtrele
    gorecekler = [inf for inf in influencers if inf.get("email_final")][:limit]

    if not gorecekler:
        print("⚠️  E-posta adresi olan influencer bulunamadı.")
        return

    print(f"\n{'='*60}")
    print(f"📧 GÖNDERİLECEK E-POSTALAR ({len(gorecekler)} adet)")
    print(f"{'='*60}")
    for i, inf in enumerate(gorecekler, 1):
        print(f"  {i:2d}. @{inf['kullanici_adi']:25s} → {inf['email_final']}")
    print(f"{'='*60}")

    if dry_run:
        print("\n[DRY-RUN] E-postalar gönderilmedi.")
        print("\n🔎 İlk 2 mesaj önizlemesi:")
        for inf in gorecekler[:2]:
            isim = inf.get("tam_ad") or inf["kullanici_adi"]
            konu = EMAIL_KONU_TR.format(isim=isim)
            metin = EMAIL_METIN_TR.format(
                isim=isim,
                platform=inf["platform"],
                niş=KISISEL_BILGILER.get("niş") or "[niş]",
                etkinlik_adi=KISISEL_BILGILER.get("etkinlik_adi") or "[etkinlik]",
                gonderici_adi=KISISEL_BILGILER.get("gonderici_adi") or "[gönderici adı]",
            )
            print(f"\n{'─'*40}")
            print(f"Kime  : {inf['email_final']}")
            print(f"Konu  : {konu}")
            print(f"{'─'*40}")
            print(metin[:300])
        return

    # Onay
    print(f"\n⚠️  {len(gorecekler)} e-posta gönderilecek. Devam? (e/h): ", end="")
    cevap = input().strip().lower()
    if cevap not in ("e", "evet", "y", "yes"):
        print("[INFO] İptal edildi.")
        return

    # Görev
    yollanan = 0
    hatali   = 0
    kayitlar = []
    mesajlar = {}

    for inf in gorecekler:
        isim = inf.get("tam_ad") or inf["kullanici_adi"]
        email = inf["email_final"]
        konu  = EMAIL_KONU_TR.format(isim=isim)
        metin = EMAIL_METIN_TR.format(
            isim=isim,
            platform=inf["platform"],
            niş=KISISEL_BILGILER.get("niş") or "",
            etkinlik_adi=KISISEL_BILGILER.get("etkinlik_adi") or "",
            gonderici_adi=KISISEL_BILGILER.get("gonderici_adi") or "",
        )

        try:
            msg_id = gonder_email(service, email, konu, metin)
            print(f"  ✅ @{inf['kullanici_adi']:25s} → {email} (ID: {msg_id})")
            gonderildi = "Evet"
            yollanan += 1
        except Exception as ex:
            print(f"  ❌ @{inf['kullanici_adi']:25s} → {email} HATA: {ex}")
            gonderildi = "Hayır"
            hatali += 1

        # Kayıt
        email_kaynagi = ""
        if inf.get("email_bio"):     email_kaynagi = "Bio"
        elif inf.get("email_buton"): email_kaynagi = "Instagram Butonu"
        elif inf.get("email_hunter"):email_kaynagi = "Hunter.io"
        elif inf.get("email_apollo"):email_kaynagi = "Apollo.io"

        kayitlar.append({
            "isim": isim,
            "platform": inf["platform"],
            "profil_url": inf["profil_url"],
            "takipci": inf.get("takipci", 0),
            "email": email,
            "email_kaynagi": email_kaynagi,
            "gonderildi_mi": gonderildi,
            "gonderim_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "mesaj_turu": "TR",
            "konu": konu,
            "yanit": "",
            "notlar": "",
        })

        mesajlar[inf["kullanici_adi"]] = {
            "isim": isim,
            "email": email,
            "konu": konu,
            "metin": metin,
            "platform": inf["platform"],
            "profil_url": inf["profil_url"],
        }

    # Mesajları kaydet
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_MESSAGES, "w", encoding="utf-8") as f:
        json.dump(mesajlar, f, ensure_ascii=False, indent=2)

    # Takip listesini güncelle
    takip_csv_guncelle(kayitlar)

    print(f"\n{'='*60}")
    print(f"📊 SONUÇ: {yollanan} gönderildi, {hatali} başarısız")
    print(f"{'='*60}")
    print(f"\n➡️  Sonraki adım: python3 4_takip_guncelle.py")


if __name__ == "__main__":
    main()
