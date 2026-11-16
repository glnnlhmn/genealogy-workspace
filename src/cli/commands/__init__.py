"""Path: src/cli/commands/__init__.py

Operational CLI command suite for Genealogy Digital Archive pipelines.
"""

from __future__ import annotations

from cli.commands.load_setup import SetupLoader

__version__ = "1.0.0+build.3"

__all__ = ["SetupLoader"]
