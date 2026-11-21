<!--Path: .skills/python-module-standards/SKILL.md-->
---
name: python-module-standards
description: Universal Python module headers, PEP 440 build versioning, Ruff formatting/linting, mypy type safety, UTF-8 I/O, and package README parity. Use whenever creating, editing, or refactoring Python source files, configuration, or package documentation in any Python project.
---

# Python Module Standards

Project-agnostic engineering conventions for Python 3.13 modules, formatting, typing, and documentation.

## When to Use

- Creating or refactoring Python modules and packages.
- Setting up module headers, versioning, or package `README.md` files.
- Running formatting, linting, and static type checks before committing.

## Standards

### 1. File Headers and Versioning

- Open every Python file on Line 1 with a triple double-quoted module docstring containing `Path: <relative/path/to/file.py>` on Line 1 or Line 2. Do not add `# Name:` or `# Path:` comment headers.
- Place `from __future__ import annotations` immediately after the module docstring, followed by grouped alphabetical imports and `__version__`.
- Declare `__version__` using PEP 440 local build identifiers with monotonic cumulative counters (`<major>.<minor>.<rev>+build.<counter>`). Increment the build counter on each regeneration; never change major, minor, or rev unless explicitly directed.

### 2. Tooling, Formatting, and Typing

- Target Python 3.13 with a 100-character maximum line length configured in `pyproject.toml`.
- Run `rfmt` (or `ruff format` and `ruff check --fix`) to enforce consistent formatting and alphabetical import sorting.
- Run `mypy` on modified packages to maintain zero static type errors.
- Keep Radon cyclomatic complexity at Grade A or B by splitting large orchestrators into focused helper functions.

### 3. Safe I/O and Documentation Parity

- Enforce `encoding="utf-8"` on all file read and write operations.
- Verify path existence (`Path.exists()`) before destructive file operations and use atomic writes (`tempfile.mkstemp` + `os.replace`) when mutating important files.
- Maintain a current `README.md` in every architectural package directory documenting its role, public exports, and verification status.
- Deliver files directly in native formats (`.py`, `.md`, `.json`, `.toml`) without wrapping them in string-emitter scripts.

## Gotchas

- Never embed unresolved bracketed tokens or inline citation markers inside generated Markdown documentation or Python string literals.
- Treat implementation, tests, and package `README.md` updates as one atomic unit of delivery.
