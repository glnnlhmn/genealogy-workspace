"""Path: tests/test_system/test_check_structure.py

Comprehensive unit test suite for directory inspection utility in src.system.check_structure.

Operational Role:
    Verifies recursive directory traversal, ignore-list filtering, default
    report target selection, depth capping, and command-line argument handling.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Decorated with @pytest.mark.unit and @pytest.mark.smoke.
    - Dependencies: Isolated filesystem sandboxing via tmp_path.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import system.check_structure as cs

__version__ = "0.0.1+build.r3"


# ==============================================================================
# GROUP 1: Tree Traversal and Path Filtering
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_build_tree_filters_ignored_directories_and_hidden_files(
    tmp_path: Path,
) -> None:
    """Verify build_tree ignores dot-prefixed files, .git, and gtemp directories."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").touch()
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").touch()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "cached.pyc").touch()
    (tmp_path / "gtemp").mkdir()
    (tmp_path / "gtemp" / "scratch.py").touch()
    (tmp_path / ".hidden").touch()

    lines = cs.build_tree(tmp_path, prefix=".")

    assert "./src" in lines
    assert "./src/main.py" in lines
    assert not any(".git" in line for line in lines)
    assert not any("__pycache__" in line for line in lines)
    assert not any("gtemp" in line for line in lines)
    assert not any(".hidden" in line for line in lines)


@pytest.mark.unit
def test_build_tree_respects_max_depth_boundary(tmp_path: Path) -> None:
    """Verify build_tree stops recursion when current_depth reaches max_depth."""
    level1 = tmp_path / "l1"
    level2 = level1 / "l2"
    level3 = level2 / "l3"
    level3.mkdir(parents=True)
    (level3 / "deep.py").touch()

    lines = cs.build_tree(tmp_path, prefix=".", max_depth=2)

    assert "./l1" in lines
    assert "./l1/l2" in lines
    assert not any("l3" in line for line in lines)


@pytest.mark.unit
def test_build_tree_handles_unreadable_or_missing_directory(tmp_path: Path) -> None:
    """Verify build_tree returns an empty list gracefully when directory does not exist."""
    missing = tmp_path / "nonexistent"
    lines = cs.build_tree(missing, prefix=".")
    assert lines == []


# ==============================================================================
# GROUP 2: Execution, File Emission, and Entrypoint
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_main_emits_default_filtered_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify main without arguments scans src/ and tests/ and writes GenDeskStructure.txt."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").touch()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").touch()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.txt").touch()

    exit_code = cs.main([])
    captured = capsys.readouterr()

    expected_file = tmp_path / cs.DEFAULT_FILTERED_REPORT
    assert exit_code == 0
    assert "Report created: GenDeskStructure.txt" in captured.out
    assert expected_file.exists()

    content = expected_file.read_text(encoding="utf-8")
    assert "./src" in content
    assert "./tests" in content
    assert "./docs" not in content


@pytest.mark.unit
def test_main_with_all_flag_emits_complete_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify main with --all scans from root down and writes GenDeskStructureComplete.txt."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()

    exit_code = cs.main(["--all"])
    captured = capsys.readouterr()

    expected_file = tmp_path / cs.DEFAULT_COMPLETE_REPORT
    assert exit_code == 0
    assert "Report created: GenDeskStructureComplete.txt" in captured.out
    assert expected_file.exists()

    content = expected_file.read_text(encoding="utf-8")
    assert "./src" in content
    assert "./docs" in content


@pytest.mark.unit
def test_main_with_custom_output_argument(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify main with -o writes to the explicitly requested file path."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()

    custom_out = "reports/custom_report.txt"
    exit_code = cs.main(["-o", custom_out])
    captured = capsys.readouterr()

    expected_file = tmp_path / custom_out
    assert exit_code == 0
    assert "Report created: custom_report.txt" in captured.out
    assert expected_file.exists()


@pytest.mark.smoke
@pytest.mark.unit
def test_check_structure_module_execution_entrypoint() -> None:
    """Verify line 159 entrypoint executes main and exits when invoked as __main__."""
    saved_module = sys.modules.get("system.check_structure")
    try:
        sys.modules.pop("system.check_structure", None)
        with (
            patch.object(cs, "main", return_value=0),
            pytest.raises(SystemExit) as exc,
        ):
            with patch.object(sys, "argv", ["check_structure.py"]):
                runpy.run_module(
                    "system.check_structure", run_name="__main__", alter_sys=True
                )
        assert exc.value.code == 0
    finally:
        if saved_module is not None:
            sys.modules["system.check_structure"] = saved_module
