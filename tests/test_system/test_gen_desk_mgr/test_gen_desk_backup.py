"""Path: tests/test_system/test_gen_desk_mgr/test_gen_desk_backup.py

End-to-end integration and CLI test suite for gen_desk_backup.

Operational Role:
    Validates CLI parsing, auto-backup dispatching, audits (-A),
    single-file backup, single-file restoration (-r), directory backups,
    dry-run simulation, batch restore (-R), and exit codes without warnings.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

from system.gen_desk_mgr.gen_desk_backup import main

__version__ = "1.0.0+build.9"

# ==============================================================================
# GROUP 1: CLI Invocations & Commands
# Note: Verification of main() flags, dispatching, and return codes
# ==============================================================================


@pytest.mark.integration
def test_main_audit_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() executes audit flag (-A) with table output."""
    arch = tmp_path / "archive" / "backups_gda" / "src" / "gda"
    arch.mkdir(parents=True)
    (arch / "missing.py.20261109_120000.bk").write_text("old", encoding="utf-8")

    cfg_file = tmp_path / "gen_desk_config.toml"
    cfg_file.write_text(
        f"""
[workspace]
root = "{tmp_path.as_posix()}"
archive_dir = "archive"
logs_dir = "logs"
[logging]
log_file = "logs/backup.log"
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        ["gen_desk_backup", "-A", "--config", str(cfg_file)],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


@pytest.mark.integration
def test_main_single_restore_cli_success_and_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify main() executes single-file restore flag (-r) on success and failure."""
    arch = tmp_path / "archive" / "backups_gda"
    arch.mkdir(parents=True)
    (arch / "atom.py.20261108_120000.bk").write_text("restored atom", encoding="utf-8")

    cfg_file = tmp_path / "gen_desk_config.toml"
    cfg_file.write_text(
        f"""
[workspace]
root = "{tmp_path.as_posix()}"
archive_dir = "archive"
logs_dir = "logs"
[logging]
log_file = "logs/backup.log"
""",
        encoding="utf-8",
    )

    # Success
    monkeypatch.setattr(
        "sys.argv",
        ["gen_desk_backup", "-r", "src/gda/atom.py", "--config", str(cfg_file)],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    assert (tmp_path / "src" / "gda" / "atom.py").read_text(encoding="utf-8") == "restored atom"

    # Failure (unavailable)
    monkeypatch.setattr(
        "sys.argv",
        ["gen_desk_backup", "-r", "src/gda/missing.py", "--config", str(cfg_file)],
    )
    with pytest.raises(SystemExit) as exc_fail:
        main()
    assert exc_fail.value.code == 1


@pytest.mark.integration
def test_main_auto_backup_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() executes auto-backup flag cleanly."""
    src_file = tmp_path / "src" / "gda" / "test.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("code", encoding="utf-8")

    cfg_file = tmp_path / "gen_desk_config.toml"
    cfg_file.write_text(
        f"""
[workspace]
root = "{tmp_path.as_posix()}"
archive_dir = "archive"
logs_dir = "logs"
[logging]
log_file = "logs/backup.log"
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        ["gen_desk_backup", "-a", "--config", str(cfg_file)],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    assert (tmp_path / "archive" / "backups_gda" / "src" / "gda").is_dir()


@pytest.mark.integration
def test_main_single_file_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() executes single-file target backup."""
    src_file = tmp_path / "src" / "gda" / "sample.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("sample", encoding="utf-8")

    cfg_file = tmp_path / "gen_desk_config.toml"
    cfg_file.write_text(
        f"""
[workspace]
root = "{tmp_path.as_posix()}"
archive_dir = "archive"
logs_dir = "logs"
[logging]
log_file = "logs/backup.log"
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        ["gen_desk_backup", str(src_file), "--config", str(cfg_file)],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


@pytest.mark.integration
def test_main_single_file_outside_domain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() reports when file target is outside protected domain."""
    outside_file = tmp_path / "docs" / "sample.txt"
    outside_file.parent.mkdir(parents=True)
    outside_file.write_text("text", encoding="utf-8")

    cfg_file = tmp_path / "gen_desk_config.toml"
    cfg_file.write_text(
        f'[workspace]\nroot = "{tmp_path.as_posix()}"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        ["gen_desk_backup", str(outside_file), "--config", str(cfg_file)],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


@pytest.mark.integration
def test_main_directory_non_recursive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() executes directory backup with --no-recursive flag."""
    src_dir = tmp_path / "src" / "gda"
    src_dir.mkdir(parents=True)
    (src_dir / "mod.py").write_text("code", encoding="utf-8")

    cfg_file = tmp_path / "gen_desk_config.toml"
    cfg_file.write_text(
        f'[workspace]\nroot = "{tmp_path.as_posix()}"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        ["gen_desk_backup", str(src_dir), "--no-recursive", "--config", str(cfg_file)],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


@pytest.mark.integration
def test_main_prune_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() executes retention pruning flag cleanly."""
    arch = tmp_path / "archive"
    arch.mkdir(parents=True)
    (arch / "old.py.20250101_120000.bk").write_text("old", encoding="utf-8")

    cfg_file = tmp_path / "gen_desk_config.toml"
    cfg_file.write_text(
        f"""
[workspace]
root = "{tmp_path.as_posix()}"
archive_dir = "archive"
[retention]
max_versions = 0
max_age_days = 30
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        ["gen_desk_backup", "-p", "--config", str(cfg_file)],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


@pytest.mark.integration
def test_main_restore_list_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() executes -R / --restore-list manifest restore."""
    arch = tmp_path / "archive" / "backups_gda"
    arch.mkdir(parents=True)
    (arch / "target.py.20261108_120000.bk").write_text("restored payload", encoding="utf-8")

    manifest = tmp_path / "restore_manifest.txt"
    manifest.write_text("src/gda/target.py\n", encoding="utf-8")

    cfg_file = tmp_path / "gen_desk_config.toml"
    cfg_file.write_text(
        f"""
[workspace]
root = "{tmp_path.as_posix()}"
archive_dir = "archive"
logs_dir = "logs"
[logging]
log_file = "logs/backup.log"
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        ["gen_desk_backup", "-R", str(manifest), "--config", str(cfg_file)],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    assert (tmp_path / "src" / "gda" / "target.py").read_text(
        encoding="utf-8"
    ) == "restored payload"


@pytest.mark.integration
def test_main_restore_list_missing_manifest_exits_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify main() exits 1 when restore manifest does not exist."""
    cfg_file = tmp_path / "gen_desk_config.toml"
    cfg_file.write_text(
        f'[workspace]\nroot = "{tmp_path.as_posix()}"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        ["gen_desk_backup", "-R", "/nonexistent/manifest.txt", "--config", str(cfg_file)],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


@pytest.mark.unit
def test_main_no_action_shows_help(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() prints help and exits 0 when no flags are supplied."""
    monkeypatch.setattr("sys.argv", ["gen_desk_backup"])
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 0


@pytest.mark.regression
def test_main_invalid_target_exits_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() exits 1 on non-existent target."""
    monkeypatch.setattr(
        "sys.argv",
        ["gen_desk_backup", "/invalid/path/to/file.py"],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


# ==============================================================================
# GROUP 2: Main Entrypoint (__name__ == "__main__")
# Note: Verification of main entrypoint execution
# ==============================================================================


@pytest.mark.unit
def test_gen_desk_backup_module_runpy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify script execution under runpy as __main__."""
    monkeypatch.setattr("sys.argv", ["gen_desk_backup", "-h"])
    monkeypatch.delitem(sys.modules, "system.gen_desk_mgr.gen_desk_backup", raising=False)
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("system.gen_desk_mgr.gen_desk_backup", run_name="__main__")
    assert exc.value.code == 0
