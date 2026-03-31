import time
from config import settings
from logger import get_logger

log = get_logger("MainApp")

def main():
    log.info(f"🚀 Uygulama başlatılıyor... (Mod: {'DRY-RUN' if settings.IS_DRY_RUN else 'PRODUCTION'})")
    
    try:
        # Business logic başlar: core/ ve infrastructure/ çağrılır
        # Örnek çağrı:
        # data = fetch_data_from_api()
        # process_data(data)
        
        log.info("İşlem başarıyla tamamlandı.")
        
    except Exception as e:
        # Asla pass geçme veya sadece print() kullanma!
        log.error("Kritik Hata (P1 / P2 logu)", exc_info=True)
        # Eğer bu bir polling/cron loop'u ise ve P1/Kritik ise raise e yapıp programın çökmesini sağla
        raise

if __name__ == "__main__":
    main()
