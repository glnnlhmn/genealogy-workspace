"""Path: src/gen_desk_tools/metrics/config.py

Layered configuration loader for gd_metrics with 4-tier diagnostic logging.

Operational Role:
    Resolves runtime telemetry settings across layered TOML sources
    (pyproject.toml -> src/gen_desk_tools/gen_desk_tools.toml ->
    src/gen_desk_tools/metrics/metrics.toml -> optional custom TOML file),
    GDA_METRICS_* environment variables, and explicit CLI overrides—producing
    immutable MetricsConfig and BatchDefinition records for downstream
    collectors and exporters.

Classes:
    BatchDefinition: Declarative batch grouping mapping source and test paths.
    MetricsConfig: Immutable runtime configuration for a gd_metrics execution.

Functions:
    load_config: Load and merge gd_metrics configuration across all layers.
    resolve_batches: Filter configured batches by active scopes or explicit IDs.
"""

from __future__ import annotations

import logging
import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_desk_tools.core.config import deep_merge, load_gdt_config
from gen_desk_tools.core.logging import VERBOSE

__version__ = "1.0.0+build.5"

__all__ = [
    "BatchDefinition",
    "DEFAULT_CONFIG_REL_PATH",
    "DEFAULT_COVERAGE_GATES",
    "DEFAULT_PACKAGE_CONFIG_REL_PATH",
    "MetricsConfig",
    "VALID_SCOPES",
    "load_config",
    "resolve_batches",
]

logger = logging.getLogger(__name__)

DEFAULT_PACKAGE_CONFIG_REL_PATH = Path("src/gen_desk_tools/gen_desk_tools.toml")
DEFAULT_CONFIG_REL_PATH = Path("src/gen_desk_tools/metrics/metrics.toml")
VALID_SCOPES = frozenset({"gda", "system", "cli", "ancestry_desk", "all"})
DEFAULT_COVERAGE_GATES: dict[str, float] = {
    "gda": 95.0,
    "cli": 95.0,
    "system": 100.0,
    "ancestry_desk": 85.0,
}

_VALID_TELEMETRY_KEYS = frozenset(
    {
        "default_scopes",
        "sync_sheets_by_default",
        "sheet_id",
        "sheet_url",
        "write_local_report",
        "local_report_dir",
        "pytest_basetemp",
    }
)
_VALID_ENV_KEYS = frozenset(
    {
        "GDA_METRICS_CONFIG",
        "GDA_METRICS_SCOPE",
        "GDA_METRICS_SYNC_SHEETS",
        "GDA_METRICS_SHEET_ID",
        "GDA_METRICS_SHEET_URL",
        "GDA_METRICS_GOOGLE_CREDS",
    }
)


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
        logger.debug("Optional TOML file not found (skipping): %s", path)
        return {}
    logger.log(VERBOSE, "Reading TOML configuration file: %s", path)
    try:
        raw_text = path.read_text(encoding="utf-8")
        return tomllib.loads(raw_text)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        logger.error("Failed to load TOML file %s: %s", path, exc)
        raise


def _validate_env_keys(environ: Mapping[str, str]) -> None:
    """Reject unrecognized GDA_METRICS_* environment variable names."""
    unknown = sorted(
        key for key in environ if key.startswith("GDA_METRICS_") and key not in _VALID_ENV_KEYS
    )
    if unknown:
        msg = f"Unknown environment variable(s): {', '.join(unknown)}"
        logger.error(msg)
        raise KeyError(msg)


