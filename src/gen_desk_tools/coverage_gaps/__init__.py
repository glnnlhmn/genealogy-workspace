"""Path: src/gen_desk_tools/coverage_gaps/__init__.py

GenDesk Coverage Gaps package (gaps).

Operational Role:
    Re-exports line-range parsing, gap report generation, and CLI entrypoints.
"""

from __future__ import annotations

from gen_desk_tools.coverage_gaps.cli import build_parser, main, run
from gen_desk_tools.coverage_gaps.extractor import generate_gap_report, parse_gap_range

__version__ = "1.0.0+build.1"

__all__ = [
    "build_parser",
    "generate_gap_report",
    "main",
    "parse_gap_range",
    "run",
]
