"""Path: src/system/hooks/pre_push.py

Pre-push Git hook orchestrator enforcing branch protection and test passes.

Operational Role:
    Prevents direct pushes to protected branches (main, master, release) and executes
    pytest test verification prior to transmitting changes to a remote repository.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

__version__ = "1.0.0+build.2"

ROOT_ANCHOR = Path("G:/My Drive/genealogy-workspace")
LOGGER = logging.getLogger("system.hooks.pre_push")
PROTECTED_BRANCHES: tuple[str, ...] = ("main", "master", "release")


def get_current_branch(repo_root: Path | None = None) -> str:
    """Retrieve the current active Git branch name.

    Args:
        repo_root: Optional workspace root directory.

    Returns:
        Clean branch name string, or empty string on error.
    """
    root = repo_root or ROOT_ANCHOR
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(root),
            check=True,
        )
        return res.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def run_pre_push(
    repo_root: Path | None = None,
    allow_protected: bool = False,
    skip_tests: bool = False,
) -> int:
    """Execute pre-push validations.

    Args:
        repo_root: Optional workspace root.
        allow_protected: Override flag allowing direct pushes to protected branches.
        skip_tests: Skip full test suite execution.

    Returns:
        0 on success; non-zero integer on validation failure.
    """
    root = repo_root or ROOT_ANCHOR
    branch = get_current_branch(root)
    LOGGER.info("Evaluating pre-push checks for branch: %s", branch)

    if branch in PROTECTED_BRANCHES and not allow_protected:
        print(f"PRE-PUSH REJECTED: Direct push to protected branch '{branch}' is prohibited.")
        print("Please push to an operational feature branch and open a pull request.")
        return 1

    if not skip_tests:
        print(f"Running verification test sweep prior to pushing '{branch}'...")
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "-q",
            "--basetemp=C:/temp/pytest_tmp",
        ]
        result = subprocess.run(cmd, cwd=str(root), check=False)
        if result.returncode != 0:
            print("PRE-PUSH REJECTED: Test suite failure detected prior to remote push.")
            return result.returncode

    print("Pre-push checks passed successfully.")
    return 0


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint for the pre-push hook runner."""
    parser = argparse.ArgumentParser(description="GDA Git Pre-Push Hook Runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--debug", action="store_true", help="Enable diagnostic debug logging")
    parser.add_argument(
        "--allow-protected",
        action="store_true",
        help="Allow push directly to protected branches",
    )
    parser.add_argument("--skip-tests", action="store_true", help="Bypass test execution")
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if args.debug else (logging.INFO if args.verbose else logging.WARNING)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    code = run_pre_push(
        allow_protected=args.allow_protected,
        skip_tests=args.skip_tests,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
