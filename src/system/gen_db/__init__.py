"""Path: src/system/gen_db/__init__.py

Database provisioning and environment setup subsystem facade.
"""

from __future__ import annotations

from system.gen_db.create_dev_database import (
    create_environment_database,
    main,
    parse_args,
)

__version__ = "1.0.0+build.2"

__all__ = [
    "create_environment_database",
    "main",
    "parse_args",
]
