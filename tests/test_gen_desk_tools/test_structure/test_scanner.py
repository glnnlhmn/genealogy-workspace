"""Path: tests/test_gen_desk_tools/test_structure/test_scanner.py

Unit, regression, and integration tests for gen_desk_tools.structure.scanner.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from gen_desk_tools.structure.scanner import (
    build_git_tree,
    build_tree,
    generate_structure_report,
)

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Primary gda mode report generation with and without matching tests/.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_generate_structure_report_gda_and_tests_writes_expected_files(
    tmp_path: Path,
) -> None:
    """Verify generate_structure_report emits gda-only and gda+tests reports."""
    (tmp_path / "src" / "gda").mkdir(parents=True)
    (tmp_path / "src" / "gda" / "core.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "tests" / "test_gda").mkdir(parents=True)
    (tmp_path / "tests" / "test_gda" / "test_core.py").write_text("pass\n", encoding="utf-8")

    rpt_src, cnt_src = generate_structure_report(
        "gda",
        include_tests=False,
        workspace_root=tmp_path,
        reports_dir="reports",
    )
    rpt_both, cnt_both = generate_structure_report(
        "gda",
        include_tests=True,
        workspace_root=tmp_path,
        reports_dir=tmp_path / "abs_reports",
    )

    assert rpt_src == tmp_path / "reports" / "GenDeskStructure_gda.txt"
    assert cnt_src == 2
    assert rpt_both == tmp_path / "abs_reports" / "GenDeskStructure_gda_tests.txt"
    assert cnt_both == 4
    assert "./tests/test_gda/test_core.py" in rpt_both.read_text(encoding="utf-8")


# ==========================================================================
# GROUP 2: Directory Tree & Git Tree Traversal
# Note: Depth bounds, exclusions, permission errors, and git ls-files parsing.
# ==========================================================================


@pytest.mark.unit
def test_build_tree_respects_depth_exclusions_and_permission_errors(tmp_path: Path) -> None:
    """Verify build_tree enforces max_depth, skips hidden/excluded dirs, and handles errors."""
    nested = tmp_path / "pkg" / "sub"
    nested.mkdir(parents=True)
    (nested / "deep.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / "skip_me").mkdir()

    shallow = build_tree(tmp_path, max_depth=1, excluded_names={"skip_me"})
    assert shallow == ["./pkg"]

    assert build_tree(tmp_path, max_depth=2, current_depth=2) == []

    with patch.object(Path, "iterdir", side_effect=PermissionError("denied")):
        assert build_tree(tmp_path) == []


@pytest.mark.unit
def test_build_git_tree_parses_paths_respects_depth_and_handles_errors(tmp_path: Path) -> None:
    """Verify build_git_tree expands parent dirs up to max_depth and wraps git errors."""
    fake_out = "\nsrc\\gda\\core\\mod.py\nREADME.md\n"
    with patch(
        "subprocess.run",
        return_value=subprocess.CompletedProcess(["git"], 0, stdout=fake_out),
    ):
        lines = build_git_tree(tmp_path, max_depth=2)

    assert lines == ["./README.md", "./src", "./src/gda"]

    with patch("subprocess.run", side_effect=FileNotFoundError("no git")):
        with pytest.raises(RuntimeError, match="Failed to query git-tracked/unignored files"):
            build_git_tree(tmp_path)


# ==========================================================================
# GROUP 3: All Modes, Empty Targets & Invalid Mode Rejection
# Note: all, git, missing target directories, and ValueError on unknown mode.
# ==========================================================================


@pytest.mark.integration
def test_generate_structure_report_all_git_and_missing_target_modes(tmp_path: Path) -> None:
    """Verify all, git, and missing-directory subsystem modes write valid reports."""
    (tmp_path / "README.md").write_text("# hi\n", encoding="utf-8")

    rpt_all, cnt_all = generate_structure_report("all", workspace_root=tmp_path)
    assert rpt_all.name == "GenDeskStructure_all.txt"
    assert cnt_all >= 2

    with patch("gen_desk_tools.structure.scanner.build_git_tree", return_value=["./README.md"]):
        rpt_git, cnt_git = generate_structure_report("git", workspace_root=tmp_path)
    assert rpt_git.name == "GenDeskStructure_git.txt"
    assert cnt_git == 2

    # Missing target directory produces empty report without crashing
    rpt_empty, cnt_empty = generate_structure_report("ancestry_desk", workspace_root=tmp_path)
    assert cnt_empty == 0
    assert rpt_empty.read_text(encoding="utf-8") == ""


@pytest.mark.regression
def test_generate_structure_report_invalid_mode_raises_value_error(tmp_path: Path) -> None:
    """Verify unknown structure mode raises ValueError."""
    with pytest.raises(ValueError, match="Unknown structure mode"):
        generate_structure_report("invalid_mode", workspace_root=tmp_path)
