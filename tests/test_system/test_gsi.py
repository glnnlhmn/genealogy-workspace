# Name: test_gsi.py
# Path: tests/test_system/test_gsi.py
# Version: 1.3.1+build.r1

"""Verification Test Suite for Genealogy Script Importer (GSI).

Operational Role:
    Exhaustively verifies GSI intake parsing, destination backup routing into
    isolated archive directories, overwrite policies, clean purges, and execution
    dispatch mechanisms.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification of functional behaviors and branch boundaries.
    - Fully decorated: Pytest marker taxonomy (--strict-markers).
    - Dependencies: Isolated tmp_path test harnesses with zero production writes.
"""

from __future__ import annotations

import io
import json
import runpy
import shutil
import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import system.gsi as gsi

# ==============================================================================
# FIXTURES & ISOLATED SANDBOX SETUP
# ==============================================================================


@pytest.fixture
def isolated_workspace(tmp_path: Path) -> Generator[Path]:
    """Create a fully isolated workspace environment matching repository topology."""
    root = tmp_path / "workspace"
    root.mkdir(parents=True, exist_ok=True)

    # Establish workspace directory topology
    (root / "download").mkdir(parents=True, exist_ok=True)
    (root / "archive" / "backups_gda").mkdir(parents=True, exist_ok=True)
    (root / "archive" / "backups_ancestry_desk").mkdir(parents=True, exist_ok=True)
    (root / "archive" / "backups_cli").mkdir(parents=True, exist_ok=True)
    (root / "archive" / "backups_system").mkdir(parents=True, exist_ok=True)
    (root / "src" / "gda" / "core").mkdir(parents=True, exist_ok=True)
    (root / "src" / "ancestry_desk").mkdir(parents=True, exist_ok=True)
    (root / "src" / "cli").mkdir(parents=True, exist_ok=True)
    (root / "src" / "system").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_gda").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_ancestry_desk").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_cli").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_system").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "design").mkdir(parents=True, exist_ok=True)
    (root / "nb" / "exploration").mkdir(parents=True, exist_ok=True)

    with patch.object(gsi, "get_workspace_root", return_value=root):
        yield root


# ==============================================================================
# GROUP 1: WORKSPACE ROOT RESOLUTION
# Note: Verifies workspace root resolution across standard and shallow layouts.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_get_workspace_root_standard_resolution(tmp_path: Path) -> None:
    """Verify workspace root resolves via parent directory when src is present."""
    fake_script = tmp_path / "repo" / "src" / "system" / "gsi.py"
    fake_script.parent.mkdir(parents=True, exist_ok=True)
    fake_script.touch()
    (tmp_path / "repo" / "src").mkdir(parents=True, exist_ok=True)

    with patch.object(gsi, "__file__", str(fake_script)):
        root = gsi.get_workspace_root()
        assert root == tmp_path / "repo"


@pytest.mark.unit
def test_get_workspace_root_shallow_fallback(tmp_path: Path) -> None:
    """Verify workspace root resolves via current working directory when parents check fails."""
    dummy_script = tmp_path / "shallow" / "gsi.py"
    dummy_script.parent.mkdir(parents=True, exist_ok=True)
    dummy_script.touch()

    with (
        patch.object(gsi, "__file__", str(dummy_script)),
        patch.object(Path, "cwd", return_value=tmp_path),
    ):
        resolved = gsi.get_workspace_root()
        assert resolved == tmp_path


# ==============================================================================
# GROUP 2: HEADER & METADATA EXTRACTION VIA PHYSICAL FIXTURES
# Note: Verifies metadata extraction from static golden baselines on disk.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_parse_metadata_header_golden_python(
    isolated_workspace: Path, fixtures_dir: Path
) -> None:
    """Verify header extraction from physical Python golden fixture."""
    src = fixtures_dir / "golden" / "gemini_valid_code.py"
    dest = isolated_workspace / "download" / "candidate_code.py"
    shutil.copy2(src, dest)

    name, target = gsi.parse_metadata_header(dest, isolated_workspace)
    assert name == "config.py"
    assert target == isolated_workspace / "src" / "gda" / "core" / "config.py"


