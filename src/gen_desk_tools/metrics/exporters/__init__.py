"""Path: src/gen_desk_tools/metrics/exporters/__init__.py

Telemetry exporters for Google Sheets sync and local JSON snapshots.
"""

from __future__ import annotations

from gen_desk_tools.metrics.exporters.payload_builders import TAB_NAMES, build_sheet_payloads
from gen_desk_tools.metrics.exporters.report_exporter import write_local_json_report
from gen_desk_tools.metrics.exporters.sheets_exporter import sync_to_google_sheets

__version__ = "1.0.0+build.2"

__all__ = [
    "TAB_NAMES",
    "__version__",
    "build_sheet_payloads",
    "sync_to_google_sheets",
    "write_local_json_report",
]
