"""Path: src/gen_desk_tools/metrics/exporters/sheets_exporter.py

Direct Google Sheets exporter for gd_metrics telemetry.

Operational Role:
    Authenticates with gspread (service account or OAuth), opens the configured
    target spreadsheet by URL or key, and clears/creates and updates each
    telemetry worksheet tab with live progress reporting.

Functions:
    sync_to_google_sheets: Push all telemetry tabs directly to Google Sheets.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from typing import Any

from gen_desk_tools.metrics.config import MetricsConfig
from gen_desk_tools.metrics.exporters.payload_builders import TAB_NAMES, build_sheet_payloads
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.3"

__all__ = [
    "TAB_NAMES",
    "build_sheet_payloads",
    "sync_to_google_sheets",
]


def _default_gspread_client(creds_path: str) -> Any:
    """Create an authenticated gspread client using service account or OAuth.

    Imports gspread lazily so offline runs and unit tests do not require
    gspread credentials at import time.
    """
    gspread = importlib.import_module("gspread")
    if creds_path:
        return gspread.service_account(filename=creds_path)
    return gspread.oauth()


def sync_to_google_sheets(
    config: MetricsConfig,
    payloads: Mapping[str, list[list[Any]]],
    *,
    progress: ProgressReporter | None = None,
    client_factory: Callable[[str], Any] | None = None,
) -> str:
    """Push all telemetry tabs directly to the configured Google Sheet.

    Creates missing worksheet tabs automatically and overwrites existing ones
    in place, returning the resolved spreadsheet URL or key.

    Args:
        progress: Optional reporter receiving per-tab sync progress updates.
        client_factory: Optional gspread client factory injected for testing.

    Raises:
        ValueError: If neither config.sheet_url nor config.sheet_id is set.
    """
    if not config.sheet_url and not config.sheet_id:
        msg = "Google Sheets sync requires sheet_url or sheet_id (config.toml, ENV, or --sheet-url)"
        raise ValueError(msg)

    # --- Authenticate & Open Target Spreadsheet ---
    factory = _default_gspread_client if client_factory is None else client_factory
    client = factory(config.google_creds_path)
    spreadsheet = (
        client.open_by_url(config.sheet_url)
        if config.sheet_url
        else client.open_by_key(config.sheet_id)
    )

    # --- Clear or Provision Each Tab & Push Rows ---
    tab_items = list(payloads.items())
    for idx, (tab_name, rows) in enumerate(tab_items, start=1):
        try:
            ws = spreadsheet.worksheet(tab_name)
            ws.clear()
        except Exception:
            ws = spreadsheet.add_worksheet(
                title=tab_name,
                rows=max(len(rows), 1),
                cols=max(len(rows[0]), 1),
            )
        ws.update(rows)
        if progress is not None:
            progress.update(f"Synced tab {tab_name}", current=idx, total=len(tab_items))

    return str(getattr(spreadsheet, "url", config.sheet_url or config.sheet_id))
