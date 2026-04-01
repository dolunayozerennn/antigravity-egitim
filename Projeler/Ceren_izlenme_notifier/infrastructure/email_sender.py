import base64
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from logger import get_logger
from config import settings

logger = get_logger(__name__)

def get_gmail_service():
    try:
        creds = Credentials.from_authorized_user_file(settings.OAUTH_TOKEN_PATH, ['https://www.googleapis.com/auth/gmail.modify'])
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Gmail servisi baslatilamadi: {e}", exc_info=True)
        return None

def send_performance_report(videos):
    if not videos:
        logger.info("Raporlanacak sınırları asan video bulunmadi.")
        return
        
    service = get_gmail_service()
    if not service:
        return

    msg = EmailMessage()
    
    html_content = "<h2>Sosyal Medya Performans Raporu</h2>"
    html_content += "<p>Son 7 gün içerisinde barajı aşan yeni videolar (Shorts: 100K+, Long-Form: 10K+, IG: 200K+, TikTok: 100K+):</p>"
    html_content += "<ul>"
    
    for v in videos:
        html_content += f"<li style='margin-bottom: 10px;'>"
        html_content += f"<b>Platform:</b> {v['platform']}<br>"
        # Format numbers safely
        views = f"{v.get('views', 0):,}" if isinstance(v.get('views'), (int, float)) else v.get('views')
        html_content += f"<b>İzlenme Sayısı:</b> {views}<br>"
        html_content += f"<b>Tarih:</b> {v.get('date', 'Bilinmiyor')}<br>"
        html_content += f"<b>Link:</b> <a href='{v['url']}'>İzlemek için tıkla</a>"
        html_content += f"</li>"
    
    html_content += "</ul>"
    
    msg.set_content("HTML destekleyen bir mail istemcisi kullanin.")
    msg.add_alternative(html_content, subtype='html')

    msg['To'] = 'ceren@dolunay.ai'
    msg['From'] = 'Dolunay Özeren <dolunay@dolunay.ai>'
    msg['Subject'] = 'Otomatik Sosyal Medya Raporu'

    raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

    if settings.IS_DRY_RUN:
        logger.info("[DRY-RUN] Mail gonderimi atlaniyor. Duzenlenen HTML Icerik:")
        logger.info(html_content)
        return
        
    try:
        message = service.users().messages().send(userId="me", body={'raw': raw_msg}).execute()
        logger.info(f"Rapor basariyla gonderildi. Message Id: {message['id']}")
    except Exception as e:
        logger.error(f"Rapor gonderilim hatasi: {e}", exc_info=True)
