<!--Path: src/gen_desk_tools/metrics/exporters/README.md-->
# GenDesk Metrics Exporters (gen_desk_tools.metrics.exporters)

## Architectural Role
Telemetry report exporters building worksheet tab payloads and writing local JSON reports or syncing to Google Sheets.

## Quality Gate & Verification Status
- **Quality Gate:** 100.00% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gen_desk_tools/test_metrics/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `payload_builders.py` | `1.0.0+build.5` | Row-matrix builders for all nine gd_metrics Google Sheets telemetry tabs. |
| `report_exporter.py` | `1.0.0+build.3` | Local UTF-8 JSON report exporter for gd_metrics telemetry snapshots. |
| `sheets_exporter.py` | `1.0.0+build.3` | Direct Google Sheets exporter for gd_metrics telemetry. |

## Public Exports & Consumption Contract
Exports: `TAB_NAMES`, `__version__`, `build_sheet_payloads`, `sync_to_google_sheets`, `write_local_json_report`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 6ca50fdf019265b6 -->
