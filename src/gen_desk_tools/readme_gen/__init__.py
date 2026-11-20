"""Path: src/gen_desk_tools/readme_gen/__init__.py

AST-driven package README.md documentation generator package (gdrm).

Operational Role:
    Re-exports the public metadata parser, README renderer, hash helpers, and
    execution orchestrator for GenDesk Tools documentation automation.
"""

from __future__ import annotations

from gen_desk_tools.readme_gen.cli import build_parser, main
from gen_desk_tools.readme_gen.generator import (
    DEFAULT_PACKAGES_REL_PATH,
    SCOPE_ALIASES,
    compute_content_hash,
    generate_package_readme,
    is_unmodified_generated_readme,
    load_package_definitions,
    prompt_overwrite,
    resolve_target_packages,
    run,
)
from gen_desk_tools.readme_gen.parser import extract_module_metadata

__version__ = "1.0.0+build.3"

__all__ = [
    "DEFAULT_PACKAGES_REL_PATH",
    "SCOPE_ALIASES",
    "build_parser",
    "compute_content_hash",
    "extract_module_metadata",
    "generate_package_readme",
    "is_unmodified_generated_readme",
    "load_package_definitions",
    "main",
    "prompt_overwrite",
    "resolve_target_packages",
    "run",
]
