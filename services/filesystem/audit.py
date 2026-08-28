import os
import time
from pathlib import Path
from typing import Optional

class AuditLogger:
    def __init__(self, log_path: Optional[str] = None):
        if log_path:
            self.log_file = Path(log_path)
        else:
            env_path = os.getenv("JARX_AUDIT_LOG_PATH", "data/logs/filesystem_audit.log")
            self.log_file = Path(env_path)
        
        self.enabled = os.getenv("JARX_AUDIT_LOG", "true").lower() in ("true", "1", "yes")
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def log(self, operation: str, path: str, success: bool, details: str = ""):
        if not self.enabled:
            return
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCCESS" if success else "FAILED"
        msg = f"{timestamp} | {operation:<18} | {path} | {status}"
        if details:
            msg += f" | {details}"
        msg += "\n"
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(msg)
        except Exception:
            pass
