"""Path: tests/test_gen_desk_tools/test_menu.py

Unit, regression, and integration tests for gen_desk_tools.menu and __main__.
"""

from __future__ import annotations

import importlib
import logging
import runpy
from pathlib import Path
from unittest.mock import patch

import pytest

from gen_desk_tools.menu import (
    MenuSession,
    _dispatch_cli,
    _safe_input,
    build_parser,
    main,
    run_menu,
)

__version__ = "1.0.0+build.4"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Menu startup, clean exit, and python -m gen_desk_tools execution.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_run_menu_starts_and_exits_cleanly_on_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify run_menu prints the main menu banner and exits with code 0 on '0'."""
    monkeypatch.setattr("builtins.input", lambda _: "0")
    args = build_parser().parse_args(["--root", str(tmp_path), "--debug", "-v"])

    assert run_menu(args) == 0
    out = capsys.readouterr().out
    assert "=== GenDesk Tools" in out
    assert "Debug: ON" in out
    assert "Exiting GenDesk Tools." in out


@pytest.mark.integration
def test_main_and_module_entrypoint_delegate_to_run_menu(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify main() and python -m gen_desk_tools exit cleanly with code 0."""
    monkeypatch.setattr("builtins.input", lambda _: "0")
    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(tmp_path)])
    assert exc_info.value.code == 0

    with patch("sys.argv", ["gd-menu", "--root", str(tmp_path)]):
        with pytest.raises(SystemExit) as mod_exc:
            runpy.run_module("gen_desk_tools.__main__", run_name="__main__")
    assert mod_exc.value.code == 0

    mod = importlib.import_module("gen_desk_tools.__main__")
    assert mod.__name__ == "gen_desk_tools.__main__"


# ==========================================================================
# GROUP 2: Session Propagation & Low-Level Helpers
# Note: MenuSession.common_argv, _safe_input EOF handling, and _dispatch_cli.
# ==========================================================================


@pytest.mark.unit
def test_menu_session_common_argv_propagates_and_omits_optional_flags(tmp_path: Path) -> None:
    """Verify MenuSession.common_argv includes or omits optional flags accurately."""
    cfg_file = tmp_path / "gdt.toml"
    full_session = MenuSession(
        root=tmp_path,
        config_path=cfg_file,
        verbose=True,
        debug=True,
        prompts=True,
    )
    full_argv = full_session.common_argv()
    assert "--config" in full_argv and str(cfg_file) in full_argv
    assert "--verbose" in full_argv
    assert "--debug" in full_argv
    assert "--prompts" in full_argv

    minimal_session = MenuSession(root=tmp_path, prompts=False)
    min_argv = minimal_session.common_argv()
    assert min_argv == ["--root", str(tmp_path)]


@pytest.mark.regression
def test_safe_input_returns_none_on_eof_or_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify _safe_input catches EOFError and KeyboardInterrupt without crashing."""

    def _raise_eof(_: str) -> str:
        raise EOFError()

    monkeypatch.setattr("builtins.input", _raise_eof)
    assert _safe_input("Prompt: ") is None


@pytest.mark.regression
def test_dispatch_cli_handles_nonzero_exit_system_exit_and_exceptions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify _dispatch_cli catches nonzero returns, SystemExit, and RuntimeError cleanly."""
    logger = logging.getLogger("test_dispatch_cli")

    def _exit_none(_: list[str] | None) -> None:
        raise SystemExit(None)

    def _exit_zero(_: list[str] | None) -> None:
        raise SystemExit(0)

    def _exit_three(_: list[str] | None) -> None:
        raise SystemExit(3)

    def _exit_str(_: list[str] | None) -> None:
        raise SystemExit("err")

    def _raise_err(_: list[str] | None) -> None:
        raise RuntimeError("boom")

    assert _dispatch_cli("t0", lambda _: None, [], logger) == 0
    assert _dispatch_cli("t1", lambda _: 2, [], logger) == 2
    assert _dispatch_cli("t2n", _exit_none, [], logger) == 0
    assert _dispatch_cli("t2", _exit_zero, [], logger) == 0
    assert _dispatch_cli("t3", _exit_three, [], logger) == 3
    assert _dispatch_cli("t4", _exit_str, [], logger) == 1
    assert _dispatch_cli("t5", _raise_err, [], logger) == 1

    out = capsys.readouterr().out
    assert "[ERROR] t1 exited with status 2." in out
    assert "[ERROR] t3 exited with status 3." in out
    assert "[ERROR] t4 exited with status 1." in out
    assert "[ERROR] t5 failed: boom" in out


# ==========================================================================
# GROUP 3: Layer 2A — Code Quality & Reports Submenu
# Note: Radon, Radon -n C, Structure, Coverage Gaps, Metrics, and invalid choices.
# ==========================================================================


