"""Path: src/system/gen_desk_mgr/gen_desk_backup.py

Main operational CLI manager for digital archive backups, audits, and restorations.

Operational Role:
    Provides automated Safe Backup generation, workspace audits (-A / --audit),
    retention pruning (-p / --prune), single file restoration (-r / --restore),
    and batch restoration from text manifests (-R / --restore-list).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from system.gen_desk_mgr.gd_backup_tools.auditor import (
    audit_workspace,
    format_full_audit_report,
)
from system.gen_desk_mgr.gd_backup_tools.config import load_config, resolve_workspace_root
from system.gen_desk_mgr.gd_backup_tools.engine import (
    backup_folder,
    create_single_backup,
    run_auto_backup,
)
from system.gen_desk_mgr.gd_backup_tools.pruner import execute_prune
from system.gen_desk_mgr.gd_backup_tools.restorer import (
    restore_batch_from_list,
    restore_file_entry,
)

__version__ = "1.0.0+build.5"


def setup_logger(root_dir: Path, log_file_rel: str) -> logging.Logger:
    """Initialize structured append logger."""
    log_path = root_dir / Path(log_file_rel)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("gen_desk_backup")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(handler)
    return logger


def main(argv: list[str] | None = None) -> None:
    """CLI orchestrator for backup, audit, pruning, and restoration operations."""
    parser = argparse.ArgumentParser(
        prog="gen_desk_backup",
        description="GenDesk Backup Manager: Safe Backups, 4-Section Audits, Pruning, and Restoration",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Target file or directory path to back up (e.g., src/gda/core/config.py)",
    )
    parser.add_argument(
        "-a",
        "--auto",
        action="store_true",
        help="Execute automated backup of all protected code domains lacking current snapshots",
    )
    parser.add_argument(
        "-A",
        "--audit",
        action="store_true",
        help="Execute 4-section audit report (BACKUP NEWER, NO BACKUP, BACK OKAY, NO ORIGIN)",
    )
    parser.add_argument(
        "-p",
        "--prune",
        action="store_true",
        help="Execute retention pruning of old backup snapshots violating version/age rules",
    )
    parser.add_argument(
        "-r",
        "--restore",
        type=str,
        default=None,
        help="Restore a single file from its newest archive Safe Backup or Git HEAD",
    )
    parser.add_argument(
        "-R",
        "--restore-list",
        type=Path,
        default=None,
        help="Path to a text file containing line-delimited relative file paths to restore",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="For directory targets, back up only immediate files (non-recursive)",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Simulate operations without writing or deleting snapshots on disk",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to custom gen_desk_config.toml configuration file",
    )

    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    root = resolve_workspace_root(cfg)
    log_rel = cfg.get("logging", {}).get("log_file", "logs/gen_desk_backup.log")
    logger = setup_logger(root, log_rel)

    actions_executed = 0

    if args.audit:
        actions_executed += 1
        partitioned = audit_workspace(root, cfg, target_rel_path=args.target)
        print(format_full_audit_report(partitioned))

    if args.auto:
        actions_executed += 1
        results = run_auto_backup(root, cfg, logger=logger, dry_run=args.dry_run)
        mode_str = "[DRY-RUN] " if args.dry_run else ""
        print(f"{mode_str}Auto-backup completed: {len(results)} files processed.")

    if args.restore:
        actions_executed += 1
        ok, msg = restore_file_entry(args.restore, root, cfg, logger=logger, dry_run=args.dry_run)
        print(msg)
        if not ok:
            sys.exit(1)

    if args.restore_list:
        actions_executed += 1
        manifest = (
            args.restore_list if args.restore_list.is_absolute() else (root / args.restore_list)
        )
        if not manifest.is_file():
            print(f"Error: Restore manifest not found: {args.restore_list}", file=sys.stderr)
            sys.exit(1)

        succ, fail, msgs = restore_batch_from_list(
            manifest, root, cfg, logger=logger, dry_run=args.dry_run
        )
        mode_str = "[DRY-RUN] " if args.dry_run else ""
        for m in msgs:
            print(f"  {m}")
        print(f"{mode_str}Restoration completed: {succ} restored, {fail} failed/unavailable.")

    if args.prune:
        actions_executed += 1
        archive_root = root / cfg.get("workspace", {}).get("archive_dir", "archive")
        pruned = execute_prune(archive_root, cfg, logger=logger, dry_run=args.dry_run)
        mode_str = "[DRY-RUN] " if args.dry_run else ""
        print(f"{mode_str}Retention prune completed: {len(pruned)} snapshots purged.")

    if args.target and not args.audit:
        actions_executed += 1
        target_path = Path(args.target)
        resolved_target = target_path if target_path.is_absolute() else (root / target_path)

        if resolved_target.is_file():
            bk = create_single_backup(
                resolved_target, root, cfg, logger=logger, dry_run=args.dry_run
            )
            if bk:
                print(f"Backed up file: {bk.relative_to(root).as_posix()}")
            else:
                print(f"Target not eligible or outside protected code domains: {args.target}")
        elif resolved_target.is_dir():
            bks = backup_folder(
                resolved_target,
                root,
                cfg,
                recursive=not args.no_recursive,
                logger=logger,
                dry_run=args.dry_run,
            )
            print(f"Backed up directory: {len(bks)} files preserved.")
        else:
            print(f"Error: Target path does not exist: {args.target}", file=sys.stderr)
            sys.exit(1)

    if actions_executed == 0:
        parser.print_help()
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
