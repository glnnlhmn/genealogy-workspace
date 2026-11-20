<!--Path: src/gen_desk_tools/coverage_gaps/README.md-->
# GenDesk Coverage Gaps (gd-gaps)

## Architectural Role
Parses line numbers, ranges, or branch arrow spans and extracts line-numbered source context into reports.

## Quality Gate & Verification Status
- **Quality Gate:** 100.00% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gen_desk_tools/test_coverage_gaps/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `cli.py` | `1.0.0+build.1` | Command-line interface entrypoint for GenDesk Coverage Gaps (gaps). |
| `extractor.py` | `1.0.0+build.2` | Line-range parser and coverage gap report generator for GenDesk Coverage Gaps (gaps). |

## Public Exports & Consumption Contract
Exports: `build_parser`, `generate_gap_report`, `main`, `parse_gap_range`, `run`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 68782538c678387b -->
