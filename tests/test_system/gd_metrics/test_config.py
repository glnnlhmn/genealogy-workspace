"""Path: tests/test_system/gd_metrics/test_config.py

Unit and integration tests for system.gd_metrics.config.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from system.gd_metrics.config import load_config, resolve_batches

__version__ = "1.0.0+build.1"


# ==========================================================================
# GROUP 1: Default & File-Based Configuration Loading
# Note: Verifies pyproject.toml and config.toml ingestion and defaults.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_load_config_reads_pyproject_and_config_toml_successfully(tmp_path: Path) -> None:
    """Verify load_config merges pyproject.toml and config.toml settings."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.ruff]\nline-length = 100\n"
        '[tool.pytest.ini_options]\nmarkers = ["unit: Unit tests", "smoke: Smoke", ""]\n',
        encoding="utf-8",
    )
    cfg_dir = tmp_path / "config" / "gd_metrics"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.toml").write_text(
        '[telemetry]\ndefault_scopes = ["gda"]\nsync_sheets_by_default = true\n'
        'sheet_id = "abc123"\nsheet_url = "https://example.com/sheet"\n'
        "[gates.coverage]\ngda = 96.0\n"
        '[[batches]]\nid = "GDA-Batch-1"\nscope = "gda"\ntier = "Tier 0"\n'
        'paths = ["src/gda/core"]\ntest_paths = ["tests/test_gda/test_core"]\n',
        encoding="utf-8",
    )

    cfg = load_config(workspace_root=tmp_path, env={})

    assert cfg.ruff_line_length == 100
    assert cfg.registered_markers == ("unit", "smoke")
    assert cfg.scopes == ("gda",)
    assert cfg.sync_sheets is True
    assert cfg.sheet_id == "abc123"
    assert cfg.coverage_gates["gda"] == 96.0
    assert len(cfg.batches) == 1
    assert cfg.batches[0].id == "GDA-Batch-1"


@pytest.mark.unit
def test_load_config_missing_files_uses_safe_defaults(tmp_path: Path) -> None:
    """Verify missing pyproject.toml and config.toml fall back to defaults."""
    cfg = load_config(workspace_root=tmp_path, env={})

    assert cfg.scopes == ("gda",)
    assert cfg.sync_sheets is True
    assert cfg.ruff_line_length == 100
    assert cfg.registered_markers == ()
    assert cfg.batches == ()


# ==========================================================================
# GROUP 2: Environment Variable & CLI Precedence Overrides
# Note: Verifies GDA_METRICS_* env vars and CLI flags override file config.
# ==========================================================================


@pytest.mark.unit
def test_load_config_env_overrides_config_and_custom_path(tmp_path: Path) -> None:
    """Verify GDA_METRICS_* environment variables override config.toml."""
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
def test_load_config_env_false_boolean_disables_sheets(tmp_path: Path) -> None:
    """Verify GDA_METRICS_SYNC_SHEETS=false disables Google Sheets sync."""
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SYNC_SHEETS": "0"})

    assert cfg.sync_sheets is False


@pytest.mark.unit
def test_load_config_cli_overrides_take_highest_precedence(tmp_path: Path) -> None:
    """Verify explicit CLI flags override both config.toml and ENV values."""
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


@pytest.mark.regression
def test_load_config_invalid_bool_env_raises_value_error(tmp_path: Path) -> None:
    """Verify invalid GDA_METRICS_SYNC_SHEETS value raises ValueError."""
    with pytest.raises(ValueError, match="Invalid boolean value"):
        load_config(workspace_root=tmp_path, env={"GDA_METRICS_SYNC_SHEETS": "maybe"})


@pytest.mark.regression
def test_load_config_invalid_scope_raises_value_error(tmp_path: Path) -> None:
    """Verify unsupported scope name raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported scope"):
        load_config(workspace_root=tmp_path, env={}, cli_scopes=("unknown",))


# ==========================================================================
# GROUP 3: Batch Resolution & Filtering
# Note: Verifies scope-based, 'all', and explicit batch ID filtering.
# ==========================================================================


@pytest.mark.unit
def test_resolve_batches_filters_by_scope(tmp_path: Path) -> None:
    """Verify resolve_batches returns only batches matching active scopes."""
    cfg_file = tmp_path / "config.toml"
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
    cfg_file = tmp_path / "config.toml"
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
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        '[[batches]]\nid = "B1"\nscope = "gda"\npaths = ["src/gda"]\n'
        '[[batches]]\nid = "S1"\nscope = "system"\npaths = ["src/system"]\n',
        encoding="utf-8",
    )
    cfg = load_config(workspace_root=tmp_path, config_path=cfg_file, env={}, cli_batches=("S1",))

    resolved = resolve_batches(cfg)

    assert [b.id for b in resolved] == ["S1"]


@pytest.mark.regression
def test_resolve_batches_unknown_batch_id_raises_value_error(tmp_path: Path) -> None:
    """Verify requesting an unknown batch ID raises ValueError."""
    cfg = load_config(workspace_root=tmp_path, env={}, cli_batches=("NO-SUCH-BATCH",))

    with pytest.raises(ValueError, match="Unknown batch ID"):
        resolve_batches(cfg)
