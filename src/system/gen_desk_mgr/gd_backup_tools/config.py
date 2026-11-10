"""Path: src/system/gen_desk_mgr/gd_backup_tools/config.py

Configuration provider for the Genealogy Digital Archive Backup Manager.

Operational Role:
    Loads and validates gen_desk_config.toml, furnishing robust defaults,
    resolving absolute workspace roots, and exposing typed configuration
    dictionaries across backup and pruning operations.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

__version__ = "1.0.0+build.6"

DEFAULT_CONFIG: dict[str, Any] = {
    "workspace": {
        "root": ".",
        "archive_dir": "archive",
        "logs_dir": "logs",
        "gtemp_dir": "gtemp",
    },
    "logging": {
        "log_file": "logs/gen_desk_backup.log",
        "log_level": "INFO",
    },
    "code_domains": {
        "protected_domains": ["src", "tests", "schemas", "data/setup"],
    },
    "backup_routing": {
        "src/gda": "backups_gda",
        "tests/test_gda": "backups_gda",
        "src/ancestry_desk": "backups_ancestry_desk",
        "tests/test_ancestry_desk": "backups_ancestry_desk",
        "src/cli": "backups_cli",
        "tests/test_cli": "backups_cli",
        "src/system": "backups_system",
        "tests/test_system": "backups_system",
        "schemas": "backups_schemas",
        "data/setup": "backups_data_setup",
        "default": "backups_system",
    },
    "retention": {
        "max_versions": 5,
        "max_age_days": 90,
    },
}


def load_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """Load configuration from TOML file, merging with default settings.

    Args:
        config_path: Optional explicit path to gen_desk_config.toml.

    Returns:
        dict[str, Any]: Consolidated configuration mapping.
    """
    cfg: dict[str, Any] = {
        "workspace": dict(DEFAULT_CONFIG["workspace"]),
        "logging": dict(DEFAULT_CONFIG["logging"]),
        "code_domains": dict(DEFAULT_CONFIG["code_domains"]),
        "backup_routing": dict(DEFAULT_CONFIG["backup_routing"]),
        "retention": dict(DEFAULT_CONFIG["retention"]),
    }

    if config_path is None:
        candidate = Path(__file__).resolve().parent.parent / "gen_desk_config.toml"
        if candidate.is_file():
            config_path = candidate

    if config_path is not None:
        p = Path(config_path)
        if p.is_file():
            try:
                with open(p, "rb") as fh:
                    loaded = tomllib.load(fh)
                for section, values in loaded.items():
                    if section in cfg and isinstance(values, dict):
                        cfg[section].update(values)
                    else:
                        cfg[section] = values
            except Exception:
                pass

    return cfg


def resolve_workspace_root(cfg: dict[str, Any]) -> Path:
    """Resolve and return the canonical workspace root directory.

    Args:
        cfg: Configuration dictionary.

    Returns:
        Path: Absolute workspace root path.
    """
    root_val = cfg.get("workspace", {}).get("root")
    if root_val:
        candidate = Path(root_val).resolve()
        if candidate.is_dir():
            return candidate

    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        if (parent / "src").is_dir() and (parent / "archive").is_dir():
            return parent
        if (parent / "pyproject.toml").is_file():
            return parent

    return Path.cwd().resolve()