@pytest.mark.unit
def test_parse_metadata_header_golden_markdown(
    isolated_workspace: Path, fixtures_dir: Path
) -> None:
    """Verify header extraction from physical Markdown HTML comment golden fixture."""
    src = fixtures_dir / "golden" / "gemini_valid_doc.md"
    dest = isolated_workspace / "download" / "candidate_doc.md"
    shutil.copy2(src, dest)

    name, target = gsi.parse_metadata_header(dest, isolated_workspace)
    assert name == "architecture.md"
    assert target == isolated_workspace / "docs" / "design" / "architecture.md"


@pytest.mark.unit
def test_parse_metadata_header_golden_json(
    isolated_workspace: Path, fixtures_dir: Path
) -> None:
    """Verify header extraction from physical JSON root attributes golden fixture."""
    src = fixtures_dir / "golden" / "gemini_valid_json.json"
    dest = isolated_workspace / "download" / "candidate_json.json"
    shutil.copy2(src, dest)

    name, target = gsi.parse_metadata_header(dest, isolated_workspace)
    assert name == "sample.json"
    assert target == isolated_workspace / "download" / "sample.json"


@pytest.mark.unit
def test_parse_metadata_header_golden_ipynb_metadata(
    isolated_workspace: Path, fixtures_dir: Path
) -> None:
    """Verify header extraction from physical Jupyter notebook top-level metadata fixture."""
    src = fixtures_dir / "golden" / "gemini_valid_nb_meta.ipynb"
    dest = isolated_workspace / "download" / "candidate_nb_meta.ipynb"
    shutil.copy2(src, dest)

    name, target = gsi.parse_metadata_header(dest, isolated_workspace)
    assert name == "tour.ipynb"
    assert target == isolated_workspace / "nb" / "exploration" / "tour.ipynb"


@pytest.mark.unit
def test_parse_metadata_header_golden_ipynb_cell(
    isolated_workspace: Path, fixtures_dir: Path
) -> None:
    """Verify header extraction from physical Jupyter notebook first cell comment fixture."""
    src = fixtures_dir / "golden" / "gemini_valid_nb_cell.ipynb"
    dest = isolated_workspace / "download" / "candidate_nb_cell.ipynb"
    shutil.copy2(src, dest)

    name, target = gsi.parse_metadata_header(dest, isolated_workspace)
    assert name == "fallback_tour.ipynb"
    assert target == isolated_workspace / "nb" / "exploration" / "fallback_tour.ipynb"


# ==============================================================================
# GROUP 3: DEFECT FIXTURES & PARSING BOUNDARY DEFENSES
# Note: Verifies defensive rejection of corrupt payloads, traversal, and missing keys.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.unit
def test_parse_metadata_header_corrupt_json_fixture(
    isolated_workspace: Path, fixtures_dir: Path
) -> None:
    """Verify corrupted JSON defect fixture safely returns (None, None)."""
    src = fixtures_dir / "failure" / "gemini_corrupt.json"
    dest = isolated_workspace / "download" / "corrupt.json"
    shutil.copy2(src, dest)

    name, target = gsi.parse_metadata_header(dest, isolated_workspace)
    assert name is None
    assert target is None


@pytest.mark.regression
@pytest.mark.unit
def test_parse_metadata_header_path_traversal_fixture(
    isolated_workspace: Path, fixtures_dir: Path
) -> None:
    """Verify path traversal exploit fixture is safely rejected with (None, None)."""
    src = fixtures_dir / "failure" / "gemini_path_traversal.py"
    dest = isolated_workspace / "download" / "exploit.py"
    shutil.copy2(src, dest)

    name, target = gsi.parse_metadata_header(dest, isolated_workspace)
    assert name is None
    assert target is None


@pytest.mark.regression
@pytest.mark.unit
def test_parse_metadata_header_no_header_fixture(
    isolated_workspace: Path, fixtures_dir: Path
) -> None:
    """Verify text file lacking metadata headers returns (None, None)."""
    src = fixtures_dir / "failure" / "gemini_no_header.txt"
    dest = isolated_workspace / "download" / "no_header.txt"
    shutil.copy2(src, dest)

    name, target = gsi.parse_metadata_header(dest, isolated_workspace)
    assert name is None
    assert target is None


