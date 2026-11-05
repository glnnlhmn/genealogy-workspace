"""Path: src/system/install_hooks.py

Automated workstation onboarding and Git hook deployer.

Operational Role:
    Deploys POSIX-compliant pre-commit and pre-push shell wrappers into
    .git/hooks/ and sets executable bit permissions across developer environments.
"""

from __future__ import annotations

import argparse
import logging
import stat
import subprocess
import sys
from pathlib import Path

__version__ = "1.0.0+build.4"

ROOT_ANCHOR = Path("G:/My Drive/genealogy-workspace")
LOGGER = logging.getLogger("system.install_hooks")

HOOK_WRAPPER_POSIX = """#!/usr/bin/env sh
# Automated GDA pre-commit hook wrapper
python src/system/hooks/pre_commit.py
"""

HOOK_WRAPPER_PRE_PUSH = """#!/usr/bin/env sh
# Automated GDA pre-push hook wrapper
python src/system/hooks/pre_push.py
"""


def get_repo_root() -> Path:
    """Resolve and return the root directory of the current git repository.

    Returns:
        Path: Absolute path to the git workspace root.
    """
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(res.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        cur = Path.cwd().resolve()
        for parent in [cur, *cur.parents]:
            if (parent / ".git").is_dir():
                return parent
        return cur


def install_pre_commit_hook(repo_root: Path) -> bool:
    """Deploy pre-commit wrapper script to .git/hooks/pre-commit.

    Args:
        repo_root: Path to the target git repository root.

    Returns:
        bool: True if installation succeeded; False otherwise.
    """
    git_dir = repo_root / ".git"
    if not git_dir.is_dir():
        print(f"Error: .git directory not found in {repo_root}")
        return False

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hooks_dir / "pre-commit"

    try:
        hook_file.write_text(HOOK_WRAPPER_POSIX, encoding="utf-8")
        current_mode = hook_file.stat().st_mode
        hook_file.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"Pre-commit hook installed successfully at: {hook_file}")
        return True
    except OSError as exc:
        print(f"Error: Failed to write or configure pre-commit hook: {exc}")
        return False


def install_pre_push_hook(repo_root: Path) -> bool:
    """Deploy pre-push wrapper script to .git/hooks/pre-push.

    Args:
        repo_root: Path to the target git repository root.

    Returns:
        bool: True if installation succeeded; False otherwise.
    """
    git_dir = repo_root / ".git"
    if not git_dir.is_dir():
        print(f"Error: .git directory not found in {repo_root}")
        return False

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hooks_dir / "pre-push"

    try:
        hook_file.write_text(HOOK_WRAPPER_PRE_PUSH, encoding="utf-8")
        current_mode = hook_file.stat().st_mode
        hook_file.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"Pre-push hook installed successfully at: {hook_file}")
        return True
    except OSError as exc:
        print(f"Error: Failed to write or configure pre-push hook: {exc}")
        return False


def install_hooks(workspace_root: Path | None = None) -> list[Path]:
    """Deploy all Git hooks (pre-commit, pre-push) into the repository.

    Args:
        workspace_root: Canonical repository root path.

    Returns:
        list[Path]: List of successfully configured hook files.

    Raises:
        FileNotFoundError: If .git directory does not exist.
    """
    root = workspace_root or get_repo_root()
    if not (root / ".git").is_dir():
        raise FileNotFoundError(f"Git root not found at {root}")

    installed: list[Path] = []
    if install_pre_commit_hook(root):
        installed.append(root / ".git" / "hooks" / "pre-commit")
    if install_pre_push_hook(root):
        installed.append(root / ".git" / "hooks" / "pre-push")
    return installed


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint for hook installation.

    Args:
        argv: Optional command-line argument list.
    """
    parser = argparse.ArgumentParser(description="Install GDA Git hooks")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--debug", action="store_true", help="Enable diagnostic debug logging")
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if args.debug else (logging.INFO if args.verbose else logging.WARNING)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    root = get_repo_root()
    success_commit = install_pre_commit_hook(root)
    if not success_commit:
        sys.exit(1)

    success_push = install_pre_push_hook(root)
    if not success_push:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
