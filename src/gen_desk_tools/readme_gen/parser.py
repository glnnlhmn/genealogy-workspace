"""Path: src/gen_desk_tools/readme_gen/parser.py

AST-driven metadata extraction for Python source modules.

Operational Role:
    Inspects Python files without side-effect imports to extract canonical
    one-line descriptions, PEP 440 __version__ strings, and __all__ public
    symbol exports for automated README.md generation.

Functions:
    extract_module_metadata: Parse a Python file via AST and return metadata fields.
"""

from __future__ import annotations

import ast
from pathlib import Path

__version__ = "1.0.0+build.1"

__all__ = [
    "extract_module_metadata",
]

_HEADER_PREFIXES: tuple[str, ...] = ("Path:", "Name:", "<!--", "-->")


def _extract_docstring_summary(tree: ast.Module) -> str:
    """Return the first non-metadata line from a module docstring, or a fallback."""
    doc = ast.get_docstring(tree)
    if not doc:
        return "No description available."

    for raw_line in doc.splitlines():
        line = raw_line.strip()
        if line and not line.startswith(_HEADER_PREFIXES):
            return line

    return "No description available."


def _extract_string_list(node: ast.expr) -> str:
    """Format an AST list of string constants into a comma-separated backtick string."""
    if not isinstance(node, ast.List):
        return ""
    names = [
        elt.value
        for elt in node.elts
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
    ]
    return ", ".join(f"`{name}`" for name in names)


def _extract_assignments(tree: ast.Module) -> tuple[str, str]:
    """Extract __version__ and __all__ assignments from top-level module statements."""
    version = "Unversioned"
    all_exports = ""

    for node in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None

        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value

        if value is None:
            continue

        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            if target.id == "__version__" and isinstance(value, ast.Constant):
                version = str(value.value)
            elif target.id == "__all__":
                all_exports = _extract_string_list(value)

    return version, all_exports


def extract_module_metadata(file_path: Path) -> dict[str, str]:
    """Parse a Python source file using AST to extract description, version, and exports.

    Returns a dictionary containing 'description', 'version', and 'all_exports'.
    Never raises on syntax or I/O failures; records the error in 'description' instead.
    """
    metadata = {
        "description": "No description available.",
        "version": "Unversioned",
        "all_exports": "",
    }
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        metadata["description"] = _extract_docstring_summary(tree)
        version, all_exports = _extract_assignments(tree)
        metadata["version"] = version
        metadata["all_exports"] = all_exports
    except Exception as exc:
        metadata["description"] = f"Extraction error: {exc}"

    return metadata
