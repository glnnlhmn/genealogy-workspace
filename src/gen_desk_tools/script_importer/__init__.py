"""Path: src/gen_desk_tools/script_importer/__init__.py

Hermetic script and asset intake pipeline package (gsi).

Operational Role:
    Re-exports the public header parser, intake orchestrator, and CLI
    entrypoints for GenDesk Tools staging automation.
"""

from __future__ import annotations

from gen_desk_tools.script_importer.cli import build_parser, main
from gen_desk_tools.script_importer.headers import parse_metadata_header
from gen_desk_tools.script_importer.intake import run_intake

__version__ = "1.0.0+build.2"

__all__ = [
    "build_parser",
    "main",
    "parse_metadata_header",
    "run_intake",
]
