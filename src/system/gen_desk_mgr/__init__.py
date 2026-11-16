"""Path: src/system/gen_desk_mgr/__init__.py

GenDesk Backup Manager facade package.

Operational Role:
    Unifies top-level management interfaces, configuration, execution hooks,
    audits, single-file restoration, and batch restoration capabilities.
"""

from __future__ import annotations

from system.gen_desk_mgr.gd_backup_tools.auditor import (
    AuditRecord,
    AuditStatus,
    NewerBackupRecord,
    audit_workspace,
    find_newer_backups,
    format_audit_table,
    format_full_audit_report,
    format_section_table,
)
from system.gen_desk_mgr.gd_backup_tools.config import load_config, resolve_workspace_root
from system.gen_desk_mgr.gd_backup_tools.engine import (
    backup_folder,
    create_single_backup,
    run_auto_backup,
)
from system.gen_desk_mgr.gd_backup_tools.pruner import execute_prune, find_prune_candidates
from system.gen_desk_mgr.gd_backup_tools.restorer import (
    parse_restore_list,
    restore_batch_from_list,
    restore_file_entry,
)
from system.gen_desk_mgr.gen_desk_backup import main

__version__ = "1.0.0+build.5"

__all__ = [
    "AuditRecord",
    "AuditStatus",
    "NewerBackupRecord",
    "audit_workspace",
    "backup_folder",
    "create_single_backup",
    "execute_prune",
    "find_newer_backups",
    "find_prune_candidates",
    "format_audit_table",
    "format_full_audit_report",
    "format_section_table",
    "load_config",
    "main",
    "parse_restore_list",
    "resolve_workspace_root",
    "restore_batch_from_list",
    "restore_file_entry",
    "run_auto_backup",
]
