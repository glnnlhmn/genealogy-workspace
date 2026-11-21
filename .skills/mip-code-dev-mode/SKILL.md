<!--Path: .skills/mip-code-dev-mode/SKILL.md-->
---
name: mip-code-dev-mode
description: Master Intelligence Profile (MIP) workflow controller for the genealogy-workspace repository. Use at session start or when coordinating development workflows, task completion gates, workspace path anchors, and skill delegation.
---

# MIP Code Dev Mode

Workflow controller for `genealogy-workspace` development sessions.

## When to Use

- Starting or coordinating a development session in `genealogy-workspace`.
- Enforcing session-level workflow safeguards, path anchors, and completion checks.
- Routing specialized work to dedicated skills rather than duplicating their rules.

## Workflow Control

1. **Resolve Live Layout:** Read `pyproject.toml` and live `gd-struct` output for directory layout. Do not hardcode directory trees.
2. **Load Context When Needed:** Read `references/workspace-conventions.md` for path anchors, coverage gates, and I/O safeguards. Load `data/profiles/glenn_profile.json` and `data/profiles/gda_profile.json` when operator or task/backlog context is needed.
3. **Delegate to Specialized Skills:**
   - **Code & Architecture:** `gda-library`, `gen-desk-tools`, `gda-system-cli`.
   - **Code & Test Quality:** `python-module-standards`, `python-code-commenting`, `python-testing-standards`.
   - **Intake, Backups & Coverage Gaps:** `gsi-pipeline`, `gen-desk-backup`, `extract-coverage-gaps`.
   - **Databases:** `create-database`, `update-database-schema`.
   - **Reviews & Audits:** `code-review-report`, `ground-up-code-audit`, `test-suite-audit`.
4. **Enforce Workflow Guardrails:**
   - Emit deliverables directly in native format with the `gsi` routing header on Line 1; never wrap deliverables in secondary string-emitter scripts.
   - Keep Markdown and string literals free of unresolved bracketed markers and inline citation tokens.
   - Treat implementation, tests, `README.md` updates, Ruff/mypy checks, and Git commits as one unit of work.
