"""Path: src/gen_desk_tools/menu.py

Layered interactive console menu for GenDesk Tools (gd-menu).

Operational Role:
    Provides a standard-library, crash-proof, layered menu (at most 8 options
    per screen) allowing operators to configure session options once (target
    mode, include tests, reports directory, verbose/debug logging, force mode)
    and invoke any GenDesk Tools utility in-process with consistent logging
    and debug flag propagation.

Classes:
    MenuSession: Mutable session state shared across all menu actions.

Functions:
    build_parser: Construct the ArgumentParser for gd-menu.
    run_menu: Execute the interactive layered menu loop.
    main: Parse CLI arguments and launch the menu.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_desk_tools.backup_mgr import cli as backup_cli
from gen_desk_tools.core.cli import add_common_args, prompt_int_default
from gen_desk_tools.core.config import load_gdt_config
from gen_desk_tools.core.logging import setup_tool_logger
from gen_desk_tools.core.workspace import MODE_TARGETS, resolve_workspace_root
from gen_desk_tools.coverage_gaps import cli as gaps_cli
from gen_desk_tools.metrics import cli as metrics_cli
from gen_desk_tools.radon_report import cli as radon_cli
from gen_desk_tools.readme_gen import cli as readme_cli
from gen_desk_tools.script_importer import cli as gsi_cli
from gen_desk_tools.structure import cli as structure_cli

__version__ = "1.0.0+build.2"

__all__ = [
    "MenuSession",
    "build_parser",
    "main",
    "run_menu",
]

VALID_MODES: tuple[str, ...] = tuple(sorted([*MODE_TARGETS, "all"]))

_STRUCT_MODE_FLAGS: dict[str, str] = {
    "gda": "--gd",
    "ancestry_desk": "--ancestry-desk",
    "gd_tools": "--gd-tools",
    "system": "--system",
    "cli": "--cli",
    "src": "--src",
    "all": "--all",
}


@dataclass
class MenuSession:
    """Mutable session state inherited by every tool invoked from the menu."""

    root: Path
    config_path: Path | None = None
    mode: str = "gd_tools"
    include_tests: bool = False
    reports_dir: Path = Path("reports")
    verbose: bool = False
    debug: bool = False
    force: bool = False
    prompts: bool = True

    def common_argv(self) -> list[str]:
        """Build common CLI flags propagating root, config, verbose, debug, and prompts."""
        argv: list[str] = ["--root", str(self.root)]
        if self.config_path is not None:
            argv.extend(["--config", str(self.config_path)])
        if self.verbose:
            argv.append("--verbose")
        if self.debug:
            argv.append("--debug")
        if self.prompts:
            argv.append("--prompts")
        return argv

    def status_banner(self) -> str:
        """Return a single-line summary of active session configuration."""
        tests_str = "ON" if self.include_tests else "OFF"
        dbg_str = "ON" if self.debug else "OFF"
        verb_str = "ON" if self.verbose else "OFF"
        return (
            f"Mode: {self.mode} | Tests: {tests_str} | Reports: {self.reports_dir} "
            f"| Verbose: {verb_str} | Debug: {dbg_str}"
        )


def _safe_input(prompt: str) -> str | None:
    """Read a line from stdin, returning None cleanly on EOF or Ctrl+C."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("")
        return None


def _dispatch_cli(
    tool_name: str,
    main_fn: Callable[[list[str] | None], Any],
    argv: list[str],
    logger: logging.Logger,
) -> int:
    """Invoke a GDT tool CLI main(argv) in-process, catching all errors cleanly."""
    logger.debug("Dispatching %s with argv=%s", tool_name, argv)
    try:
        result = main_fn(argv)
        code = int(result) if isinstance(result, int) else 0
        if code != 0:
            print(f"[ERROR] {tool_name} exited with status {code}.")
        return code
    except SystemExit as exc:
        if exc.code is None:
            return 0
        code = int(exc.code) if isinstance(exc.code, int) else 1
        if code != 0:
            print(f"[ERROR] {tool_name} exited with status {code}.")
        return code
    except Exception as exc:
        logger.exception("Unhandled error while running %s", tool_name)
        print(f"[ERROR] {tool_name} failed: {exc}")
        return 1


def _run_coverage_gaps_prompted(session: MenuSession, logger: logging.Logger) -> None:
    """Prompt for file path, start line, and line count (default 20), then run gd-gaps."""
    file_path = _safe_input("Target file path (blank to cancel): ")
    if not file_path:
        print("Cancelled.")
        return

    candidate = Path(file_path)
    resolved = candidate if candidate.is_absolute() else (session.root / candidate)
    if not resolved.is_file():
        print(f"[ERROR] File not found: {file_path}")
        return

    start = prompt_int_default("Start line", 1, minimum=1)
    count = prompt_int_default("Number of lines", 20, minimum=1)
    gap_spec = f"{start}-{start + count - 1}"

    argv = [
        *session.common_argv(),
        file_path,
        gap_spec,
        "-o",
        str(session.reports_dir),
    ]
    _dispatch_cli("gd-gaps", gaps_cli.main, argv, logger)


