"""Path: src/gen_desk_tools/metrics/collectors/pytest_analyzer.py

AST-based pytest suite analyzer for conftest mapping, fixture reuse, and markers.

Operational Role:
    Inspects conftest.py and test_*.py files via Python AST without executing
    pytest, building a complete map of fixture scopes, reuse counts, unused or
    shadowed fixtures, marker distributions, unregistered markers, and smoke
    inflation even when collection errors exist.

Classes:
    ConftestFixtureRecord: Metadata, reuse, and shadowing telemetry for a fixture.
    FileMarkerSummary: Per-test-file marker counts and hygiene flags.
    PytestSuiteAnalysis: Aggregated fixture map and marker summary for a run.

Functions:
    analyze_pytest_suite: Execute static AST analysis across active test batches.
"""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from gen_desk_tools.metrics.config import BatchDefinition
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.6"

__all__ = [
    "BUILTIN_PYTEST_MARKERS",
    "ConftestFixtureRecord",
    "DEFAULT_REGISTERED_MARKERS",
    "FileMarkerSummary",
    "PytestSuiteAnalysis",
    "SMOKE_PER_FILE_LIMIT",
    "analyze_pytest_suite",
]

DEFAULT_REGISTERED_MARKERS = frozenset({"unit", "regression", "integration", "integrity", "smoke"})
BUILTIN_PYTEST_MARKERS = frozenset({"parametrize", "skip", "skipif", "xfail", "filterwarnings"})
SMOKE_PER_FILE_LIMIT = 2
IGNORED_PARAMS = frozenset({"self", "cls"})


@dataclass(frozen=True)
class ConftestFixtureRecord:
    """Metadata and reuse telemetry for a single fixture in a conftest.py."""

    conftest_path: str
    scope_dir: str
    name: str
    lineno: int
    fixture_scope: str
    autouse: bool
    parameterized: bool
    reuse_count: int
    consumer_file_count: int
    is_unused: bool
    is_shadowed: bool
    shadowed_by: tuple[str, ...] = ()


@dataclass(frozen=True)
class FileMarkerSummary:
    """Per-test-file marker distribution and hygiene flags."""

    batch_id: str
    file_path: str
    test_count: int
    unmarked_count: int
    unit_count: int
    regression_count: int
    integration_count: int
    integrity_count: int
    smoke_count: int
    unregistered_markers: tuple[str, ...]
    smoke_inflation: bool
    parse_error: str


@dataclass(frozen=True)
class PytestSuiteAnalysis:
    """Aggregated conftest fixture map and marker hygiene summary."""

    fixtures: tuple[ConftestFixtureRecord, ...]
    marker_summaries: tuple[FileMarkerSummary, ...]
    total_test_files: int
    total_test_functions: int
    total_unmarked_tests: int
    total_unused_fixtures: int


@dataclass(frozen=True)
class _RawFixture:
    """Internal AST representation of a fixture prior to reuse aggregation."""

    conftest_path: str
    scope_dir: str
    name: str
    lineno: int
    fixture_scope: str
    autouse: bool
    parameterized: bool
    depends_on: tuple[str, ...]


def _parse_ast_safe(file_path: Path) -> tuple[ast.Module | None, str]:
    """Parse a Python file into an AST, returning an error string on SyntaxError."""
    try:
        source = file_path.read_text(encoding="utf-8")
        return ast.parse(source, filename=str(file_path)), ""
    except SyntaxError as exc:
        return None, f"SyntaxError line {exc.lineno}: {exc.msg}"


def _is_fixture_decorator(node: ast.expr) -> ast.Call | ast.expr | None:
    """Return the decorator node if it represents @pytest.fixture or @fixture."""
    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Name) and target.id == "fixture":
        return node
    if isinstance(target, ast.Attribute) and target.attr == "fixture":
        return node
    return None


def _str_kwarg(kw: ast.keyword, expected_name: str) -> str | None:
    """Return string value when kw matches expected_name with a string literal."""
    if (
        kw.arg == expected_name
        and isinstance(kw.value, ast.Constant)
        and isinstance(kw.value.value, str)
    ):
        return kw.value.value
    return None


