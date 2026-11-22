"""Path: src/gen_desk_tools/metrics/collectors/import_collector.py

AST-based import dependency graph and architectural boundary violation collector.

Operational Role:
    Parses non-stdlib imports across all scoped Python modules (including
    multi-level relative, star, and string-literal dynamic imports), maps
    source and target modules to architectural subsystem layers, and flags
    unidirectional GDA dependency boundary violations with 4-tier diagnostic
    logging and syntax/encoding resilience.

Classes:
    ImportEdgeRecord: Single directed import edge with boundary evaluation.

Functions:
    collect_import_graph: Build the directed import graph across active batches.
"""

from __future__ import annotations

import ast
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from gen_desk_tools.core.logging import VERBOSE
from gen_desk_tools.metrics.collectors.radon_collector import discover_batch_files
from gen_desk_tools.metrics.config import BatchDefinition
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.7"

__all__ = [
    "ImportEdgeRecord",
    "collect_import_graph",
]

logger = logging.getLogger(__name__)

# Ordered from most specific to most general so sub-layers match before "gda".
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

# Unidirectional dependency matrix governing internal GDA package imports.
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
    """Evaluate whether importing target_layer from source_layer violates architecture.

    Returns (True, reason) only when source_layer has an explicit allowlist and
    target_layer is an internal workspace layer outside that allowlist.
    """
    allowed = _ALLOWED_INTERNAL_TARGETS.get(source_layer)
    if allowed is not None and target_layer in _INTERNAL_LAYERS and target_layer not in allowed:
        return True, f"{source_layer} cannot import {target_layer}"
    return False, ""


def _is_stdlib(module_name: str) -> bool:
    """Return True when the top-level package belongs to the Python standard library."""
    return module_name.split(".", 1)[0] in sys.stdlib_module_names


def _resolve_relative_import(
    source_module: str,
    is_package: bool,
    level: int,
    module: str | None,
) -> str | None:
    """Resolve a relative ImportFrom node to an absolute dotted module name."""
    pkg_parts = source_module.split(".") if is_package else source_module.split(".")[:-1]
    up = level - 1
    if up > len(pkg_parts):
        return module
    base_parts = pkg_parts[: len(pkg_parts) - up] if up > 0 else pkg_parts
    if module:
        return ".".join([*base_parts, module])
    return ".".join(base_parts) if base_parts else None


def _extract_dynamic_import_target(node: ast.Call) -> str | None:
    """Extract a string-literal module name from importlib.import_module or __import__."""
    is_import_call = (
        isinstance(node.func, ast.Attribute) and node.func.attr == "import_module"
    ) or (isinstance(node.func, ast.Name) and node.func.id in {"import_module", "__import__"})
    if not is_import_call or not node.args:
        return None
    first_arg = node.args[0]
    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
        target = first_arg.value.strip()
        return target or None
    return None


def _extract_imports(
    tree: ast.Module,
    source_module: str,
    is_package: bool,
) -> tuple[str, ...]:
    """Extract sorted unique non-stdlib imported module names from an AST."""
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                resolved = _resolve_relative_import(
                    source_module,
                    is_package,
                    node.level,
                    node.module,
                )
                if resolved:  # pragma: no branch
                    imported.add(resolved)
            else:
                assert node.module is not None
                imported.add(node.module)
        elif isinstance(node, ast.Call):
            dynamic_target = _extract_dynamic_import_target(node)
            if dynamic_target:
                imported.add(dynamic_target)
    return tuple(sorted(mod for mod in imported if not _is_stdlib(mod)))


def collect_import_graph(
    workspace_root: Path,
    batches: tuple[BatchDefinition, ...],
    *,
    progress: ProgressReporter | None = None,
) -> tuple[ImportEdgeRecord, ...]:
    """Build the directed import dependency graph and flag layer boundary violations.

    Files with syntax, encoding, or read errors are logged at ERROR level and
    skipped gracefully so remaining modules in the batch are still analyzed.
    """
    logger.info("Starting import dependency graph collection across %d batch(es)", len(batches))

    # --- Discover Scoped Modules ---
    discovered = [
        (batch.id, py_file)
        for batch in batches
        for py_file in discover_batch_files(workspace_root, batch)
    ]
    edges: list[ImportEdgeRecord] = []
    total = len(discovered)
    logger.log(VERBOSE, "Analyzing imports across %d discovered Python module(s)", total)

    # --- Extract Imports & Evaluate Layer Boundaries ---
    for idx, (batch_id, py_file) in enumerate(discovered, start=1):
        rel_path = py_file.relative_to(workspace_root).as_posix()
        source_mod = _module_name_from_path(rel_path)
        source_layer = _classify_layer(source_mod)
        is_package = py_file.name == "__init__.py"
        tree: ast.Module | None = None
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError, OSError) as exc:
            logger.error("Import graph analysis failed for %s: %s", rel_path, exc)

        if tree is not None:
            targets = _extract_imports(tree, source_mod, is_package)
            logger.debug("Extracted %d non-stdlib import(s) from %s", len(targets), rel_path)
            for target_mod in targets:
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

    logger.info("Completed import dependency graph: %d edge(s) collected", len(edges))
    return tuple(edges)
