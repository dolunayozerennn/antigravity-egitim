"""
Ceren_Marka_Takip — Logging Konfigürasyonu
=============================================
Standart logging setup — hem konsol hem dosya çıktısı.
"""

import logging
import os
import sys
from datetime import datetime


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Merkezi logging konfigürasyonu.
    
    Args:
        level: Log seviyesi (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Root logger
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Format
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Mevcut handler'ları temizle (duplicate engellemek için)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Gürültülü kütüphaneleri sustur
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("google.auth").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httplib2").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root_logger
