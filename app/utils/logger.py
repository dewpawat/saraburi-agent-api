import os
import sys
import logging
from datetime import datetime
from typing import Optional

# Determine project root and logs directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_DIR = os.path.join(BASE_DIR, "logs")

try:
    os.makedirs(LOG_DIR, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create log directory {LOG_DIR}: {e}")

class DailyAccessHandler(logging.Handler):
    """
    Writes access logs to a separate daily file (access_YYYY-MM-DD.log).
    - Exactly 1 file per day (365 files per year).
    - Never deletes or purges any past log files.
    - Thread-safe and resilient to restarts.
    """
    def __init__(self, log_dir: str):
        super().__init__()
        self.log_dir = log_dir
        self._current_date = None
        self._file_handle = None

    def emit(self, record):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            if today != self._current_date or self._file_handle is None or self._file_handle.closed:
                if self._file_handle and not self._file_handle.closed:
                    try:
                        self._file_handle.close()
                    except Exception:
                        pass
                
                self._current_date = today
                filepath = os.path.join(self.log_dir, f"access_{today}.log")
                self._file_handle = open(filepath, "a", encoding="utf-8")

            msg = self.format(record)
            self._file_handle.write(msg + "\n")
            self._file_handle.flush()
        except Exception:
            self.handleError(record)

    def close(self):
        try:
            if self._file_handle and not self._file_handle.closed:
                self._file_handle.close()
        except Exception:
            pass
        super().close()

# Configure access logger
access_logger = logging.getLogger("saraburi_agent.access")
access_logger.setLevel(logging.INFO)
access_logger.propagate = False  # Avoid duplicate entries in root logger

# Attach DailyAccessHandler
try:
    daily_handler = DailyAccessHandler(LOG_DIR)
    formatter = logging.Formatter("%(message)s")
    daily_handler.setFormatter(formatter)
    access_logger.addHandler(daily_handler)
except Exception as e:
    print(f"Warning: Could not initialize DailyAccessHandler: {e}")

# Standard server console logger
console_logger = logging.getLogger("saraburi_agent")

def log_access(
    client_ip: str,
    method: str,
    path: str,
    hospcode: Optional[str] = "-",
    status_code: int = 200,
    process_time_ms: float = 0.0,
    detail: Optional[str] = None
):
    """
    Logs an API request event to both daily file and server console.
    Guaranteed non-blocking: never raises an exception back into caller.
    """
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hospcode_str = hospcode if hospcode and hospcode != "" else "-"
        
        log_line = (
            f"{now_str} | IP: {client_ip} | {method} {path} | "
            f"Hospcode: {hospcode_str} | Status: {status_code} | Time: {process_time_ms:.2f}ms"
        )
        if detail:
            log_line += f" | Detail: {detail}"

        # 1. Write to daily access log file (access_YYYY-MM-DD.log)
        access_logger.info(log_line)
        
        # 2. Also log to console for 'docker compose logs -f'
        if status_code >= 400:
            console_logger.warning(log_line)
        else:
            console_logger.info(log_line)
    except Exception:
        # Logging failure must NEVER crash the actual API response
        pass
