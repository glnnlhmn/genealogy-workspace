"""Path: src/gen_desk_tools/metrics/cli.py

Command-line interface and 7-stage pipeline orchestrator for gd_metrics.

Operational Role:
    Defines the gd-metrics CLI parser, coordinates the seven telemetry stages
    (batch resolution, Radon analysis, pytest coverage, AST pytest suite
    inspection, mypy/Ruff diagnostics, module hygiene/import graph, and report
    export), and ensures ProgressReporter log handles close cleanly on exit.

Functions:
    build_parser: Construct the standard gd-metrics ArgumentParser.
    run_pipeline: Execute all seven telemetry stages and return a POSIX exit code.
    main: Parse CLI arguments, load config, and run the telemetry pipeline.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import Any

from gen_desk_tools.metrics.collectors.coverage_collector import (
    FileCoverageMetrics,
    run_pytest_coverage,
)
from gen_desk_tools.metrics.collectors.hygiene_collector import collect_hygiene_metrics
from gen_desk_tools.metrics.collectors.import_collector import collect_import_graph
from gen_desk_tools.metrics.collectors.mypy_collector import MypyDiagnostic, run_mypy_check
from gen_desk_tools.metrics.collectors.pytest_analyzer import analyze_pytest_suite
from gen_desk_tools.metrics.collectors.radon_collector import collect_radon_metrics
from gen_desk_tools.metrics.collectors.ruff_collector import RuffDiagnostic, run_ruff_check
from gen_desk_tools.metrics.config import VALID_SCOPES, MetricsConfig, load_config, resolve_batches
from gen_desk_tools.metrics.exporters.payload_builders import build_sheet_payloads
from gen_desk_tools.metrics.exporters.report_exporter import write_local_json_report
from gen_desk_tools.metrics.exporters.sheets_exporter import sync_to_google_sheets
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.3"

__all__ = ["build_parser", "main", "run_pipeline"]


def build_parser() -> argparse.ArgumentParser:
    """Construct the standard gd-metrics argument parser."""
    parser = argparse.ArgumentParser(
        prog="gd-metrics",
        description="GDA code quality, coverage, and pytest suite telemetry utility.",
    )
    parser.add_argument("--root", type=Path, default=None, help="Workspace root directory.")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.toml.")
    parser.add_argument(
        "--scope",
        action="append",
        choices=sorted(VALID_SCOPES),
        default=None,
        help="Subsystem scope to evaluate (default from config.toml: gda).",
    )
    parser.add_argument(
        "--batch",
        action="append",
        default=None,
        help="Explicit batch ID to evaluate (repeatable).",
    )
    parser.add_argument("--sheet-url", type=str, default=None, help="Target Google Sheet URL.")
    parser.add_argument(
        "--no-sheets",
        action="store_true",
        help="Disable direct Google Sheets sync for offline runs.",
    )
    parser.add_argument(
        "--no-pytest",
        action="store_true",
        help="Skip pytest coverage execution and run static analysis only.",
    )
    parser.add_argument("--no-mypy", action="store_true", help="Skip mypy static type checking.")
    parser.add_argument("--no-ruff", action="store_true", help="Skip ruff lint diagnostics.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose progress.")
    parser.add_argument("--debug", action="store_true", help="Enable debug diagnostics.")
    parser.add_argument("--log-file", type=Path, default=None, help="Optional UTF-8 log path.")
    return parser


def run_pipeline(
    config: MetricsConfig,
    progress: ProgressReporter,
    *,
    skip_pytest: bool = False,
    skip_mypy: bool = False,
    skip_ruff: bool = False,
    client_factory: Callable[[str], Any] | None = None,
) -> int:
    """Execute the 7-stage gd_metrics telemetry pipeline and return 0 on success.

    Args:
        skip_pytest: Skip pytest-cov execution and leave coverage_map empty.
        skip_mypy: Skip mypy static type checking.
        skip_ruff: Skip Ruff lint collection.
        client_factory: Optional gspread client factory injected for hermetic testing.
    """
    # --- Stage 1: Batch Resolution ---
    progress.start_stage("Resolving batches")
    batches = resolve_batches(config)
    progress.finish_stage(f"{len(batches)} batch(es)")

    # --- Stage 2: Radon Static Metrics ---
    progress.start_stage("Collecting Radon metrics")
    file_metrics, rollups = collect_radon_metrics(config.workspace_root, batches, progress=progress)
    progress.finish_stage(f"{len(file_metrics)} file(s)")

    # --- Stage 3: Pytest Statement & Branch Coverage ---
    progress.start_stage("Collecting pytest coverage")
    coverage_map: dict[str, FileCoverageMetrics] = {}
    if skip_pytest:
        progress.finish_stage("skipped (--no-pytest)")
    else:
        cov_result = run_pytest_coverage(config, batches, progress=progress)
        coverage_map = dict(cov_result.files)
        progress.finish_stage(cov_result.summary_note)

    # --- Stage 4: Conftest Hierarchy & Marker AST Analysis ---
    progress.start_stage("Analyzing conftest & pytest markers")
    suite_analysis = analyze_pytest_suite(
        config.workspace_root,
        batches,
        registered_markers=config.registered_markers,
        progress=progress,
    )
    progress.finish_stage(
        f"{suite_analysis.total_test_functions} tests, {len(suite_analysis.fixtures)} fixtures"
    )

    # --- Stage 5: Mypy & Ruff Diagnostics ---
    progress.start_stage("Running mypy & ruff diagnostics")
    mypy_diags: tuple[MypyDiagnostic, ...] = ()
    ruff_diags: tuple[RuffDiagnostic, ...] = ()
    if not skip_mypy:
        mypy_diags = run_mypy_check(config, batches, progress=progress).diagnostics
    if not skip_ruff:
        ruff_diags = run_ruff_check(config, batches, progress=progress).diagnostics
    progress.finish_stage(f"{len(mypy_diags)} mypy, {len(ruff_diags)} ruff")

    # --- Stage 6: Module Hygiene & Import Boundary Graph ---
    progress.start_stage("Auditing module hygiene & import graph")
    hygiene_records = collect_hygiene_metrics(config.workspace_root, batches, progress=progress)
    import_edges = collect_import_graph(config.workspace_root, batches, progress=progress)
    progress.finish_stage(f"{len(hygiene_records)} modules, {len(import_edges)} edges")

    # --- Stage 7: Payload Assembly & Telemetry Export ---
    progress.start_stage("Exporting telemetry")
    payloads = build_sheet_payloads(
        rollups,
        file_metrics,
        coverage_map,
        suite_analysis,
        mypy_diagnostics=mypy_diags,
        ruff_diagnostics=ruff_diags,
        hygiene_records=hygiene_records,
        import_edges=import_edges,
    )
    if config.write_local_report:
        report_path = write_local_json_report(config, payloads)
        progress.update(f"Wrote local report: {report_path}")
    if config.sync_sheets:
        sheet_target = sync_to_google_sheets(
            config,
            payloads,
            progress=progress,
            client_factory=client_factory,
        )
        progress.update(f"Synced Google Sheet: {sheet_target}")
    progress.finish_stage("export complete")
    return 0


def main(
    argv: list[str] | None = None,
    *,
    client_factory: Callable[[str], Any] | None = None,
) -> int:
    """Parse CLI arguments, execute the telemetry pipeline, and return a POSIX exit code.

    Args:
        argv: Optional argument list; defaults to sys.argv[1:] when None.
        client_factory: Optional gspread client factory forwarded to run_pipeline.
    """
    args = build_parser().parse_args(argv)
    config = load_config(
        workspace_root=args.root,
        config_path=args.config,
        cli_scopes=tuple(args.scope) if args.scope else None,
        cli_batches=tuple(args.batch) if args.batch else None,
        cli_sheet_url=args.sheet_url,
        cli_no_sheets=args.no_sheets,
    )
    progress = ProgressReporter(
        total_stages=7,
        verbose=args.verbose,
        debug=args.debug,
        log_file=args.log_file,
    )
    # Guarantee UTF-8 log handles are flushed and closed even on pipeline errors.
    try:
        return run_pipeline(
            config,
            progress,
            skip_pytest=args.no_pytest,
            skip_mypy=args.no_mypy,
            skip_ruff=args.no_ruff,
            client_factory=client_factory,
        )
    finally:
        progress.close()