def _menu_quality(session: MenuSession, logger: logging.Logger) -> None:
    """Layer 2A: Code Quality & Reports submenu (6 options)."""
    while True:
        print(f"\n--- Code Quality & Reports ({session.status_banner()}) ---")
        print("  1. Run Combined Radon Report (gdradon)")
        print("  2. Run Radon Grade C+ Hotspots Only (gdradon -n C)")
        print("  3. Run Directory Structure Report (gd-struct)")
        print("  4. Extract Coverage Gaps (gd-gaps)")
        print("  5. Run Full Metrics Pipeline (gd-metrics)")
        print("  0. Back")
        choice = _safe_input("Select [0-5]: ")
        if choice in (None, "0"):
            return
        if choice in ("1", "2"):
            argv = [
                *session.common_argv(),
                "-m",
                session.mode,
                "--reports-dir",
                str(session.reports_dir),
            ]
            if session.include_tests:
                argv.append("-t")
            if choice == "2":
                argv.extend(["-n", "C"])
            _dispatch_cli("gdradon", radon_cli.main, argv, logger)
        elif choice == "3":
            flag = _STRUCT_MODE_FLAGS.get(session.mode, "--gd-tools")
            argv = [*session.common_argv(), flag, "--reports-dir", str(session.reports_dir)]
            if session.include_tests:
                argv.append("-t")
            _dispatch_cli("gd-struct", structure_cli.main, argv, logger)
        elif choice == "4":
            _run_coverage_gaps_prompted(session, logger)
        elif choice == "5":
            _dispatch_cli("gd-metrics", metrics_cli.main, [*session.common_argv()], logger)
        else:
            print(f"[ERROR] Invalid selection: '{choice}'. Choose 0-5.")


def _menu_intake_docs(session: MenuSession, logger: logging.Logger) -> None:
    """Layer 2B: File Intake & Documentation submenu (5 options)."""
    while True:
        print(f"\n--- File Intake & Docs ({session.status_banner()}) ---")
        print("  1. Run Script Importer (gsi)")
        print("  2. Run Script Importer + Clean Unparseable (gsi --clean)")
        print("  3. Regenerate Package READMEs (gdrm)")
        print("  4. Force Regenerate READMEs (gdrm -f)")
        print("  0. Back")
        choice = _safe_input("Select [0-4]: ")
        if choice in (None, "0"):
            return
        if choice in ("1", "2"):
            argv = [*session.common_argv()]
            if choice == "2":
                argv.append("--clean")
            _dispatch_cli("gsi", gsi_cli.main, argv, logger)
        elif choice in ("3", "4"):
            target_alias = "gdt" if session.mode == "gd_tools" else session.mode
            argv = [*session.common_argv(), "-t", target_alias]
            if choice == "4" or session.force:
                argv.append("-f")
            _dispatch_cli("gdrm", readme_cli.main, argv, logger)
        else:
            print(f"[ERROR] Invalid selection: '{choice}'. Choose 0-4.")


def _menu_backup(session: MenuSession, logger: logging.Logger) -> None:
    """Layer 2C: Backup Manager submenu (6 options)."""
    while True:
        print(f"\n--- Backup Manager (gdb) ({session.status_banner()}) ---")
        print("  1. Backup Status Audit (gdb -s)")
        print("  2. Auto-Backup Untracked Protected Files (gdb -a)")
        print("  3. Backup Specific File or Folder")
        print("  4. Prune Old Snapshots (gdb -p)")
        print("  5. Restore Single File (gdb -r)")
        print("  0. Back")
        choice = _safe_input("Select [0-5]: ")
        if choice in (None, "0"):
            return
        if choice == "1":
            _dispatch_cli("gdb", backup_cli.main, [*session.common_argv(), "-s"], logger)
        elif choice == "2":
            _dispatch_cli("gdb", backup_cli.main, [*session.common_argv(), "-a"], logger)
        elif choice == "3":
            target = _safe_input("File or folder to back up (blank to cancel): ")
            if not target:
                print("Cancelled.")
                continue
            resolved = Path(target) if Path(target).is_absolute() else (session.root / target)
            if not resolved.exists():
                print(f"[ERROR] Target path not found: {target}")
                continue
            _dispatch_cli("gdb", backup_cli.main, [*session.common_argv(), target], logger)
        elif choice == "4":
            _dispatch_cli("gdb", backup_cli.main, [*session.common_argv(), "-p"], logger)
        elif choice == "5":
            target = _safe_input("Relative path to restore (blank to cancel): ")
            if not target:
                print("Cancelled.")
                continue
            _dispatch_cli("gdb", backup_cli.main, [*session.common_argv(), "-r", target], logger)
        else:
            print(f"[ERROR] Invalid selection: '{choice}'. Choose 0-5.")