@pytest.mark.unit
def test_parse_metadata_header_unreadable_file_exception(
    isolated_workspace: Path,
) -> None:
    """Verify unreadable file or permission error in read_text safely returns (None, None)."""
    target_file = isolated_workspace / "download" / "unreadable.py"
    target_file.touch()

    with patch.object(Path, "read_text", side_effect=OSError("Read failure")):
        name, target = gsi.parse_metadata_header(target_file, isolated_workspace)
        assert name is None
        assert target is None


@pytest.mark.unit
def test_parse_metadata_header_corrupt_ipynb_json_exception(
    isolated_workspace: Path,
) -> None:
    """Verify invalid JSON in .ipynb file safely triggers exception branch returning (None, None)."""
    f = isolated_workspace / "download" / "bad_nb.ipynb"
    f.write_text("{invalid_json: true", encoding="utf-8")

    name, target = gsi.parse_metadata_header(f, isolated_workspace)
    assert name is None
    assert target is None


@pytest.mark.unit
def test_parse_metadata_header_ipynb_cells_without_header(
    isolated_workspace: Path,
) -> None:
    """Verify notebook with cells but lacking Name or Path comment lines returns (None, None)."""
    nb = {
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 2,
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["# Generic Markdown Title\n", "No headers here."],
            }
        ],
    }
    f = isolated_workspace / "download" / "empty_cells.ipynb"
    f.write_text(json.dumps(nb), encoding="utf-8")

    name, target = gsi.parse_metadata_header(f, isolated_workspace)
    assert name is None
    assert target is None


@pytest.mark.unit
def test_parse_metadata_header_ipynb_non_matching_cell_type(
    isolated_workspace: Path,
) -> None:
    """Verify notebook cell with non-matching cell_type bypasses cell parsing branch."""
    nb = {
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 2,
        "cells": [{"cell_type": "custom_unknown", "source": ["# Name: skip.py\n"]}],
    }
    f = isolated_workspace / "download" / "custom_cell.ipynb"
    f.write_text(json.dumps(nb), encoding="utf-8")

    name, target = gsi.parse_metadata_header(f, isolated_workspace)
    assert name is None
    assert target is None


@pytest.mark.unit
def test_parse_metadata_header_ipynb_partial_cell_header(
    isolated_workspace: Path,
) -> None:
    """Verify notebook cell containing Name but missing Path returns (None, None)."""
    nb = {
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 2,
        "cells": [{"cell_type": "markdown", "source": ["# Name: only_name.ipynb\n"]}],
    }
    f = isolated_workspace / "download" / "partial_cell.ipynb"
    f.write_text(json.dumps(nb), encoding="utf-8")

    name, target = gsi.parse_metadata_header(f, isolated_workspace)
    assert name is None
    assert target is None


@pytest.mark.unit
def test_parse_metadata_header_json_without_keys(isolated_workspace: Path) -> None:
    """Verify valid JSON lacking _name and _path root keys returns (None, None)."""
    f = isolated_workspace / "download" / "valid_no_keys.json"
    f.write_text(json.dumps({"records": [1, 2, 3], "status": "ok"}), encoding="utf-8")

    name, target = gsi.parse_metadata_header(f, isolated_workspace)
    assert name is None
    assert target is None


@pytest.mark.unit
def test_parse_metadata_header_json_parsing_exception(isolated_workspace: Path) -> None:
    """Verify exception branch in JSON header parser returns (None, None)."""
    f = isolated_workspace / "download" / "err.json"
    f.write_text('{"test": 1}', encoding="utf-8")

    with patch("system.gsi.re.search", side_effect=Exception("Regex fault")):
        name, target = gsi.parse_metadata_header(f, isolated_workspace)
        assert name is None
        assert target is None


@pytest.mark.unit
def test_parse_metadata_header_directory_path_append(isolated_workspace: Path) -> None:
    """Verify directory path in Path header properly appends target filename."""
    f = isolated_workspace / "download" / "dir_path.py"
    f.write_text(
        "# Name: appended_mod.py\n# Path: src/gda/core/\n",
        encoding="utf-8",
    )
    name, target = gsi.parse_metadata_header(f, isolated_workspace)
    assert name == "appended_mod.py"
    assert target == isolated_workspace / "src" / "gda" / "core" / "appended_mod.py"