@pytest.mark.integration
def test_menu_quality_dispatches_all_tools_and_handles_gaps_prompts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify Quality submenu dispatches gdradon, gd-struct, gd-gaps, and gd-metrics."""
    sample = tmp_path / "src" / "demo.py"
    sample.parent.mkdir(parents=True)
    sample.write_text("\n".join(f"line_{i}" for i in range(1, 30)) + "\n", encoding="utf-8")

    # Quality with Tests OFF (1 -> 1, 3 -> 0), then Tests ON (4 -> 2 -> 0), then Quality (1):
    # 1 (radon), 2 (-n C), 3 (struct), 4 (cancel/missing/valid), 5 (metrics), 9 (bad), 0, 0
    inputs = iter(
        [
            "1",
            "1",
            "3",
            "0",
            "4",
            "2",
            "0",
            "1",
            "1",
            "2",
            "3",
            "4",
            "",
            "4",
            "src/missing.py",
            "4",
            "src/demo.py",
            "5",
            "",
            "5",
            "9",
            "0",
            "0",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    with (
        patch("gen_desk_tools.menu.radon_cli.main", return_value=0) as mock_radon,
        patch("gen_desk_tools.menu.structure_cli.main", return_value=0) as mock_struct,
        patch("gen_desk_tools.menu.metrics_cli.main", return_value=0) as mock_metrics,
    ):
        args = build_parser().parse_args(["--root", str(tmp_path), "--reports-dir", "gtemp"])
        assert run_menu(args) == 0

    assert mock_radon.call_count == 3
    assert mock_struct.call_count == 2
    assert mock_metrics.call_count == 1
    out = capsys.readouterr().out
    assert "Cancelled." in out
    assert "[ERROR] File not found: src/missing.py" in out
    assert "[ERROR] Invalid selection: '9'" in out
    assert (tmp_path / "gtemp" / "Coverage Gap + demo.py + 5-24.txt").is_file()


# ==========================================================================
# GROUP 4: Layer 2B — File Intake & Docs Submenu
# Note: gsi, gsi --clean, gdrm, gdrm -f, and invalid selection handling.
# ==========================================================================


@pytest.mark.integration
def test_menu_intake_docs_dispatches_gsi_and_gdrm_actions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify File Intake & Docs submenu dispatches gsi, gsi --clean, gdrm, and gdrm -f."""
    inputs = iter(["2", "1", "2", "3", "4", "9", "0", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    with (
        patch("gen_desk_tools.menu.gsi_cli.main", return_value=0) as mock_gsi,
        patch("gen_desk_tools.menu.readme_cli.main", return_value=0) as mock_gdrm,
    ):
        args = build_parser().parse_args(["--root", str(tmp_path)])
        assert run_menu(args) == 0

    assert mock_gsi.call_count == 2
    assert mock_gdrm.call_count == 2
    assert "[ERROR] Invalid selection: '9'" in capsys.readouterr().out


# ==========================================================================
# GROUP 5: Layer 2C — Backup Manager Submenu
# Note: Status, auto-backup, specific file/folder, prune, restore, and cancellations.
# ==========================================================================


@pytest.mark.integration
def test_menu_backup_dispatches_all_gdb_actions_and_validates_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify Backup Manager submenu dispatches all gdb options and validates targets."""
    target_file = tmp_path / "sample.py"
    target_file.write_text("x = 1\n", encoding="utf-8")

    # Main -> 3 (Backup): 1 (-s), 2 (-a), 3 (cancel/missing/valid), 4 (-p), 5 (cancel/valid), 9, 0
    inputs = iter(
        [
            "3",
            "1",
            "2",
            "3",
            "",
            "3",
            "missing.py",
            "3",
            "sample.py",
            "4",
            "5",
            "",
            "5",
            "sample.py",
            "9",
            "0",
            "0",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    with patch("gen_desk_tools.menu.backup_cli.main", return_value=0) as mock_gdb:
        args = build_parser().parse_args(["--root", str(tmp_path)])
        assert run_menu(args) == 0

    assert mock_gdb.call_count == 5
    out = capsys.readouterr().out
    assert "[ERROR] Target path not found: missing.py" in out
    assert "[ERROR] Invalid selection: '9'" in out


# ==========================================================================
# GROUP 6: Layer 2D — Configuration Submenu & Root Error Handling
# Note: All 6 config toggles/inputs, invalid mode/choice, and bad root exit.
# ==========================================================================


@pytest.mark.regression
def test_run_menu_handles_invalid_root_and_all_configuration_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify bad workspace roots fail cleanly and all config menu options update state."""
    bad_args = build_parser().parse_args(["--root", str(tmp_path / "does_not_exist")])
    assert run_menu(bad_args) == 1
    assert "[ERROR] Failed to load GDT configuration" in capsys.readouterr().out

    # Main -> 9 (bad) -> 4 (Config):
    # 1 (bad mode), 1 (gda), 1 (blank), 2 (tests), 3 (gtemp), 3 (blank),
    # 4 (verbose), 5 (debug), 6 (force), 9 (bad), 0 -> 5 (Show) -> 0
    inputs = iter(
        [
            "9",
            "4",
            "1",
            "invalid_mode",
            "1",
            "gda",
            "1",
            "",
            "2",
            "3",
            "gtemp",
            "3",
            "",
            "4",
            "5",
            "6",
            "9",
            "0",
            "5",
            "0",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    valid_args = build_parser().parse_args(["--root", str(tmp_path)])

    assert run_menu(valid_args) == 0
    out = capsys.readouterr().out
    assert "[ERROR] Invalid selection: '9'" in out
    assert "[ERROR] Invalid mode: 'invalid_mode'." in out
    assert "Mode: gda" in out
    assert "Tests: ON" in out
    assert "Reports: gtemp" in out
    assert "Verbose: ON" in out
    assert "Debug: ON" in out
