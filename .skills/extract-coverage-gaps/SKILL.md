<!--Path: .skills/extract-coverage-gaps/SKILL.md-->
---
name: extract-coverage-gaps
description: Extract missing source lines and branch gap context with formatted line numbers into reports/ using gd-gaps (src/gen_desk_tools/coverage_gaps/). Use when the user pastes pytest-cov Missing tables, mentions coverage gaps, or asks to inspect missing lines from test runs.
---

# Extract Coverage Gaps (`gd-gaps`)

Workflow for parsing `pytest-cov` missing line/branch reports and generating line-numbered extraction commands using `gd-gaps` (`src/gen_desk_tools/coverage_gaps/`).

## When to Use

- When the user shares test coverage tables showing `Miss`, `Branch`, `BrPart`, or `Missing` columns.
- When the user asks to extract, inspect, or see missing coverage lines from a file.
- When troubleshooting failing coverage quality gates.

## Tool Invocation Syntax

Run from the workspace root (`G:/My Drive/genealogy-workspace`):

```bash
gd-gaps <file_path> [gap_range] [options]
```

Output is emitted by default to `reports/Coverage Gap + <filename> + <start-end>.txt`.

## Workflow: From Pytest Table to Extraction Command

### 1. Identify File Path and Gap Range

From a `pytest --cov` output table such as:

```text
Name                  Stmts   Miss Branch BrPart   Cover   Missing
------------------------------------------------------------------
src/gda/util/text.py    144     21     86     18  83.04%   217, 219, 221, 222->226, 227, 237->243, 249-250
```

- **Normalize the file path**: Convert Windows backslashes (`\`) to forward slashes (`/`).
- **Identify line bounds**:
  - For contiguous or tight clusters: select the minimum line to the maximum line (e.g., `217-295`).
  - For isolated single lines (e.g., `Missing: 67`): specify the exact line (e.g., `67`).
  - For widely separated gaps: generate individual commands for each distinct gap range.

### 2. Generate the Exact Shell Commands

```bash
# Range extraction
gd-gaps src/gda/util/text.py 217-295

# Single line extraction
gd-gaps src/gda/util/dates.py 67

# Full file with line numbers (omit gap argument)
gd-gaps src/gda/util/text.py
```

### 3. Inspect Generated Report

```bash
cat "reports/Coverage Gap + text.py + 217-295.txt"
```

## Gotchas & Guidelines

- **Branch Syntax**: Coverage tables often show branch indicators like `222->226`. Strip arrows (`->`) and take the span enclosing the branching statement and target.
- **Path Resolution**: Always specify file paths relative to the repository root anchor (`src/...`).
- **Reports Directory**: The tool automatically creates `reports/` if it does not already exist.
