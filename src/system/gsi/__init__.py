"""Path: src/system/gsi/__init__.py

Genealogy Script Importer (GSI) package facade.

Operational Role:
    Exposes top-level public functions and version metadata for GSI automation.
"""

from __future__ import annotations

from system.gsi.gsi import (
    load_gsi_config,
    parse_metadata_header,
    run_intake,
)

__version__ = "1.5.0+build.1"

__all__ = [
    "load_gsi_config",
    "parse_metadata_header",
    "run_intake",
]
