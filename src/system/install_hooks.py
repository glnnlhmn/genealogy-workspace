"""Path: src/system/install_hooks.py

Genealogy Workspace Git Hooks Installer.

Operational Role:
    Installs the staged-file aware pre-commit hook from src/system/hooks/
    into .git/hooks/pre-commit, configures executable permissions, and validates
    repository Git hook topology.
"""

from __future__ import annotations

import argparse
import stat
import sys
from pathlib import Path

__version__ = "1.0.0+build.r2"

HOOK_WRAPPER_POSIX = """#!/usr/bin/env bash
# Auto-generated wrapper for Python pre-commit hook
python src/system/hooks/pre_commit.py "$@"
"""


def get_repo_root() -> Path:
    """Locate the git repository root relative to script execution.

    Returns:
        Path: Canonical workspace root directory.
    """
    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        if (parent / ".git").is_dir():
            return parent
    return Path.cwd().resolve()


def install_pre_commit_hook(repo_root: Path) -> bool:
    """Deploy the pre-commit hook script to .git/hooks/pre-commit.

    Args:
        repo_root: Canonical repository root directory.

    Returns:
        bool: True if installation succeeded; False otherwise.
    """
    git_dir = repo_root / ".git"
    if not git_dir.is_dir():
        print(
            f"Error: .git directory not found at {git_dir}. Is this a git repository?"
        )
        return False

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_file = hooks_dir / "pre-commit"
    hook_file.write_text(HOOK_WRAPPER_POSIX, encoding="utf-8")

    current_mode = hook_file.stat().st_mode
    hook_file.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(
        f"Pre-commit hook installed successfully at {hook_file.relative_to(repo_root)}"
    )
    return True


def main(argv: list[str] | None = None) -> None:
    """Run hook installation command-line interface.

    Args:
        argv: Optional argument overrides.
    """
    parser = argparse.ArgumentParser(
        prog="install_hooks",
        description="Deploy Git verification hooks into repository .git/hooks/",
    )
    parser.parse_args(argv)

    root = get_repo_root()
    success = install_pre_commit_hook(root)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
