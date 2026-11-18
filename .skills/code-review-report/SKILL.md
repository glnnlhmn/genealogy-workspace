---
# Path: .skills/code-review-report/SKILL.md
name: code-review-report
description: Conduct a structured collaborative peer-review report on source code and tests. Use when the user asks to "review code and report", requests a team code review, or shares files/modules for quality, style, architecture, code creep, best-practice, and test completeness evaluation before refactoring.
---

# Code Review and Report

Conduct a structured, peer-level code review delivered directly in chat as a numbered diagnostic report. Hold off on generating full refactored code files until the findings and design alternatives have been discussed and confirmed with the user.

## When to Use

- The user says "review code and report" or asks for a code review / peer review of one or more modules.
- The user wants an architectural, style, dependency, and test-completeness audit in chat before deciding on code changes.
- Note: When the user asks for a full package or workspace "Ground-Up Direct-Read Audit" tracked in a Google Sheet, use `ground-up-code-audit` instead.

## Review Dimensions

Evaluate the provided code across all applicable dimensions:

1. **Strengths and Weaknesses**: Identify well-engineered patterns worth preserving alongside structural flaws, fragile logic, or readability bottlenecks.
2. **Project Coding Style**: Verify adherence to project conventions (module docstrings with `Path:` routing headers, `__version__`, `__all__`, `from __future__ import annotations`, Ruff formatting/linting norms, strict type annotations, and naming conventions).
3. **Lower-Level Library Usage**: Check whether the code makes optimal use of foundational project layers (`gda.core.*`, `gda.io.*`, `gda.util.*`) and standard/third-party libraries (Pydantic `strict=True`, `ConfigDict`, `functools.total_ordering`, and `re` pre-compilation) rather than reinventing helpers.
4. **Code Creep and Scope Bloat**: Flag responsibilities that belong in a different architectural layer, dead code, speculative abstractions, or feature bloat.
5. **Best Practices and Edge Cases**: Assess immutability, silent type coercion hazards (`bool` as `int`, unintended whitespace stripping), boundary conditions, error handling with structured error codes/details, and performance/security hygiene.
6. **Architectural Boundaries and Contracts**: Verify strict one-way dependency flow across tiers (`core/io/util` -> `model` -> `db` -> `repository/entity` -> `engine/manager` -> `cli/ui`) and alignment with domain schemas and invariants.
7. **Test Completeness and Quality**: Evaluate whether tests cover happy paths, boundary off-by-one cases, invalid type vectors, custom dunder protocols, and branch coverage gaps without relying on disk I/O in unit tests.

## Report Format

Deliver the review directly in chat using clear Markdown structure with **sequentially numbered findings** (`1.`, `2.`, `3.`, ...) so every item is easy to reference in discussion:

### 1. Executive Summary & Strengths

- Brief assessment of overall readiness and key strengths to keep intact.

### 2. Numbered Review Findings

List all findings sequentially (`1.`, `2.`, `3.`, ...), tagging each with severity (**Blocker**, **Warning**, or **Suggestion**) and category:

- **1. [Severity - Category] Short Title**: Explain what was observed, why it matters (referencing specific functions, classes, or line ranges), and the trade-offs or design alternatives to consider.

### 3. Test Suite Assessment (if tests are included)

- Continue the sequential numbering (`N.`, `N+1.`, ...) for test coverage, missing edge cases, or test-structure observations.

### 4. Discussion & Next Steps

- Highlight the top 1 to 3 decision points or alternative approaches and ask the user which findings they want to discuss or approve before generating updated code.

## Guardrails

- **Hold on Code Fixes**: Do NOT output full rewritten modules or unsolicited patches in the initial review report. Short inline snippets (1 to 5 lines) are permitted only when needed to illustrate a finding or compare design alternatives.
- **Peer-Review Tone**: Be candid, specific, and constructive: like a senior engineering teammate reviewing a pull request. Avoid generic praise or vague advice.
- **No Em-Dashes or En-Dashes**: Use hyphens or colons in report prose and skill documentation.