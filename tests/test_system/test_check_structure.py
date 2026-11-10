"""Path: tests/test_system/test_check_structure.py

Unit and integration test suite for check_structure.py.

Operational Role:
    Verifies workspace root resolution, domain scopes (all, clean, src,
    src-no-tests, schemas, data), depth boundaries, exclusion filtering,
    interactive menu toggle interactions, and CLI argument parsing achieving
    100.00% statement and branch coverage.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from system.util.check_structure import (
    build_tree,
    generate_structure_report,
    main,
    parse_args,
    resolve_workspace_root,
    run_interactive_menu,
)

__version__ = "1.0.0+build.6"


# ==============================================================================
# GROUP 1: Root Resolution & Traversal Tree Invariants
# ==============================================================================


@pytest.mark.unit
def test_resolve_workspace_root_variants(tmp_path: Path) -> None:
    """Verify workspace root resolution via explicit path, parent anchors, and cwd fallback."""
    # 1. Explicit directory
    assert resolve_workspace_root(str(tmp_path)) == tmp_path.resolve()

    # 2. Parent traversal finding pyproject.toml
    proj_root = tmp_path / "proj_root"
    proj_root.mkdir(parents=True)
    (proj_root / "pyproject.toml").write_text("", encoding="utf-8")
    script_proj = proj_root / "src" / "system" / "util" / "check_structure.py"
    script_proj.parent.mkdir(parents=True)

    with patch("system.util.check_structure.__file__", str(script_proj)):
        assert resolve_workspace_root(".") == proj_root.resolve()

    # 3. Fallback to cwd when pyproject.toml is not in parents
    with patch("system.util.check_structure.__file__", "/isolated/nowhere/tool.py"):
        assert resolve_workspace_root(".") == Path.cwd().resolve()


@pytest.mark.regression
def test_resolve_workspace_root_nonexistent_directory_falls_through(tmp_path: Path) -> None:
    """Verify non-existent directory argument falls through to parent anchor discovery (branch 51->54)."""
    proj_root = tmp_path / "anchor_root"
    proj_root.mkdir(parents=True)
    (proj_root / "pyproject.toml").write_text("", encoding="utf-8")
    script_proj = proj_root / "src" / "system" / "util" / "check_structure.py"
    script_proj.parent.mkdir(parents=True)

    nonexistent_path = str(tmp_path / "does_not_exist_xyz")

    with patch("system.util.check_structure.__file__", str(script_proj)):
        resolved = resolve_workspace_root(nonexistent_path)
        assert resolved == proj_root.resolve()


@pytest.mark.unit
def test_build_tree_depth_and_permission_resilience(tmp_path: Path) -> None:
    """Verify max_depth boundary and graceful recovery from inaccessible directories."""
    d1 = tmp_path / "l1" / "l2" / "l3"
    d1.mkdir(parents=True)
    (d1 / "deep.txt").write_text("deep", encoding="utf-8")

    tree_shallow = build_tree(tmp_path, max_depth=1)
    assert "./l1" in tree_shallow
    assert "./l1/l2" not in tree_shallow

    assert build_tree(tmp_path, max_depth=2, current_depth=2) == []

    with patch("pathlib.Path.iterdir", side_effect=PermissionError("Access denied")):
        assert build_tree(tmp_path) == []


@pytest.mark.unit
def test_build_tree_mandatory_and_custom_exclusions(tmp_path: Path) -> None:
    """Verify mandatory hidden dirs and custom exclusions are skipped."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "gtemp").mkdir()
    (tmp_path / "active_dir").mkdir()
    (tmp_path / "active_dir" / "file.py").write_text("code", encoding="utf-8")
    (tmp_path / "custom_exclude").mkdir()

    lines = build_tree(tmp_path, excluded_names={"custom_exclude", "gtemp"})
    assert "./active_dir" in lines
    assert "./active_dir/file.py" in lines
    assert "./.git" not in lines
    assert "./.venv" not in lines
    assert "./gtemp" not in lines
    assert "./custom_exclude" not in lines

    lines_default = build_tree(tmp_path)
    assert "./gtemp" in lines_default
    assert "./.git" not in lines_default


