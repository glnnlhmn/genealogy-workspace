"""Path: src/system/hooks/pre_push.py

Git pre-push hook orchestrator enforcing branch protection and test gates.

Operational Role:
    Prevents direct pushes to protected branches ('main', 'master'),
    verifies repository state, and dispatches the authoritative pre-push
    test suite before remote transfer occurs.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence

__version__ = "1.0.0+build.8"

PROTECTED_BRANCHES: frozenset[str] = frozenset({"main", "master"})


def get_current_branch() -> str:
    """Retrieve the name of the currently checked out Git branch.

    Returns:
        The branch name, or 'unknown' if resolution fails.
    """
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        branch = res.stdout.strip()
        return branch if branch else "unknown"
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def validate_branch(branch: str) -> bool:
    """Verify that the target push branch is not protected against direct push.

    Args:
        branch: Active Git branch name.

    Returns:
        True if push is permitted, False if branch is protected.
    """
    if branch in PROTECTED_BRANCHES:
        print(f"PRE-PUSH REJECTED: Direct push to protected branch '{branch}' is prohibited.")
        print("Please push to an operational feature branch and open a pull request.")
        return False
    return True


def run_pre_push_suite(verbose: bool = False) -> bool:
    """Execute pre-push verification commands including structure, formatting, and tests.

    Args:
        verbose: Whether to pass verbose flags to underlying test commands.

    Returns:
        True if all checks pass, False if any check fails or encounters an error.
    """
    commands: list[list[str]] = [
        [sys.executable, "-m", "ruff", "check", "src", "tests"],
        [sys.executable, "-m", "ruff", "format", "--check", "src", "tests"],
    ]

    pytest_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_system/",
        "--basetemp=gtemp/pytest_tmp",
    ]
    if verbose:
        pytest_cmd.append("-v")
    commands.append(pytest_cmd)

    for cmd in commands:
        try:
            res = subprocess.run(cmd, check=False)
            if res.returncode != 0:
                print(f"Pre-push check failed on command: {' '.join(cmd)}")
                return False
        except OSError as exc:
            print(f"Pre-push command execution failed: {exc}")
            return False

    return True


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for pre-push verification.

    Args:
        argv: Optional command-line arguments.

    Returns:
        0 on success, non-zero on failure.
    """
    parser = argparse.ArgumentParser(
        description="GDA Git Pre-Push Hook Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output during validation run.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode and verbose tracebacks.",
    )
    args = parser.parse_args(argv)

    branch = get_current_branch()
    if not validate_branch(branch):
        sys.exit(1)

    if not run_pre_push_suite(verbose=args.verbose):
        sys.exit(1)

    print("Pre-push checks passed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
