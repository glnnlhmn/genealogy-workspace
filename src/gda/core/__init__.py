# Name: __init__.py
# Path: src/gda/core/__init__.py
# Version: 1.0.0+build.r2

"""GDA Core framework library.

Exposes domain-agnostic foundational primitives, configuration schemas,
structured logging pipelines, runtime introspection mixins, and exception trees.
"""

from __future__ import annotations

from gda.core.config import AppConfig, DatabaseConfig, LoggingConfig
from gda.core.errors import (
    ConfigError,
    ConfigParseError,
    ConfigValidationError,
    GenealogyDeskError,
)
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import ConsoleFormatter, GDALogger, JsonFormatter

__version__ = "1.0.0+build.r2"

__all__ = [
    "AppConfig",
    "ConfigError",
    "ConfigParseError",
    "ConfigValidationError",
    "ConsoleFormatter",
    "DatabaseConfig",
    "GDALogger",
    "GenealogyDeskError",
    "IntrospectableMixin",
    "JsonFormatter",
    "LoggingConfig",
]