# ==============================================================================
# GROUP 2: Domain Scope Reporting Tests
# ==============================================================================


@pytest.mark.integration
def test_generate_structure_report_scopes(tmp_path: Path) -> None:
    """Verify all report scopes generate corresponding reports and format lines."""
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "mod.py").write_text("x=1", encoding="utf-8")

    (tmp_path / "tests" / "test_pkg").mkdir(parents=True)
    (tmp_path / "tests" / "test_pkg" / "test_mod.py").write_text(
        "def test_x(): pass", encoding="utf-8"
    )

    (tmp_path / "schemas").mkdir(parents=True)
    (tmp_path / "schemas" / "core.json").write_text("{}", encoding="utf-8")

    (tmp_path / "data").mkdir(parents=True)
    (tmp_path / "data" / "sites.json").write_text("{}", encoding="utf-8")

    (tmp_path / "gtemp").mkdir(parents=True)
    (tmp_path / "gtemp" / "scratch.txt").write_text("scratch", encoding="utf-8")

    # 1. Scope: 'all'
    rep_all, count_all = generate_structure_report(scope="all", workspace_root=tmp_path)
    assert rep_all.name == "GenDeskStructureComplete.txt"
    assert count_all > 0
    assert rep_all.exists()

    # 2. Scope: 'clean'
    rep_clean, count_clean = generate_structure_report(scope="clean", workspace_root=tmp_path)
    assert rep_clean.name == "GenDeskStructureClean.txt"
    content_clean = rep_clean.read_text(encoding="utf-8")
    assert "./gtemp" not in content_clean
    assert "./src" in content_clean

    # 3. Scope: 'src'
    rep_src, count_src = generate_structure_report(scope="src", workspace_root=tmp_path)
    assert rep_src.name == "GenDeskStructureSrcTests.txt"
    content_src = rep_src.read_text(encoding="utf-8")
    assert "./src" in content_src
    assert "./tests" in content_src
    assert "./schemas" not in content_src

    # 4. Scope: 'src-no-tests'
    rep_no_tests, count_no_tests = generate_structure_report(
        scope="src-no-tests", workspace_root=tmp_path
    )
    assert rep_no_tests.name == "GenDeskStructureSrcOnly.txt"
    content_no_tests = rep_no_tests.read_text(encoding="utf-8")
    assert "./src" in content_no_tests
    assert "./tests" not in content_no_tests

    # 5. Scope: 'schemas'
    rep_schemas, count_schemas = generate_structure_report(
        scope="schemas", workspace_root=tmp_path
    )
    assert rep_schemas.name == "GenDeskStructureSchemas.txt"
    assert "./schemas/core.json" in rep_schemas.read_text(encoding="utf-8")

    # 6. Scope: 'data'
    rep_data, count_data = generate_structure_report(scope="data", workspace_root=tmp_path)
    assert rep_data.name == "GenDeskStructureData.txt"
    assert "./data/sites.json" in rep_data.read_text(encoding="utf-8")

    # 7. Explicit output path
    custom_dest = tmp_path / "custom" / "custom_tree.txt"
    rep_custom, _ = generate_structure_report(
        scope="src-no-tests", workspace_root=tmp_path, output_path=custom_dest
    )
    assert rep_custom == custom_dest
    assert custom_dest.exists()


@pytest.mark.integration
def test_generate_structure_report_nonexistent_domains(tmp_path: Path) -> None:
    """Verify scopes when target directories do not exist."""
    empty_workspace = tmp_path / "empty_workspace"
    empty_workspace.mkdir()

    rep1, count1 = generate_structure_report(
        scope="src-no-tests", workspace_root=empty_workspace
    )
    assert rep1.name == "GenDeskStructureSrcOnly.txt"
    assert count1 == 0

    rep2, count2 = generate_structure_report(scope="schemas", workspace_root=empty_workspace)
    assert rep2.name == "GenDeskStructureSchemas.txt"
    assert count2 == 0

    rep3, count3 = generate_structure_report(scope="data", workspace_root=empty_workspace)
    assert rep3.name == "GenDeskStructureData.txt"
    assert count3 == 0


