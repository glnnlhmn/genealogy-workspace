"""Path: src/gen_desk_tools/core/config.py

Layered TOML configuration loader for GenDesk Tools (GDT).

Operational Role:
    Resolves runtime settings across four precedence layers (built-in defaults,
    pyproject.toml [tool.gen_desk_tools], optional root gda_conf.toml, and an
    explicit CLI --config override) without mutating baseline dictionaries.

Functions:
    deep_merge: Recursively merge two configuration dictionaries without mutation.
    load_gdt_config: Load and merge GenDesk Tools settings across all active layers.
"""

from __future__ import annotations

import copy
import tomllib
from pathlib import Path
from typing import Any

from gen_desk_tools.core.workspace import resolve_workspace_root

__version__ = "1.0.0+build.1"

__all__ = [
    "DEFAULT_GDT_CONFIG",
    "deep_merge",
    "load_gdt_config",
]

DEFAULT_GDT_CONFIG: dict[str, Any] = {
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
        "src/ancestry_desk": "backups_ancestry_desk",
        "tests/test_ancestry_desk": "backups_ancestry_desk",
        "src/cli": "backups_cli",
        "tests/test_cli": "backups_cli",
        "src/system": "backups_system",
        "tests/test_system": "backups_system",
        "schemas": "backups_schemas",
        "data/setup": "backups_data_setup",
        "default": "backups_gen_desk_tools",
    },
    "retention": {
        "max_versions": 5,
        "max_age_days": 90,
    },
}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override onto base, returning a new deep-copied dictionary."""
    merged: dict[str, Any] = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _load_toml_file(path: Path) -> dict[str, Any]:
    """Read and parse a TOML file from disk in binary mode."""
    with path.open("rb") as handle:
        data: dict[str, Any] = tomllib.load(handle)
    return data


def load_gdt_config(
    root_dir: Path | None = None,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Load and merge GenDesk Tools configuration across all active layers.

    Precedence (lowest to highest):
        1. DEFAULT_GDT_CONFIG
        2. pyproject.toml [tool.gen_desk_tools]
        3. Optional root gda_conf.toml
        4. Explicit config_path override

    Raises:
        FileNotFoundError: If an explicit config_path is provided but does not exist.
    """
    root = root_dir.resolve() if root_dir is not None else resolve_workspace_root()
    merged: dict[str, Any] = copy.deepcopy(DEFAULT_GDT_CONFIG)

    # --- Layer 1: pyproject.toml ([tool.gen_desk_tools]) ---
    pyproject_file = root / "pyproject.toml"
    if pyproject_file.is_file():
        pyproject_data = _load_toml_file(pyproject_file)
        gdt_section = pyproject_data.get("tool", {}).get("gen_desk_tools")
        if isinstance(gdt_section, dict):
            merged = deep_merge(merged, gdt_section)

    # --- Layer 2: Optional Root gda_conf.toml ---
    gda_conf_file = root / "gda_conf.toml"
    if gda_conf_file.is_file():
        merged = deep_merge(merged, _load_toml_file(gda_conf_file))

    # --- Layer 3: Explicit CLI --config Override ---
    if config_path is not None:
        resolved_cfg = config_path.resolve()
        if not resolved_cfg.is_file():
            raise FileNotFoundError(f"Explicit config file not found: {resolved_cfg}")
        merged = deep_merge(merged, _load_toml_file(resolved_cfg))

    return merged
