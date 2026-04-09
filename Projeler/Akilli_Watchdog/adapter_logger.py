from ops_logger import get_ops_logger
import sys

class OpsLoggerAdapter:
    def __init__(self, name="Watchdog", project="Akilli_Watchdog"):
        self._ops = get_ops_logger(project, name)
        
    def info(self, msg, *args, **kwargs):
        self._ops.info(str(msg))
        
    def warning(self, msg, *args, **kwargs):
        self._ops.warning(str(msg))
        
    def error(self, msg, *args, **kwargs):
        exc_info = kwargs.get("exc_info")
        if exc_info:
            _, exc_value, _ = sys.exc_info()
            self._ops.error(str(msg), exception=exc_value)
        else:
            self._ops.error(str(msg))
            
    def critical(self, msg, *args, **kwargs):
        self.error(msg, *args, **kwargs)
            
    def debug(self, msg, *args, **kwargs):
        self._ops.info(f"[DEBUG] {msg}")

def get_logger(name):
    return OpsLoggerAdapter(name, "Akilli_Watchdog")
