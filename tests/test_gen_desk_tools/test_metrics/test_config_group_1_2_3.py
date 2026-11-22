"""Path: tests/test_gen_desk_tools/test_metrics/test_config_group_1_2_3.py

Config loading, 3-level TOML precedence, and batch filtering tests for gd_metrics.

Operational Role:
    Verifies layered TOML ingestion (pyproject.toml -> gen_desk_tools.toml ->
    metrics.toml), full built-in default values, custom TOML overrides,
    GDA_METRICS_* environment precedence, CLI overrides, and batch resolution.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gen_desk_tools.metrics import config as config_mod
from gen_desk_tools.metrics.config import load_config, resolve_batches

__version__ = "1.0.0+build.4"


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end 3-level TOML merge across pyproject, package, and tool configs.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_load_config_merges_three_toml_levels_with_proper_precedence(tmp_path: Path) -> None:
    """Verify pyproject.toml < gen_desk_tools.toml < metrics.toml precedence."""
    # Level 1: Workspace root pyproject.toml
    (tmp_path / "pyproject.toml").write_text(
        "[tool.ruff]\nline-length = 100\n"
        '[tool.pytest.ini_options]\nmarkers = ["unit: Unit tests", "smoke: Smoke", ""]\n'
        '[tool.gen_desk_tools.workspace]\nreports_dir = "reports"\ngtemp_dir = "gtemp"\n'
        '[tool.gen_desk_tools.metrics.telemetry]\ndefault_scopes = ["gda"]\n'
        "sync_sheets_by_default = true\n",
        encoding="utf-8",
    )

    # Level 2: Package root src/gen_desk_tools/gen_desk_tools.toml
    pkg_dir = tmp_path / "src" / "gen_desk_tools"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "gen_desk_tools.toml").write_text(
        '[workspace]\nreports_dir = "reports/gdt"\n'
        '[metrics.telemetry]\nsync_sheets_by_default = false\nsheet_id = "pkg_sheet_123"\n'
        "[metrics.gates.coverage]\ngda = 95.0\nsystem = 100.0\n",
        encoding="utf-8",
    )

    # Level 3: Tool level src/gen_desk_tools/metrics/metrics.toml
    metrics_dir = pkg_dir / "metrics"
    metrics_dir.mkdir(parents=True)
    (metrics_dir / "metrics.toml").write_text(
        '[telemetry]\ndefault_scopes = ["gda", "system"]\n'
        'sheet_url = "https://example.com/metrics-sheet"\n'
        "[gates.coverage]\ngda = 98.0\n"
        '[[batches]]\nid = "GDA-Batch-1"\nscope = "gda"\ntier = "Tier 0"\n'
        'paths = ["src/gda/core"]\ntest_paths = ["tests/test_gda/test_core"]\n',
        encoding="utf-8",
    )

    cfg = load_config(workspace_root=tmp_path, env={})

    assert cfg.ruff_line_length == 100
    assert cfg.registered_markers == ("unit", "smoke")
    assert cfg.local_report_dir == tmp_path / "reports/gdt"
    assert cfg.pytest_basetemp == tmp_path / "gtemp/pytest_tmp"
    assert cfg.sync_sheets is False
    assert cfg.sheet_id == "pkg_sheet_123"
    assert cfg.sheet_url == "https://example.com/metrics-sheet"
    assert cfg.scopes == ("gda", "system")
    assert cfg.coverage_gates["gda"] == 98.0
    assert cfg.coverage_gates["system"] == 100.0
    assert len(cfg.batches) == 1
    assert cfg.batches[0].id == "GDA-Batch-1"


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Public interface, defaults, custom TOML, env/CLI overrides, and batches.
# ==========================================================================


@pytest.mark.unit
def test_config_module_exposes_expected_public_interface() -> None:
    """Verify config module exports its expected public symbols."""
    expected = {
        "BatchDefinition",
        "MetricsConfig",
        "VALID_SCOPES",
        "load_config",
        "resolve_batches",
    }
    assert expected.issubset(set(config_mod.__all__))


@pytest.mark.unit
def test_load_config_missing_files_uses_safe_defaults(tmp_path: Path) -> None:
    """Verify missing TOML files fall back to all expected built-in defaults."""
    cfg = load_config(workspace_root=tmp_path, env={})

    assert cfg.workspace_root == tmp_path.resolve()
    assert cfg.scopes == ("gda",)
    assert cfg.batch_filter == ()
    assert cfg.sync_sheets is True
    assert cfg.sheet_id == ""
    assert cfg.sheet_url == ""
    assert cfg.google_creds_path == ""
    assert cfg.write_local_report is True
    assert cfg.local_report_dir == tmp_path.resolve() / "reports"
    assert cfg.pytest_basetemp == tmp_path.resolve() / "gtemp" / "pytest_tmp"
    assert cfg.ruff_line_length == 100
    assert cfg.registered_markers == ()
    assert cfg.coverage_gates == {
        "gda": 95.0,
        "cli": 95.0,
        "system": 100.0,
        "ancestry_desk": 85.0,
    }
    assert cfg.batches == ()


@pytest.mark.unit
def test_load_config_accepts_arbitrary_custom_toml_file(tmp_path: Path) -> None:
    """Verify any manually passed-in .toml file overrides lower config layers."""
    custom_toml = tmp_path / "audit_override.toml"
    custom_toml.write_text(
        '[telemetry]\ndefault_scopes = ["system"]\nsync_sheets_by_default = false\n'
        'sheet_id = "custom_999"\n',
        encoding="utf-8",
    )

    cfg = load_config(workspace_root=tmp_path, config_path=custom_toml, env={})

    assert cfg.config_path == custom_toml
    assert cfg.scopes == ("system",)
    assert cfg.sync_sheets is False
    assert cfg.sheet_id == "custom_999"


@pytest.mark.unit
def test_load_config_env_overrides_config_and_custom_path(tmp_path: Path) -> None:
    """Verify GDA_METRICS_* environment variables override file configuration."""
    custom_cfg = tmp_path / "custom.toml"
    custom_cfg.write_text("[telemetry]\nsync_sheets_by_default = false\n", encoding="utf-8")
    env = {
        "GDA_METRICS_CONFIG": str(custom_cfg),
        "GDA_METRICS_SCOPE": "system, cli",
        "GDA_METRICS_SYNC_SHEETS": "true",
        "GDA_METRICS_SHEET_ID": "env_id",
        "GDA_METRICS_SHEET_URL": "https://sheets.local/env",
        "GDA_METRICS_GOOGLE_CREDS": "/tmp/creds.json",
    }

    cfg = load_config(workspace_root=tmp_path, env=env)

    assert cfg.config_path == custom_cfg
    assert cfg.scopes == ("system", "cli")
    assert cfg.sync_sheets is True
    assert cfg.sheet_id == "env_id"
    assert cfg.sheet_url == "https://sheets.local/env"
    assert cfg.google_creds_path == "/tmp/creds.json"


@pytest.mark.unit
def test_load_config_env_zero_boolean_disables_sheets(tmp_path: Path) -> None:
    """Verify GDA_METRICS_SYNC_SHEETS=0 disables Google Sheets sync."""
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SYNC_SHEETS": "0"})

    assert cfg.sync_sheets is False


@pytest.mark.unit
def test_load_config_cli_overrides_take_highest_precedence(tmp_path: Path) -> None:
    """Verify explicit CLI flags override both TOML files and ENV values."""
    env = {
        "GDA_METRICS_SCOPE": "system",
        "GDA_METRICS_SYNC_SHEETS": "true",
        "GDA_METRICS_SHEET_URL": "https://sheets.local/env",
    }

    cfg = load_config(
        workspace_root=tmp_path,
        config_path=tmp_path / "missing.toml",
        env=env,
        cli_scopes=("all",),
        cli_batches=("GDA-Batch-1",),
        cli_sheet_url="https://sheets.local/cli",
        cli_no_sheets=True,
    )

    assert cfg.scopes == ("all",)
    assert cfg.batch_filter == ("GDA-Batch-1",)
    assert cfg.sheet_url == "https://sheets.local/cli"
    assert cfg.sync_sheets is False


@pytest.mark.unit
def test_resolve_batches_filters_by_scope(tmp_path: Path) -> None:
    """Verify resolve_batches returns only batches matching active scopes."""
    cfg_file = tmp_path / "metrics.toml"
    cfg_file.write_text(
        '[[batches]]\nid = "B1"\nscope = "gda"\npaths = ["src/gda"]\n'
        '[[batches]]\nid = "S1"\nscope = "system"\npaths = ["src/system"]\n',
        encoding="utf-8",
    )
    cfg = load_config(workspace_root=tmp_path, config_path=cfg_file, env={}, cli_scopes=("gda",))

    resolved = resolve_batches(cfg)

    assert [b.id for b in resolved] == ["B1"]


@pytest.mark.unit
def test_resolve_batches_all_scope_returns_every_batch(tmp_path: Path) -> None:
    """Verify 'all' scope returns all configured batches."""
    cfg_file = tmp_path / "metrics.toml"
    cfg_file.write_text(
        '[[batches]]\nid = "B1"\nscope = "gda"\npaths = ["src/gda"]\n'
        '[[batches]]\nid = "S1"\nscope = "system"\npaths = ["src/system"]\n',
        encoding="utf-8",
    )
    cfg = load_config(workspace_root=tmp_path, config_path=cfg_file, env={}, cli_scopes=("all",))

    resolved = resolve_batches(cfg)

    assert [b.id for b in resolved] == ["B1", "S1"]


@pytest.mark.unit
def test_resolve_batches_explicit_batch_filter_matches_id(tmp_path: Path) -> None:
    """Verify explicit cli_batches selects matching batch IDs."""
    cfg_file = tmp_path / "metrics.toml"
    cfg_file.write_text(
        '[[batches]]\nid = "B1"\nscope = "gda"\npaths = ["src/gda"]\n'
        '[[batches]]\nid = "S1"\nscope = "system"\npaths = ["src/system"]\n',
        encoding="utf-8",
    )
    cfg = load_config(workspace_root=tmp_path, config_path=cfg_file, env={}, cli_batches=("S1",))

    resolved = resolve_batches(cfg)

    assert [b.id for b in resolved] == ["S1"]


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Env boolean whitespace/case handling, blank fallbacks, and filter precedence.
# ==========================================================================


@pytest.mark.regression
@pytest.mark.parametrize(
    ("raw_val", "expected"),
    [
        (" True ", True),
        ("YES", True),
        ("on", True),
        (" False ", False),
        ("NO", False),
        ("OFF", False),
    ],
)
def test_load_config_bool_env_handles_case_and_whitespace(
    tmp_path: Path,
    raw_val: str,
    expected: bool,
) -> None:
    """Verify boolean env parsing strips whitespace and ignores letter case."""
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SYNC_SHEETS": raw_val})

    assert cfg.sync_sheets is expected


@pytest.mark.regression
def test_load_config_empty_env_values_fall_back_to_file_config(tmp_path: Path) -> None:
    """Verify blank or whitespace-only env vars do not wipe out file settings."""
    custom_cfg = tmp_path / "metrics.toml"
    custom_cfg.write_text(
        '[telemetry]\ndefault_scopes = ["system"]\nsync_sheets_by_default = false\n',
        encoding="utf-8",
    )
    env = {
        "GDA_METRICS_SCOPE": "   ",
        "GDA_METRICS_SYNC_SHEETS": "  ",
    }

    cfg = load_config(workspace_root=tmp_path, config_path=custom_cfg, env=env)

    assert cfg.scopes == ("system",)
    assert cfg.sync_sheets is False


@pytest.mark.regression
def test_resolve_batches_explicit_filter_overrides_scope_filter(tmp_path: Path) -> None:
    """Verify explicit batch_filter takes precedence even when scope excludes that batch."""
    cfg_file = tmp_path / "metrics.toml"
    cfg_file.write_text(
        '[[batches]]\nid = "B1"\nscope = "gda"\npaths = ["src/gda"]\n'
        '[[batches]]\nid = "S1"\nscope = "system"\npaths = ["src/system"]\n',
        encoding="utf-8",
    )
    cfg = load_config(
        workspace_root=tmp_path,
        config_path=cfg_file,
        env={},
        cli_scopes=("gda",),
        cli_batches=("S1",),
    )

    resolved = resolve_batches(cfg)

    assert [b.id for b in resolved] == ["S1"]
