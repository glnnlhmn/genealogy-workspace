"""Path: src/gen_desk_tools/metrics/exporters/sheets_exporter.py

Direct Google Sheets exporter for gd_metrics telemetry.

Operational Role:
    Authenticates with gspread (service account or OAuth), opens the configured
    target spreadsheet by URL or key, and clears/creates and updates each
    telemetry worksheet tab with 4-tier diagnostic logging, transient retry
    handling, 50,000-character cell truncation, and actionable error diagnostics.

Functions:
    sync_to_google_sheets: Push all telemetry tabs directly to Google Sheets.
"""

from __future__ import annotations

import importlib
import logging
import time
from collections.abc import Callable, Mapping
from typing import Any

from gen_desk_tools.core.logging import VERBOSE
from gen_desk_tools.metrics.config import MetricsConfig
from gen_desk_tools.metrics.exporters.payload_builders import TAB_NAMES, build_sheet_payloads
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.5"

__all__ = [
    "TAB_NAMES",
    "build_sheet_payloads",
    "sync_to_google_sheets",
]

logger = logging.getLogger(__name__)

_MAX_CELL_CHARS = 50_000
_TRUNCATION_SUFFIX = "...[truncated]"
_MAX_UPDATE_ATTEMPTS = 3


def _default_gspread_client(creds_path: str) -> Any:
    """Create an authenticated gspread client using service account or OAuth.

    Imports gspread lazily so offline runs and unit tests do not require
    gspread credentials at import time.
    """
    gspread = importlib.import_module("gspread")
    if creds_path:
        return gspread.service_account(filename=creds_path)
    return gspread.oauth()


def _sanitize_rows(rows: list[list[Any]]) -> list[list[Any]]:
    """Truncate string cell values exceeding Google Sheets' 50,000-character limit."""
    limit = _MAX_CELL_CHARS - len(_TRUNCATION_SUFFIX)
    sanitized: list[list[Any]] = []
    for row in rows:
        sanitized.append(
            [
                f"{cell[:limit]}{_TRUNCATION_SUFFIX}"
                if isinstance(cell, str) and len(cell) > _MAX_CELL_CHARS
                else cell
                for cell in row
            ]
        )
    return sanitized


def _open_target_spreadsheet(
    config: MetricsConfig,
    factory: Callable[[str], Any],
) -> Any:
    """Authenticate and open the configured spreadsheet with actionable diagnostics."""
    target_label = config.sheet_url or config.sheet_id
    try:
        client = factory(config.google_creds_path)
        spreadsheet = (
            client.open_by_url(config.sheet_url)
            if config.sheet_url
            else client.open_by_key(config.sheet_id)
        )
    except Exception as exc:
        if type(exc).__name__ == "SpreadsheetNotFound":
            msg = f"Target Google Sheet not found: {target_label}"
            logger.error("%s (%s)", msg, exc)
            raise RuntimeError(msg) from exc
        if isinstance(exc, (PermissionError, FileNotFoundError)) or "403" in str(exc):
            msg = (
                f"Google Sheets authorization failed for {target_label}: "
                f"verify credentials and edit permissions ({exc})"
            )
            logger.error("%s", msg)
            raise RuntimeError(msg) from exc
        raise
    return spreadsheet


def _prepare_worksheet(
    spreadsheet: Any,
    tab_name: str,
    rows: list[list[Any]],
) -> Any:
    """Clear an existing worksheet or create it only when WorksheetNotFound is raised."""
    try:
        ws = spreadsheet.worksheet(tab_name)
        ws.clear()
        logger.debug("Cleared existing worksheet tab: %s", tab_name)
        return ws
    except Exception as exc:
        if type(exc).__name__ != "WorksheetNotFound":
            msg = f"Failed to access worksheet '{tab_name}': {exc}"
            logger.error("%s", msg)
            raise RuntimeError(msg) from exc
        num_cols = max(len(rows[0]), 1) if rows else 1
        logger.debug("Creating missing worksheet tab: %s", tab_name)
        return spreadsheet.add_worksheet(
            title=tab_name,
            rows=max(len(rows), 1),
            cols=num_cols,
        )


def _update_worksheet_with_retry(
    ws: Any,
    tab_name: str,
    rows: list[list[Any]],
    synced_count: int,
    total_tabs: int,
) -> None:
    """Push sanitized rows to a worksheet with bounded retries on transient errors."""
    for attempt in range(1, _MAX_UPDATE_ATTEMPTS + 1):  # pragma: no branch
        try:
            ws.update(rows)
            return
        except (TimeoutError, ConnectionError) as exc:
            if attempt < _MAX_UPDATE_ATTEMPTS:
                logger.debug(
                    "Transient error updating tab '%s' (attempt %d/%d): %s",
                    tab_name,
                    attempt,
                    _MAX_UPDATE_ATTEMPTS,
                    exc,
                )
                time.sleep(0.5 * attempt)
                continue
            msg = (
                f"Partial Google Sheets sync failure on tab '{tab_name}' "
                f"after {_MAX_UPDATE_ATTEMPTS} attempts "
                f"({synced_count}/{total_tabs} tabs synced): {exc}"
            )
            logger.error("%s", msg)
            raise RuntimeError(msg) from exc


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
        config: Active MetricsConfig specifying target sheet and credentials.
        payloads: Mapping of worksheet tab names to 2D row matrices.
        progress: Optional reporter receiving per-tab sync progress updates.
        client_factory: Optional gspread client factory injected for testing.

    Raises:
        ValueError: If neither config.sheet_url nor config.sheet_id is set.
        RuntimeError: If the target sheet is missing, inaccessible, or fails mid-sync.
    """
    if not config.sheet_url and not config.sheet_id:
        msg = "Google Sheets sync requires sheet_url or sheet_id (config.toml, ENV, or --sheet-url)"
        raise ValueError(msg)

    logger.info("Starting Google Sheets sync across %d tab(s)", len(payloads))

    # --- Authenticate & Open Target Spreadsheet ---
    factory = _default_gspread_client if client_factory is None else client_factory
    spreadsheet = _open_target_spreadsheet(config, factory)
    resolved_url = str(getattr(spreadsheet, "url", config.sheet_url or config.sheet_id))
    logger.log(VERBOSE, "Opened target Google Sheet: %s", resolved_url)

    # --- Clear or Provision Each Tab & Push Rows ---
    tab_items = list(payloads.items())
    for idx, (tab_name, rows) in enumerate(tab_items, start=1):
        sanitized_rows = _sanitize_rows(rows)
        ws = _prepare_worksheet(spreadsheet, tab_name, sanitized_rows)
        _update_worksheet_with_retry(ws, tab_name, sanitized_rows, idx - 1, len(tab_items))
        logger.debug("Synced tab '%s' (%d row(s))", tab_name, len(sanitized_rows))
        if progress is not None:
            progress.update(f"Synced tab {tab_name}", current=idx, total=len(tab_items))

    logger.info("Completed Google Sheets sync: %d tab(s) updated", len(tab_items))
    return resolved_url
