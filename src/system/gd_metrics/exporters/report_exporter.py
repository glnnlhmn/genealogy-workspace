"""Path: src/system/gd_metrics/exporters/report_exporter.py

Local UTF-8 JSON report exporter for gd_metrics telemetry snapshots.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from system.gd_metrics.config import MetricsConfig

__version__ = "1.0.0+build.1"

__all__ = ["write_local_json_report"]


def write_local_json_report(
    config: MetricsConfig,
    payloads: Mapping[str, list[list[Any]]],
) -> Path:
    """Write all telemetry tab matrices to a local UTF-8 JSON snapshot."""
    config.local_report_dir.mkdir(parents=True, exist_ok=True)
    out_path = config.local_report_dir / "gd_metrics_report.json"
    document = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "workspace_root": config.workspace_root.as_posix(),
        "scopes": list(config.scopes),
        "tabs": dict(payloads),
    }
    out_path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return out_path
