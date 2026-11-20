"""Path: src/gen_desk_tools/backup_mgr/cli.py

Command-line interface entrypoint for GenDesk Backup Manager (gdb).

Operational Role:
    Registers shared gen_desk_tools.core CLI flags alongside target backup,
    -a/--auto, -s/--status (4-section audit), -p/--prune, -r/--restore,
    -R/--restore-list, and --no-recursive.

Functions:
    build_parser: Construct the ArgumentParser for gdb.
    run: Execute parsed gdb actions and return a POSIX exit code.
    main: Parse CLI arguments and exit with run()'s status code.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from gen_desk_tools.backup_mgr.auditor import audit_workspace, format_full_audit_report
from gen_desk_tools.backup_mgr.engine import (
    backup_folder,
    create_single_backup,
    run_auto_backup,
)
from gen_desk_tools.backup_mgr.pruner import execute_prune
from gen_desk_tools.backup_mgr.restorer import restore_batch_from_list, restore_file_entry
from gen_desk_tools.core.cli import add_common_args
from gen_desk_tools.core.config import load_gdt_config
from gen_desk_tools.core.logging import setup_tool_logger
from gen_desk_tools.core.workspace import resolve_workspace_root

__version__ = "1.0.0+build.2"

__all__ = [
    "build_parser",
    "main",
    "run",
]


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the ArgumentParser for gdb."""
    parser = argparse.ArgumentParser(
        prog="gdb",
        description="GenDesk Backup Manager (gdb) - Safe Backups, Status Audits, Pruning & Restore",
    )
    add_common_args(parser)
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Target file or directory to back up (also filters -s/--status output).",
    )
    parser.add_argument(
        "-a",
        "--auto",
        action="store_true",
        help="Back up all protected-domain files currently lacking an archive snapshot.",
    )
    parser.add_argument(
        "-s",
        "--status",
        action="store_true",
        help="Print 4-section backup status report (BACKUP NEWER, NO BACKUP, BACK OKAY, NO ORIGIN).",
    )
    parser.add_argument(
        "-p",
        "--prune",
        action="store_true",
        help="Prune old archive snapshots exceeding configured retention limits.",
    )
    parser.add_argument(
        "-r",
        "--restore",
        type=str,
        default=None,
        help="Restore a single protected file from its newest archive snapshot or Git HEAD.",
    )
    parser.add_argument(
        "-R",
        "--restore-list",
        type=Path,
        default=None,
        help="Batch-restore relative file paths listed in a plain-text manifest file.",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="For directory targets, back up immediate files only (non-recursive).",
    )
    return parser


def _handle_restore_list(
    restore_list: Path,
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> int:
    """Execute batch restoration from a manifest file and return a POSIX exit code."""
    manifest = restore_list if restore_list.is_absolute() else (root / restore_list)
    if not manifest.is_file():
        print(f"Error: Restore manifest not found: {restore_list}", file=sys.stderr)
        return 1
    succ, fail, msgs = restore_batch_from_list(manifest, root, cfg, logger=logger)
    for msg in msgs:
        print(f"  {msg}")
    print(f"Restoration completed: {succ} restored, {fail} failed.")
    return 1 if fail > 0 else 0


def _handle_target_backup(
    target_arg: str,
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    *,
    no_recursive: bool,
) -> int:
    """Back up a single file or directory target and return a POSIX exit code."""
    target_path = Path(target_arg)
    resolved_target = target_path if target_path.is_absolute() else (root / target_path)
    if resolved_target.is_dir():
        created = backup_folder(
            resolved_target, root, cfg, recursive=not no_recursive, logger=logger
        )
        print(f"Folder backup completed: {len(created)} snapshots created.")
        return 0
    if resolved_target.is_file():
        bk = create_single_backup(resolved_target, root, cfg, logger=logger)
        if bk is None:
            print(f"Skipped (outside protected domains): {target_arg}")
            return 1
        print(f"Backup created: {bk.relative_to(root).as_posix()}")
        return 0

    print(f"Error: Target not found: {target_arg}", file=sys.stderr)
    return 1


def run(args: argparse.Namespace) -> int:
    """Execute the requested gdb operations and return a POSIX exit code."""
    try:
        root = resolve_workspace_root(cfg_root=args.root)
        cfg = load_gdt_config(root_dir=root, config_path=args.config)
    except Exception as exc:
        print(f"[ERROR] Failed to load GDT configuration: {exc}")
        return 1

    logger = setup_tool_logger("gdb", root, cfg, verbose=args.verbose, debug=args.debug)
    actions_executed = 0

    if args.status:
        actions_executed += 1
        partitioned = audit_workspace(root, cfg, target_rel_path=args.target)
        print(format_full_audit_report(partitioned))

    if args.auto:
        actions_executed += 1
        results = run_auto_backup(root, cfg, logger=logger)
        print(f"Auto-backup completed: {len(results)} files processed.")

    if args.restore:
        actions_executed += 1
        ok, msg = restore_file_entry(args.restore, root, cfg, logger=logger)
        print(msg)
        if not ok:
            return 1

    if args.restore_list:
        actions_executed += 1
        if _handle_restore_list(args.restore_list, root, cfg, logger) != 0:
            return 1

    if args.prune:
        actions_executed += 1
        archive_root = root / str(cfg.get("workspace", {}).get("archive_dir", "archive"))
        pruned = execute_prune(archive_root, cfg, logger=logger)
        print(f"Prune completed: {len(pruned)} snapshots removed.")

    if args.target and not args.status:
        actions_executed += 1
        return _handle_target_backup(args.target, root, cfg, logger, no_recursive=args.no_recursive)

    if actions_executed == 0:
        print("No action specified. Run 'gdb --help' for usage.")
        return 1

    return 0


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments, execute gdb, and exit with its status code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run(args))
