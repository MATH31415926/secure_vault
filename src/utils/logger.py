"""
Secure Vault - Logging System
Daily rotating logs with 30-day auto cleanup.
"""

import logging
from datetime import datetime
from typing import Optional
import threading

from src.core.i18n import _



class VaultLogger:
    """Logger with memory-only logs for UI display."""
    
    _instance: Optional["VaultLogger"] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._logger = logging.getLogger("SecureVault")
        self._logger.setLevel(logging.DEBUG)
        self._callbacks: list = []
        
        # We no longer setup file handlers as requested: "不要保存log文件"
    
    def add_callback(self, callback) -> None:
        """Add callback for log messages (for UI updates)."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback) -> None:
        """Remove a log callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self, level: str, message: str) -> None:
        """Notify all callbacks of new log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        for callback in self._callbacks:
            try:
                callback(timestamp, level, message)
            except Exception:
                pass
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self._logger.debug(message)
        self._notify_callbacks("DEBUG", message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self._logger.info(message)
        self._notify_callbacks("INFO", message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self._logger.warning(message)
        self._notify_callbacks("WARNING", message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self._logger.error(message)
        self._notify_callbacks("ERROR", message)
    
    def operation(self, operation: str, target: str, details: str = "", status: str = "") -> None:
        """Log an operation with structured format."""
        message = f"[{operation}] {target}"
        if details:
            message += f" - {details}"
        if status:
            message = f"{status}: {message}"
        self.info(message)
        
    def operation_start(self, operation: str, target: str, details: str = "") -> None:
        """Log the start of a long-running operation."""
        self.operation(operation, target, details, status=_("status_start"))
        
    def operation_end(self, operation: str, target: str, details: str = "", success: bool = True) -> None:
        """Log the end of a long-running operation."""
        status = _("status_finish") if success else _("status_failed")
        self.operation(operation, target, details, status=status)


def get_logger() -> VaultLogger:
    """Get the global logger instance."""
    return VaultLogger()
