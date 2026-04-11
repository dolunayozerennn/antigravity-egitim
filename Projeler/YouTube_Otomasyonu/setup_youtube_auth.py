"""
YouTube OAuth2 Token Oluşturucu
Tarayıcı açılacak, Google hesabınızla giriş yapıp izin verin.
Token otomatik kaydedilecek.
"""
import os
import json

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CREDS_FILE = os.path.join(os.path.dirname(__file__), "youtube_credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "youtube_token.json")

def main():
    from google_auth_oauthlib.flow import InstalledAppFlow
    
    print("🔐 YouTube OAuth2 akışı başlatılıyor...")
    print("   Tarayıcı açılacak — Google hesabınızla giriş yapın.")
    
    flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
    credentials = flow.run_local_server(port=8090, open_browser=True)
    
    with open(TOKEN_FILE, "w") as f:
        f.write(credentials.to_json())
    
    print(f"✅ Token kaydedildi: {TOKEN_FILE}")
    print("   Artık YouTube upload otomatik çalışacak!")

if __name__ == "__main__":
    main()
