from config import settings
from logger import get_logger
from core.apify_client import fetch_all_social_media
from infrastructure.email_sender import send_performance_report, send_technical_error_report
from core.llm_helper import generate_report_summary
from infrastructure.state_manager import NotifiedVideosManager

logger = get_logger(__name__)

from ops_logger import wait_all_loggers

def main():
    logger.info(f"Ceren Sosyal Medya Performans Raporu Botu Baslatildi (ENV={settings.ENV}, DRY_RUN={settings.IS_DRY_RUN})")
    try:
        state_manager = NotifiedVideosManager()
        videos, errors = fetch_all_social_media()
        
        if errors:
            logger.warning(f"Apify cekerken {len(errors)} hata olustu. Dev e-postasina bildiriliyor.")
            send_technical_error_report(errors)
            
        new_videos = []
        for v in videos:
            url = v.get("url")
            if url and not state_manager.is_notified(url):
                new_videos.append(v)
            
        if new_videos:
            logger.info(f"Toplam {len(new_videos)} YENİ baraji asan video bulundu, maile hazirlaniyor...")
            summary = generate_report_summary(new_videos)
            
            try:
                send_performance_report(new_videos, report_summary=summary)
                for v in new_videos:
                    state_manager.mark_as_notified(v["url"], v.get("platform", "Unknown"), v.get("views", 0))
                logger.info(f"{len(new_videos)} video başarıyla state manager'a kaydedildi.")
            except Exception as e:
                logger.error(f"Performans raporu gönderilirken hata oluştu, state işlenmedi: {e}", exc_info=True)
                raise e
        else:
            logger.info("Baraji asan hicbir YENİ video bulunamadi, Ceren'e e-posta gonderilmiyor.")
            
        logger.info("Islem basariyla tamamlandi.")
    except Exception as e:
        logger.error(f"Uygulama calisirken fatal bir hata olustu: {e}", exc_info=True)
        send_technical_error_report([f"Fatal Uygulama Hatası (Sistem Çöktü): {e}"])
    finally:
        wait_all_loggers()

if __name__ == "__main__":
    main()