# ==============================================================================
# GROUP 4: DESTINATION BACKUP ISOLATION ARCHITECTURE
# Note: Verifies pre-write Safe Backup redirection into isolated archive/ directories.
# ==============================================================================


@pytest.mark.integration
@pytest.mark.parametrize(
    ("dest_rel", "archive_folder"),
    [
        ("src/gda/core/mod.py", "backups_gda"),
        ("src/ancestry_desk/app.py", "backups_ancestry_desk"),
        ("src/cli/main.py", "backups_cli"),
        ("src/system/gsi.py", "backups_system"),
        ("src/custom_sub/mod.py", "backups_custom_sub"),
        ("tests/test_gda/test_mod.py", "backups_gda"),
        ("tests/test_ancestry_desk/test_v.py", "backups_ancestry_desk"),
        ("tests/test_cli/test_c.py", "backups_cli"),
        ("tests/test_system/test_s.py", "backups_system"),
        ("tests/unknown/test_u.py", "backups_system"),
        ("root_file.py", "backups_system"),
    ],
)
def test_determine_backup_directory_routes(
    isolated_workspace: Path, dest_rel: str, archive_folder: str
) -> None:
    """Verify backup directory mapping resolves correctly across all project modules."""
    dest = isolated_workspace / dest_rel
    backup_dir = gsi._determine_backup_directory(dest, isolated_workspace)
    expected_parent_rel = dest.parent.relative_to(isolated_workspace)
    expected_dir = isolated_workspace / "archive" / archive_folder / expected_parent_rel
    assert backup_dir == expected_dir


@pytest.mark.smoke
@pytest.mark.integration
def test_run_intake_creates_isolated_backup_for_code(isolated_workspace: Path) -> None:
    """Verify existing code file is backed up to archive/ and replaced at destination."""
    dest = isolated_workspace / "src" / "gda" / "core" / "existing.py"
    dest.write_text("ORIGINAL_CONTENT", encoding="utf-8")

    cand = isolated_workspace / "download" / "candidate_existing.py"
    cand.write_text(
        "# Name: existing.py\n# Path: src/gda/core/existing.py\nNEW_CONTENT",
        encoding="utf-8",
    )

    code = gsi.run_intake()
    assert code == 0
    assert (
        dest.read_text(encoding="utf-8")
        == "# Name: existing.py\n# Path: src/gda/core/existing.py\nNEW_CONTENT"
    )

    # Backup must NOT reside alongside original
    assert len(list(dest.parent.glob("*.bk"))) == 0

    # Backup MUST reside in archive/backups_gda/src/gda/core/
    backup_repo = (
        isolated_workspace / "archive" / "backups_gda" / "src" / "gda" / "core"
    )
    bk_files = list(backup_repo.glob("existing.py.*.bk"))
    assert len(bk_files) == 1
    assert bk_files[0].read_text(encoding="utf-8") == "ORIGINAL_CONTENT"


@pytest.mark.integration
def test_run_intake_force_flag_bypasses_backup(isolated_workspace: Path) -> None:
    """Verify --force flag overwrites existing code file without creating backup."""
    dest = isolated_workspace / "src" / "gda" / "core" / "forced.py"
    dest.write_text("OLD", encoding="utf-8")

    cand = isolated_workspace / "download" / "candidate_forced.py"
    cand.write_text(
        "# Name: forced.py\n# Path: src/gda/core/forced.py\nNEW",
        encoding="utf-8",
    )

    code = gsi.run_intake(force=True)
    assert code == 0
    assert (
        dest.read_text(encoding="utf-8")
        == "# Name: forced.py\n# Path: src/gda/core/forced.py\nNEW"
    )
    backups = list((isolated_workspace / "archive").rglob("forced.py.*.bk"))
    assert len(backups) == 0


@pytest.mark.integration
def test_run_intake_force_flag_overwrites_non_code_without_prompt(
    isolated_workspace: Path,
) -> None:
    """Verify force=True bypasses prompt on existing non-code files."""
    dest = isolated_workspace / "docs" / "design" / "forced_doc.md"
    dest.write_text("OLD_DOC", encoding="utf-8")

    cand = isolated_workspace / "download" / "candidate_forced_doc.md"
    cand.write_text(
        "<!-- Name: forced_doc.md -->\n<!-- Path: docs/design/forced_doc.md -->\nNEW_DOC",
        encoding="utf-8",
    )

    code = gsi.run_intake(force=True)
    assert code == 0
    assert "NEW_DOC" in dest.read_text(encoding="utf-8")


