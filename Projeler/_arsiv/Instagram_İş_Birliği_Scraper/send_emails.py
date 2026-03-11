#!/usr/bin/env python3
"""
Gmail API üzerinden outreach e-postaları gönderen script.

İlk çalıştırıldığında tarayıcıda OAuth2 kimlik doğrulama akışı başlar.
Token kaydedildikten sonra tekrar giriş yapmanıza gerek kalmaz.

Kullanım:
  python3 send_emails.py                # Tüm e-postaları gönder (onay ister)
  python3 send_emails.py --dry-run      # Gönderilecek e-postaları listele
  python3 send_emails.py --brand X      # Sadece X markasına gönder
  python3 send_emails.py --auth-only    # Sadece OAuth2 kimlik doğrulaması yap
"""

import json
import sys
import base64
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ── Config ──────────────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
MESSAGES_FILE = "data/outreach_messages.json"
SENDER_EMAIL = None  # OAuth2 ile otomatik belirlenir


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
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES,
            )
            creds = flow.run_local_server(port=8080)

        # Token'ı kaydet
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print("[INFO] ✅ Token kaydedildi.")

    return creds


def create_message(to: str, subject: str, body: str, sender: str = None) -> dict:
    """MIME e-posta oluşturur."""
    message = MIMEMultipart("alternative")
    message["to"] = to
    message["subject"] = subject
    if sender:
        message["from"] = sender

    # Plain text
    text_part = MIMEText(body, "plain", "utf-8")
    message.attach(text_part)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"raw": raw}


def send_email(service, message: dict) -> dict:
    """Gmail API ile e-posta gönderir."""
    result = service.users().messages().send(userId="me", body=message).execute()
    return result


def load_messages() -> dict:
    """Outreach mesajlarını yükler."""
    with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    dry_run = "--dry-run" in sys.argv
    auth_only = "--auth-only" in sys.argv
    target_brand = None

    for i, arg in enumerate(sys.argv):
        if arg == "--brand" and i + 1 < len(sys.argv):
            target_brand = sys.argv[i + 1].lower()

    # Kimlik doğrulama
    creds = authenticate()
    print("[INFO] ✅ Gmail API kimlik doğrulaması başarılı.")

    if auth_only:
        print("[INFO] Sadece kimlik doğrulaması yapıldı. Çıkış.")
        return

    service = build("gmail", "v1", credentials=creds)
    messages = load_messages()

    # Gönderilecek e-postaları hazırla
    to_send = []
    for handle, data in messages.items():
        email = data.get("general_email")
        if not email:
            continue
        if target_brand and target_brand not in handle.lower() and target_brand not in data["brand_name"].lower():
            continue

        to_send.append({
            "handle": handle,
            "brand_name": data["brand_name"],
            "to": email,
            "subject": data["email_subject"],
            "body": data["email_body"],
            "instagram_url": data["instagram_url"],
        })

    if not to_send:
        print("[WARN] Gönderilecek e-posta bulunamadı.")
        return

    # Listele
    print(f"\n{'='*60}")
    print(f"📧 GÖNDERİLECEK E-POSTALAR ({len(to_send)} adet)")
    print(f"{'='*60}")
    for i, item in enumerate(to_send, 1):
        print(f"  {i:2d}. {item['brand_name']:20s} → {item['to']}")
    print(f"{'='*60}")

    if dry_run:
        print("\n[DRY-RUN] E-postalar gönderilmedi. Gerçek gönderim için --dry-run argümanını kaldırın.")

        # Her bir mesajın önizlemesini göster
        for item in to_send[:3]:
            print(f"\n{'─'*60}")
            print(f"📧 {item['brand_name']} → {item['to']}")
            print(f"Konu: {item['subject']}")
            print(f"{'─'*60}")
            print(item['body'][:300] + "...")

        return

    # Onay iste
    print(f"\n⚠️  {len(to_send)} e-posta gönderilecek. Devam etmek istiyor musunuz? (e/h): ", end="")
    answer = input().strip().lower()
    if answer not in ("e", "evet", "y", "yes"):
        print("[INFO] İptal edildi.")
        return

    # Gönder
    sent = 0
    failed = 0
    for item in to_send:
        try:
            msg = create_message(
                to=item["to"],
                subject=item["subject"],
                body=item["body"],
            )
            result = send_email(service, msg)
            print(f"  ✅ {item['brand_name']:20s} → {item['to']} (ID: {result['id']})")
            sent += 1
        except Exception as e:
            print(f"  ❌ {item['brand_name']:20s} → {item['to']} HATA: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"📊 SONUÇ: {sent} gönderildi, {failed} başarısız")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
