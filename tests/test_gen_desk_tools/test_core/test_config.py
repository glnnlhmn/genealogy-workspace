"""Path: tests/test_gen_desk_tools/test_core/test_config.py

Unit, regression, and integration tests for gen_desk_tools.core.config.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gen_desk_tools.core.config import (
    DEFAULT_GDT_CONFIG,
    deep_merge,
    load_gdt_config,
)

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end layered TOML loading across all precedence tiers.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_load_gdt_config_applies_full_four_layer_precedence(gdt_workspace: Path) -> None:
    """Verify defaults < pyproject.toml < gda_conf.toml < explicit --config precedence."""
    # Arrange: populate all three on-disk TOML layers with overlapping keys
    (gdt_workspace / "pyproject.toml").write_text(
        '[tool.gen_desk_tools.logging]\nlog_level = "WARNING"\n'
        "[tool.gen_desk_tools.retention]\nmax_versions = 7\nmax_age_days = 60\n",
        encoding="utf-8",
    )
    (gdt_workspace / "gda_conf.toml").write_text(
        '[logging]\nlog_level = "ERROR"\n[retention]\nmax_versions = 10\n',
        encoding="utf-8",
    )
    explicit_cfg = gdt_workspace / "cli_override.toml"
    explicit_cfg.write_text('[logging]\nlog_level = "DEBUG"\n', encoding="utf-8")

    # Act
    cfg = load_gdt_config(root_dir=gdt_workspace, config_path=explicit_cfg)

    # Assert: each key reflects its highest-precedence layer while preserving sibling defaults
    assert cfg["logging"]["log_level"] == "DEBUG"
    assert cfg["retention"]["max_versions"] == 10
    assert cfg["retention"]["max_age_days"] == 60
    assert cfg["workspace"]["archive_dir"] == "archive"


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Pure in-memory deep_merge behavior and immutability guarantees.
# ==========================================================================


@pytest.mark.unit
def test_deep_merge_recursively_merges_nested_dicts_without_mutating_inputs() -> None:
    """Verify deep_merge preserves sibling keys and leaves base and override untouched."""
    base = {"a": {"x": 1, "y": 2}, "items": [1, 2]}
    override = {"a": {"y": 99, "z": 3}, "items": [3]}

    merged = deep_merge(base, override)

    assert merged == {"a": {"x": 1, "y": 99, "z": 3}, "items": [3]}
    assert base == {"a": {"x": 1, "y": 2}, "items": [1, 2]}
    assert override == {"a": {"y": 99, "z": 3}, "items": [3]}


@pytest.mark.unit
def test_deep_merge_replaces_dict_with_scalar_and_vice_versa() -> None:
    """Verify deep_merge replaces values wholesale when types differ between layers."""
    base = {"section": {"nested": True}, "flag": "off"}
    override = {"section": "disabled", "flag": {"enabled": True}}

    merged = deep_merge(base, override)

    assert merged == {"section": "disabled", "flag": {"enabled": True}}


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Missing TOML files, missing [tool.gen_desk_tools], and auto-discovered root.
# ==========================================================================


@pytest.mark.regression
def test_load_gdt_config_empty_directory_returns_default_copy(tmp_path: Path) -> None:
    """Verify load_gdt_config returns a fresh copy of DEFAULT_GDT_CONFIG when no files exist."""
    cfg = load_gdt_config(root_dir=tmp_path)

    assert cfg == DEFAULT_GDT_CONFIG
    assert cfg is not DEFAULT_GDT_CONFIG


@pytest.mark.regression
def test_load_gdt_config_ignores_non_dict_tool_section(gdt_workspace: Path) -> None:
    """Verify a non-table [tool.gen_desk_tools] value in pyproject.toml is safely ignored."""
    (gdt_workspace / "pyproject.toml").write_text(
        '[tool]\ngen_desk_tools = "not-a-table"\n',
        encoding="utf-8",
    )

    cfg = load_gdt_config(root_dir=gdt_workspace)
    assert cfg["retention"]["max_versions"] == DEFAULT_GDT_CONFIG["retention"]["max_versions"]


@pytest.mark.regression
def test_load_gdt_config_auto_resolves_root_when_omitted(
    gdt_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify load_gdt_config discovers the workspace root automatically when root_dir is None."""
    (gdt_workspace / "gda_conf.toml").write_text(
        "[retention]\nmax_versions = 12\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(gdt_workspace / "src" / "gen_desk_tools")

    cfg = load_gdt_config()
    assert cfg["retention"]["max_versions"] == 12


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Missing explicit --config file rejection.
# ==========================================================================


@pytest.mark.regression
def test_load_gdt_config_missing_explicit_config_raises_file_not_found(
    gdt_workspace: Path,
) -> None:
    """Verify a nonexistent explicit config_path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Explicit config file not found"):
        load_gdt_config(root_dir=gdt_workspace, config_path=gdt_workspace / "missing.toml")
