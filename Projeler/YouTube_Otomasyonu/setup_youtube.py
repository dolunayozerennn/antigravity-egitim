#!/usr/bin/env python3
"""
YouTube Kanal Bağlama — OAuth2 Setup Script
============================================
Bu scripti BİR KEZ çalıştırman yeterli.
Tarayıcı açılır → Google hesabınla giriş yap → YouTube izni ver → Token kaydedilir.

Kullanım:
  python3 setup_youtube.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

# ── Paths ──
PROJECT_DIR = os.path.dirname(__file__)
CREDS_PATH = os.path.join(PROJECT_DIR, "youtube_credentials.json")
TOKEN_PATH = os.path.join(PROJECT_DIR, "youtube_token.json")

# ── YouTube API Scopes ──
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def main():
    print("=" * 60)
    print("🔐 YouTube Kanal Bağlama — OAuth2 Setup")
    print("=" * 60)

    # ── 1. Bağımlılık kontrolü ──
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError as e:
        print(f"\n❌ Eksik bağımlılık: {e}")
        print("   Çözüm: pip install google-auth google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    # ── 2. Client ID & Secret ──
    # master.env'den veya env variable'lardan al
    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        # master.env'den oku
        master_env = os.path.expanduser("~/Desktop/Antigravity/_knowledge/credentials/master.env")
        if os.path.exists(master_env):
            with open(master_env, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("YOUTUBE_CLIENT_ID="):
                        client_id = line.split("=", 1)[1].strip()
                    elif line.startswith("YOUTUBE_CLIENT_SECRET="):
                        client_secret = line.split("=", 1)[1].strip()

    if not client_id or not client_secret:
        print("\n❌ YOUTUBE_CLIENT_ID veya YOUTUBE_CLIENT_SECRET bulunamadı!")
        print("   master.env dosyasını veya env variable'ları kontrol et.")
        sys.exit(1)

    print(f"\n✅ Client ID: {client_id[:30]}...")
    print(f"✅ Client Secret: {client_secret[:10]}...")

    # ── 3. credentials.json oluştur ──
    credentials_data = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"],
        }
    }

    with open(CREDS_PATH, "w") as f:
        json.dump(credentials_data, f, indent=2)
    print(f"\n📝 Credentials dosyası oluşturuldu: {CREDS_PATH}")

    # ── 4. Mevcut token var mı? ──
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if creds and creds.valid:
            print(f"\n✅ Mevcut token geçerli! Yeniden yetkilendirme gerekmez.")
        elif creds and creds.expired and creds.refresh_token:
            print("\n🔄 Token süresi dolmuş, yenileniyor...")
            creds.refresh(Request())
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
            print("✅ Token yenilendi!")
        else:
            creds = None

    # ── 5. Yeni yetkilendirme ──
    if not creds or not creds.valid:
        print("\n🌐 Tarayıcı açılacak — Google hesabınla giriş yap ve YouTube iznini ver.")
        print("   (Eğer 'This app isn't verified' uyarısı gelirse → Advanced → Go to ... tıkla)")
        print()
        input("   Hazır olduğunda ENTER'a bas...")

        flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
        creds = flow.run_local_server(
            port=8080,
            prompt="consent",
            access_type="offline",  # refresh_token almak için
        )

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        print(f"\n✅ Token kaydedildi: {TOKEN_PATH}")

    # ── 6. Kanal bilgisi test ──
    print("\n🔍 YouTube kanalı kontrol ediliyor...")
    try:
        youtube = build("youtube", "v3", credentials=creds)
        response = youtube.channels().list(
            part="snippet,statistics",
            mine=True
        ).execute()

        channels = response.get("items", [])
        if channels:
            ch = channels[0]
            snippet = ch.get("snippet", {})
            stats = ch.get("statistics", {})

            print(f"\n{'=' * 60}")
            print(f"✅ YOUTUBE KANALI BAŞARIYLA BAĞLANDI!")
            print(f"{'=' * 60}")
            print(f"   📺 Kanal: {snippet.get('title', 'N/A')}")
            print(f"   📝 Açıklama: {snippet.get('description', 'N/A')[:80]}")
            print(f"   👥 Abone: {stats.get('subscriberCount', 'N/A')}")
            print(f"   🎬 Video: {stats.get('videoCount', 'N/A')}")
            print(f"   👁️ Görüntülenme: {stats.get('viewCount', 'N/A')}")
            print(f"   🔗 ID: {ch.get('id', 'N/A')}")
            print(f"\n   Token: {TOKEN_PATH}")
            print(f"   ⚠️ Bu token ile video yükleme yapılabilir!")
        else:
            print("\n⚠️ Bu Google hesabında YouTube kanalı bulunamadı.")
            print("   YouTube'da bir kanal oluşturup scripti tekrar çalıştır.")

    except Exception as e:
        print(f"\n⚠️ Kanal bilgisi alınamadı: {e}")
        print("   Token yine de kaydedildi, upload denemesi yapılabilir.")

    print(f"\n{'=' * 60}")
    print("📋 Sonraki adımlar:")
    print("   1. config.py'de YOUTUBE_ENABLED=true yap")
    print("   2. Bot'u yeniden başlat")
    print("   3. Artık üretilen videolar otomatik YouTube'a yüklenecek!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
