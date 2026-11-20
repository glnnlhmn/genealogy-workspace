"""Path: tests/test_gen_desk_tools/conftest.py

Shared hermetic pytest fixtures for the GenDesk Tools test suite.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

__version__ = "1.0.0+build.1"


@pytest.fixture
def gdt_workspace(tmp_path: Path) -> Path:
    """Provision an isolated synthetic workspace tree under tmp_path."""
    for rel in (
        "src/gda",
        "src/gen_desk_tools",
        "src/system",
        "tests/test_gen_desk_tools",
        "archive/backups_gen_desk_tools",
        "download",
        "logs",
        "reports",
        "gtemp",
    ):
        (tmp_path / rel).mkdir(parents=True, exist_ok=True)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "synthetic-gda"\n',
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def gdt_config() -> dict[str, Any]:
    """Provide a baseline in-memory GDT configuration mapping."""
    return {
        "workspace": {
            "root": ".",
            "download_dir": "download",
            "archive_dir": "archive",
            "logs_dir": "logs",
            "reports_dir": "reports",
            "gtemp_dir": "gtemp",
        },
        "logging": {
            "log_level": "INFO",
        },
        "code_domains": {
            "protected_domains": ["src", "tests", "schemas", "data/setup"],
        },
        "backup_routing": {
            "src/gda": "backups_gda",
            "tests/test_gda": "backups_gda",
            "src/gen_desk_tools": "backups_gen_desk_tools",
            "tests/test_gen_desk_tools": "backups_gen_desk_tools",
            "src/system": "backups_system",
            "tests/test_system": "backups_system",
            "default": "backups_gen_desk_tools",
        },
        "retention": {
            "max_versions": 5,
            "max_age_days": 90,
        },
    }
