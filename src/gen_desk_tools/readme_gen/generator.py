"""Path: src/gen_desk_tools/readme_gen/generator.py

Package README.md rendering, scope filtering, hash protection, and execution engine.

Operational Role:
    Loads package definitions from readme_gen.toml, resolves exact or prefix-scoped
    targets (e.g., 'src', 'gda', 'cli', 'src/gda/model'), renders standardized
    Markdown with an embedded SHA-256 integrity tag, skips unchanged files,
    auto-updates unmodified generated files, and prompts before overwriting
    hand-edited READMEs.

Functions:
    compute_content_hash: Compute a short SHA-256 digest for rendered Markdown.
    is_unmodified_generated_readme: Check whether an existing README matches its embedded hash.
    load_package_definitions: Load package metadata entries from a TOML manifest.
    resolve_target_packages: Filter by alias/prefix or synthesize an unlisted directory entry.
    generate_package_readme: Render Markdown README content with an embedded hash tag.
    prompt_overwrite: Prompt the operator for yes/no/all/quit overwrite confirmation.
    run: Execute the end-to-end README generation workflow.
"""

from __future__ import annotations

import hashlib
import logging
import re
import tomllib
from pathlib import Path
from typing import Any

from gen_desk_tools.core.backup import atomic_write_text
from gen_desk_tools.core.config import load_gdt_config
from gen_desk_tools.core.logging import setup_tool_logger
from gen_desk_tools.core.workspace import resolve_workspace_root
from gen_desk_tools.readme_gen.parser import extract_module_metadata

__version__ = "1.0.0+build.2"

__all__ = [
    "DEFAULT_PACKAGES_REL_PATH",
    "SCOPE_ALIASES",
    "compute_content_hash",
    "generate_package_readme",
    "is_unmodified_generated_readme",
    "load_package_definitions",
    "prompt_overwrite",
    "resolve_target_packages",
    "run",
]

DEFAULT_PACKAGES_REL_PATH = Path("src/gen_desk_tools/readme_gen/readme_gen.toml")

SCOPE_ALIASES: dict[str, str] = {
    "gda": "src/gda",
    "cli": "src/cli",
    "gdt": "src/gen_desk_tools",
    "gen_desk_tools": "src/gen_desk_tools",
    "system": "src/system",
    "ancestry_desk": "src/ancestry_desk",
}

_HASH_TAG_RE = re.compile(r"\n<!-- gdrm-hash: ([0-9a-f]{16}) -->\n?\Z")


def compute_content_hash(body: str) -> str:
    """Return a 16-character SHA-256 hex digest for a rendered README body."""
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def is_unmodified_generated_readme(content: str) -> bool:
    """Return True if content ends with a valid gdrm-hash matching its preceding body."""
    normalized = content.replace("\r\n", "\n")
    match = _HASH_TAG_RE.search(normalized)
    if not match:
        return False
    body = normalized[: match.start()]
    return compute_content_hash(body) == match.group(1)


def load_package_definitions(packages_file: Path) -> tuple[str | None, list[dict[str, Any]]]:
    """Load optional default_root and package entries from a TOML manifest.

    Raises:
        FileNotFoundError: If packages_file does not exist.
    """
    if not packages_file.is_file():
        raise FileNotFoundError(f"Package manifest not found: {packages_file}")

    with packages_file.open("rb") as handle:
        data: dict[str, Any] = tomllib.load(handle)

    default_root = data.get("default_root")
    packages: list[dict[str, Any]] = list(data.get("packages", []))
    return (str(default_root) if default_root is not None else None), packages


def resolve_target_packages(
    all_packages: list[dict[str, Any]],
    root_path: Path,
    target: str | None = None,
) -> list[dict[str, Any]]:
    """Filter configured packages by alias/prefix, or synthesize an entry for a directory.

    Supports short subsystem aliases ('gda', 'cli', 'gdt', 'system', 'ancestry_desk')
    and directory prefixes ('src', 'src/gda/model').

    Raises:
        FileNotFoundError: If target matches neither configured packages nor a directory.
    """
    if not target:
        return all_packages

    raw_norm = target.strip().replace("\\", "/").rstrip("/")
    target_norm = SCOPE_ALIASES.get(raw_norm.lower(), raw_norm)

    # --- Exact or Prefix Match Against Configured Manifest ---
    matched = [
        pkg
        for pkg in all_packages
        if pkg.get("path") == target_norm or str(pkg.get("path", "")).startswith(f"{target_norm}/")
    ]
    if matched:
        return matched

    # --- Fallback: Synthesize Entry for Unlisted Existing Directory ---
    candidate = Path(target_norm)
    resolved_dir = candidate if candidate.is_absolute() else root_path / target_norm
    if resolved_dir.is_dir():
        return [
            {
                "path": target_norm,
                "title": f"Package Documentation ({target_norm})",
                "role": "Architectural subsystem package.",
                "test_path": f"tests/test_{Path(target_norm).name}",
                "quality_gate": ">= 95.0% Statement & Branch Coverage",
            }
        ]

    raise FileNotFoundError(f"Target package '{target}' not found in configuration or filesystem.")


def _render_subpackages_section(pkg_dir: Path) -> list[str]:
    """Build the Markdown Subpackages section for child directories inside pkg_dir."""
    subdirs = sorted(
        d for d in pkg_dir.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))
    )
    if not subdirs:
        return []

    lines: list[str] = ["## Subpackages"]
    for subdir in subdirs:
        init_file = subdir / "__init__.py"
        desc = "Subpackage domain entities and enumerations."
        if init_file.is_file():
            meta = extract_module_metadata(init_file)
            if meta["description"] != "No description available.":
                desc = meta["description"]

        link_label = (
            f"[{subdir.name}/]({subdir.name}/README.md)"
            if (subdir / "README.md").is_file()
            else f"`{subdir.name}/`"
        )
        lines.append(f"- **{link_label}**: {desc}")

    lines.append("")
    return lines


