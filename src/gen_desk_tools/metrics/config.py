"""Path: src/gen_desk_tools/metrics/config.py

Four-layer configuration loader for gd_metrics.

Operational Role:
    Resolves runtime telemetry settings across four precedence layers—workspace
    pyproject.toml (and core GDT workspace defaults via load_gdt_config),
    metrics config.toml, GDA_METRICS_* environment variables, and explicit CLI
    overrides—producing immutable MetricsConfig and BatchDefinition records for
    downstream collectors and exporters.

Classes:
    BatchDefinition: Declarative batch grouping mapping source and test paths.
    MetricsConfig: Immutable runtime configuration for a gd_metrics execution.

Functions:
    load_config: Load and merge gd_metrics configuration across all four layers.
    resolve_batches: Filter configured batches by active scopes or explicit IDs.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_desk_tools.core.config import load_gdt_config

__version__ = "1.0.0+build.3"

__all__ = [
    "BatchDefinition",
    "DEFAULT_CONFIG_REL_PATH",
    "MetricsConfig",
    "VALID_SCOPES",
    "load_config",
    "resolve_batches",
]

DEFAULT_CONFIG_REL_PATH = Path("src/gen_desk_tools/metrics/config.toml")
VALID_SCOPES = frozenset({"gda", "system", "cli", "ancestry_desk", "all"})
DEFAULT_COVERAGE_GATES: dict[str, float] = {
    "gda": 95.0,
    "cli": 95.0,
    "system": 100.0,
    "ancestry_desk": 85.0,
}


@dataclass(frozen=True)
class BatchDefinition:
    """Declarative batch grouping mapping source and test directories."""

    id: str
    scope: str
    tier: str
    paths: tuple[str, ...]
    test_paths: tuple[str, ...]


@dataclass(frozen=True)
class MetricsConfig:
    """Immutable runtime configuration for a gd_metrics execution."""

    workspace_root: Path
    config_path: Path
    scopes: tuple[str, ...]
    batch_filter: tuple[str, ...]
    sync_sheets: bool
    sheet_id: str
    sheet_url: str
    google_creds_path: str
    write_local_report: bool
    local_report_dir: Path
    pytest_basetemp: Path
    ruff_line_length: int
    registered_markers: tuple[str, ...]
    coverage_gates: Mapping[str, float]
    batches: tuple[BatchDefinition, ...]


def _read_toml_file(path: Path) -> dict[str, Any]:
    """Load a UTF-8 TOML file into a dictionary, returning empty if missing."""
    if not path.exists():
        return {}
    raw_text = path.read_text(encoding="utf-8")
    return tomllib.loads(raw_text)


def _parse_bool_env(value: str) -> bool:
    """Parse a boolean environment variable string into a strict bool.

    Accepts case-insensitive truthy (1, true, yes, on) and falsy
    (0, false, no, off) tokens.

    Raises:
        ValueError: If value does not match a recognized boolean token.
    """
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    msg = f"Invalid boolean value for environment variable: {value!r}"
    raise ValueError(msg)


def _parse_markers(pyproject_data: Mapping[str, Any]) -> tuple[str, ...]:
    """Extract registered pytest marker names from pyproject.toml."""
    tool = pyproject_data.get("tool", {})
    pytest_opts = tool.get("pytest", {}).get("ini_options", {})
    raw_markers = pytest_opts.get("markers", [])
    markers: list[str] = []
    for entry in raw_markers:
        # Pytest marker declarations use "name: description"; keep only the name.
        name = str(entry).split(":", maxsplit=1)[0].strip()
        if name:
            markers.append(name)
    return tuple(markers)


def _parse_batches(config_data: Mapping[str, Any]) -> tuple[BatchDefinition, ...]:
    """Build immutable BatchDefinition tuples from config.toml."""
    parsed: list[BatchDefinition] = []
    for item in config_data.get("batches", []):
        parsed.append(
            BatchDefinition(
                id=str(item["id"]),
                scope=str(item["scope"]),
                tier=str(item.get("tier", "")),
                paths=tuple(str(p) for p in item.get("paths", [])),
                test_paths=tuple(str(p) for p in item.get("test_paths", [])),
            )
        )
    return tuple(parsed)


def _validate_scopes(scopes: tuple[str, ...]) -> tuple[str, ...]:
    """Validate requested subsystem scopes against VALID_SCOPES.

    Raises:
        ValueError: If one or more scope names are not in VALID_SCOPES.
    """
    invalid = [s for s in scopes if s not in VALID_SCOPES]
    if invalid:
        msg = f"Unsupported scope(s): {', '.join(invalid)}"
        raise ValueError(msg)
    return scopes


def load_config(
    workspace_root: Path | None = None,
    config_path: Path | None = None,
    env: Mapping[str, str] | None = None,
    *,
    cli_scopes: tuple[str, ...] | None = None,
    cli_batches: tuple[str, ...] | None = None,
    cli_sheet_url: str | None = None,
    cli_no_sheets: bool = False,
) -> MetricsConfig:
    """Load and merge gd_metrics configuration across all four layers.

    Precedence (lowest to highest):
        1. Workspace pyproject.toml & core GDT defaults (pytest markers, Ruff line length, dirs)
        2. Metrics config.toml (batches, coverage gates, defaults)
        3. GDA_METRICS_* environment variables
        4. Explicit CLI override arguments

    Args:
        workspace_root: Optional repository root; defaults to Path.cwd().
        config_path: Optional explicit TOML path bypassing GDA_METRICS_CONFIG.
        env: Optional environment mapping for hermetic testing; defaults to os.environ.
        cli_scopes: Optional subsystem scope overrides from CLI flags.
        cli_batches: Optional explicit batch ID filter from CLI flags.
        cli_sheet_url: Optional target Google Sheet URL override.
        cli_no_sheets: When True, forces Google Sheets sync off regardless of config/env.

    Raises:
        ValueError: If an environment boolean or requested scope is invalid.
    """
    # --- Layer 1 & 2: Resolve Paths & Read TOML Sources ---
    root = (workspace_root or Path.cwd()).resolve()
    environ = os.environ if env is None else env

    resolved_config_path = config_path
    if resolved_config_path is None:
        env_cfg = environ.get("GDA_METRICS_CONFIG", "").strip()
        resolved_config_path = Path(env_cfg) if env_cfg else root / DEFAULT_CONFIG_REL_PATH

    gdt_cfg = load_gdt_config(root_dir=root)
    ws_cfg = gdt_cfg.get("workspace", {})
    default_reports_dir = str(ws_cfg.get("reports_dir", "reports"))
    default_basetemp = f"{ws_cfg.get('gtemp_dir', 'gtemp')}/pytest_tmp"

    pyproject_data = _read_toml_file(root / "pyproject.toml")
    config_data = _read_toml_file(resolved_config_path)

    telemetry = config_data.get("telemetry", {})
    ruff_cfg = pyproject_data.get("tool", {}).get("ruff", {})
    ruff_line_length = int(ruff_cfg.get("line-length", 100))
    registered_markers = _parse_markers(pyproject_data)

    # Start from built-in subsystem gates, then overlay config.toml overrides.
    gates = dict(DEFAULT_COVERAGE_GATES)
    gates.update(
        {str(k): float(v) for k, v in config_data.get("gates", {}).get("coverage", {}).items()}
    )

    # --- Layer 3 & 4: Resolve Scopes & Sync Overrides ---
    default_scopes = tuple(str(s) for s in telemetry.get("default_scopes", ["gda"]))
    env_scope = environ.get("GDA_METRICS_SCOPE", "").strip()
    if env_scope:
        effective_scopes = tuple(s.strip() for s in env_scope.split(",") if s.strip())
    else:
        effective_scopes = default_scopes
    if cli_scopes:
        effective_scopes = cli_scopes
    effective_scopes = _validate_scopes(effective_scopes)

    sync_sheets = bool(telemetry.get("sync_sheets_by_default", True))
    env_sync = environ.get("GDA_METRICS_SYNC_SHEETS", "").strip()
    if env_sync:
        sync_sheets = _parse_bool_env(env_sync)
    if cli_no_sheets:
        sync_sheets = False

    sheet_id = environ.get("GDA_METRICS_SHEET_ID", str(telemetry.get("sheet_id", ""))).strip()
    sheet_url = environ.get("GDA_METRICS_SHEET_URL", str(telemetry.get("sheet_url", ""))).strip()
    if cli_sheet_url:
        sheet_url = cli_sheet_url.strip()

    google_creds = environ.get("GDA_METRICS_GOOGLE_CREDS", "").strip()

    # --- Assemble Immutable Runtime Config ---
    return MetricsConfig(
        workspace_root=root,
        config_path=resolved_config_path,
        scopes=effective_scopes,
        batch_filter=cli_batches or (),
        sync_sheets=sync_sheets,
        sheet_id=sheet_id,
        sheet_url=sheet_url,
        google_creds_path=google_creds,
        write_local_report=bool(telemetry.get("write_local_report", True)),
        local_report_dir=root / str(telemetry.get("local_report_dir", default_reports_dir)),
        pytest_basetemp=root / str(telemetry.get("pytest_basetemp", default_basetemp)),
        ruff_line_length=ruff_line_length,
        registered_markers=registered_markers,
        coverage_gates=gates,
        batches=_parse_batches(config_data),
    )


def resolve_batches(config: MetricsConfig) -> tuple[BatchDefinition, ...]:
    """Filter configured batches by active scopes and optional explicit batch IDs.

    Explicit batch_filter IDs take precedence over scope filtering and require
    every requested ID to exist in config.batches.

    Raises:
        ValueError: If any ID in config.batch_filter is not defined in config.batches.
    """
    # --- Explicit Batch ID Selection ---
    if config.batch_filter:
        wanted = set(config.batch_filter)
        matched = tuple(b for b in config.batches if b.id in wanted)
        found_ids = {b.id for b in matched}
        missing = sorted(wanted - found_ids)
        if missing:
            msg = f"Unknown batch ID(s): {', '.join(missing)}"
            raise ValueError(msg)
        return matched

    # --- Scope-Based Selection ---
    if "all" in config.scopes:
        return config.batches

    active_scopes = set(config.scopes)
    return tuple(b for b in config.batches if b.scope in active_scopes)