def _extract_fixture_kwargs(decorator: ast.expr) -> tuple[str, bool, bool, str]:
    """Extract (scope, autouse, parameterized, custom_name) from a fixture decorator.

    Defaults to ("function", False, False, "") for bare @fixture decorators or
    omitted keyword arguments.
    """
    fixture_scope = "function"
    autouse = False
    parameterized = False
    custom_name = ""

    if not isinstance(decorator, ast.Call):
        return fixture_scope, autouse, parameterized, custom_name

    for kw in decorator.keywords:
        scope_val = _str_kwarg(kw, "scope")
        if scope_val is not None:
            fixture_scope = scope_val
            continue
        name_val = _str_kwarg(kw, "name")
        if name_val is not None:
            custom_name = name_val
            continue
        if kw.arg == "autouse" and isinstance(kw.value, ast.Constant):
            autouse = bool(kw.value.value)
        elif kw.arg == "params":
            parameterized = True

    return fixture_scope, autouse, parameterized, custom_name


def _extract_conftest_fixtures(
    conftest_path: Path,
    workspace_root: Path,
) -> list[_RawFixture]:
    """Extract all top-level pytest fixture definitions from a conftest.py file.

    Records both fixture metadata and upstream fixture parameter dependencies.
    """
    tree, err = _parse_ast_safe(conftest_path)
    if tree is None or err:
        return []

    rel_path = conftest_path.relative_to(workspace_root).as_posix()
    scope_dir = conftest_path.parent.relative_to(workspace_root).as_posix()
    found: list[_RawFixture] = []

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            matched = _is_fixture_decorator(dec)
            if matched is None:
                continue
            f_scope, autouse, parameterized, custom_name = _extract_fixture_kwargs(matched)
            params = tuple(arg.arg for arg in node.args.args if arg.arg not in IGNORED_PARAMS)
            found.append(
                _RawFixture(
                    conftest_path=rel_path,
                    scope_dir=scope_dir,
                    name=custom_name or node.name,
                    lineno=int(node.lineno),
                    fixture_scope=f_scope,
                    autouse=autouse,
                    parameterized=parameterized,
                    depends_on=params,
                )
            )
            break

    return found


def _mark_attribute_name(dec: ast.expr) -> tuple[str | None, ast.Call | None]:
    """Return (mark_name, call_node) when dec is @pytest.mark.<name>(...), else (None, None)."""
    call_node = dec if isinstance(dec, ast.Call) else None
    target = call_node.func if call_node is not None else dec
    if (
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Attribute)
        and target.value.attr == "mark"
    ):
        return target.attr, call_node
    return None, None


def _extract_markers_and_usefixtures(
    decorators: list[ast.expr],
) -> tuple[list[str], list[str]]:
    """Extract pytest.mark.<name> markers and usefixtures arguments from decorators.

    Separates @pytest.mark.usefixtures string literal arguments from regular
    marker names so fixture usage tracking remains accurate.
    """
    markers: list[str] = []
    used_fixtures: list[str] = []

    for dec in decorators:
        mark_name, call_node = _mark_attribute_name(dec)
        if mark_name is None:
            continue
        if mark_name == "usefixtures" and call_node is not None:
            for arg in call_node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    used_fixtures.append(arg.value)
        else:
            markers.append(mark_name)

    return markers, used_fixtures


