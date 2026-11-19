"""Path: src/system/gd_metrics/__init__.py

First-class code quality, coverage, and test suite telemetry package.

Provides modular configuration loading, live progress reporting, Radon/pytest
metric collection, AST-based conftest/marker analysis, and Google Sheets sync.
"""

from __future__ import annotations

from system.gd_metrics.config import (
    BatchDefinition,
    MetricsConfig,
    load_config,
    resolve_batches,
)
from system.gd_metrics.progress import ProgressReporter

__version__ = "1.0.0+build.1"

__all__ = [
    "BatchDefinition",
    "MetricsConfig",
    "ProgressReporter",
    "__version__",
    "load_config",
    "resolve_batches",
]
