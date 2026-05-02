import base64
import datetime
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build

from logger import get_logger
from config import settings

logger = get_logger(__name__)

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class GmailAuthError(Exception):
    """Gmail OAuth refresh/credential failure — kullanıcı müdahalesi gerek."""


def get_gmail_service():
    """Gmail API servisini başlatır. Hatada None değil exception fırlatır."""
    if not settings.OAUTH_TOKEN_PATH:
        raise GmailAuthError("OAUTH_TOKEN_PATH boş — GMAIL_OAUTH_JSON env'i kontrol et")

    try:
        creds = Credentials.from_authorized_user_file(settings.OAUTH_TOKEN_PATH, GMAIL_SCOPES)
    except Exception as e:
        raise GmailAuthError(f"OAuth token okunamadı ({settings.OAUTH_TOKEN_PATH}): {e}") from e

    if not creds.valid:
        if not creds.refresh_token:
            raise GmailAuthError("Token expired ve refresh_token yok — yeniden authorize gerek")
        try:
            logger.info("OAuth token expired, refresh deneniyor")
            creds.refresh(Request())
            logger.info("OAuth token başarıyla yenilendi")
        except RefreshError as e:
            raise GmailAuthError(
                f"Refresh token reddedildi (büyük ihtimalle revoke/expired): {e}. "
                "Lokal `gmail_oauth_setup` skill'ini çalıştır ve GMAIL_OAUTH_JSON env'ini güncelle."
            ) from e
        except Exception as e:
            raise GmailAuthError(f"Refresh sırasında beklenmeyen hata: {e}") from e

        # Yenilenen token'ı disk'e geri yazmayı dene (Railway ephemeral, lokal kalıcı)
        try:
            with open(settings.OAUTH_TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        except Exception as save_err:
            logger.warning(f"Yenilenen token diske kaydedilemedi: {save_err}")

    return build("gmail", "v1", credentials=creds)


def _send_message(service, msg):
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return service.users().messages().send(userId="me", body={"raw": raw}).execute(num_retries=3)


def _format_errors_html(errors):
    """errors: list of dict({platform, stage, actor_id, error}) veya str."""
    items = []
    for err in errors:
        if isinstance(err, dict):
            items.append(
                f"<li><b>{err.get('platform','?')}</b> [{err.get('stage','?')}] "
                f"actor={err.get('actor_id','?')}<br>"
                f"<code style='color:#7f8c8d'>{err.get('error','?')}</code></li>"
            )
        else:
            items.append(f"<li>{err}</li>")
    return "".join(items)


def send_performance_report(videos, report_summary="", missing_platforms=None):
    """Barajı aşan videoları Ceren'e gönderir. Hata durumunda exception raise eder."""
    if not videos:
        logger.info("Raporlanacak video yok, mail atlanıyor")
        return

    service = get_gmail_service()  # raises GmailAuthError

    msg = EmailMessage()
    today_str = datetime.datetime.now().strftime("%d %B %Y")

    html = [f"""
    <html><body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
      <h2 style="color: #2c3e50;">Sosyal Medya Performans Raporu 🚀</h2>
      <p style="font-size: 14px; margin-bottom: 20px;"><strong>Tarih:</strong> {today_str}</p>
    """]

    if missing_platforms:
        platforms_text = ", ".join(missing_platforms)
        html.append(f"""
        <div style="background-color:#fff3cd; padding:12px; border-left:4px solid #f39c12; margin-bottom:20px;">
            ⚠️ Bu hafta <b>{platforms_text}</b> verisi alınamadı, rapor diğer platformlardan oluşturuldu.
        </div>
        """)

    if report_summary:
        html.append(f"""
        <div style="background-color: #f1f8ff; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 25px;">
            {report_summary}
        </div>
        """)

    html.append(f"""
        <p>Aşağıda hedeflenen barajları aşan içerikler listelenmiştir:</p>
        <p style="font-size: 13px; color: #7f8c8d;">
          Barajlar: Instagram Reels ≥ {settings.IG_VIEW_THRESHOLD:,} |
          TikTok ≥ {settings.TIKTOK_VIEW_THRESHOLD:,} |
          YouTube Shorts ≥ {settings.YT_SHORTS_THRESHOLD:,} |
          YouTube Long-Form ≥ {settings.YT_LONG_THRESHOLD:,}
        </p>
        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
          <thead><tr style="background-color: #f8f9fa;">
              <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Platform</th>
              <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">İzlenme</th>
              <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Tarih</th>
              <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">Link</th>
          </tr></thead><tbody>
    """.replace(",", "."))

    for v in videos:
        try:
            formatted_views = f"{int(v['views']):,}".replace(",", ".")
        except (ValueError, TypeError):
            formatted_views = str(v.get("views", "?"))
        date_str = v.get("date", "Bilinmiyor")
        if isinstance(date_str, str) and "T" in date_str:
            date_str = date_str[:10]
        url = v.get("url", "#")
        html.append(f"""
            <tr>
              <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">{v['platform']}</td>
              <td style="padding: 12px; border: 1px solid #ddd; color: #e74c3c; font-weight: bold;">{formatted_views}</td>
              <td style="padding: 12px; border: 1px solid #ddd;">{date_str}</td>
              <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">
                <a href="{url}" style="background-color: #3498db; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; display: inline-block;">Videoya Git</a>
              </td>
            </tr>
        """)

    html.append("""
          </tbody></table>
        <p style="margin-top: 30px; font-size: 13px; color: #7f8c8d;">
          <em>Bu rapor Antigravity AI tarafından otomatik olarak oluşturulmuştur.</em>
        </p>
    </body></html>
    """)

    msg.set_content("HTML destekleyen bir mail istemcisi kullanın.")
    msg.add_alternative("".join(html), subtype="html")
    msg["To"] = settings.REPORT_TO
    msg["From"] = settings.REPORT_FROM
    msg["Subject"] = f"🔥 Haftalık Sosyal Medya Çıktıları ({today_str})"

    if settings.IS_DRY_RUN:
        logger.info(f"[DRY-RUN] {len(videos)} video, {settings.REPORT_TO} adresine gidecekti")
        return

    result = _send_message(service, msg)
    logger.info(f"Performans raporu gönderildi: id={result.get('id')}")


def send_technical_error_report(errors):
    """Dev'e teknik hata raporu. Auth hatasında sadece logla — hiç mail atılamasın diye."""
    if not errors:
        return

    try:
        service = get_gmail_service()
    except GmailAuthError as e:
        logger.error(f"Gmail auth çöktü, teknik hata maili gönderilemedi: {e}")
        return

    msg = EmailMessage()
    error_html = _format_errors_html(errors)

    html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
      <h2 style="color: #c0392b;">Ceren Notifier — Teknik Hata Raporu ⚠️</h2>
      <p>Pipeline'da aşağıdaki hatalar oluştu:</p>
      <ul>{error_html}</ul>
      <p style="margin-top: 20px; font-size: 13px; color: #7f8c8d;">
        Lütfen Apify dashboard'unu, OAuth token'ını ve Notion DB'sini kontrol et.<br>
        <code>railway run python -m scripts.diagnose</code> ile pre-flight check çalıştırılabilir.
      </p>
    </body></html>
    """

    msg.set_content("HTML destekleyen bir mail istemcisi kullanın.")
    msg.add_alternative(html, subtype="html")
    msg["To"] = settings.TECH_ERROR_TO
    msg["From"] = settings.REPORT_FROM
    msg["Subject"] = "⚠️ Ceren Notifier — Teknik Hata Raporu"

    if settings.IS_DRY_RUN:
        logger.info(f"[DRY-RUN] {len(errors)} hata, {settings.TECH_ERROR_TO} adresine gidecekti")
        return

    try:
        result = _send_message(service, msg)
        logger.info(f"Teknik hata raporu gönderildi: id={result.get('id')}")
    except Exception as e:
        logger.error(f"Teknik hata raporu gönderilemedi: {e}", exc_info=True)
