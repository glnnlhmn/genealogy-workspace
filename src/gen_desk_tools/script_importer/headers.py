"""Path: src/gen_desk_tools/script_importer/headers.py

Multi-format routing header parser for GenDesk Script Importer (gsi).

Operational Role:
    Inspects staged candidate files in download/ across Python, Markdown
    (including YAML frontmatter), YAML, JSON, TOML, plain-text downloads,
    and Jupyter Notebook formats to extract canonical workspace destination
    paths while enforcing root containment guards.

Functions:
    parse_metadata_header: Extract destination filename and resolved workspace path.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from gen_desk_tools.core.workspace import ensure_within_root

__version__ = "1.0.0+build.3"

__all__ = [
    "parse_metadata_header",
]

_TRAILING_DELIMS_RE = re.compile(r'(?:[\s\-]*-->|[\s\-]*\*/|\s*"""|\s*\'\'\'|--+)\s*$')
_YAML_FRONTMATTER_RE = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---", re.DOTALL)


def _clean_token(value: str) -> str:
    """Strip trailing comment delimiters, quotes, and surrounding whitespace."""
    return _TRAILING_DELIMS_RE.sub("", value).strip().strip("\"'")


def _extract_ipynb_path(content: str) -> tuple[str | None, str | None]:
    """Extract optional name and path from Jupyter Notebook metadata or first cell."""
    nb_data = json.loads(content)
    metadata = nb_data.get("metadata", {})
    target_name = metadata.get("_name") or metadata.get("name") or nb_data.get("_name")
    target_path = metadata.get("_path") or metadata.get("path") or nb_data.get("_path")

    if not target_path:
        cells = nb_data.get("cells", [])
        if cells and cells[0].get("cell_type") in ("raw", "markdown", "code"):
            first_cell = "".join(cells[0].get("source", []))
            name_m = re.search(
                r"(?:#|<!--)[ \t]*Name:[ \t]*([^\r\n>*/]+)", first_cell, re.IGNORECASE
            )
            path_m = re.search(r"(?:#|<!--)[ \t]*Path:[ \t]*([^\r\n>]+)", first_cell, re.IGNORECASE)
            if name_m:
                target_name = name_m.group(1).strip()
            if path_m:
                target_path = path_m.group(1).strip()

    return (str(target_name) if target_name else None), (str(target_path) if target_path else None)


def _extract_structured_path(head_block: str) -> tuple[str | None, str | None]:
    """Extract _name/_path keys from JSON, TOML, or YAML header blocks."""
    name_m = re.search(r'["\']?_?name["\']?\s*[:=]\s*["\']?([^"\'\r\n]+)["\']?', head_block)
    path_m = re.search(r'["\']?_?path["\']?\s*[:=]\s*["\']?([^"\'\r\n]+)["\']?', head_block)
    target_name = name_m.group(1).strip() if name_m else None
    target_path = path_m.group(1).strip() if path_m else None
    return target_name, target_path


def _extract_generic_path(head_block: str) -> tuple[str | None, str | None]:
    """Extract Path: and optional Name: from docstrings, HTML comments, or line comments."""
    target_path: str | None = None
    target_name: str | None = None

    docstring_m = re.search(
        r'^(?:"""|\'\'\')[ \t]*Path:[ \t]*["\']?([^\r\n"\']+)["\']?',
        head_block,
        re.MULTILINE | re.IGNORECASE,
    )
    if docstring_m:
        target_path = docstring_m.group(1).strip()
    else:
        generic_m = re.search(
            r"^[ \t]*(?:#|<!--|//|/\*|\*)*[ \t]*Path:[ \t]*[\"\']?([^\r\n>\"\*]+)[\"\']?",
            head_block,
            re.MULTILINE | re.IGNORECASE,
        )
        if generic_m:
            target_path = generic_m.group(1).strip()

    name_m = re.search(
        r"^[ \t]*(?:#|<!--|//|/\*|\*)*[ \t]*Name:[ \t]*[\"\']?([^\r\n>*/\"']+)[\"\']?",
        head_block,
        re.MULTILINE | re.IGNORECASE,
    )
    if name_m:
        target_name = name_m.group(1).strip()

    return target_name, target_path


def parse_metadata_header(file_path: Path, root_dir: Path) -> tuple[str | None, Path | None]:
    """Extract destination filename and resolved workspace path from a staged file.

    Returns (None, None) if the file cannot be read, lacks a routing header, or
    resolves outside root_dir.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None, None

    suffix = file_path.suffix.lower()
    head_block = "\n".join(content.splitlines()[:25])
    target_name: str | None = None
    target_path_str: str | None = None

    # --- Format-Specific Extraction ---
    if suffix == ".ipynb":
        try:
            target_name, target_path_str = _extract_ipynb_path(content)
        except Exception:
            return None, None
    elif suffix in (".json", ".toml", ".yaml", ".yml", ".txt"):
        target_name, target_path_str = _extract_structured_path(head_block)
    elif suffix == ".md":
        fm_match = _YAML_FRONTMATTER_RE.match(content)
        if fm_match:
            target_name, target_path_str = _extract_structured_path(fm_match.group(1))

    # --- Generic Docstring / Comment Fallback ---
    if not target_path_str:
        gen_name, gen_path = _extract_generic_path(head_block)
        target_path_str = gen_path
        if not target_name:
            target_name = gen_name

    if not target_path_str:
        return None, None

    # --- Normalize & Enforce Root Containment ---
    cleaned_path = _clean_token(target_path_str)
    cleaned_name = _clean_token(target_name) if target_name else Path(cleaned_path).name

    raw_dest = root_dir / Path(cleaned_path)
    if raw_dest.is_dir() or cleaned_path.endswith(("/", "\\")):
        candidate_dest = raw_dest / cleaned_name
    else:
        candidate_dest = raw_dest

    try:
        resolved_dest = ensure_within_root(candidate_dest, root_dir)
    except ValueError:
        return None, None

    return cleaned_name, resolved_dest
