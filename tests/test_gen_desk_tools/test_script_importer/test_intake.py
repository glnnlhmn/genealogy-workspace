"""Path: tests/test_gen_desk_tools/test_script_importer/test_intake.py

Unit, regression, and integration tests for gen_desk_tools.script_importer.intake.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from gen_desk_tools.script_importer.intake import run_intake

__version__ = "1.0.0+build.1"


def _close_gsi_logger() -> None:
    """Close and remove gsi logger handlers to prevent Windows tmp_path file locks."""
    logger = logging.getLogger("gsi")
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end relocation of a staged Python file from download/ into src/.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_run_intake_relocates_staged_file_and_reports_summary(
    gdt_workspace: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify run_intake moves a valid staged file from download/ to its destination."""
    staged = gdt_workspace / "download" / "new_mod.py"
    staged.write_text('"""Path: src/gen_desk_tools/new_mod.py"""\nx = 1\n', encoding="utf-8")

    try:
        code = run_intake(root_dir=gdt_workspace, verbose=True)
    finally:
        _close_gsi_logger()

    dest = gdt_workspace / "src" / "gen_desk_tools" / "new_mod.py"
    assert code == 0
    assert dest.is_file()
    assert not staged.exists()
    assert "-> src/gen_desk_tools/new_mod.py" in capsys.readouterr().out


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Mandatory Safe Backup on protected domains even under --force.
# ==========================================================================


@pytest.mark.integration
def test_run_intake_protected_domain_always_creates_safe_backup_even_with_force(
    gdt_workspace: Path,
) -> None:
    """Verify overwriting a protected-domain file creates a Safe Backup even when force=True."""
    existing = gdt_workspace / "src" / "gen_desk_tools" / "protected.py"
    existing.write_text("v = 1\n", encoding="utf-8")

    staged = gdt_workspace / "download" / "protected.py"
    staged.write_text('"""Path: src/gen_desk_tools/protected.py"""\nv = 2\n', encoding="utf-8")

    try:
        code = run_intake(root_dir=gdt_workspace, force=True)
    finally:
        _close_gsi_logger()

    backups = list(
        (gdt_workspace / "archive" / "backups_gen_desk_tools" / "src" / "gen_desk_tools").glob(
            "protected.py.*.bk"
        )
    )
    assert code == 0
    assert existing.read_text(encoding="utf-8").endswith("v = 2\n")
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "v = 1\n"


@pytest.mark.integration
def test_run_intake_unprotected_domain_prompts_and_honors_force(
    gdt_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify unprotected overwrites prompt without --force and overwrite immediately with --force."""
    existing = gdt_workspace / "docs" / "note.md"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("v1\n", encoding="utf-8")

    staged = gdt_workspace / "download" / "note.md"
    staged.write_text("<!--Path: docs/note.md-->\nv2\n", encoding="utf-8")

    try:
        # Decline overwrite -> file remains in download/ and destination stays v1
        monkeypatch.setattr("builtins.input", lambda _p: "n")
        assert run_intake(root_dir=gdt_workspace) == 0
        assert existing.read_text(encoding="utf-8") == "v1\n"
        assert staged.is_file()

        # Accept overwrite -> destination updates to v2
        monkeypatch.setattr("builtins.input", lambda _p: "y")
        assert run_intake(root_dir=gdt_workspace) == 0
        assert "v2" in existing.read_text(encoding="utf-8")

        # Re-stage and overwrite with force=True without prompting
        staged.write_text("<!--Path: docs/note.md-->\nv3\n", encoding="utf-8")
        assert run_intake(root_dir=gdt_workspace, force=True) == 0
        assert "v3" in existing.read_text(encoding="utf-8")
    finally:
        _close_gsi_logger()


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Empty download/, dotfiles ignored, and unparseable --clean handling.
# ==========================================================================


@pytest.mark.regression
def test_run_intake_empty_download_dir_returns_zero(
    gdt_workspace: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify empty download/ (ignoring hidden dotfiles) exits 0 cleanly."""
    (gdt_workspace / "download" / ".gitkeep").write_text("", encoding="utf-8")

    try:
        code = run_intake(root_dir=gdt_workspace)
    finally:
        _close_gsi_logger()

    assert code == 0
    assert "No intake candidates found" in capsys.readouterr().out


@pytest.mark.regression
def test_run_intake_unparseable_files_skip_or_clean_based_on_flags(
    gdt_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify unparseable staged files skip by default, prompt on --clean, and purge on --clean -f."""
    junk = gdt_workspace / "download" / "mystery.txt"
    junk.write_text("no header here\n", encoding="utf-8")

    try:
        # Default mode skips without deleting
        assert run_intake(root_dir=gdt_workspace) == 0
        assert junk.is_file()

        # --clean with declined prompt preserves file
        monkeypatch.setattr("builtins.input", lambda _p: "n")
        assert run_intake(root_dir=gdt_workspace, clean=True) == 0
        assert junk.is_file()

        # --clean --force purges immediately without prompting
        assert run_intake(root_dir=gdt_workspace, clean=True, force=True) == 0
        assert not junk.exists()
    finally:
        _close_gsi_logger()


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Invalid config path and missing download/ directory return exit code 1.
# ==========================================================================


@pytest.mark.regression
def test_run_intake_invalid_config_or_missing_download_dir_returns_one(
    gdt_workspace: Path,
) -> None:
    """Verify run_intake returns 1 on bad config path or missing download/ directory."""
    assert run_intake(root_dir=gdt_workspace, config_path=gdt_workspace / "missing.toml") == 1

    (gdt_workspace / "download").rmdir()
    try:
        assert run_intake(root_dir=gdt_workspace) == 1
    finally:
        _close_gsi_logger()
