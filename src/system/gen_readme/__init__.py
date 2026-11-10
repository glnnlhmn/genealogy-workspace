"""Path: src/system/gen_readme/__init__.py

Dynamic package documentation generator subsystem facade.
"""

from __future__ import annotations

from system.gen_readme.gen_readme import (
    extract_module_metadata,
    generate_package_readme,
    load_configuration,
    main,
    run,
)

__version__ = "1.0.0+build.4"

__all__ = [
    "extract_module_metadata",
    "generate_package_readme",
    "load_configuration",
    "main",
    "run",
]
