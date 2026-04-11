"""
YouTube Uploader — YouTube Data API v3 ile video yükleme.
OAuth2 authentication, resumable upload, dry-run desteği.

NOT: İlk çalıştırmada OAuth2 token'ı oluşturmak için tarayıcı gerekir.
Sonraki çalıştırmalarda token otomatik yenilenir.
"""
import os
import json
from config import settings
from logger import get_logger

log = get_logger("YouTubeUploader")

# YouTube API scopes
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def upload_to_youtube(video_path: str, content: dict) -> str:
    """
    Videoyu YouTube'a yükler.
    
    Args:
        video_path: Yerel video dosyasının yolu
        content: {title, description, tags} — prompt_generator'dan gelen veri
        
    Returns:
        str: YouTube video URL'si (veya dry-run'da mock URL)
        
    Raises:
        RuntimeError: Upload başarısız olduğunda
    """
    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: YouTube upload simüle ediliyor...")
        log.info(f"   Başlık: {content.get('title', 'N/A')}")
        log.info(f"   Dosya: {video_path}")
        return "https://youtube.com/shorts/DRY-RUN-MOCK-ID"

    if not settings.YOUTUBE_ENABLED:
        log.warning("⚠️ YouTube upload devre dışı (YOUTUBE_ENABLED=false)")
        log.info("   Video sadece indirildi, YouTube'a yüklenmedi.")
        return ""

    # Lazy import — sadece gerçek upload'da yükle
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as e:
        log.error(f"❌ Google API kütüphaneleri yüklü değil: {e}")
        raise RuntimeError(
            "YouTube upload için gerekli kütüphaneler eksik. "
            "pip install google-auth google-auth-oauthlib google-api-python-client"
        )

    # ── OAuth2 Credentials ──
    creds = _get_credentials()

    # ── YouTube Service ──
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)

    # ── Video Metadata ──
    title = content.get("title", "AI Generated Video")[:100]  # YouTube max 100 char
    description = _build_description(content)
    tags = content.get("tags", ["ai", "shorts", "space"])

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": settings.YOUTUBE_CATEGORY_ID,
        },
        "status": {
            "privacyStatus": settings.YOUTUBE_PRIVACY,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
        }
    }

    # ── Resumable Upload ──
    log.info(f"📺 YouTube'a yükleniyor: \"{title}\"")

    media = MediaFileUpload(
        video_path,
        chunksize=1024 * 1024,  # 1MB chunks
        resumable=True,
        mimetype="video/mp4"
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            log.info(f"   Upload: {progress}%")

    video_id = response.get("id", "")
    video_url = f"https://youtube.com/shorts/{video_id}"

    log.info(f"✅ YouTube'a yüklendi!")
    log.info(f"   URL: {video_url}")
    log.info(f"   Video ID: {video_id}")

    return video_url


def _get_credentials():
    """OAuth2 credentials'ı al veya yenile."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "youtube_token.json")
    creds_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "youtube_credentials.json")

    creds = None

    # Mevcut token'ı yükle
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, [YOUTUBE_UPLOAD_SCOPE])

    # Token geçersiz veya expired ise yenile
    if creds and creds.expired and creds.refresh_token:
        log.info("🔄 YouTube token yenileniyor...")
        creds.refresh(Request())
        with open(token_path, "w") as f:
            f.write(creds.to_json())
        log.info("✅ Token yenilendi.")

    elif not creds or not creds.valid:
        # İlk kez — tarayıcı ile OAuth akışı
        if not os.path.exists(creds_path):
            # Credentials dosyası yoksa, config'den oluştur
            _create_credentials_file(creds_path)

        log.info("🔐 YouTube OAuth2 akışı başlatılıyor (tarayıcı açılacak)...")
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, [YOUTUBE_UPLOAD_SCOPE])
        creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())
        log.info("✅ YouTube token kaydedildi.")

    return creds


def _create_credentials_file(creds_path: str):
    """Config'deki Client ID/Secret'tan credentials.json oluşturur."""
    if not settings.YOUTUBE_CLIENT_ID or not settings.YOUTUBE_CLIENT_SECRET:
        raise RuntimeError(
            "YouTube upload için YOUTUBE_CLIENT_ID ve YOUTUBE_CLIENT_SECRET "
            "ortam değişkenleri gerekli!"
        )

    credentials_data = {
        "installed": {
            "client_id": settings.YOUTUBE_CLIENT_ID,
            "client_secret": settings.YOUTUBE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"]
        }
    }

    with open(creds_path, "w") as f:
        json.dump(credentials_data, f, indent=2)

    log.info(f"📝 YouTube credentials dosyası oluşturuldu: {creds_path}")


def _build_description(content: dict) -> str:
    """YouTube video açıklaması oluşturur."""
    desc = content.get("description", "")
    tags = content.get("tags", [])

    hashtags = " ".join(f"#{tag}" for tag in tags[:5])

    return f"""{desc}

🤖 This video was generated using AI (Seedance 2.0)
📹 Bodycam POV | AI-Generated Content

{hashtags}
#shorts #ai #aiart #seedance #space"""
