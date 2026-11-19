"""Path: src/system/gd_metrics/exporters/sheets_exporter.py

Direct Google Sheets exporter for gd_metrics telemetry.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from typing import Any

from system.gd_metrics.config import MetricsConfig
from system.gd_metrics.exporters.payload_builders import TAB_NAMES, build_sheet_payloads
from system.gd_metrics.progress import ProgressReporter

__version__ = "1.0.0+build.2"

__all__ = [
    "TAB_NAMES",
    "build_sheet_payloads",
    "sync_to_google_sheets",
]


def _default_gspread_client(creds_path: str) -> Any:
    """Create an authenticated gspread client using service account or OAuth."""
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
    """Push all telemetry tabs directly to the configured Google Sheet."""
    if not config.sheet_url and not config.sheet_id:
        msg = "Google Sheets sync requires sheet_url or sheet_id (config.toml, ENV, or --sheet-url)"
        raise ValueError(msg)

    factory = _default_gspread_client if client_factory is None else client_factory
    client = factory(config.google_creds_path)
    spreadsheet = (
        client.open_by_url(config.sheet_url)
        if config.sheet_url
        else client.open_by_key(config.sheet_id)
    )

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
