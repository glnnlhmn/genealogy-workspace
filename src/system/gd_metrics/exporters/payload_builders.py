"""Path: src/system/gd_metrics/exporters/payload_builders.py

Row-matrix builders for all nine gd_metrics Google Sheets telemetry tabs.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from system.gd_metrics.collectors.coverage_collector import FileCoverageMetrics
from system.gd_metrics.collectors.hygiene_collector import ModuleHygieneRecord
from system.gd_metrics.collectors.import_collector import ImportEdgeRecord
from system.gd_metrics.collectors.mypy_collector import MypyDiagnostic
from system.gd_metrics.collectors.pytest_analyzer import PytestSuiteAnalysis
from system.gd_metrics.collectors.radon_collector import BatchRadonRollup, FileRadonMetrics
from system.gd_metrics.collectors.ruff_collector import RuffDiagnostic

__version__ = "1.0.0+build.2"

__all__ = [
    "TAB_NAMES",
    "build_sheet_payloads",
]

TAB_NAMES = (
    "Master_Scorecard",
    "Raw_Module_Telemetry",
    "CC_MI_Hotspots",
    "Test_Markers_Summary",
    "Conftest_Fixture_Map",
    "Mypy_Diagnostics",
    "Ruff_Diagnostics",
    "Module_Hygiene_Audit",
    "Import_Dependency_Graph",
)


def _coverage_totals(
    file_metrics: Iterable[FileRadonMetrics],
    coverage_map: Mapping[str, FileCoverageMetrics],
) -> tuple[float | str, float | str, float | str]:
    """Compute statement, branch, and total coverage percentages for a file set."""
    stmts = cov_lines = branches = cov_branches = 0
    for item in file_metrics:
        cov = coverage_map.get(item.file_path)
        if cov is None:
            continue
        stmts += cov.num_statements
        cov_lines += cov.covered_lines
        branches += cov.num_branches
        cov_branches += cov.covered_branches

    if stmts == 0:
        return "N/A", "N/A", "N/A"
    stmt_pct = round((cov_lines / stmts) * 100.0, 1)
    branch_pct: float | str = round((cov_branches / branches) * 100.0, 1) if branches > 0 else "N/A"
    total_pct = round(((cov_lines + cov_branches) / (stmts + branches)) * 100.0, 1)
    return stmt_pct, branch_pct, total_pct


def _build_workspace_total_row(
    rollups: tuple[BatchRadonRollup, ...],
    file_metrics: tuple[FileRadonMetrics, ...],
    coverage_map: Mapping[str, FileCoverageMetrics],
    counts: tuple[int, int, int, int, int],
) -> list[Any]:
    """Build the bottom TOTAL / WORKSPACE rollup row for Master_Scorecard."""
    total_files = sum(r.file_count for r in rollups)
    total_loc = sum(r.loc for r in rollups)
    total_lloc = sum(r.lloc for r in rollups)
    total_sloc = sum(r.sloc for r in rollups)
    total_blank = sum(r.blank for r in rollups)
    total_cmt = sum(r.comments for r in rollups)
    total_doc = sum(r.docstrings for r in rollups)
    doc_pct = round(((total_cmt + total_doc) / total_sloc) * 100.0, 1) if total_sloc > 0 else 0.0
    avg_cc = (
        round(sum(r.avg_cc * r.file_count for r in rollups) / total_files, 2)
        if total_files > 0
        else 0.0
    )
    stmt_pct, br_pct, tot_pct = _coverage_totals(file_metrics, coverage_map)
    mypy_tot, ruff_tot, hyg_tot, bnd_tot, smoke_tot = counts
    return [
        "TOTAL / WORKSPACE",
        "All Scoped Batches",
        "-",
        total_files,
        total_loc,
        total_lloc,
        total_sloc,
        total_blank,
        total_cmt,
        total_doc,
        doc_pct,
        avg_cc,
        sum(r.cc_c_plus_count for r in rollups),
        sum(r.mi_below_a_count for r in rollups),
        stmt_pct,
        br_pct,
        tot_pct,
        mypy_tot,
        ruff_tot,
        hyg_tot,
        bnd_tot,
        smoke_tot,
        0,
        "",
    ]


def _build_master_rows(
    rollups: tuple[BatchRadonRollup, ...],
    file_metrics: tuple[FileRadonMetrics, ...],
    coverage_map: Mapping[str, FileCoverageMetrics],
    suite_analysis: PytestSuiteAnalysis,
    mypy_diagnostics: tuple[MypyDiagnostic, ...],
    ruff_diagnostics: tuple[RuffDiagnostic, ...],
    hygiene_records: tuple[ModuleHygieneRecord, ...],
    import_edges: tuple[ImportEdgeRecord, ...],
) -> list[list[Any]]:
    """Build Master_Scorecard tab rows with per-batch rollups and workspace total."""
    mypy_err = Counter(d.batch_id for d in mypy_diagnostics if d.severity == "error")
    ruff_err = Counter(r.batch_id for r in ruff_diagnostics)
    hyg_cnt = Counter(h.batch_id for h in hygiene_records if h.hygiene_flags)
    bnd_cnt = Counter(e.batch_id for e in import_edges if e.boundary_violation)
    smoke_cnt = Counter(m.batch_id for m in suite_analysis.marker_summaries if m.smoke_inflation)

    rows: list[list[Any]] = [
        [
            "Batch ID",
            "Tier & Scope",
            "Audit Status",
            "Files",
            "LOC",
            "LLOC",
            "SLOC",
            "Blank",
            "# Cmt",
            "Docstr",
            "(C+Doc)/SLOC %",
            "Avg CC",
            "CC C+ Count",
            "MI < A Count",
            "Stmt Cov %",
            "Branch Cov %",
            "Total Cov %",
            "Mypy Errors",
            "Ruff Errors",
            "Hygiene Flags",
            "Boundary Violations",
            "Smoke Inflation",
            "Open Findings",
            "Batch Sheet Link",
        ]
    ]
    for r in rollups:
        batch_files = [m for m in file_metrics if m.batch_id == r.batch_id]
        stmt_pct, br_pct, tot_pct = _coverage_totals(batch_files, coverage_map)
        rows.append(
            [
                r.batch_id,
                f"{r.tier} ({r.scope})",
                "PENDING",
                r.file_count,
                r.loc,
                r.lloc,
                r.sloc,
                r.blank,
                r.comments,
                r.docstrings,
                r.doc_pct,
                r.avg_cc,
                r.cc_c_plus_count,
                r.mi_below_a_count,
                stmt_pct,
                br_pct,
                tot_pct,
                mypy_err[r.batch_id],
                ruff_err[r.batch_id],
                hyg_cnt[r.batch_id],
                bnd_cnt[r.batch_id],
                smoke_cnt[r.batch_id],
                0,
                "",
            ]
        )

    totals = (
        sum(mypy_err.values()),
        sum(ruff_err.values()),
        sum(hyg_cnt.values()),
        sum(bnd_cnt.values()),
        sum(smoke_cnt.values()),
    )
    rows.append(_build_workspace_total_row(rollups, file_metrics, coverage_map, totals))
    return rows


def _build_raw_and_hotspot_rows(
    file_metrics: tuple[FileRadonMetrics, ...],
    coverage_map: Mapping[str, FileCoverageMetrics],
) -> tuple[list[list[Any]], list[list[Any]]]:
    """Build Raw_Module_Telemetry and worst-first sorted CC_MI_Hotspots tab rows."""
    raw_rows: list[list[Any]] = [
        [
            "Batch",
            "File Path",
            "LOC",
            "LLOC",
            "SLOC",
            "Blank",
            "Cmt",
            "Doc",
            "Doc%",
            "MI Score",
            "MI Grade",
            "Max CC",
            "Max CC Symbol",
            "Total Cov%",
            "Missing Lines",
        ]
    ]
    cc_rows: list[list[Any]] = []
    mi_rows: list[list[Any]] = []
    for m in file_metrics:
        cov = coverage_map.get(m.file_path)
        cov_pct: Any = cov.total_cov_pct if cov is not None else "N/A"
        missing = cov.missing_lines if cov is not None else "-"
        raw_rows.append(
            [
                m.batch_id,
                m.file_path,
                m.loc,
                m.lloc,
                m.sloc,
                m.blank,
                m.comments,
                m.docstrings,
                m.doc_pct,
                m.mi_score,
                m.mi_grade,
                m.max_cc,
                m.max_cc_symbol,
                cov_pct,
                missing,
            ]
        )
        for h in m.hotspots:
            cc_rows.append(
                [
                    "CC >= 11",
                    h.batch_id,
                    h.file_path,
                    h.lineno,
                    h.kind,
                    h.symbol,
                    h.complexity,
                    h.grade,
                ]
            )
        if m.mi_grade != "A":
            mi_rows.append(
                ["MI < A", m.batch_id, m.file_path, 1, "MOD", m.file_path, m.mi_score, m.mi_grade]
            )

    cc_rows.sort(key=lambda row: (-row[6], row[1], row[2], row[3]))
    mi_rows.sort(key=lambda row: (row[6], row[1], row[2]))
    hotspot_header = ["Category", "Batch", "File Path", "Line", "Kind", "Symbol", "Score", "Grade"]
    return raw_rows, [hotspot_header, *cc_rows, *mi_rows]


def _build_pytest_rows(
    suite_analysis: PytestSuiteAnalysis,
) -> tuple[list[list[Any]], list[list[Any]]]:
    """Build Test_Markers_Summary and priority-sorted Conftest_Fixture_Map tab rows."""
    marker_rows: list[list[Any]] = [
        [
            "Batch",
            "Test File",
            "Tests",
            "Unmarked",
            "unit",
            "regression",
            "integration",
            "integrity",
            "smoke",
            "Unregistered Markers",
            "Smoke Inflation",
            "Parse Error",
        ]
    ]
    for ms in suite_analysis.marker_summaries:
        marker_rows.append(
            [
                ms.batch_id,
                ms.file_path,
                ms.test_count,
                ms.unmarked_count,
                ms.unit_count,
                ms.regression_count,
                ms.integration_count,
                ms.integrity_count,
                ms.smoke_count,
                ", ".join(ms.unregistered_markers),
                "YES" if ms.smoke_inflation else "NO",
                ms.parse_error,
            ]
        )

    fixture_rows: list[list[Any]] = [
        [
            "Conftest Path",
            "Scope Dir",
            "Fixture Name",
            "Line",
            "Scope",
            "Autouse",
            "Parameterized",
            "Reuse Count",
            "Consumer Files",
            "Unused",
            "Shadowed",
            "Shadowed By",
        ]
    ]
    sorted_fixtures = sorted(
        suite_analysis.fixtures,
        key=lambda fx: (not fx.is_unused, not fx.is_shadowed, fx.conftest_path, fx.lineno),
    )
    for fx in sorted_fixtures:
        fixture_rows.append(
            [
                fx.conftest_path,
                fx.scope_dir,
                fx.name,
                fx.lineno,
                fx.fixture_scope,
                "YES" if fx.autouse else "NO",
                "YES" if fx.parameterized else "NO",
                fx.reuse_count,
                fx.consumer_file_count,
                "YES" if fx.is_unused else "NO",
                "YES" if fx.is_shadowed else "NO",
                ", ".join(fx.shadowed_by),
            ]
        )
    return marker_rows, fixture_rows


def _build_diagnostic_rows(
    mypy_diagnostics: tuple[MypyDiagnostic, ...],
    ruff_diagnostics: tuple[RuffDiagnostic, ...],
) -> tuple[list[list[Any]], list[list[Any]]]:
    """Build Mypy_Diagnostics and Ruff_Diagnostics tab rows."""
    mypy_rows: list[list[Any]] = [
        ["Batch", "File Path", "Line", "Severity", "Error Code", "Message"]
    ]
    for d in mypy_diagnostics:
        mypy_rows.append([d.batch_id, d.file_path, d.lineno, d.severity, d.error_code, d.message])

    ruff_rows: list[list[Any]] = [
        ["Batch", "File Path", "Line", "Col", "Rule Code", "Message", "Fixable"]
    ]
    for r in ruff_diagnostics:
        ruff_rows.append(
            [
                r.batch_id,
                r.file_path,
                r.lineno,
                r.col,
                r.rule_code,
                r.message,
                "YES" if r.fixable else "NO",
            ]
        )
    return mypy_rows, ruff_rows


def _build_hygiene_and_import_rows(
    hygiene_records: tuple[ModuleHygieneRecord, ...],
    import_edges: tuple[ImportEdgeRecord, ...],
) -> tuple[list[list[Any]], list[list[Any]]]:
    """Build Module_Hygiene_Audit and violation-first Import_Dependency_Graph tab rows."""
    hygiene_rows: list[list[Any]] = [
        [
            "Batch",
            "File Path",
            "Path Header OK",
            "Version",
            "PEP440 Valid",
            "Has __all__",
            "Future Annotations",
            "README Listed",
            "Test File Exists",
            "Hygiene Flags",
        ]
    ]
    for h in hygiene_records:
        hygiene_rows.append(
            [
                h.batch_id,
                h.file_path,
                "YES" if h.path_header_ok else "NO",
                h.version,
                "YES" if h.pep440_valid else "NO",
                "YES" if h.has_all else "NO",
                "YES" if h.has_future_annotations else "NO",
                "YES" if h.readme_listed else "NO",
                "YES" if h.test_file_exists else "NO",
                ", ".join(h.hygiene_flags),
            ]
        )

    import_rows: list[list[Any]] = [
        [
            "Batch",
            "Source Module",
            "Imported Module",
            "Source Layer",
            "Target Layer",
            "Boundary Violation",
            "Violation Reason",
        ]
    ]
    sorted_edges = sorted(
        import_edges,
        key=lambda e: (not e.boundary_violation, e.batch_id, e.source_module, e.imported_module),
    )
    for e in sorted_edges:
        import_rows.append(
            [
                e.batch_id,
                e.source_module,
                e.imported_module,
                e.source_layer,
                e.target_layer,
                "YES" if e.boundary_violation else "NO",
                e.violation_reason,
            ]
        )
    return hygiene_rows, import_rows


def build_sheet_payloads(
    rollups: tuple[BatchRadonRollup, ...],
    file_metrics: tuple[FileRadonMetrics, ...],
    coverage_map: Mapping[str, FileCoverageMetrics],
    suite_analysis: PytestSuiteAnalysis,
    *,
    mypy_diagnostics: tuple[MypyDiagnostic, ...] = (),
    ruff_diagnostics: tuple[RuffDiagnostic, ...] = (),
    hygiene_records: tuple[ModuleHygieneRecord, ...] = (),
    import_edges: tuple[ImportEdgeRecord, ...] = (),
) -> dict[str, list[list[Any]]]:
    """Assemble 2D row matrices for all nine Google Sheets telemetry tabs."""
    master_rows = _build_master_rows(
        rollups,
        file_metrics,
        coverage_map,
        suite_analysis,
        mypy_diagnostics,
        ruff_diagnostics,
        hygiene_records,
        import_edges,
    )
    raw_rows, hotspot_rows = _build_raw_and_hotspot_rows(file_metrics, coverage_map)
    marker_rows, fixture_rows = _build_pytest_rows(suite_analysis)
    mypy_rows, ruff_rows = _build_diagnostic_rows(mypy_diagnostics, ruff_diagnostics)
    hygiene_rows, import_rows = _build_hygiene_and_import_rows(hygiene_records, import_edges)

    return {
        "Master_Scorecard": master_rows,
        "Raw_Module_Telemetry": raw_rows,
        "CC_MI_Hotspots": hotspot_rows,
        "Test_Markers_Summary": marker_rows,
        "Conftest_Fixture_Map": fixture_rows,
        "Mypy_Diagnostics": mypy_rows,
        "Ruff_Diagnostics": ruff_rows,
        "Module_Hygiene_Audit": hygiene_rows,
        "Import_Dependency_Graph": import_rows,
    }
