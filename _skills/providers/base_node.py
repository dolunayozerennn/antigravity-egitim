import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def ana_retry_and_catch(node_name: str, max_retries: int = 3, base_delay: int = 2):
    """
    Antigravity Node Architecture (ANA) standard retry and observable catch decorator.
    Provides exponential backoff and structured error logging.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    err_msg = str(e)
                    
                    # Observable Catch Standartlarına uygun loglama
                    logger.warning(f"🚨 [{node_name}] Attempt {retries}/{max_retries + 1} Failed: {err_msg}")
                    
                    if retries > max_retries:
                        logger.error(f"❌ [{node_name}] Max retries reached. Final Error: {err_msg}", exc_info=True)
                        raise Exception(f"[{node_name}] Fatal Error after {max_retries} retries: {err_msg}") from e
                    
                    # Exponential backoff
                    time.sleep(base_delay ** retries)
        return wrapper
    return decorator
