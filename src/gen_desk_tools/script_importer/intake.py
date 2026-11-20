"""Path: src/gen_desk_tools/script_importer/intake.py

Hermetic file intake orchestrator for GenDesk Script Importer (gsi).

Operational Role:
    Scans the configured download/ staging directory, parses routing headers,
    enforces mandatory Safe Backups on configured protected domains, prompts
    before overwriting unprotected files unless --force is active, and moves
    staged files to their canonical workspace destinations.

Functions:
    run_intake: Execute the end-to-end staging and relocation workflow.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from gen_desk_tools.core.backup import create_safe_backup, is_protected_domain
from gen_desk_tools.core.cli import prompt_yes_no
from gen_desk_tools.core.config import load_gdt_config
from gen_desk_tools.core.logging import setup_tool_logger
from gen_desk_tools.core.workspace import resolve_workspace_root, to_posix_rel
from gen_desk_tools.script_importer.headers import parse_metadata_header

__version__ = "1.0.0+build.3"

__all__ = [
    "run_intake",
]


def _handle_unparseable_candidate(
    candidate: Path,
    download_dir_name: str,
    *,
    clean: bool,
    force: bool,
    logger: logging.Logger,
) -> None:
    """Skip or purge a staged file lacking valid routing headers."""
    if not clean:
        logger.info("Skipping %s: Missing valid metadata headers.", candidate.name)
        print(f"Skipping {candidate.name}: Missing valid metadata headers.")
        return

    confirmed = force or prompt_yes_no(
        f"Delete unparseable file '{candidate.name}' from {download_dir_name}/?"
    )
    if confirmed:
        candidate.unlink(missing_ok=True)
        logger.info("PURGED: %s", candidate.name)
        print(f"Purged: {candidate.name}")


def _relocate_candidate(
    candidate: Path,
    dest_path: Path,
    root_dir: Path,
    cfg: dict[str, Any],
    *,
    force: bool,
    logger: logging.Logger,
) -> str | None:
    """Apply Safe Backup / overwrite policy and move candidate to dest_path."""
    if dest_path.is_file():
        if is_protected_domain(dest_path, root_dir, cfg):
            # Protected domains always receive a Safe Backup, even under --force
            create_safe_backup(dest_path, root_dir, cfg, logger=logger)
        elif not force:
            if not prompt_yes_no(f"Overwrite destination '{dest_path.name}'?"):
                logger.info("Skipped relocation: %s", candidate.name)
                print(f"Skipped relocation: {candidate.name}")
                return None

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(candidate), str(dest_path))
    rel_dest = to_posix_rel(dest_path, root_dir)
    logger.info("FILE_CREATED: %s", rel_dest)
    return rel_dest


def _process_candidates(
    candidates: list[Path],
    resolved_root: Path,
    cfg: dict[str, Any],
    download_dir_name: str,
    *,
    force: bool,
    clean: bool,
    logger: logging.Logger,
) -> list[str]:
    """Parse, validate, and relocate all staged candidate files."""
    moved_files: list[str] = []
    for candidate in candidates:
        target_name, dest_path = parse_metadata_header(candidate, resolved_root)
        if not target_name or not dest_path:
            _handle_unparseable_candidate(
                candidate, download_dir_name, clean=clean, force=force, logger=logger
            )
            continue

        rel_dest = _relocate_candidate(
            candidate, dest_path, resolved_root, cfg, force=force, logger=logger
        )
        if rel_dest is not None:
            moved_files.append(rel_dest)
    return moved_files


def run_intake(
    *,
    force: bool = False,
    clean: bool = False,
    verbose: bool = False,
    debug: bool = False,
    root_dir: Path | None = None,
    config_path: Path | None = None,
) -> int:
    """Execute the script importer intake pipeline against download/ and return a POSIX exit code.

    Args:
        force: Bypass interactive overwrite and clean prompts (never bypasses protected backups).
        clean: Prompt to delete unparseable staged files from download/.
    """
    # --- Resolve Workspace, Config & Logger ---
    try:
        resolved_root = resolve_workspace_root(cfg_root=root_dir)
        cfg = load_gdt_config(root_dir=resolved_root, config_path=config_path)
    except Exception as exc:
        print(f"[ERROR] Failed to load GDT configuration: {exc}")
        return 1

    logger = setup_tool_logger("gsi", resolved_root, cfg, verbose=verbose, debug=debug)
    download_dir_name = str(cfg.get("workspace", {}).get("download_dir", "download"))
    download_dir = resolved_root / download_dir_name

    if not download_dir.is_dir():
        logger.error("Download directory not found at %s", download_dir)
        print(f"Error: Download directory not found at {download_dir}")
        return 1

    # --- Discover & Process Staged Candidates ---
    candidates = sorted(
        item for item in download_dir.iterdir() if item.is_file() and not item.name.startswith(".")
    )
    if not candidates:
        print(f"No intake candidates found in {download_dir_name}/.")
        return 0

    moved_files = _process_candidates(
        candidates,
        resolved_root,
        cfg,
        download_dir_name,
        force=force,
        clean=clean,
        logger=logger,
    )

    # --- Report Summary ---
    if moved_files:
        print("Intake completed successfully. Relocated files:")
        for moved in moved_files:
            print(f"  -> {moved}")
    else:
        print("No files were relocated.")

    return 0
