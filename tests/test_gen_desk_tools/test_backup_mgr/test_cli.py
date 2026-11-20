"""Path: tests/test_gen_desk_tools/test_backup_mgr/test_cli.py

Unit, regression, and integration tests for gen_desk_tools.backup_mgr.cli and __main__.
"""

from __future__ import annotations

import importlib
import logging
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from gen_desk_tools.backup_mgr import cli

__version__ = "1.0.0+build.1"


def _close_gdb_logger() -> None:
    """Close and remove gdb logger handlers to prevent Windows tmp_path file locks."""
    logger = logging.getLogger("gdb")
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Parser construction and primary -s/--status and -a/--auto invocations.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_build_parser_parses_all_gdb_flags() -> None:
    """Verify build_parser registers target, -a, -s, -p, -r, -R, --no-recursive, and core flags."""
    parser = cli.build_parser()
    args = parser.parse_args(
        ["src/gda", "-a", "-s", "-p", "-r", "src/gda/a.py", "-R", "list.txt", "--no-recursive"]
    )

    assert args.target == "src/gda"
    assert args.auto is True
    assert args.status is True
    assert args.prune is True
    assert args.restore == "src/gda/a.py"
    assert args.restore_list == Path("list.txt")
    assert args.no_recursive is True


# ==========================================================================
# GROUP 2: Action Dispatching (Status, Auto, Prune, Target, Restore)
# Note: Exercises all run() action branches against isolated gdt_workspace.
# ==========================================================================


@pytest.mark.integration
def test_run_status_auto_prune_and_target_backups(gdt_workspace: Path) -> None:
    """Verify run() executes -s, -a, -p, directory backup, and single-file backup."""
    src_file = gdt_workspace / "src" / "gen_desk_tools" / "mod.py"
    src_file.write_text("x = 1\n", encoding="utf-8")
    parser = cli.build_parser()

    try:
        assert cli.run(parser.parse_args(["--root", str(gdt_workspace), "-s"])) == 0
        assert cli.run(parser.parse_args(["--root", str(gdt_workspace), "-a"])) == 0
        assert cli.run(parser.parse_args(["--root", str(gdt_workspace), "-p"])) == 0
        assert cli.run(parser.parse_args(["--root", str(gdt_workspace), "src/gen_desk_tools"])) == 0
        assert (
            cli.run(parser.parse_args(["--root", str(gdt_workspace), "src/gen_desk_tools/mod.py"]))
            == 0
        )
    finally:
        _close_gdb_logger()


@pytest.mark.integration
def test_run_restore_single_and_batch_success_and_failure(gdt_workspace: Path) -> None:
    """Verify -r and -R handle both successful restorations and error exits."""
    arch = gdt_workspace / "archive" / "backups_gen_desk_tools" / "src" / "gen_desk_tools"
    arch.mkdir(parents=True)
    (arch / "ok.py.20261119_120000.bk").write_text("ok", encoding="utf-8")

    ok_manifest = gdt_workspace / "ok_list.txt"
    ok_manifest.write_text("src/gen_desk_tools/ok.py\n", encoding="utf-8")
    bad_manifest = gdt_workspace / "bad_list.txt"
    bad_manifest.write_text("docs/nope.md\n", encoding="utf-8")
    parser = cli.build_parser()

    try:
        assert (
            cli.run(
                parser.parse_args(["--root", str(gdt_workspace), "-r", "src/gen_desk_tools/ok.py"])
            )
            == 0
        )
        assert cli.run(parser.parse_args(["--root", str(gdt_workspace), "-r", "docs/nope.md"])) == 1
        assert cli.run(parser.parse_args(["--root", str(gdt_workspace), "-R", "ok_list.txt"])) == 0
        assert (
            cli.run(parser.parse_args(["--root", str(gdt_workspace), "-R", str(bad_manifest)])) == 1
        )
        assert (
            cli.run(parser.parse_args(["--root", str(gdt_workspace), "-R", "missing_list.txt"]))
            == 1
        )
    finally:
        _close_gdb_logger()


# ==========================================================================
# GROUP 3: Error Branches, main(), & __main__ Shim
# Note: Config errors, missing/unprotected targets, no-action exit, and runpy.
# ==========================================================================


@pytest.mark.regression
def test_run_error_branches_and_no_action_return_one(gdt_workspace: Path) -> None:
    """Verify bad config, unprotected file, missing target, and no-action return 1."""
    outside = gdt_workspace / "docs" / "note.md"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text("# doc\n", encoding="utf-8")
    parser = cli.build_parser()

    try:
        assert (
            cli.run(
                parser.parse_args(
                    ["--root", str(gdt_workspace), "--config", str(gdt_workspace / "bad.toml")]
                )
            )
            == 1
        )
        assert cli.run(parser.parse_args(["--root", str(gdt_workspace), "docs/note.md"])) == 1
        assert cli.run(parser.parse_args(["--root", str(gdt_workspace), "src/missing.py"])) == 1
        assert cli.run(parser.parse_args(["--root", str(gdt_workspace)])) == 1
    finally:
        _close_gdb_logger()


@pytest.mark.unit
def test_main_and_package_main_module_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify cli.main() calls sys.exit(run(args)) and __main__ invokes cli.main()."""
    with patch.object(cli, "run", return_value=0):
        with pytest.raises(SystemExit) as exc_info:
            cli.main(["-s"])
        assert exc_info.value.code == 0

    called: list[bool] = []
    monkeypatch.setattr(cli, "main", lambda: called.append(True))

    importlib.import_module("gen_desk_tools.backup_mgr.__main__")
    assert called == []

    monkeypatch.delitem(sys.modules, "gen_desk_tools.backup_mgr.__main__", raising=False)
    runpy.run_module("gen_desk_tools.backup_mgr", run_name="__main__")
    assert called == [True]
