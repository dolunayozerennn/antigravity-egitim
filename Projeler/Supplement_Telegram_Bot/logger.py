import logging
import sys

def get_logger(name):
    """
    Antigravity V2 Standard Logger
    - INFO ve üzeri
    - Stack trace kaybetmez
    - Railway loglarında okunabilir format
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
