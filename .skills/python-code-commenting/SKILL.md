---
name: python-code-commenting
description: Applies standardized PEP 257 and Google-style Python docstring and inline commenting conventions. Use when writing, refactoring, or documenting Python source files, modules, classes, or functions.
---

# Python Code Commenting

Maintains clean, high-value documentation across Python source files without repeating what type hints already communicate.

## When to Use

- Writing new Python modules, classes, or functions.
- Refactoring existing Python files to align docstrings and inline comments.
- Reviewing code documentation before commits or code reviews.

## Standards

### 1. Module Header Docstring

Start every Python file on Line 1 with a PEP 257 compliant docstring containing:

- **Line 1:** `Path: <relative/path/to/file.py>` inside the opening triple quotes (when working in a workspace that uses file routing headers).
- **Summary:** A concise one-line description of the module.
- **`Operational Role:`** A short paragraph explaining the module's architectural purpose and responsibilities.
- **`Classes:` / `Functions:`** A compact inventory listing the primary public symbols and their roles.

```python
"""Path: src/gda/core/config.py

Multi-tiered configuration engine for GDA Core components.

Operational Role:
    Defines strongly-typed schemas for application configuration and resolves
    settings across TOML files, environment variables, and runtime overrides.

Classes:
    DatabaseConfig: Connection parameters and SQLite PRAGMA settings.
    AppConfig: Root application configuration aggregator.
"""
```

### 2. Function, Method, and Class Docstrings (PEP 257 + Google Style)

- **One-line docstrings by default:** When a function's purpose, parameters, and return value are already clear from its name and Python type hints, use a crisp single-line PEP 257 docstring in imperative mood ending with a period (`"""Return True if path sits under a configured protected domain."""`).
- **Multiline Google-style docstrings when needed:** Expand to a multiline docstring only when there are behavioral nuances, precedence rules, format constraints, or specific exceptions that the type hints alone do not describe.
- **Do not redocument obvious type hints:** In `Args:` and `Returns:`, document only parameters or return semantics that carry extra requirements (such as expected string formats, side effects, or `None` behavior).
- **Plain markup:** Use plain Google-style prose and plain symbol names (or single backticks where helpful). Avoid Sphinx double-backticks (` ``...`` `).

```python
def create_safe_backup(
    target: Path,
    root: Path,
    cfg: dict[str, Any],
    *,
    dry_run: bool = False,
    timestamp: str | None = None,
) -> Path | None:
    """Create a timestamped atomic pre-write Safe Backup snapshot of target.

    Returns None without error when target does not yet exist on disk.

    Args:
        dry_run: Compute and return the planned snapshot path without writing.
        timestamp: Optional UTC timestamp override (YYYYMMDD_HHMMSS) for determinism.
    """
```

### 3. Boilerplate & Trivial Exemptions

- **`__init__`**: Omit when attributes and initialization arguments are already documented on the class (unless `__init__` performs non-trivial validation or side effects).
- **Dunder methods**: Omit on standard protocol methods (`__repr__`, `__str__`, `__eq__`, `__iter__`, `__enter__`, `__exit__`).
- **`__main__` blocks**: Do not add docstrings to `if __name__ == "__main__":` blocks.

### 4. Inline Comments (`#`)

Keep function bodies clean and readable—avoid commenting every `if` statement or guard clause:

- **Phase dividers in multi-step orchestrators:** Use `# --- Phase Name ---` (or `# --- Layer N: ... ---`) to separate distinct stages in longer functions.
- **Intent-only inline comments:** Add a brief `#` comment only when a non-obvious invariant, workaround, regex, or sorting key needs explanation.
- **Never restate syntax:** Avoid narrating obvious code (`# increment counter`, `# return result`).

## Gotchas

- Keep the opening `"""` on Line 1 of the file so module docstrings satisfy PEP 257 and Ruff `D100`/`E402` checks.
- Keep docstrings and `#` comments synchronized whenever logic or signatures change.