def _validate_telemetry_keys(telemetry: Mapping[str, Any]) -> None:
    """Reject unrecognized setting names under [telemetry]."""
    unknown = sorted(key for key in telemetry if key not in _VALID_TELEMETRY_KEYS)
    if unknown:
        msg = f"Unknown telemetry setting(s): {', '.join(unknown)}"
        logger.error(msg)
        raise KeyError(msg)


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
    logger.error(msg)
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
    """Build immutable BatchDefinition tuples from merged metrics config."""
    parsed: list[BatchDefinition] = []
    for item in config_data.get("batches", []):
        try:
            batch_id = str(item["id"])
            scope = str(item["scope"])
        except KeyError as exc:
            logger.error("Batch definition missing required key: %s", exc)
            raise
        parsed.append(
            BatchDefinition(
                id=batch_id,
                scope=scope,
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
        logger.error(msg)
        raise ValueError(msg)
    return scopes


def _resolve_scopes(
    telemetry: Mapping[str, Any],
    environ: Mapping[str, str],
    cli_scopes: tuple[str, ...] | None,
) -> tuple[str, ...]:
    """Resolve and validate effective scopes across config, env, and CLI layers."""
    default_scopes = tuple(str(s) for s in telemetry.get("default_scopes", ["gda"]))
    env_scope = environ.get("GDA_METRICS_SCOPE", "").strip()
    if env_scope:
        effective = tuple(s.strip() for s in env_scope.split(",") if s.strip())
    else:
        effective = default_scopes
    if cli_scopes:
        effective = cli_scopes
    return _validate_scopes(effective)


def _resolve_sync_sheets(
    telemetry: Mapping[str, Any],
    environ: Mapping[str, str],
    cli_no_sheets: bool,
) -> bool:
    """Resolve whether Google Sheets sync is enabled across config, env, and CLI."""
    sync_sheets = bool(telemetry.get("sync_sheets_by_default", True))
    env_sync = environ.get("GDA_METRICS_SYNC_SHEETS", "").strip()
    if env_sync:
        sync_sheets = _parse_bool_env(env_sync)
    if cli_no_sheets:
        sync_sheets = False
    return sync_sheets


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
    """Load and merge gd_metrics configuration across all precedence layers.

    Precedence (lowest to highest):
        1. Workspace pyproject.toml & core GDT defaults ([tool.gen_desk_tools])
        2. Package root src/gen_desk_tools/gen_desk_tools.toml
        3. Tool level src/gen_desk_tools/metrics/metrics.toml
        4. Optional manual TOML override (config_path or GDA_METRICS_CONFIG)
        5. GDA_METRICS_* environment variables
        6. Explicit CLI override arguments

    Args:
        workspace_root: Optional repository root; defaults to Path.cwd().
        config_path: Optional explicit TOML path bypassing GDA_METRICS_CONFIG.
        env: Optional environment mapping for hermetic testing; defaults to os.environ.
        cli_scopes: Optional subsystem scope overrides from CLI flags.
        cli_batches: Optional explicit batch ID filter from CLI flags.
        cli_sheet_url: Optional target Google Sheet URL override.
        cli_no_sheets: When True, forces Google Sheets sync off regardless of config/env.

    Raises:
        KeyError: If an unknown [telemetry] setting, unknown GDA_METRICS_* env var,
            or incomplete [[batches]] entry is encountered.
        ValueError: If an environment boolean, coverage gate, or scope is invalid.
    """
    # --- Layer 0: Resolve Root & Validate Environment Keys ---
    root = (workspace_root or Path.cwd()).resolve()
    environ = os.environ if env is None else env
    logger.info("Loading gd_metrics configuration for workspace: %s", root)
    _validate_env_keys(environ)

    # --- Layer 1: Workspace pyproject.toml & Core GDT Defaults ---
    gdt_cfg = load_gdt_config(root_dir=root)
    pyproject_data = _read_toml_file(root / "pyproject.toml")
    ws_cfg: dict[str, Any] = dict(gdt_cfg.get("workspace", {}))

    merged_metrics: dict[str, Any] = {}
    pyproject_metrics = pyproject_data.get("tool", {}).get("gen_desk_tools", {}).get("metrics")
    if isinstance(pyproject_metrics, dict):
        merged_metrics = deep_merge(merged_metrics, pyproject_metrics)

    # --- Layer 2: Package Root (src/gen_desk_tools/gen_desk_tools.toml) ---
    pkg_config_path = root / DEFAULT_PACKAGE_CONFIG_REL_PATH
    pkg_data = _read_toml_file(pkg_config_path)
    if isinstance(pkg_data.get("workspace"), dict):
        ws_cfg = deep_merge(ws_cfg, pkg_data["workspace"])
    if isinstance(pkg_data.get("metrics"), dict):
        merged_metrics = deep_merge(merged_metrics, pkg_data["metrics"])

    # --- Layer 3: Tool Level (src/gen_desk_tools/metrics/metrics.toml) ---
    tool_config_path = root / DEFAULT_CONFIG_REL_PATH
    tool_data = _read_toml_file(tool_config_path)
    if tool_data:
        merged_metrics = deep_merge(merged_metrics, tool_data)

    # --- Layer 4: Optional Explicit Custom TOML Override ---
    explicit_path = config_path
    if explicit_path is None:
        env_cfg = environ.get("GDA_METRICS_CONFIG", "").strip()
        explicit_path = Path(env_cfg) if env_cfg else None

    if explicit_path is not None:
        custom_data = _read_toml_file(explicit_path)
        if custom_data:
            merged_metrics = deep_merge(merged_metrics, custom_data)
        resolved_config_path = explicit_path
    else:
        resolved_config_path = tool_config_path

    logger.log(VERBOSE, "Active metrics config path resolved to: %s", resolved_config_path)

    # --- Validate Telemetry & Parse Tool Baselines ---
    telemetry = merged_metrics.get("telemetry", {})
    _validate_telemetry_keys(telemetry)

    default_reports_dir = str(ws_cfg.get("reports_dir", "reports"))
    default_basetemp = f"{ws_cfg.get('gtemp_dir', 'gtemp')}/pytest_tmp"

    ruff_cfg = pyproject_data.get("tool", {}).get("ruff", {})
    ruff_line_length = int(ruff_cfg.get("line-length", 100))
    registered_markers = _parse_markers(pyproject_data)

    # Start from built-in subsystem gates, then overlay merged TOML overrides.
    gates = dict(DEFAULT_COVERAGE_GATES)
    try:
        gates.update(
            {
                str(k): float(v)
                for k, v in merged_metrics.get("gates", {}).get("coverage", {}).items()
            }
        )
    except (TypeError, ValueError) as exc:
        logger.error("Invalid coverage gate value in configuration: %s", exc)
        raise ValueError(f"Invalid coverage gate value: {exc}") from exc

    # --- Layer 5 & 6: Resolve Scopes, Sync & Sheet Targets ---
    effective_scopes = _resolve_scopes(telemetry, environ, cli_scopes)
    sync_sheets = _resolve_sync_sheets(telemetry, environ, cli_no_sheets)

    sheet_id = environ.get("GDA_METRICS_SHEET_ID", str(telemetry.get("sheet_id", ""))).strip()
    sheet_url = environ.get("GDA_METRICS_SHEET_URL", str(telemetry.get("sheet_url", ""))).strip()
    if cli_sheet_url:
        sheet_url = cli_sheet_url.strip()

    google_creds = environ.get("GDA_METRICS_GOOGLE_CREDS", "").strip()
    batches = _parse_batches(merged_metrics)

    logger.debug(
        "Resolved MetricsConfig: scopes=%s, sync_sheets=%s, batches=%d",
        effective_scopes,
        sync_sheets,
        len(batches),
    )

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
        batches=batches,
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
            logger.error(msg)
            raise ValueError(msg)
        return matched

    # --- Scope-Based Selection ---
    if "all" in config.scopes:
        return config.batches

    active_scopes = set(config.scopes)
    return tuple(b for b in config.batches if b.scope in active_scopes)
