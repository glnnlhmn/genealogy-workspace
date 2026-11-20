"""Path: src/gen_desk_tools/backup_mgr/__init__.py

GenDesk Backup Manager package (gdb).

Operational Role:
    Re-exports Safe Backup creation, 4-section status auditing, retention
    pruning, single/batch restoration, and CLI entrypoints.
"""

from __future__ import annotations

from gen_desk_tools.backup_mgr.auditor import (
    AuditRecord,
    AuditStatus,
    audit_workspace,
    format_full_audit_report,
    format_section_table,
    resolve_original_path,
)
from gen_desk_tools.backup_mgr.cli import build_parser, main, run
from gen_desk_tools.backup_mgr.engine import (
    backup_folder,
    create_single_backup,
    parse_backup_filename,
    run_auto_backup,
)
from gen_desk_tools.backup_mgr.pruner import (
    PruneCandidate,
    execute_prune,
    find_prune_candidates,
)
from gen_desk_tools.backup_mgr.restorer import (
    BackupCandidate,
    find_latest_archive_backup,
    parse_restore_list,
    restore_batch_from_list,
    restore_file_entry,
    restore_from_git,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "AuditRecord",
    "AuditStatus",
    "BackupCandidate",
    "PruneCandidate",
    "audit_workspace",
    "backup_folder",
    "build_parser",
    "create_single_backup",
    "execute_prune",
    "find_latest_archive_backup",
    "find_prune_candidates",
    "format_full_audit_report",
    "format_section_table",
    "main",
    "parse_backup_filename",
    "parse_restore_list",
    "resolve_original_path",
    "restore_batch_from_list",
    "restore_file_entry",
    "restore_from_git",
    "run",
    "run_auto_backup",
]