@pytest.mark.unit
def test_generate_structure_report_invalid_scope(tmp_path: Path) -> None:
    """Verify ValueError is raised for unrecognized scope."""
    with pytest.raises(ValueError, match="Unknown inspection scope"):
        generate_structure_report(scope="unsupported", workspace_root=tmp_path)


# ==============================================================================
# GROUP 3: Interactive Menu & Toggle Controls
# ==============================================================================


@pytest.mark.unit
def test_run_interactive_menu_scope_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify selecting menu scopes and submitting with enter."""
    inputs1 = iter(["1", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs1))
    scope1, _ = run_interactive_menu()
    assert scope1 == "all"

    inputs2 = iter(["2", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs2))
    scope2, _ = run_interactive_menu()
    assert scope2 == "clean"

    inputs4 = iter(["4", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs4))
    scope4, _ = run_interactive_menu()
    assert scope4 == "src-no-tests"

    inputs5 = iter(["5", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs5))
    scope5, _ = run_interactive_menu()
    assert scope5 == "schemas"

    inputs6 = iter(["6", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs6))
    scope6, _ = run_interactive_menu()
    assert scope6 == "data"


@pytest.mark.unit
def test_run_interactive_menu_toggles_and_invalid_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify toggling exclusions (g, r, l, t) and retrying on invalid choice."""
    inputs = iter(["invalid_choice", "3", "r", "t", "g", "l", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    scope, exclusions = run_interactive_menu()
    assert scope == "src"
    assert "reports" in exclusions
    assert "tests" in exclusions
    assert "gtemp" not in exclusions


@pytest.mark.unit
def test_run_interactive_menu_quit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify 'q' and EOFError exit menu immediately."""
    monkeypatch.setattr("builtins.input", lambda _: "q")
    with pytest.raises(SystemExit) as exc:
        run_interactive_menu()
    assert exc.value.code == 0

    def raise_eof(_: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    with pytest.raises(SystemExit) as exc2:
        run_interactive_menu()
    assert exc2.value.code == 0


# ==============================================================================
# GROUP 4: CLI Execution & Main Entrypoint
# ==============================================================================


@pytest.mark.integration
def test_main_cli_execution_flags(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify CLI flags execute report generation and report statistics."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print()", encoding="utf-8")

    out_file = tmp_path / "cli_report.txt"

    monkeypatch.setattr(
        "sys.argv",
        [
            "check_structure",
            "--scope",
            "src-no-tests",
            "--root",
            str(tmp_path),
            "-o",
            str(out_file),
        ],
    )

    exit_code = main()
    assert exit_code == 0
    assert out_file.exists()
    captured = capsys.readouterr()
    assert "Report file created:" in captured.out


@pytest.mark.integration
def test_main_cli_menu_dispatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify --menu flag dispatches interactive menu."""
    (tmp_path / "src").mkdir()
    inputs = iter(["3", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    monkeypatch.setattr(
        "sys.argv",
        ["check_structure", "--menu", "--root", str(tmp_path)],
    )

    exit_code = main()
    assert exit_code == 0


@pytest.mark.unit
def test_main_cli_error_handling(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify main returns 1 on execution exception."""
    monkeypatch.setattr("sys.argv", ["check_structure", "--scope", "src"])
    with patch(
        "system.util.check_structure.generate_structure_report",
        side_effect=RuntimeError("Disk fault"),
    ):
        exit_code = main()
    assert exit_code == 1
    assert "Error: Disk fault" in capsys.readouterr().err


@pytest.mark.unit
def test_check_structure_module_runpy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify execution as __main__ module."""
    monkeypatch.setattr("sys.argv", ["check_structure", "-h"])
    monkeypatch.delitem(sys.modules, "system.util.check_structure", raising=False)
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("system.util.check_structure", run_name="__main__")
    assert exc.value.code == 0