def generate_package_readme(pkg_info: dict[str, Any], root_path: Path) -> str:
    """Render standardized Markdown README.md content with an embedded SHA-256 tag."""
    pkg_dir = root_path / pkg_info["path"]
    py_files = sorted(
        f for f in pkg_dir.glob("*.py") if f.is_file() and not f.name.startswith((".", "__"))
    )

    # --- Header & Quality Gate ---
    lines: list[str] = [
        f"<!--Path: {pkg_info['path']}/README.md-->",
        f"# {pkg_info['title']}",
        "",
        "## Architectural Role",
        pkg_info["role"],
        "",
        "## Quality Gate & Verification Status",
        f"- **Quality Gate:** {pkg_info['quality_gate']}",
        f"- **Verification Suite:** `{pkg_info['test_path']}/`",
        "- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.",
        "",
    ]

    # --- Optional Subpackages & Module Table ---
    lines.extend(_render_subpackages_section(pkg_dir))
    lines.extend(
        [
            "## Module Inventory & Descriptions",
            "| Module | Version | Canonical Description |",
            "| :--- | :--- | :--- |",
        ]
    )
    for py_file in py_files:
        meta = extract_module_metadata(py_file)
        lines.append(f"| `{py_file.name}` | `{meta['version']}` | {meta['description']} |")

    # --- Public Exports & Integrity Footer ---
    lines.extend(["", "## Public Exports & Consumption Contract"])
    init_file = pkg_dir / "__init__.py"
    if init_file.is_file():
        init_meta = extract_module_metadata(init_file)
        if init_meta["all_exports"]:
            lines.append(f"Exports: {init_meta['all_exports']}.")
        else:
            lines.append("Modules export public interfaces explicitly declared in `__all__`.")
    else:
        lines.append("Direct submodule imports supported.")

    lines.extend(["", "---", "Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`)."])
    body = "\n".join(lines)
    digest = compute_content_hash(body)
    return f"{body}\n<!-- gdrm-hash: {digest} -->\n"


def prompt_overwrite(target_file: Path) -> str:
    """Prompt the operator to overwrite a hand-edited README.md ('y', 'n', 'a', or 'q')."""
    while True:
        try:
            choice = (
                input(
                    f"Hand-edited file '{target_file}' differs. Overwrite? "
                    "[y]es / [n]o / [a]ll / [q]uit: "
                )
                .strip()
                .lower()
            )
        except EOFError:
            return "q"

        if choice in ("y", "yes"):
            return "y"
        if choice in ("n", "no"):
            return "n"
        if choice in ("a", "all"):
            return "a"
        if choice in ("q", "quit"):
            return "q"
        print("Invalid choice. Please enter 'y', 'n', 'a', or 'q'.")


def _write_package_readmes(
    packages: list[dict[str, Any]],
    root_path: Path,
    *,
    force: bool,
    logger: logging.Logger,
) -> int:
    """Render and atomically write README.md files, skipping unchanged targets."""
    overwrite_all = force

    for pkg in packages:
        target_dir = root_path / pkg["path"]
        if not target_dir.is_dir():
            logger.info("[SKIP] Directory not found: %s", target_dir)
            continue

        readme_file = target_dir / "README.md"
        readme_content = generate_package_readme(pkg, root_path)

        if readme_file.is_file():
            existing_content = readme_file.read_text(encoding="utf-8").replace("\r\n", "\n")
            if existing_content == readme_content:
                logger.info("[UNCHANGED] %s", readme_file)
                continue

            if not overwrite_all and not is_unmodified_generated_readme(existing_content):
                decision = prompt_overwrite(readme_file)
                if decision == "n":
                    logger.info("[SKIP] User declined overwrite: %s", readme_file)
                    continue
                if decision == "a":
                    overwrite_all = True
                elif decision == "q":
                    logger.warning("[ABORT] Documentation generation cancelled by user.")
                    return 0

        atomic_write_text(readme_file, readme_content)
        logger.info("[OK] Generated: %s", readme_file)

    return 0


def run(
    target: str | None = None,
    *,
    force: bool = False,
    verbose: bool = False,
    debug: bool = False,
    root_dir: Path | None = None,
    config_path: Path | None = None,
    packages_config: Path | None = None,
) -> int:
    """Execute the dynamic README generation pipeline and return a POSIX exit code."""
    # --- Resolve Workspace, Config & Logger ---
    try:
        resolved_root = resolve_workspace_root(cfg_root=root_dir)
        cfg = load_gdt_config(root_dir=resolved_root, config_path=config_path)
    except Exception as exc:
        print(f"[ERROR] Failed to load GDT configuration: {exc}")
        return 1

    logger = setup_tool_logger("gdrm", resolved_root, cfg, verbose=verbose, debug=debug)
    manifest_path = packages_config or (resolved_root / DEFAULT_PACKAGES_REL_PATH)

    # --- Load Manifest & Resolve Targets ---
    try:
        manifest_root, all_packages = load_package_definitions(manifest_path)
        effective_root = (
            resolve_workspace_root(cfg_root=manifest_root, start_dir=resolved_root)
            if root_dir is None
            else resolved_root
        )
        packages = resolve_target_packages(all_packages, effective_root, target=target)
    except Exception as exc:
        logger.error("Failed to resolve README targets: %s", exc)
        return 1

    # --- Generate Documentation ---
    logger.info("Beginning automated dynamic README generation...")
    exit_code = _write_package_readmes(packages, effective_root, force=force, logger=logger)
    logger.info("Dynamic README generation complete.")
    return exit_code
