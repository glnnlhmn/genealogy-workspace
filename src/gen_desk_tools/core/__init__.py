"""Path: src/gen_desk_tools/core/__init__.py

Shared internal primitives for GenDesk Tools (workspace, config, backup, logging, CLI, process).

Operational Role:
    Re-exports the public core API so GenDesk Tools subpackages can import
    directly from gen_desk_tools.core without coupling to internal module names.
"""

from __future__ import annotations

from gen_desk_tools.core.backup import (
    atomic_copy,
    atomic_write_text,
    create_safe_backup,
    is_protected_domain,
    resolve_backup_dir,
)
from gen_desk_tools.core.cli import add_common_args, prompt_yes_no
from gen_desk_tools.core.config import DEFAULT_GDT_CONFIG, deep_merge, load_gdt_config
from gen_desk_tools.core.logging import setup_tool_logger
from gen_desk_tools.core.process import CommandResult, run_command
from gen_desk_tools.core.workspace import (
    MANDATORY_EXCLUSIONS,
    MODE_TARGETS,
    ensure_within_root,
    iter_workspace_files,
    resolve_report_path,
    resolve_workspace_root,
    to_posix_rel,
)

__version__ = "1.0.0+build.4"

__all__ = [
    "CommandResult",
    "DEFAULT_GDT_CONFIG",
    "MANDATORY_EXCLUSIONS",
    "MODE_TARGETS",
    "add_common_args",
    "atomic_copy",
    "atomic_write_text",
    "create_safe_backup",
    "deep_merge",
    "ensure_within_root",
    "is_protected_domain",
    "iter_workspace_files",
    "load_gdt_config",
    "prompt_yes_no",
    "resolve_backup_dir",
    "resolve_report_path",
    "resolve_workspace_root",
    "run_command",
    "setup_tool_logger",
    "to_posix_rel",
]
