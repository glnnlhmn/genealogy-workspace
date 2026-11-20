"""Path: src/gen_desk_tools/structure/__init__.py

GenDesk Structure package (gd-struct).

Operational Role:
    Re-exports directory tree scanning, Git-aware listing, report generation,
    and CLI entrypoints.
"""

from __future__ import annotations

from gen_desk_tools.structure.cli import build_parser, main, resolve_mode, run
from gen_desk_tools.structure.scanner import (
    DEFAULT_MAX_DEPTH,
    MANDATORY_EXCLUSIONS,
    MODE_TARGETS,
    build_git_tree,
    build_tree,
    generate_structure_report,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "DEFAULT_MAX_DEPTH",
    "MANDATORY_EXCLUSIONS",
    "MODE_TARGETS",
    "build_git_tree",
    "build_parser",
    "build_tree",
    "generate_structure_report",
    "main",
    "resolve_mode",
    "run",
]
