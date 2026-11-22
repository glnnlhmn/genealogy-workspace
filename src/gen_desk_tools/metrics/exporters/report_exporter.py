"""Path: src/gen_desk_tools/metrics/exporters/report_exporter.py

Local UTF-8 JSON report exporter for gd_metrics telemetry snapshots.

Operational Role:
    Serializes the nine-tab telemetry payload dictionary along with UTC
    generation metadata and active scopes atomically into gd_metrics_report.json
    inside the configured local report directory via gen_desk_tools.core, with
    4-tier diagnostic logging and Windows/Google Drive file-lock retry handling.

Functions:
    write_local_json_report: Write all telemetry tab matrices to a JSON file.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gen_desk_tools.core.backup import atomic_write_text
from gen_desk_tools.core.logging import VERBOSE
from gen_desk_tools.core.workspace import resolve_report_path
from gen_desk_tools.metrics.config import MetricsConfig

__version__ = "1.0.0+build.5"

__all__ = ["write_local_json_report"]

logger = logging.getLogger(__name__)

_MAX_WRITE_ATTEMPTS = 3


def write_local_json_report(
    config: MetricsConfig,
    payloads: Mapping[str, list[list[Any]]],
) -> Path:
    """Write all telemetry tab matrices atomically to a local UTF-8 JSON snapshot.

    Creates config.local_report_dir if it does not already exist and returns
    the written gd_metrics_report.json path. Retries transient
    PermissionError locks (such as WinError 32 on Windows/Google Drive)
    before logging an ERROR and re-raising.
    """
    logger.info("Starting local JSON report export across %d tab(s)", len(payloads))

    # --- Resolve Report Path & Serialize Snapshot ---
    out_path = resolve_report_path(
        config.workspace_root,
        {},
        "gd_metrics_report.json",
        override_dir=config.local_report_dir,
    )
    logger.log(VERBOSE, "Resolved local JSON report path: %s", out_path)

    document = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "workspace_root": config.workspace_root.as_posix(),
        "scopes": list(config.scopes),
        "tabs": dict(payloads),
    }
    serialized = json.dumps(document, indent=2)
    logger.debug("Serialized %d byte(s) for local JSON report %s", len(serialized), out_path)

    # --- Atomic Write With Transient File-Lock Retry ---
    for attempt in range(1, _MAX_WRITE_ATTEMPTS + 1):  # pragma: no branch
        try:
            atomic_write_text(out_path, serialized)
            break
        except PermissionError as exc:
            if attempt < _MAX_WRITE_ATTEMPTS:
                logger.debug(
                    "Transient file lock on %s (attempt %d/%d): %s",
                    out_path,
                    attempt,
                    _MAX_WRITE_ATTEMPTS,
                    exc,
                )
                time.sleep(0.25 * attempt)
                continue
            logger.error(
                "Failed to write local JSON report %s after %d attempt(s): %s",
                out_path,
                _MAX_WRITE_ATTEMPTS,
                exc,
            )
            raise

    logger.info("Completed local JSON report export: %s", out_path)
    return out_path
