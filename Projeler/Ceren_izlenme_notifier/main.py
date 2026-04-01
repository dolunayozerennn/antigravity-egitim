from config import settings
from logger import get_logger
from core.apify_client import fetch_all_social_media
from infrastructure.email_sender import send_performance_report

logger = get_logger(__name__)

def main():
    logger.info(f"Ceren Sosyal Medya Performans Raporu Botu Baslatildi (ENV={settings.ENV}, DRY_RUN={settings.IS_DRY_RUN})")
    try:
        videos = fetch_all_social_media()
        
        if videos:
            logger.info(f"Toplam {len(videos)} baraji asan video bulundu, maile hazirlaniyor...")
            send_performance_report(videos)
        else:
            logger.info("Baraji asan hicbir video bulunamadi, e-posta gonderilmiyor.")
            
        logger.info("Islem basariyla tamamlandi.")
    except Exception as e:
        logger.error(f"Uygulama calisirken fatal bir hata olustu: {e}", exc_info=True)

if __name__ == "__main__":
    main()
