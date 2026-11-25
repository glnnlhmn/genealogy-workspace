"""Path: src/gen_desk_tools/metrics/collectors/hygiene_collector.py

AST-based module hygiene collector for header, PEP 440 version, and test parity checks.

Operational Role:
    Audits every scoped Python module for workspace standards: Line 1/2 Path:
    routing headers, PEP 440 +build.<counter> __version__ strings, __all__
    exports, future annotations, package README.md listing, and matching test
    file existence under tests/, with 4-tier diagnostic logging and resilience
    to syntax or encoding errors.

Classes:
    ModuleHygieneRecord: Per-file structural and documentation hygiene record.

Functions:
    collect_hygiene_metrics: Scan all scoped modules and emit hygiene records.
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from gen_desk_tools.core.logging import VERBOSE
from gen_desk_tools.metrics.collectors.radon_collector import discover_batch_files
from gen_desk_tools.metrics.config import BatchDefinition
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.7"

__all__ = [
    "ModuleHygieneRecord",
    "collect_hygiene_metrics",
]

logger = logging.getLogger(__name__)

# Enforces PEP 440 local build versioning: <major>.<minor>.<rev>+build.<counter>.
_PEP440_BUILD_RE = re.compile(r"^\d+\.\d+\.\d+\+build\.\d+$")
_EXEMPT_FILES = frozenset({"__init__.py", "__main__.py"})


@dataclass(frozen=True)
class ModuleHygieneRecord:
    """Per-file structural and documentation hygiene telemetry."""

    batch_id: str
    file_path: str
    path_header_ok: bool
    version: str
    pep440_valid: bool
    has_all: bool
    has_future_annotations: bool
    readme_listed: bool
    test_file_exists: bool
    hygiene_flags: tuple[str, ...]


def _check_path_header(docstring: str | None, rel_path: str) -> bool:
    """Verify the module docstring declares Path: <rel_path> in its first two lines."""
    if not docstring:
        return False
    expected = f"Path: {rel_path}"
    head_lines = [line.strip() for line in docstring.splitlines()[:2]]
    return expected in head_lines


def _has_future_annotations(node: ast.stmt) -> bool:
    """Return True when stmt is 'from __future__ import annotations'."""
    return (
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
    )


def _extract_ast_metadata(tree: ast.Module) -> tuple[str, bool, bool]:
    """Extract (__version__, has___all__, has_future_annotations) from module AST."""
    version = ""
    has_all = False
    has_future = False

    for node in tree.body:
        if _has_future_annotations(node):
            has_future = True
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if target.id == "__all__":
                    has_all = True
                elif (
                    target.id == "__version__"
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    version = node.value.value

    return version, has_all, has_future


def _is_listed_in_readme(py_file: Path) -> bool:
    """Check whether the package's README.md references this module.

    Package glue modules (__init__.py, __main__.py) are exempt and return True.
    """
    if py_file.name in _EXEMPT_FILES:
        return True
    readme = py_file.parent / "README.md"
    if not readme.exists():
        return False
    text = readme.read_text(encoding="utf-8")
    return py_file.name in text or py_file.stem in text


def _test_file_exists(workspace_root: Path, rel_path: str) -> bool:
    """Check whether a corresponding test file exists under tests/.

    Matches both exact/prefixed names (test_*<stem>.py) and suffixed domain or
    split test suites (test_*<stem>_*.py, e.g. test_archival_enums.py).
    Supports direct mirrored paths (tests/test_<subsys>/<pkg>/) and prefixed
    subdirectories (tests/test_<subsys>/test_<pkg>/). Exempts __init__.py and
    __main__.py.
    """
    parts = Path(rel_path).parts
    if parts[-1] in _EXEMPT_FILES:
        return True
    if len(parts) < 3 or parts[0] != "src":
        return False

    subsys = parts[1]
    middle = parts[2:-1]
    stem = Path(parts[-1]).stem
    patterns = (f"test_*{stem}.py", f"test_*{stem}_*.py")
    direct_dir = workspace_root.joinpath("tests", f"test_{subsys}", *middle)
    prefixed_dir = workspace_root.joinpath(
        "tests",
        f"test_{subsys}",
        *(f"test_{part}" for part in middle),
    )
    return any(
        candidate.is_dir() and any(any(candidate.glob(pat)) for pat in patterns)
        for candidate in (direct_dir, prefixed_dir)
    )


def _build_flags(
    *,
    path_header_ok: bool,
    pep440_valid: bool,
    has_future: bool,
    readme_listed: bool,
    test_exists: bool,
) -> tuple[str, ...]:
    """Assemble standardized hygiene flag codes for failed checks."""
    checks = (
        (path_header_ok, "MISSING_PATH_HEADER"),
        (pep440_valid, "INVALID_VERSION"),
        (has_future, "NO_FUTURE_ANNOTATIONS"),
        (readme_listed, "NOT_IN_README"),
        (test_exists, "MISSING_TEST_FILE"),
    )
    return tuple(code for ok, code in checks if not ok)


def _build_error_record(
    batch_id: str,
    rel_path: str,
    py_file: Path,
    workspace_root: Path,
    flag: str,
) -> ModuleHygieneRecord:
    """Build a fallback hygiene record when a module fails to read or parse."""
    return ModuleHygieneRecord(
        batch_id=batch_id,
        file_path=rel_path,
        path_header_ok=False,
        version="",
        pep440_valid=False,
        has_all=False,
        has_future_annotations=False,
        readme_listed=_is_listed_in_readme(py_file),
        test_file_exists=_test_file_exists(workspace_root, rel_path),
        hygiene_flags=(flag,),
    )


def collect_hygiene_metrics(
    workspace_root: Path,
    batches: tuple[BatchDefinition, ...],
    *,
    progress: ProgressReporter | None = None,
) -> tuple[ModuleHygieneRecord, ...]:
    """Scan all scoped Python modules for header, version, README, and test parity.

    Modules that fail UTF-8 decoding, file reading, or AST parsing are logged
    at ERROR level and recorded with a single diagnostic flag rather than
    aborting the telemetry run.
    """
    logger.info("Starting module hygiene audit across %d batch(es)", len(batches))

    # --- Discover Scoped Modules ---
    discovered = [
        (batch.id, py_file)
        for batch in batches
        for py_file in discover_batch_files(workspace_root, batch)
    ]
    records: list[ModuleHygieneRecord] = []
    total = len(discovered)
    logger.log(VERBOSE, "Auditing %d discovered Python module(s) for hygiene", total)

    # --- Parse & Evaluate Hygiene Rules Per Module ---
    for idx, (batch_id, py_file) in enumerate(discovered, start=1):
        rel_path = py_file.relative_to(workspace_root).as_posix()
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except UnicodeDecodeError as exc:
            logger.error("Hygiene audit encoding failure for %s: %s", rel_path, exc)
            records.append(
                _build_error_record(batch_id, rel_path, py_file, workspace_root, "ENCODING_ERROR")
            )
        except OSError as exc:
            logger.error("Hygiene audit read failure for %s: %s", rel_path, exc)
            records.append(
                _build_error_record(batch_id, rel_path, py_file, workspace_root, "READ_ERROR")
            )
        except SyntaxError as exc:
            logger.error("Hygiene audit syntax error in %s: %s", rel_path, exc)
            records.append(
                _build_error_record(batch_id, rel_path, py_file, workspace_root, "SYNTAX_ERROR")
            )
        else:
            path_ok = _check_path_header(ast.get_docstring(tree), rel_path)
            version, has_all, has_future = _extract_ast_metadata(tree)
            pep440_ok = bool(_PEP440_BUILD_RE.match(version))
            readme_ok = _is_listed_in_readme(py_file)
            test_ok = _test_file_exists(workspace_root, rel_path)
            flags = _build_flags(
                path_header_ok=path_ok,
                pep440_valid=pep440_ok,
                has_future=has_future,
                readme_listed=readme_ok,
                test_exists=test_ok,
            )
            logger.debug("Hygiene audited %s: flags=%s", rel_path, flags)
            records.append(
                ModuleHygieneRecord(
                    batch_id=batch_id,
                    file_path=rel_path,
                    path_header_ok=path_ok,
                    version=version,
                    pep440_valid=pep440_ok,
                    has_all=has_all,
                    has_future_annotations=has_future,
                    readme_listed=readme_ok,
                    test_file_exists=test_ok,
                    hygiene_flags=flags,
                )
            )

        if progress is not None:
            progress.update("Module hygiene audit", current=idx, total=total)

    logger.info("Completed module hygiene audit: %d record(s) collected", len(records))
    return tuple(records)