# ==============================================================================
# GROUP 5: INTERACTIVE PROMPTS, PREFIXES & CLEAN PURGING
# Note: Verifies interactive confirmation, refusal, prefix filters, and --clean purging.
# ==============================================================================


@pytest.mark.unit
def test_prompt_user_yes_no(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify standard input prompt parses yes and no responses."""
    monkeypatch.setattr("sys.stdin", io.StringIO("y\n"))
    assert gsi._prompt_user_yes_no("Confirm?") is True

    monkeypatch.setattr("sys.stdin", io.StringIO("n\n"))
    assert gsi._prompt_user_yes_no("Confirm?") is False


@pytest.mark.integration
def test_run_intake_prompt_confirm_overwrites_doc(isolated_workspace: Path) -> None:
    """Verify user confirmation ('y') allows overwriting documentation files without -r flag."""
    dest = isolated_workspace / "docs" / "design" / "spec.md"
    dest.write_text("OLD_DOC", encoding="utf-8")

    cand = isolated_workspace / "download" / "candidate_spec.md"
    cand.write_text(
        "<!-- Name: spec.md -->\n<!-- Path: docs/design/spec.md -->\nNEW_DOC",
        encoding="utf-8",
    )

    with patch.object(gsi, "_prompt_user_yes_no", return_value=True):
        code = gsi.run_intake(run_target=False)
        assert code == 0
        assert "NEW_DOC" in dest.read_text(encoding="utf-8")
        assert not cand.exists()


@pytest.mark.integration
def test_run_intake_non_code_interactive_refusal(
    isolated_workspace: Path, capsys: pytest.CaptureFixture
) -> None:
    """Verify operator refusal ('n') executes skip logic and leaves original intact."""
    dest = isolated_workspace / "docs" / "design" / "guide.md"
    dest.write_text("OLD_GUIDE", encoding="utf-8")

    cand = isolated_workspace / "download" / "candidate_guide.md"
    cand.write_text(
        "<!-- Name: guide.md -->\n<!-- Path: docs/design/guide.md -->\nNEW_GUIDE",
        encoding="utf-8",
    )

    with patch.object(gsi, "_prompt_user_yes_no", return_value=False):
        code = gsi.run_intake()
        assert code == 0
        assert dest.read_text(encoding="utf-8") == "OLD_GUIDE"
        assert cand.exists()
        captured = capsys.readouterr()
        assert "Skipped relocation: candidate_guide.md" in captured.out
        assert "No files were relocated." in captured.out


@pytest.mark.integration
def test_run_intake_clean_purges_unparseable_files(
    isolated_workspace: Path, capsys: pytest.CaptureFixture
) -> None:
    """Verify --clean flag prompts and removes unparseable files from download/."""
    junk = isolated_workspace / "download" / "junk.txt"
    junk.write_text("NO_HEADER_HERE", encoding="utf-8")

    with patch.object(gsi, "_prompt_user_yes_no", return_value=True):
        code = gsi.run_intake(clean=True)
        assert code == 0
        assert not junk.exists()
        captured = capsys.readouterr()
        assert "Purged: junk.txt" in captured.out


@pytest.mark.integration
def test_run_intake_clean_skips_when_refused(isolated_workspace: Path) -> None:
    """Verify --clean flag preserves file when user enters 'n'."""
    junk = isolated_workspace / "download" / "keep.txt"
    junk.write_text("NO_HEADER", encoding="utf-8")

    with patch.object(gsi, "_prompt_user_yes_no", return_value=False):
        code = gsi.run_intake(clean=True)
        assert code == 0
        assert junk.exists()


@pytest.mark.integration
def test_run_intake_clean_with_force_bypasses_prompt(isolated_workspace: Path) -> None:
    """Verify --clean with --force deletes unparseable files without prompting."""
    junk = isolated_workspace / "download" / "junk2.txt"
    junk.write_text("NO_HEADER", encoding="utf-8")

    code = gsi.run_intake(clean=True, force=True)
    assert code == 0
    assert not junk.exists()


@pytest.mark.integration
def test_run_intake_empty_directory(
    isolated_workspace: Path, capsys: pytest.CaptureFixture
) -> None:
    """Verify handling when download directory has no candidate files."""
    code = gsi.run_intake()
    assert code == 0
    captured = capsys.readouterr()
    assert "No intake candidates found in download/." in captured.out


@pytest.mark.integration
def test_run_intake_skips_unparseable_when_clean_false(
    isolated_workspace: Path, capsys: pytest.CaptureFixture
) -> None:
    """Verify unparseable files are skipped without being deleted when clean is False."""
    f = isolated_workspace / "download" / "unparseable.txt"
    f.write_text("NO_HEADERS_AVAILABLE", encoding="utf-8")
    code = gsi.run_intake(clean=False)
    assert code == 0
    assert f.exists()
    captured = capsys.readouterr()
    assert "Skipping unparseable.txt: Missing valid metadata headers." in captured.out


@pytest.mark.integration
def test_run_intake_prefix_filtering(isolated_workspace: Path) -> None:
    """Verify prefix filter only processes files matching specified prefix."""
    f1 = isolated_workspace / "download" / "gemini_script.py"
    f1.write_text("# Name: match.py\n# Path: src/system/match.py\n", encoding="utf-8")
    f2 = isolated_workspace / "download" / "other_script.py"
    f2.write_text("# Name: ignore.py\n# Path: src/system/ignore.py\n", encoding="utf-8")

    code = gsi.run_intake(prefix="gemini")
    assert code == 0
    assert (isolated_workspace / "src" / "system" / "match.py").exists()
    assert f2.exists()


@pytest.mark.integration
def test_run_intake_missing_download_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Verify error reporting if download directory does not exist."""
    with patch.object(gsi, "get_workspace_root", return_value=tmp_path):
        code = gsi.run_intake()
        assert code == 1
        captured = capsys.readouterr()
        assert "Error: Download directory not found" in captured.out


# ==============================================================================
# GROUP 6: CONTEXTUAL EXECUTION DISPATCH VIA _execute_target
# Note: Verifies execution dispatch routing across Python, PowerShell, Bash, and documents.
# ==============================================================================


@pytest.mark.unit
def test_execute_target_routes_powershell(isolated_workspace: Path) -> None:
    """Verify _execute_target routes .ps1 files directly to _execute_powershell."""
    ps_file = isolated_workspace / "runner.ps1"
    with patch.object(gsi, "_execute_powershell", return_value=0) as mock_ps:
        res = gsi._execute_target(ps_file, isolated_workspace)
        assert res == 0
        mock_ps.assert_called_once_with(ps_file, isolated_workspace)


@pytest.mark.unit
def test_execute_target_routes_bash(isolated_workspace: Path) -> None:
    """Verify _execute_target routes .sh files directly to _execute_bash."""
    sh_file = isolated_workspace / "runner.sh"
    with patch.object(gsi, "_execute_bash", return_value=0) as mock_bash:
        res = gsi._execute_target(sh_file, isolated_workspace)
        assert res == 0
        mock_bash.assert_called_once_with(sh_file, isolated_workspace)


@pytest.mark.unit
def test_execute_target_routes_python(isolated_workspace: Path) -> None:
    """Verify _execute_target routes .py files directly to _execute_python."""
    py_file = isolated_workspace / "sample_script.py"
    with patch.object(gsi, "_execute_python", return_value=0) as mock_py:
        res = gsi._execute_target(py_file, isolated_workspace)
        assert res == 0
        mock_py.assert_called_once_with(py_file, isolated_workspace)


@pytest.mark.unit
def test_execute_python_script(isolated_workspace: Path) -> None:
    """Verify execution of standard Python scripts via subprocess."""
    script = isolated_workspace / "src" / "system" / "sample_exec.py"
    script.write_text("print('hello')", encoding="utf-8")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        ret = gsi._execute_python(script, isolated_workspace)
        assert ret == 0
        mock_run.assert_called_once_with(
            [sys.executable, str(script)], cwd=str(isolated_workspace)
        )


@pytest.mark.unit
def test_execute_python_test_script(isolated_workspace: Path) -> None:
    """Verify test scripts invoke pytest execution."""
    test_script = isolated_workspace / "tests" / "test_sample.py"
    test_script.write_text("def test_dummy(): pass", encoding="utf-8")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        ret = gsi._execute_python(test_script, isolated_workspace)
        assert ret == 0
        mock_run.assert_called_once_with(
            [sys.executable, "-m", "pytest", str(test_script), "-v"],
            cwd=str(isolated_workspace),
        )


@pytest.mark.unit
def test_execute_powershell_script(isolated_workspace: Path) -> None:
    """Verify execution dispatch for PowerShell scripts."""
    ps_file = isolated_workspace / "temp.ps1"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        ret = gsi._execute_powershell(ps_file, isolated_workspace)
        assert ret == 0
        mock_run.assert_called_once_with(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(ps_file)],
            cwd=str(isolated_workspace),
        )


