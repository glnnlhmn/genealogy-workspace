"""Path: src/gda/core/logging.py

Structured JSON and console logging subsystem for GDA Core.

Operational Role:
    Implements standardized single-line JSON log formatting for machine ingestion
    and bracketed console formatting for operator terminals. Provides the GDALogger
    service configured directly via LoggingConfig, including explicit handler
    teardown and context-manager lifecycle support.

Classes:
    JsonFormatter: Formats LogRecord into canonical single-line JSON strings.
    ConsoleFormatter: Formats LogRecord into bracketed human-readable terminal output.
    GDALogger: Logging service wrapping standard library logger.
"""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import Any, Self

from gda.core.config import LoggingConfig
from gda.core.dates import utc_now_iso
from gda.core.errors import GenealogyDeskError

__version__ = "1.0.0+build.12"

__all__ = [
    "ConsoleFormatter",
    "GDALogger",
    "JsonFormatter",
]


def _serialize_exc_payload(
    formatter: logging.Formatter,
    record: logging.LogRecord,
) -> dict[str, Any] | None:
    """Serialize attached exc attribute or record.exc_info into a JSON-ready dict."""
    exc = getattr(record, "exc", None)
    if isinstance(exc, GenealogyDeskError):
        return exc.to_dict()
    if isinstance(exc, Exception):
        return {"type": type(exc).__name__, "message": str(exc)}
    if record.exc_info:
        exc_type, exc_val, _ = record.exc_info
        return {
            "type": exc_type.__name__ if exc_type else "Exception",
            "message": str(exc_val) if exc_val else "",
            "traceback": formatter.formatException(record.exc_info),
        }
    return None


def _dumps_json_safe(payload: dict[str, Any]) -> str:
    """Serialize payload to single-line JSON, falling back to repr() on cycles."""
    try:
        return json.dumps(payload, ensure_ascii=False, default=str)
    except ValueError:
        safe_payload: dict[str, Any] = {
            "timestamp": payload["timestamp"],
            "level": payload["level"],
            "logger": payload["logger"],
            "message": payload["message"],
        }
        if "details" in payload:
            safe_payload["details"] = repr(payload["details"])
        if "error" in payload:
            safe_payload["error"] = repr(payload["error"])
        return json.dumps(safe_payload, ensure_ascii=False, default=str)


class JsonFormatter(logging.Formatter):
    """Format LogRecord into deterministic, single-line JSON payloads."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a log record into a single-line JSON string."""
        payload: dict[str, Any] = {
            "timestamp": utc_now_iso(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        details = getattr(record, "details", None)
        if isinstance(details, dict):
            payload["details"] = details

        exc_payload = _serialize_exc_payload(self, record)
        if exc_payload is not None:
            payload["error"] = exc_payload

        return _dumps_json_safe(payload)


class ConsoleFormatter(logging.Formatter):
    """Format LogRecord into bracketed, readable console text."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record into bracketed terminal output."""
        msg = f"[{record.levelname}] [{record.name}] {record.getMessage()}"
        details = getattr(record, "details", None)
        if details:
            msg += f" | details={details}"

        exc = getattr(record, "exc", None)
        if isinstance(exc, GenealogyDeskError):
            msg += f" | error=[{exc.error_code}] {exc.message}"
        elif isinstance(exc, Exception):
            msg += f" | error={type(exc).__name__}: {exc}"
        elif record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"

        return msg


class GDALogger:
    """Standardized logger adapter enforcing GDA logging conventions."""

    def __init__(
        self,
        name: str,
        config: LoggingConfig | None = None,
        base_dir: str | Path | None = None,
    ) -> None:
        """Initialize GDALogger with handlers governed by LoggingConfig."""
        self.name = name
        self.config = config or LoggingConfig()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.config.level, logging.INFO))

        # Explicitly close and remove existing handlers to release Windows file locks
        self.close()
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

    def close(self) -> None:
        """Close and detach all active handlers on the underlying logger."""
        for handler in list(self.logger.handlers):
            handler.close()
            self.logger.removeHandler(handler)

    def __enter__(self) -> Self:
        """Enter context manager and return this GDALogger instance."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close and detach all handlers when exiting a with-block."""
        self.close()

    def _log(
        self,
        level: int,
        msg: str,
        *,
        details: dict[str, Any] | None = None,
        exc: Exception | None = None,
    ) -> None:
        """Dispatch a log record with optional structured details and exception metadata."""
        extra: dict[str, Any] = {}
        if details is not None:
            extra["details"] = details
        if exc is not None:
            extra["exc"] = exc
        self.logger.log(level, msg, extra=extra)

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