def _iter_test_functions(
    tree: ast.Module,
) -> list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, list[ast.expr]]]:
    """Collect top-level and Test* class-scoped test_* functions with inherited decorators."""
    items: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, list[ast.expr]]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            "test_"
        ):
            items.append((node, list(node.decorator_list)))
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for child in node.body:
                if isinstance(
                    child, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and child.name.startswith("test_"):
                    # Merge class-level decorators ahead of method-level decorators.
                    items.append((child, list(node.decorator_list) + list(child.decorator_list)))
    return items


def _collect_local_files(
    target: Path,
    batch_id: str,
    seen_tests: set[Path],
    test_files: list[tuple[str, Path]],
    conftest_files: set[Path],
) -> None:
    """Collect conftest.py and deduplicated test_*.py files beneath target."""
    for py_file in sorted(target.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        if py_file.name == "conftest.py":
            conftest_files.add(py_file)
        elif py_file.name.startswith("test_") and py_file not in seen_tests:
            seen_tests.add(py_file)
            test_files.append((batch_id, py_file))


def _collect_ancestor_conftests(
    start_target: Path,
    workspace_root: Path,
    conftest_files: set[Path],
) -> None:
    """Walk upward from start_target to tests/ and collect shared conftest.py files."""
    current = start_target if start_target.is_dir() else start_target.parent
    tests_root = workspace_root / "tests"
    while current != workspace_root and current != current.parent:
        ancestor_cf = current / "conftest.py"
        if ancestor_cf.exists():
            conftest_files.add(ancestor_cf)
        if current == tests_root:
            break
        current = current.parent


def _discover_test_and_conftest_files(
    workspace_root: Path,
    batches: tuple[BatchDefinition, ...],
) -> tuple[list[tuple[str, Path]], tuple[Path, ...]]:
    """Discover scoped test_*.py files and all relevant conftest.py files."""
    test_files: list[tuple[str, Path]] = []
    seen_tests: set[Path] = set()
    conftest_files: set[Path] = set()

    for batch in batches:
        for rel_test in batch.test_paths:
            target = workspace_root / rel_test
            if not target.exists():
                continue
            _collect_local_files(target, batch.id, seen_tests, test_files, conftest_files)
            _collect_ancestor_conftests(target, workspace_root, conftest_files)

    return test_files, tuple(sorted(conftest_files))


def _record_fixture_usage(
    fix_name: str,
    consumer_path: str,
    reuse_counts: Counter[str],
    consumer_files: dict[str, set[str]],
) -> None:
    """Increment reuse count and record consumer file for fix_name."""
    reuse_counts[fix_name] += 1
    consumer_files.setdefault(fix_name, set()).add(consumer_path)


def _tally_test_functions(
    test_funcs: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, list[ast.expr]]],
    rel_path: str,
    valid_markers: set[str],
    reuse_counts: Counter[str],
    consumer_files: dict[str, set[str]],
) -> tuple[Counter[str], int, tuple[str, ...]]:
    """Tally marker frequencies, unmarked count, unregistered markers, and fixture uses."""
    file_counts: Counter[str] = Counter()
    unmarked = 0
    unregistered: set[str] = set()

    for func_node, decorators in test_funcs:
        markers, use_fix = _extract_markers_and_usefixtures(decorators)
        custom_markers = [m for m in markers if m not in BUILTIN_PYTEST_MARKERS]
        if not custom_markers:
            unmarked += 1
        for mark in custom_markers:
            file_counts[mark] += 1
            if mark not in valid_markers:
                unregistered.add(mark)

        arg_names = [a.arg for a in func_node.args.args if a.arg not in IGNORED_PARAMS]
        for fix_name in (*arg_names, *use_fix):
            _record_fixture_usage(fix_name, rel_path, reuse_counts, consumer_files)

    return file_counts, unmarked, tuple(sorted(unregistered))


def _analyze_single_test_file(
    batch_id: str,
    test_path: Path,
    workspace_root: Path,
    valid_markers: set[str],
    reuse_counts: Counter[str],
    consumer_files: dict[str, set[str]],
) -> tuple[FileMarkerSummary, int, int]:
    """Analyze one test file and return (summary, test_count, unmarked_count)."""
    rel_path = test_path.relative_to(workspace_root).as_posix()
    tree, parse_err = _parse_ast_safe(test_path)
    if tree is None:
        return (
            FileMarkerSummary(
                batch_id=batch_id,
                file_path=rel_path,
                test_count=0,
                unmarked_count=0,
                unit_count=0,
                regression_count=0,
                integration_count=0,
                integrity_count=0,
                smoke_count=0,
                unregistered_markers=(),
                smoke_inflation=False,
                parse_error=parse_err,
            ),
            0,
            0,
        )

    test_funcs = _iter_test_functions(tree)
    file_counts, unmarked, unregistered = _tally_test_functions(
        test_funcs,
        rel_path,
        valid_markers,
        reuse_counts,
        consumer_files,
    )
    smoke_count = file_counts["smoke"]
    summary = FileMarkerSummary(
        batch_id=batch_id,
        file_path=rel_path,
        test_count=len(test_funcs),
        unmarked_count=unmarked,
        unit_count=file_counts["unit"],
        regression_count=file_counts["regression"],
        integration_count=file_counts["integration"],
        integrity_count=file_counts["integrity"],
        smoke_count=smoke_count,
        unregistered_markers=unregistered,
        smoke_inflation=smoke_count > SMOKE_PER_FILE_LIMIT,
        parse_error="",
    )
    return summary, len(test_funcs), unmarked