def _menu_configure(
    session: MenuSession,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> logging.Logger:
    """Layer 2D: Configure Session Options submenu (7 options)."""
    while True:
        print("\n--- Configure Session Options ---")
        print(f"  1. Target Mode        [{session.mode}]")
        print(f"  2. Include Tests      [{'ON' if session.include_tests else 'OFF'}]")
        print(f"  3. Reports Directory  [{session.reports_dir}]")
        print(f"  4. Verbose Output     [{'ON' if session.verbose else 'OFF'}]")
        print(f"  5. Debug Logging      [{'ON' if session.debug else 'OFF'}]")
        print(f"  6. Force Mode         [{'ON' if session.force else 'OFF'}]")
        print("  0. Back")
        choice = _safe_input("Select [0-6]: ")
        if choice in (None, "0"):
            return logger
        if choice == "1":
            print(f"Available modes: {', '.join(VALID_MODES)}")
            new_mode = _safe_input(f"Enter mode [{session.mode}]: ")
            if new_mode and new_mode in VALID_MODES:
                session.mode = new_mode
            elif new_mode:
                print(f"[ERROR] Invalid mode: '{new_mode}'.")
        elif choice == "2":
            session.include_tests = not session.include_tests
        elif choice == "3":
            new_dir = _safe_input(f"Reports directory [{session.reports_dir}]: ")
            if new_dir:
                session.reports_dir = Path(new_dir)
        elif choice == "4":
            session.verbose = not session.verbose
            logger = setup_tool_logger(
                "gd-menu", session.root, cfg, verbose=session.verbose, debug=session.debug
            )
        elif choice == "5":
            session.debug = not session.debug
            logger = setup_tool_logger(
                "gd-menu", session.root, cfg, verbose=session.verbose, debug=session.debug
            )
        elif choice == "6":
            session.force = not session.force
        else:
            print(f"[ERROR] Invalid selection: '{choice}'. Choose 0-6.")


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the ArgumentParser for gd-menu."""
    parser = argparse.ArgumentParser(
        prog="gd-menu",
        description="GenDesk Tools Interactive Menu (gd-menu)",
    )
    add_common_args(parser)
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        default="gd_tools",
        choices=list(VALID_MODES),
        help="Initial target subsystem mode (default: gd_tools).",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=None,
        help="Initial reports directory override.",
    )
    return parser


def run_menu(args: argparse.Namespace) -> int:
    """Initialize session state, configure logging, and run the layered menu loop."""
    try:
        root = resolve_workspace_root(cfg_root=args.root)
        cfg = load_gdt_config(root_dir=root, config_path=args.config)
    except Exception as exc:
        print(f"[ERROR] Failed to load GDT configuration: {exc}")
        return 1

    reports_dir = (
        args.reports_dir
        if args.reports_dir is not None
        else Path(str(cfg.get("workspace", {}).get("reports_dir", "reports")))
    )
    session = MenuSession(
        root=root,
        config_path=args.config,
        mode=args.mode,
        reports_dir=reports_dir,
        verbose=bool(args.verbose),
        debug=bool(args.debug),
        prompts=True,
    )
    logger = setup_tool_logger("gd-menu", root, cfg, verbose=session.verbose, debug=session.debug)

    while True:
        print(f"\n=== GenDesk Tools ({session.status_banner()}) ===")
        print("  1. Code Quality & Reports")
        print("  2. File Intake & Docs")
        print("  3. Backup Manager (gdb)")
        print("  4. Configure Session Options")
        print("  5. Show Current Session")
        print("  0. Exit")
        choice = _safe_input("Select [0-5]: ")
        if choice in (None, "0"):
            print("Exiting GenDesk Tools.")
            return 0
        if choice == "1":
            _menu_quality(session, logger)
        elif choice == "2":
            _menu_intake_docs(session, logger)
        elif choice == "3":
            _menu_backup(session, logger)
        elif choice == "4":
            logger = _menu_configure(session, cfg, logger)
        elif choice == "5":
            print(f"Workspace Root: {session.root}")
            print(f"Active Config:  {session.status_banner()}")
        else:
            print(f"[ERROR] Invalid selection: '{choice}'. Choose 0-5.")


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments, launch the interactive menu, and exit cleanly."""
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_menu(args))
