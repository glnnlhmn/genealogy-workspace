<!--Path: .skills/gsi_pipeline/SKILL.md-->
---
name: gsi-pipeline
description: Formats, generates, and routes Python source/test files, Markdown documentation/prompt files, and JSON schemas/data for ingestion by the Genealogy Script Importer (GSI). Use when generating or refactoring Python code, markdown files, or JSON assets for the genealogy workspace or staging files in download/.
---
# Genealogy Script Importer (GSI) Intake Pipeline

Enforces routing header conventions and intake workflows across Python scripts, Markdown documentation, and JSON assets for ingestion via `gsi` (`src/system/gsi.py`).

## When to Use

Apply these standards whenever:
- Generating or refactoring Python source code, utilities, or test suites.
- Generating Markdown documentation, prompts, topic architectures, or notes.
- Generating or editing JSON schemas, configs, or data payloads.
- Staging files in `download/` or providing commands to ingest, relocate, or auto-execute files via `gsi`.

---

## 1. File Routing Headers by Format

### Python Source & Tests
Must follow single-field header docstring architecture starting on Line 1 with `"""` (PEP 257 compliant; avoids Ruff `D100`/`E402` lint failures).

- **Line 1:** Starts with `"""`.
- **Line 1 or Line 2:** Must declare `Path: [relative/path/to/file.py]`.
- **No separate `Name:` field.**

```python
"""Path: src/gda/model/atom/date.py

Genealogical event date representations and uncertainty modifiers.
"""

from __future__ import annotations
```

### Markdown Files (`.md`)
Declare the canonical path on **Line 1** using an HTML comment tag:

```markdown
<!--Path: prompts/topics/topic_library_architecture.md-->

# Topic Library Architecture
```

- Must begin strictly on Line 1 with `<!--Path: [relative/path/to/file.md]-->`.

### JSON Files (`.json`)
Declare the canonical path as the **top-level first key** named `"_path"`:

```json
{
  "_path": "schemas/dev/intake/location_import.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object"
}
```

- Always place `"_path": "relative/path/to/file.json"` as the first property of root JSON objects.

---

## 2. Ingestion Pipeline & Execution Commands

Staged files deposited into `download/` are ingested using the `gsi` alias (`python src/system/gsi.py`):

1. **Standard Ingestion:**
   Extracts destination paths, creates an atomic backup in `archive/backups_[project]/`, relocates files to their canonical destinations, and runs pytest verification:
   ```bash
   gsi
   ```

2. **Ingest and Auto-Execute (`-r` / `--run`):**
   Discovers staged files, moves them to destination paths, and immediately runs the renamed file:
   ```bash
   gsi -r
   ```

3. **Force Overwrite (`-f` / `--force`):**
   Bypasses overwrite prompts when replacing existing files:
   ```bash
   gsi -f
   ```

4. **Clean Staging (`-c` / `--clean`):**
   Cleans unparsed or residual items from `download/`:
   ```bash
   gsi -c
   ```

---

## 3. Workflow Rules for Generated Content

When providing files destined for the workspace:
- Always embed the correct routing header on Line 1 matching the file type (Python docstring, Markdown HTML comment, or JSON `"_path"` key).
- Conclude file generation with the appropriate `gsi` ingestion command (e.g., `gsi` or `gsi -r`).
