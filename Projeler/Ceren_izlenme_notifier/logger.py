import logging
import sys
from ops_logger import get_ops_logger

class OpsLoggerAdapter:
    def __init__(self, name="Pipeline", project="Ceren_Notifier"):
        self._ops = get_ops_logger(project, name)
        
    def info(self, msg, *args, **kwargs):
        self._ops.info(str(msg))
        
    def warning(self, msg, *args, **kwargs):
        self._ops.warning(str(msg))
        
    def error(self, msg, *args, **kwargs):
        exc_info = kwargs.get("exc_info")
        import sys
        if exc_info:
            _, exc_value, _ = sys.exc_info()
            self._ops.error(str(msg), exception=exc_value)
        else:
            self._ops.error(str(msg))
            
    def debug(self, msg, *args, **kwargs):
        self._ops.info(f"[DEBUG] {msg}")

def get_logger(name):
    return OpsLoggerAdapter(name, "Ceren_Notifier")
