# Name: logging.py
# Path: src/gda/core/logging.py
# Version: 1.0.0+build.r6

"""Structured JSON and console logging subsystem for GDA Core.

Operational Role:
    Implements standardized single-line JSON log formatting for machine ingestion
    and bracketed console formatting for operator terminals. Provides the GDALogger
    service configured directly via LoggingConfig.

Classes:
    JsonFormatter: Formats LogRecord into canonical single-line JSON strings.
    ConsoleFormatter: Formats LogRecord into bracketed human-readable terminal output.
    GDALogger: Logging service wrapping standard library logger.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from gda.core.config import LoggingConfig
from gda.core.errors import GenealogyDeskError

__version__ = "1.0.0+build.r6"


class JsonFormatter(logging.Formatter):
    """Format LogRecord into deterministic, single-line JSON payloads."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a log record into a single-line JSON string.

        Args:
            record: Logging record instance.

        Returns:
            JSON-formatted string ending without newline.
        """
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Structured extra payload
        details = getattr(record, "details", None)
        if isinstance(details, dict):
            payload["details"] = details

        # Exception / Error capture under 'error'
        exc = getattr(record, "exc", None)
        if isinstance(exc, GenealogyDeskError):
            payload["error"] = exc.to_dict()
        elif isinstance(exc, Exception):
            payload["error"] = {
                "type": type(exc).__name__,
                "message": str(exc),
            }
        elif record.exc_info:
            exc_type, exc_val, _ = record.exc_info
            payload["error"] = {
                "type": exc_type.__name__ if exc_type else "Exception",
                "message": str(exc_val) if exc_val else "",
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(payload, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Format LogRecord into bracketed, readable console text."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record into bracketed terminal line.

        Args:
            record: Logging record instance.

        Returns:
            Formatted string: [LEVEL] [LOGGER] Message | details={...}.
        """
        msg = f"[{record.levelname}] [{record.name}] {record.getMessage()}"
        details = getattr(record, "details", None)
        if details:
            msg += f" | details={details}"
        return msg


class GDALogger:
    """Standardized logger adapter enforcing GDA logging conventions."""

    def __init__(
        self,
        name: str,
        config: LoggingConfig | None = None,
        base_dir: str | Path | None = None,
    ) -> None:
        """Initialize GDALogger with handlers governed by LoggingConfig.

        Args:
            name: Logger hierarchy namespace identifier.
            config: LoggingConfig instance. Defaults to default LoggingConfig().
            base_dir: Optional root anchor for resolving relative log_file_path.
        """
        self.name = name
        self.config = config or LoggingConfig()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.config.level, logging.INFO))
        self.logger.handlers.clear()
        self.logger.propagate = False

        if self.config.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(ConsoleFormatter())
            self.logger.addHandler(console_handler)

        if self.config.log_to_file:
            log_path = Path(self.config.log_file_path)
            if base_dir and not log_path.is_absolute():
                log_path = Path(base_dir) / log_path
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                filename=log_path,
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(file_handler)

    def debug(self, msg: str, *, details: dict[str, Any] | None = None) -> None:
        """Emit DEBUG level log record."""
        self._log(logging.DEBUG, msg, details=details)

    def info(self, msg: str, *, details: dict[str, Any] | None = None) -> None:
        """Emit INFO level log record."""
        self._log(logging.INFO, msg, details=details)

    def warning(
        self,
        msg: str,
        *,
        details: dict[str, Any] | None = None,
        exc: Exception | None = None,
    ) -> None:
        """Emit WARNING level log record."""
        self._log(logging.WARNING, msg, details=details, exc=exc)

    def error(
        self,
        msg: str,
        *,
        details: dict[str, Any] | None = None,
        exc: Exception | None = None,
    ) -> None:
        """Emit ERROR level log record."""
        self._log(logging.ERROR, msg, details=details, exc=exc)

    def critical(
        self,
        msg: str,
        *,
        details: dict[str, Any] | None = None,
        exc: Exception | None = None,
    ) -> None:
        """Emit CRITICAL level log record."""
        self._log(logging.CRITICAL, msg, details=details, exc=exc)

    def _log(
        self,
        level: int,
        msg: str,
        *,
        details: dict[str, Any] | None = None,
        exc: Exception | None = None,
    ) -> None:
        """Internal dispatcher attaching extra attributes."""
        extra: dict[str, Any] = {}
        if details is not None:
            extra["details"] = details
        if exc is not None:
            extra["exc"] = exc

        self.logger.log(level, msg, extra=extra)