def _finalize_fixture_records(
    raw_fixtures: list[_RawFixture],
    reuse_counts: Counter[str],
    consumer_files: dict[str, set[str]],
) -> tuple[ConftestFixtureRecord, ...]:
    """Build finalized ConftestFixtureRecord tuples with reuse and shadowing flags."""
    name_occurrences = Counter(f.name for f in raw_fixtures)
    paths_by_name: dict[str, set[str]] = {}
    for raw_fix in raw_fixtures:
        paths_by_name.setdefault(raw_fix.name, set()).add(raw_fix.conftest_path)

    fixture_records: list[ConftestFixtureRecord] = []
    for raw_fix in raw_fixtures:
        uses = reuse_counts[raw_fix.name]
        consumers = len(consumer_files.get(raw_fix.name, set()))
        conflicts = tuple(
            sorted(p for p in paths_by_name[raw_fix.name] if p != raw_fix.conftest_path)
        )
        fixture_records.append(
            ConftestFixtureRecord(
                conftest_path=raw_fix.conftest_path,
                scope_dir=raw_fix.scope_dir,
                name=raw_fix.name,
                lineno=raw_fix.lineno,
                fixture_scope=raw_fix.fixture_scope,
                autouse=raw_fix.autouse,
                parameterized=raw_fix.parameterized,
                reuse_count=uses,
                consumer_file_count=consumers,
                is_unused=(uses == 0 and not raw_fix.autouse),
                is_shadowed=name_occurrences[raw_fix.name] > 1,
                shadowed_by=conflicts,
            )
        )

    return tuple(fixture_records)


def analyze_pytest_suite(
    workspace_root: Path,
    batches: tuple[BatchDefinition, ...],
    *,
    registered_markers: tuple[str, ...] = (),
    progress: ProgressReporter | None = None,
) -> PytestSuiteAnalysis:
    """Analyze conftest.py fixture hierarchies, reuse counts, and marker hygiene.

    Args:
        registered_markers: Allowed marker names from pyproject.toml; defaults
            to DEFAULT_REGISTERED_MARKERS when empty.
        progress: Optional reporter receiving per-file AST progress updates.
    """
    # --- Phase 1: Discover Files & Index Conftest Fixtures ---
    valid_markers = (
        set(registered_markers) if registered_markers else set(DEFAULT_REGISTERED_MARKERS)
    )
    test_files, conftest_files = _discover_test_and_conftest_files(workspace_root, batches)

    raw_fixtures: list[_RawFixture] = []
    for cf_path in conftest_files:
        raw_fixtures.extend(_extract_conftest_fixtures(cf_path, workspace_root))

    reuse_counts: Counter[str] = Counter()
    consumer_files: dict[str, set[str]] = {}

    # Count fixture-to-fixture dependencies before scanning test modules.
    for raw_fix in raw_fixtures:
        for dep in raw_fix.depends_on:
            _record_fixture_usage(dep, raw_fix.conftest_path, reuse_counts, consumer_files)

    # --- Phase 2: Analyze Test Modules for Markers & Fixture Usage ---
    marker_summaries: list[FileMarkerSummary] = []
    total_tests = 0
    total_unmarked = 0
    total_files = len(test_files)

    for idx, (batch_id, test_path) in enumerate(test_files, start=1):
        summary, fn_count, unmarked_count = _analyze_single_test_file(
            batch_id,
            test_path,
            workspace_root,
            valid_markers,
            reuse_counts,
            consumer_files,
        )
        marker_summaries.append(summary)
        total_tests += fn_count
        total_unmarked += unmarked_count
        if progress is not None:
            progress.update("Pytest AST analysis", current=idx, total=total_files)

    # --- Phase 3: Compute Shadowing & Finalize Suite Analysis ---
    fixture_records = _finalize_fixture_records(raw_fixtures, reuse_counts, consumer_files)
    unused_total = sum(1 for f in fixture_records if f.is_unused)
    return PytestSuiteAnalysis(
        fixtures=fixture_records,
        marker_summaries=tuple(marker_summaries),
        total_test_files=len(marker_summaries),
        total_test_functions=total_tests,
        total_unmarked_tests=total_unmarked,
        total_unused_fixtures=unused_total,
    )