@pytest.mark.unit
def test_execute_bash_script(isolated_workspace: Path) -> None:
    """Verify execution dispatch for Bash scripts."""
    sh_file = isolated_workspace / "temp.sh"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        ret = gsi._execute_bash(sh_file, isolated_workspace)
        assert ret == 0
        mock_run.assert_called_once_with(
            ["bash", str(sh_file)], cwd=str(isolated_workspace)
        )


@pytest.mark.unit
def test_execute_target_non_executable_notice(
    isolated_workspace: Path, capsys: pytest.CaptureFixture
) -> None:
    """Verify non-executable files print notice and return 0."""
    json_file = isolated_workspace / "data.json"
    ret = gsi._execute_target(json_file, isolated_workspace)
    assert ret == 0
    captured = capsys.readouterr()
    assert "Notice: Non-executable file type '.json'" in captured.out


@pytest.mark.smoke
@pytest.mark.integration
def test_run_intake_full_relocation_and_run(isolated_workspace: Path) -> None:
    """Verify full end-to-end relocation and execution invocation with -r flag."""
    cand = isolated_workspace / "download" / "candidate_runner.py"
    cand.write_text(
        "# Name: runner.py\n# Path: src/cli/runner.py\n",
        encoding="utf-8",
    )

    with patch.object(gsi, "_execute_target", return_value=0) as mock_exec:
        code = gsi.run_intake(run_target=True)
        assert code == 0
        dest = isolated_workspace / "src" / "cli" / "runner.py"
        assert dest.exists()
        mock_exec.assert_called_once_with(dest, isolated_workspace)


