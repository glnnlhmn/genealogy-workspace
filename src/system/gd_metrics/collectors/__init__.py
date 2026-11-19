"""Path: src/system/gd_metrics/collectors/__init__.py

Telemetry collectors for Radon, pytest coverage, AST analysis, mypy, and Ruff.
"""

from __future__ import annotations

from system.gd_metrics.collectors.coverage_collector import (
    CoverageRunResult,
    FileCoverageMetrics,
    format_missing_lines,
    parse_coverage_json,
    run_pytest_coverage,
)
from system.gd_metrics.collectors.hygiene_collector import (
    ModuleHygieneRecord,
    collect_hygiene_metrics,
)
from system.gd_metrics.collectors.import_collector import (
    ImportEdgeRecord,
    collect_import_graph,
)
from system.gd_metrics.collectors.mypy_collector import (
    MypyDiagnostic,
    MypyRunResult,
    parse_mypy_output,
    run_mypy_check,
)
from system.gd_metrics.collectors.pytest_analyzer import (
    ConftestFixtureRecord,
    FileMarkerSummary,
    PytestSuiteAnalysis,
    analyze_pytest_suite,
)
from system.gd_metrics.collectors.radon_collector import (
    BatchRadonRollup,
    ComplexityHotspot,
    FileRadonMetrics,
    analyze_file_radon,
    collect_radon_metrics,
    discover_batch_files,
)
from system.gd_metrics.collectors.ruff_collector import (
    RuffDiagnostic,
    RuffRunResult,
    parse_ruff_json,
    run_ruff_check,
)

__version__ = "1.0.0+build.4"

__all__ = [
    "BatchRadonRollup",
    "ComplexityHotspot",
    "ConftestFixtureRecord",
    "CoverageRunResult",
    "FileCoverageMetrics",
    "FileMarkerSummary",
    "FileRadonMetrics",
    "ImportEdgeRecord",
    "ModuleHygieneRecord",
    "MypyDiagnostic",
    "MypyRunResult",
    "PytestSuiteAnalysis",
    "RuffDiagnostic",
    "RuffRunResult",
    "__version__",
    "analyze_file_radon",
    "analyze_pytest_suite",
    "collect_hygiene_metrics",
    "collect_import_graph",
    "collect_radon_metrics",
    "discover_batch_files",
    "format_missing_lines",
    "parse_coverage_json",
    "parse_mypy_output",
    "parse_ruff_json",
    "run_mypy_check",
    "run_pytest_coverage",
    "run_ruff_check",
]
