"""
YouTube Uploader V2 — YouTube Data API v3 ile video yükleme.
Shorts (#Shorts tag) ve Long-form desteği.

Railway-uyumlu OAuth2: Token bilgilerini ENV variable'lardan okur,
dosya sistemi olmadan çalışır. Headless ortamda browser gerekmez.
"""
import os
import json
import asyncio
import logging
from config import settings

log = logging.getLogger("YouTubeUploader")

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


async def upload_to_youtube(video_path: str, prompt_data: dict, is_shorts: bool = True) -> str:
    """
    Videoyu YouTube'a yükler.

    Args:
        video_path: Yerel video dosyasının yolu
        prompt_data: {youtube_title, youtube_description, tags}
        is_shorts: True ise #Shorts tag eklenir

    Returns:
        str: YouTube video URL'si (veya dry-run'da mock URL)
    """
    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: YouTube upload simüle ediliyor...")
        log.info(f"   Başlık: {prompt_data.get('youtube_title', 'N/A')}")
        log.info(f"   Dosya: {video_path}")
        return "https://youtube.com/shorts/DRY-RUN-MOCK-ID"

    if not settings.YOUTUBE_ENABLED:
        log.warning("⚠️ YouTube upload devre dışı (YOUTUBE_ENABLED=false)")
        return ""

    # Lazy import
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as e:
        log.error(f"❌ Google API kütüphaneleri yüklü değil: {e}")
        raise RuntimeError("YouTube upload için Google API kütüphaneleri gerekli.")

    # ── OAuth2 Credentials ──
    creds = _get_credentials()

    # ── YouTube Service ──
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)

    # ── Video Metadata ──
    title = prompt_data.get("youtube_title", "AI Generated Video")[:100]
    description = _build_description(prompt_data, is_shorts)
    tags = prompt_data.get("tags", ["ai", "shorts"])

    if is_shorts:
        tags = list(set(tags + ["Shorts"]))

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
        },
    }

    # ── Upload (sync — thread'de çalıştır) ──
    def _do_upload():
        media = MediaFileUpload(
            video_path,
            chunksize=1024 * 1024,  # 1MB chunks
            resumable=True,
            mimetype="video/mp4",
        )

        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                log.info(f"   Upload: {progress}%")

        return response

    log.info(f"📺 YouTube'a yükleniyor: \"{title}\" ({'Shorts' if is_shorts else 'Long-form'})")
    response = await asyncio.to_thread(_do_upload)

    video_id = response.get("id", "")
    if is_shorts:
        video_url = f"https://youtube.com/shorts/{video_id}"
    else:
        video_url = f"https://www.youtube.com/watch?v={video_id}"

    log.info(f"✅ YouTube'a yüklendi!")
    log.info(f"   URL: {video_url}")
    log.info(f"   Video ID: {video_id}")

    # Token'ı güncelle (refresh olduysa)
    _save_token_if_needed(creds)

    return video_url


def _get_credentials():
    """
    OAuth2 credentials'ı al.

    Öncelik sırası:
    1. ENV variable'lardan reconstruct (Railway uyumlu — ÖNCELİKLİ)
    2. Lokal dosyadan oku (geliştirme ortamı fallback)
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    creds = None

    # ── Yöntem 1: ENV'den Reconstruct (Railway) ──
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
    client_id = settings.YOUTUBE_CLIENT_ID
    client_secret = settings.YOUTUBE_CLIENT_SECRET

    if refresh_token and client_id and client_secret:
        log.info("🔑 YouTube credentials ENV'den yükleniyor (Railway modu)...")
        creds = Credentials(
            token=None,  # Expired — refresh gerekecek
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=[YOUTUBE_UPLOAD_SCOPE],
        )

        # Token'ı refresh et
        try:
            creds.refresh(Request())
            log.info("✅ YouTube token ENV'den refresh edildi.")
            return creds
        except Exception as e:
            log.error(f"❌ ENV-based token refresh başarısız: {e}", exc_info=True)
            # Production'da lokal fallback ÇALIŞMAZ — direkt fail et
            if settings.ENV == "production":
                raise RuntimeError(
                    f"YouTube OAuth2 token refresh başarısız (Railway): {e}. "
                    "YOUTUBE_REFRESH_TOKEN, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET "
                    "env variable'larını kontrol edin."
                )
            # Lokal fallback'e düş (sadece development)

    # ── Yöntem 2: Lokal Dosyadan Oku (Geliştirme) ──
    token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "youtube_token.json")

    if os.path.exists(token_path):
        log.info("📁 YouTube credentials lokal dosyadan yükleniyor...")
        creds = Credentials.from_authorized_user_file(token_path, [YOUTUBE_UPLOAD_SCOPE])

        if creds and creds.expired and creds.refresh_token:
            log.info("🔄 YouTube token yenileniyor...")
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())
            log.info("✅ Token yenilendi ve kaydedildi.")

        if creds and creds.valid:
            return creds

    # ── Yöntem 3: İlk Kez Kurulum (Sadece Lokal) ──
    if not settings.ENV == "production":
        creds_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "youtube_credentials.json")
        if os.path.exists(creds_path):
            log.info("🔐 YouTube OAuth2 akışı başlatılıyor (ilk kurulum)...")
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, [YOUTUBE_UPLOAD_SCOPE])
            creds = flow.run_local_server(port=0)

            with open(token_path, "w") as f:
                f.write(creds.to_json())
            log.info("✅ YouTube token oluşturuldu ve kaydedildi.")
            return creds

    raise RuntimeError(
        "YouTube credentials bulunamadı! "
        "Railway'de YOUTUBE_REFRESH_TOKEN, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET "
        "env variable'ları set edilmeli. "
        "Lokal'de youtube_token.json veya youtube_credentials.json olmalı."
    )


def _save_token_if_needed(creds):
    """Lokal ortamda token'ı dosyaya kaydet (Railway'de geçer)."""
    if settings.ENV == "production":
        return  # Railway'de dosya sistemi ephemeral — kaydetme

    token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "youtube_token.json")
    try:
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    except Exception:
        pass  # Kritik değil


def _build_description(prompt_data: dict, is_shorts: bool) -> str:
    """YouTube video açıklaması oluşturur."""
    desc = prompt_data.get("youtube_description", "")
    tags = prompt_data.get("tags", [])

    hashtags = " ".join(f"#{tag}" for tag in tags[:5])

    lines = [desc]

    if is_shorts:
        lines.append("\n🤖 AI-Generated Short | Powered by Antigravity")
    else:
        lines.append("\n🤖 AI-Generated Video | Powered by Antigravity")

    lines.append(f"\n{hashtags}")
    lines.append("#ai #aiart #aigeneratedvideo")

    return "\n".join(lines)
