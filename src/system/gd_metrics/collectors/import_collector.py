"""Path: src/system/gd_metrics/collectors/import_collector.py

AST-based import dependency graph and architectural boundary violation collector.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

from system.gd_metrics.collectors.radon_collector import discover_batch_files
from system.gd_metrics.config import BatchDefinition
from system.gd_metrics.progress import ProgressReporter

__version__ = "1.0.0+build.3"

__all__ = [
    "ImportEdgeRecord",
    "collect_import_graph",
]

_LAYER_PREFIXES: tuple[tuple[str, str], ...] = (
    ("gda.core", "gda.core"),
    ("gda.enums", "gda.enums"),
    ("gda.io", "gda.io"),
    ("gda.model", "gda.model"),
    ("gda", "gda.other"),
    ("cli", "cli"),
    ("system", "system"),
    ("ancestry_desk", "ancestry_desk"),
)

_INTERNAL_LAYERS = frozenset(layer for _, layer in _LAYER_PREFIXES)

_ALLOWED_INTERNAL_TARGETS: dict[str, frozenset[str]] = {
    "gda.core": frozenset({"gda.core"}),
    "gda.enums": frozenset({"gda.enums"}),
    "gda.io": frozenset({"gda.core", "gda.io"}),
    "gda.model": frozenset({"gda.core", "gda.enums", "gda.model"}),
    "gda.other": frozenset({"gda.core", "gda.enums", "gda.io", "gda.model", "gda.other"}),
}


@dataclass(frozen=True)
class ImportEdgeRecord:
    """Single directed import edge with architectural boundary evaluation."""

    batch_id: str
    source_module: str
    imported_module: str
    source_layer: str
    target_layer: str
    boundary_violation: bool
    violation_reason: str


def _module_name_from_path(rel_path: str) -> str:
    """Convert a workspace-relative POSIX file path to a dotted Python module name."""
    cleaned = rel_path.removeprefix("src/").removesuffix(".py").replace("/", ".")
    return cleaned.removesuffix(".__init__")


def _classify_layer(module_name: str) -> str:
    """Map a dotted module name to its architectural subsystem layer."""
    for prefix, layer in _LAYER_PREFIXES:
        if module_name == prefix or module_name.startswith(f"{prefix}."):
            return layer
    return "third_party"


def _check_boundary(source_layer: str, target_layer: str) -> tuple[bool, str]:
    """Evaluate whether importing target_layer from source_layer violates architecture."""
    allowed = _ALLOWED_INTERNAL_TARGETS.get(source_layer)
    if allowed is not None and target_layer in _INTERNAL_LAYERS and target_layer not in allowed:
        return True, f"{source_layer} cannot import {target_layer}"
    return False, ""


def _is_stdlib(module_name: str) -> bool:
    """Return True when the top-level package belongs to the Python standard library."""
    return module_name.split(".", 1)[0] in sys.stdlib_module_names


def _extract_imports(tree: ast.Module) -> tuple[str, ...]:
    """Extract sorted unique non-stdlib imported module names from AST."""
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return tuple(sorted(mod for mod in imported if not _is_stdlib(mod)))


def collect_import_graph(
    workspace_root: Path,
    batches: tuple[BatchDefinition, ...],
    *,
    progress: ProgressReporter | None = None,
) -> tuple[ImportEdgeRecord, ...]:
    """Build the directed import dependency graph and flag layer boundary violations."""
    discovered = [
        (batch.id, py_file)
        for batch in batches
        for py_file in discover_batch_files(workspace_root, batch)
    ]
    edges: list[ImportEdgeRecord] = []
    total = len(discovered)

    for idx, (batch_id, py_file) in enumerate(discovered, start=1):
        rel_path = py_file.relative_to(workspace_root).as_posix()
        source_mod = _module_name_from_path(rel_path)
        source_layer = _classify_layer(source_mod)
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except SyntaxError:
            tree = None

        if tree is not None:
            for target_mod in _extract_imports(tree):
                target_layer = _classify_layer(target_mod)
                violation, reason = _check_boundary(source_layer, target_layer)
                edges.append(
                    ImportEdgeRecord(
                        batch_id=batch_id,
                        source_module=source_mod,
                        imported_module=target_mod,
                        source_layer=source_layer,
                        target_layer=target_layer,
                        boundary_violation=violation,
                        violation_reason=reason,
                    )
                )

        if progress is not None:
            progress.update("Import dependency graph", current=idx, total=total)

    return tuple(edges)
