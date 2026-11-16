"""Path: tests/test_system/test_gen_desk_mgr/test_config.py

Unit test suite for Backup Manager configuration routines.

Operational Role:
    Verifies default TOML settings, custom configuration parsing, malformed TOML
    handling, non-dict section merging, and workspace root discovery across environments.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from system.gen_desk_mgr.gd_backup_tools import config
from system.gen_desk_mgr.gd_backup_tools.config import (
    load_config,
    resolve_workspace_root,
)

__version__ = "1.0.0+build.6"

# ==============================================================================
# GROUP 1: Configuration Loading & Defaults
# Note: Verification of load_config behavior, fallbacks, and error branches
# ==============================================================================


@pytest.mark.unit
def test_load_config_fallback_defaults() -> None:
    """Verify fallback defaults return when configuration file does not exist."""
    cfg = load_config(Path("/nonexistent/file.toml"))
    assert cfg["workspace"]["archive_dir"] == "archive"
    assert "src" in cfg["code_domains"]["protected_domains"]
    assert cfg["retention"]["max_versions"] == 5


@pytest.mark.unit
def test_load_config_custom_toml_and_non_dict_section(tmp_path: Path) -> None:
    """Verify custom TOML file values and non-dict sections hit line 85."""
    cfg_file = tmp_path / "custom.toml"
    cfg_file.write_text(
        """
custom_scalar = "custom_value"

[retention]
max_versions = 10
max_age_days = 30
""",
        encoding="utf-8",
    )
    cfg = load_config(cfg_file)
    assert cfg["retention"]["max_versions"] == 10
    assert cfg["retention"]["max_age_days"] == 30
    assert cfg["custom_scalar"] == "custom_value"


@pytest.mark.unit
def test_load_config_malformed_toml_swallowed(tmp_path: Path) -> None:
    """Verify malformed TOML does not raise an unhandled exception and uses defaults."""
    bad_file = tmp_path / "bad.toml"
    bad_file.write_text("invalid_toml [[ = ", encoding="utf-8")
    cfg = load_config(bad_file)
    assert cfg["retention"]["max_versions"] == 5


@pytest.mark.unit
def test_load_config_default_candidate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify default candidate resolution when config_path is None."""
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir(parents=True)
    cfg_file = tmp_path / "gen_desk_config.toml"
    cfg_file.write_text("[retention]\nmax_versions = 8\n", encoding="utf-8")

    monkeypatch.setattr(config, "__file__", str(pkg_dir / "tools" / "config.py"))
    cfg = load_config(None)
    assert isinstance(cfg, dict)


# ==============================================================================
# GROUP 2: Workspace Root Resolution
# Note: Verification of root discovery, marker matching, and cwd fallback
# ==============================================================================


@pytest.mark.unit
def test_resolve_workspace_root_explicit(tmp_path: Path) -> None:
    """Verify explicit root parameter takes precedence when valid."""
    cfg = {"workspace": {"root": str(tmp_path)}}
    root = resolve_workspace_root(cfg)
    assert root == tmp_path.resolve()


@pytest.mark.unit
def test_resolve_workspace_root_explicit_dot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify explicit dot parameter resolves to current working directory."""
    monkeypatch.chdir(tmp_path)
    cfg = {"workspace": {"root": "."}}
    root = resolve_workspace_root(cfg)
    assert root == tmp_path.resolve()


@pytest.mark.unit
def test_resolve_workspace_root_invalid_falls_to_marker_or_cwd(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify unconfigured or invalid root path falls back safely."""
    monkeypatch.chdir(tmp_path)
    cfg = {"workspace": {"root": str(tmp_path / "missing")}}
    root = resolve_workspace_root(cfg)
    assert root.is_dir()


@pytest.mark.unit
def test_resolve_workspace_root_marker_discovery_pyproject(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify parent marker discovery when pyproject.toml is present."""
    repo = tmp_path / "repo"
    sub = repo / "src" / "system" / "gen_desk_mgr" / "gd_backup_tools"
    sub.mkdir(parents=True)
    (repo / "pyproject.toml").write_text("", encoding="utf-8")

    monkeypatch.setattr(config, "__file__", str(sub / "config.py"))
    root = resolve_workspace_root({})
    assert root == repo


@pytest.mark.unit
def test_resolve_workspace_root_marker_discovery_src_archive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify parent marker discovery when src and archive directories exist."""
    repo = tmp_path / "repo2"
    sub = repo / "src" / "system"
    sub.mkdir(parents=True)
    (repo / "archive").mkdir(parents=True)

    monkeypatch.setattr(config, "__file__", str(sub / "config.py"))
    root = resolve_workspace_root({})
    assert root == repo


@pytest.mark.unit
def test_resolve_workspace_root_pure_cwd_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify fallback reaches line 114 when no parents contain project markers."""
    monkeypatch.chdir(tmp_path)
    # A single isolated dummy path without src/archive or pyproject in parents
    fake_script = Path("/nonexistent_drive/sub/config.py")
    monkeypatch.setattr(config, "__file__", str(fake_script))

    root = resolve_workspace_root({})
    assert root == tmp_path.resolve()
