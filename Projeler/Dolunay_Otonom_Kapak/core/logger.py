import logging
import sys

def get_logger(name, level="INFO"):
    """
    Antigravity V2 Standard Logger
    Özellikler:
    - Default olarak INFO ve üzeri çalışır (level parametresiyle ayarlanabilir)
    - Exception ve Hata detayı olan stack trace'leri yutmaz, formatlı loglar.
    - Tüm Railway projelerinde aynı formata sahip olmayı garanti eder.
    """
    logger = logging.getLogger(name)
    
    # Sadece bir kere handler ekleyelim (multiple runs vs için)
    if not logger.handlers:
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        
        # Format: 2026-03-24 15:30:21 - module_name - INFO - Mesaj
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger
