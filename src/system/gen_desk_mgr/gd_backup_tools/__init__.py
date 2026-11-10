"""Path: src/system/gen_desk_mgr/gd_backup_tools/__init__.py

GenDesk Backup Tools library facade.

Operational Role:
    Exposes core backup engine, 4-section audit engine, restoration engine,
    pruning functions, and configuration helpers.
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
    resolve_original_path,
)
from system.gen_desk_mgr.gd_backup_tools.config import (
    DEFAULT_CONFIG,
    load_config,
    resolve_workspace_root,
)
from system.gen_desk_mgr.gd_backup_tools.engine import (
    backup_folder,
    create_single_backup,
    is_in_code_domain,
    run_auto_backup,
)
from system.gen_desk_mgr.gd_backup_tools.pruner import (
    PruneCandidate,
    execute_prune,
    find_prune_candidates,
)
from system.gen_desk_mgr.gd_backup_tools.restorer import (
    BackupCandidate,
    parse_restore_list,
    restore_batch_from_list,
    restore_file_entry,
)

__version__ = "1.0.0+build.6"

__all__ = [
    "DEFAULT_CONFIG",
    "AuditRecord",
    "AuditStatus",
    "BackupCandidate",
    "NewerBackupRecord",
    "PruneCandidate",
    "audit_workspace",
    "backup_folder",
    "create_single_backup",
    "execute_prune",
    "find_newer_backups",
    "find_prune_candidates",
    "format_audit_table",
    "format_full_audit_report",
    "format_section_table",
    "is_in_code_domain",
    "load_config",
    "parse_restore_list",
    "resolve_original_path",
    "resolve_workspace_root",
    "restore_batch_from_list",
    "restore_file_entry",
    "run_auto_backup",
]