@pytest.mark.integration
def test_run_intake_execution_failure_returns_code(
    isolated_workspace: Path, capsys: pytest.CaptureFixture
) -> None:
    """Verify non-zero subprocess execution status halts and returns error code."""
    cand = isolated_workspace / "download" / "candidate_fail.py"
    cand.write_text("# Name: fail.py\n# Path: src/system/fail.py\n", encoding="utf-8")

    with patch.object(gsi, "_execute_target", return_value=2):
        code = gsi.run_intake(run_target=True)
        assert code == 2
        captured = capsys.readouterr()
        assert "Execution failed with non-zero exit code 2" in captured.out


@pytest.mark.unit
def test_main_cli_dispatch(isolated_workspace: Path) -> None:
    """Verify main entrypoint parses CLI flags and dispatches to run_intake."""
    with (
        patch.object(gsi, "run_intake", return_value=0) as mock_intake,
        pytest.raises(SystemExit) as exc,
    ):
        gsi.main(["-f", "-c", "-r", "-p", "gemini"])
    assert exc.value.code == 0
    mock_intake.assert_called_once_with(
        force=True, run_target=True, clean=True, prefix="gemini"
    )


@pytest.mark.smoke
@pytest.mark.unit
def test_gsi_main_module_execution_entrypoint() -> None:
    """Verify line 419 entrypoint executes main and exits when invoked as __main__."""
    saved_module = sys.modules.get("system.gsi")
    try:
        sys.modules.pop("system.gsi", None)
        with (
            patch.object(gsi, "run_intake", return_value=0),
            pytest.raises(SystemExit) as exc,
        ):
            with patch.object(sys, "argv", ["gsi.py"]):
                runpy.run_module("system.gsi", run_name="__main__", alter_sys=True)
        assert exc.value.code == 0
    finally:
        if saved_module is not None:
            sys.modules["system.gsi"] = saved_module
