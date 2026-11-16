"""Path: src/system/util/__init__.py

System utilities package facade.
"""

from __future__ import annotations

from system.util.check_structure import (
    build_tree,
    generate_structure_report,
    resolve_workspace_root,
)
from system.util.check_structure import (
    main as check_structure_main,
)
from system.util.extract_coverage_gaps import generate_gap_report, parse_gap_range

__version__ = "1.0.0+build.2"

__all__ = [
    "build_tree",
    "check_structure_main",
    "generate_gap_report",
    "generate_structure_report",
    "parse_gap_range",
    "resolve_workspace_root",
]
