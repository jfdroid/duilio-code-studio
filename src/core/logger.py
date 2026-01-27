"""
Structured Logging Service
===========================
Centralized logging with structured output, levels, and context.
"""

import logging
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra context if present
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "workspace_path"):
            log_data["workspace_path"] = record.workspace_path
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class DuilioLogger:
    """
    Structured logger for DuilioCode.
    
    Features:
    - Structured JSON output
    - Context-aware logging
    - Performance metrics
    - Error tracking
    """
    
    def __init__(
        self,
        name: str = "duiliocode",
        level: LogLevel = LogLevel.INFO,
        log_file: Optional[Path] = None,
        use_json: bool = True
    ):
        """Initialize logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))
        self.logger.handlers.clear()
        
        # Console handler with structured format
        console_handler = logging.StreamHandler(sys.stdout)
        if use_json:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            )
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(file_handler)
    
    def _log_with_context(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log with additional context."""
        extra = kwargs.copy()
        if context:
            extra["context"] = context
        
        getattr(self.logger, level.lower())(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log_with_context("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log_with_context("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log_with_context("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log_with_context("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log_with_context("CRITICAL", message, **kwargs)
    
    def log_action(
        self,
        action: str,
        action_type: str,
        workspace_path: Optional[str] = None,
        success: bool = True,
        duration_ms: Optional[float] = None,
        **kwargs
    ):
        """Log an action with metrics."""
        self.info(
            f"Action: {action}",
            context={
                "action_type": action_type,
                "success": success,
                "duration_ms": duration_ms,
            },
            workspace_path=workspace_path,
            **kwargs
        )
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        workspace_path: Optional[str] = None,
        **kwargs
    ):
        """Log performance metrics."""
        self.info(
            f"Performance: {operation}",
            context={
                "operation": operation,
                "duration_ms": duration_ms,
            },
            workspace_path=workspace_path,
            **kwargs
        )
    
    def log_security_event(
        self,
        event_type: str,
        message: str,
        workspace_path: Optional[str] = None,
        blocked: bool = False,
        **kwargs
    ):
        """Log security-related events."""
        level = "WARNING" if blocked else "INFO"
        self._log_with_context(
            level,
            f"Security: {message}",
            context={
                "event_type": event_type,
                "blocked": blocked,
            },
            workspace_path=workspace_path,
            **kwargs
        )


# Singleton instance
_logger_instance: Optional[DuilioLogger] = None


def get_logger(
    name: str = "duiliocode",
    level: LogLevel = LogLevel.INFO,
    log_file: Optional[Path] = None
) -> DuilioLogger:
    """Get or create logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = DuilioLogger(name=name, level=level, log_file=log_file)
    return _logger_instance
