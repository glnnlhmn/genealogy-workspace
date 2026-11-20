"""Path: src/gen_desk_tools/metrics/exporters/report_exporter.py

Local UTF-8 JSON report exporter for gd_metrics telemetry snapshots.

Operational Role:
    Serializes the nine-tab telemetry payload dictionary along with UTC
    generation metadata and active scopes atomically into gd_metrics_report.json
    inside the configured local report directory via gen_desk_tools.core.

Functions:
    write_local_json_report: Write all telemetry tab matrices to a JSON file.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gen_desk_tools.core.backup import atomic_write_text
from gen_desk_tools.core.workspace import resolve_report_path
from gen_desk_tools.metrics.config import MetricsConfig

__version__ = "1.0.0+build.3"

__all__ = ["write_local_json_report"]


def write_local_json_report(
    config: MetricsConfig,
    payloads: Mapping[str, list[list[Any]]],
) -> Path:
    """Write all telemetry tab matrices atomically to a local UTF-8 JSON snapshot.

    Creates config.local_report_dir if it does not already exist and returns
    the written gd_metrics_report.json path.
    """
    out_path = resolve_report_path(
        config.workspace_root,
        {},
        "gd_metrics_report.json",
        override_dir=config.local_report_dir,
    )
    document = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "workspace_root": config.workspace_root.as_posix(),
        "scopes": list(config.scopes),
        "tabs": dict(payloads),
    }
    atomic_write_text(out_path, json.dumps(document, indent=2))
    return out_path
