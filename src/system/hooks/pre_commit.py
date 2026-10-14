# Name: pre_commit.py
# Path: src/system/hooks/pre_commit.py

"""Staged-File & Targeted Component Pre-Commit Hook Executor.

Operational Role:
    Executes fast Ruff linting, formatting checks, and targeted pytest suites.
    Supports explicit component targeting via CLI flags (--target), full repository
    verification (--all), or automatic inference from staged Git changes.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

__version__ = "1.1.0+build.r1"


def get_git_root() -> Path:
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
        return Path.cwd().resolve()


def get_staged_files(repo_root: Path) -> list[str]:
    """Retrieve relative paths of all files staged for commit.

    Args:
        repo_root: Canonical git repository root directory.

    Returns:
        list[str]: Normalized list of staged file paths relative to repository root.
    """
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        return [
            line.strip().replace("\\", "/")
            for line in res.stdout.splitlines()
            if line.strip()
        ]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def determine_test_targets(
    repo_root: Path,
    staged_files: list[str] | None = None,
    explicit_targets: list[str] | None = None,
    run_all: bool = False,
) -> list[str]:
    """Map explicit targets, all-flag, or staged paths to test target paths.

    Args:
        repo_root: Canonical repository root.
        staged_files: List of relative staged file paths.
        explicit_targets: Explicit folder paths passed by operator (e.g. ['src/system']).
        run_all: If True, returns all discoverable tests/ subdirectories.

    Returns:
        list[str]: Deduplicated list of test directory or file paths to invoke.
    """
    targets: set[str] = set()

    if run_all:
        tests_dir = repo_root / "tests"
        if tests_dir.is_dir():
            for child in tests_dir.iterdir():
                if child.is_dir() and child.name.startswith("test_"):
                    targets.add(f"tests/{child.name}")
        return sorted(targets)

    if explicit_targets:
        for t in explicit_targets:
            p = Path(t)
            parts = p.parts
            if not parts:
                continue
            if parts[0] == "tests":
                targets.add(t.replace("\\", "/"))
            elif parts[0] == "src" and len(parts) >= 2:
                targets.add(f"tests/test_{parts[1]}")
            else:
                targets.add(f"tests/test_{parts[0]}")
        return sorted(targets)

    # Fallback to staged files mapping
    if staged_files:
        for path in staged_files:
            p = Path(path)
            parts = p.parts

            if parts and parts[0] == "tests" and p.suffix == ".py":
                targets.add(path)
                continue

            if len(parts) >= 2 and parts[0] == "src":
                targets.add(f"tests/test_{parts[1]}")

    return sorted(targets)


def run_ruff_checks(repo_root: Path, files_or_dirs: list[str]) -> int:
    """Execute ruff formatting and lint checks on specified targets.

    Args:
        repo_root: Repository root path.
        files_or_dirs: List of paths or directories to verify.

    Returns:
        int: Subprocess return code (0 for clean pass).
    """
    if not files_or_dirs:
        return 0

    print("Running ruff format verification...")
    fmt_res = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--check", *files_or_dirs],
        cwd=str(repo_root),
    )
    if fmt_res.returncode != 0:
        print("Error: Ruff formatting check failed. Run 'ruff format .' to correct.")
        return fmt_res.returncode

    print("Running ruff lint inspection...")
    lint_res = subprocess.run(
        [sys.executable, "-m", "ruff", "check", *files_or_dirs],
        cwd=str(repo_root),
    )
    if lint_res.returncode != 0:
        print(
            "Error: Ruff lint inspection failed. Run 'ruff check . --fix' to correct."
        )
        return lint_res.returncode

    return 0


def run_targeted_tests(repo_root: Path, test_targets: list[str]) -> int:
    """Execute pytest against localized test directories or files.

    Args:
        repo_root: Canonical repository root directory.
        test_targets: List of test paths to execute.

    Returns:
        int: Subprocess return code (0 for pass).
    """
    if not test_targets:
        print("No test targets mapped. Skipping pytest.")
        return 0

    valid_targets = [t for t in test_targets if (repo_root / t).exists()]
    if not valid_targets:
        print("Targeted test directories not found on disk. Skipping.")
        return 0

    print(f"Running targeted tests: {' '.join(valid_targets)}")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *valid_targets,
        "-v",
        "-m",
        "smoke or unit",
        "--basetemp=temp/pytest_tmp",
    ]
    res = subprocess.run(cmd, cwd=str(repo_root))
    return res.returncode


def main(argv: list[str] | None = None) -> None:
    """Execute the pre-commit workflow.

    Args:
        argv: Optional command line argument list.
    """
    parser = argparse.ArgumentParser(
        prog="pre-commit",
        description="Genealogy Workspace Pre-Commit Verification Hook",
    )
    parser.add_argument(
        "-t",
        "--target",
        action="append",
        default=[],
        help="Specify one or more explicit component directories (e.g. -t src/system).",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        default=False,
        help="Run verification across all project components.",
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        default=False,
        help="Run only Ruff checks without invoking pytest.",
    )

    args = parser.parse_args(argv)
    repo_root = get_git_root()

    # Determine files to lint/format
    if args.all:
        ruff_targets = ["src", "tests"]
    elif args.target:
        ruff_targets = args.target
    else:
        staged = get_staged_files(repo_root)
        if not staged:
            sys.exit(0)
        ruff_targets = [f for f in staged if f.endswith(".py")]

    ruff_status = run_ruff_checks(repo_root, ruff_targets)
    if ruff_status != 0:
        sys.exit(ruff_status)

    if args.no_tests:
        sys.exit(0)

    staged_files = None if (args.all or args.target) else get_staged_files(repo_root)
    test_targets = determine_test_targets(
        repo_root=repo_root,
        staged_files=staged_files,
        explicit_targets=args.target,
        run_all=args.all,
    )

    test_status = run_targeted_tests(repo_root, test_targets)
    if test_status != 0:
        sys.exit(test_status)

    sys.exit(0)


if __name__ == "__main__":
    main()
