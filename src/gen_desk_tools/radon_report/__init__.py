"""Path: src/gen_desk_tools/radon_report/__init__.py

Combined Radon static analysis report package (gdradon).

Operational Role:
    Re-exports combined CC, MI, and RAW report generation helpers and CLI
    entrypoints for GenDesk Tools.
"""

from __future__ import annotations

from gen_desk_tools.radon_report.cli import build_parser, main, run
from gen_desk_tools.radon_report.scanner import (
    DEFAULT_MAX_DEPTH,
    MODE_TARGETS,
    build_combined_radon_report,
    format_radon_section,
    generate_radon_report,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "DEFAULT_MAX_DEPTH",
    "MODE_TARGETS",
    "__version__",
    "build_combined_radon_report",
    "build_parser",
    "format_radon_section",
    "generate_radon_report",
    "main",
    "run",
]
