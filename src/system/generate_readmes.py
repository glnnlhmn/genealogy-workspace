"""Path: src/system/generate_readmes.py

Dynamic package documentation generator for completed GDA framework modules.

Operational Role:
    Inspects Python modules using AST parsing to extract canonical descriptions,
    PEP 440 build versions, and public symbols from module docstrings without
    side-effect imports. Emits standardized, up-to-date README.md files for all
    completed architectural packages or a specifically targeted package.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

__version__ = "1.0.0+build.2"

ROOT_ANCHOR = Path("G:/My Drive/genealogy-workspace")

COMPLETED_PACKAGES: list[dict[str, str]] = [
    {
        "path": "src/system",
        "title": "System Administration & Automation (src/system)",
        "role": (
            "Workstation administration, developer environment onboarding, "
            "Git hook deployment, and automated intake pipelines."
        ),
        "test_path": "tests/test_system",
        "quality_gate": "100.0% Statement & Branch Coverage",
    },
    {
        "path": "src/gda/core",
        "title": "Core Primitives & Introspection (src/gda/core)",
        "role": (
            "Domain-agnostic foundational infrastructure providing canonical error "
            "taxonomies, immutable Pydantic configuration, structured logging, "
            "and runtime class introspection."
        ),
        "test_path": "tests/test_gda/test_core",
        "quality_gate": ">= 95.0% Statement & Branch Coverage",
    },
    {
        "path": "src/gda/enums",
        "title": "Authoritative Enumeration Domains (src/gda/enums)",
        "role": (
            "Authoritative genealogical enumerations inheriting strictly from StrEnum "
            "and IntEnum, governing biological sex, evidentiary certainty (QuayScore), "
            "events, jurisdictions, and archival classifications."
        ),
        "test_path": "tests/test_gda/test_enums",
        "quality_gate": ">= 95.0% Statement & Branch Coverage",
    },
    {
        "path": "src/gda/io",
        "title": "I/O, Safe Backup & Persistence Infrastructure (src/gda/io)",
        "role": (
            "Governs physical filesystem interactions, line-ending preserving UTF-8 "
            "file access, atomic temporary staging, and automated pre-execution Safe Backups."
        ),
        "test_path": "tests/test_gda/test_io",
        "quality_gate": ">= 95.0% Statement & Branch Coverage",
    },
    {
        "path": "src/gda/types",
        "title": "Data Types & Primitives (src/gda/types)",
        "role": (
            "Foundational scalar primitives, string constraints, and custom "
            "Pydantic validators."
        ),
        "test_path": "tests/test_gda/test_types",
        "quality_gate": ">= 95.0% Statement & Branch Coverage",
    },
    {
        "path": "src/gda/util",
        "title": "Utility Algorithms & Text Normalizers (src/gda/util)",
        "role": (
            "High-performance phonetics algorithms (Soundex, NYSIIS), cryptographic "
            "hashing routines, identifier generators, and text sanitizers."
        ),
        "test_path": "tests/test_gda/test_util",
        "quality_gate": ">= 95.0% Statement & Branch Coverage",
    },
    {
        "path": "src/gda/model/atom",
        "title": "Atomic Value Objects (src/gda/model/atom)",
        "role": (
            "Immutable atomic value objects enforcing strict domain constraints: "
            "prefixed entity identifiers, calendar dates, timestamps, coordinates, and scalars."
        ),
        "test_path": "tests/test_gda/test_model/test_atom",
        "quality_gate": ">= 95.0% Statement & Branch Coverage",
    },
    {
        "path": "src/gda/model/base",
        "title": "Composite Base Records (src/gda/model/base)",
        "role": (
            "Reusable domain composite building blocks: audit stamps, tombstone records, "
            "onomastic personal names, source citations, addresses, and time periods."
        ),
        "test_path": "tests/test_gda/test_model/test_base",
        "quality_gate": ">= 95.0% Statement & Branch Coverage",
    },
    {
        "path": "src/gda/model/entity",
        "title": "Canonical Domain Entities (src/gda/model/entity)",
        "role": (
            "Primary domain entities enforcing relational integrity, temporal bounds, "
            "biological plausibility, and participant linkages (Individual, Family, "
            "Fact, Location, Site)."
        ),
        "test_path": "tests/test_gda/test_model/test_entity",
        "quality_gate": ">= 95.0% Statement & Branch Coverage",
    },
    {
        "path": "src/gda/model/military",
        "title": "Military Records Domain Package (src/gda/model/military)",
        "role": (
            "Evidentiary military records domain model suite encompassing conscription "
            "and draft registrations, active duty muster/service/separation certificates, "
            "veteran invalid and widow/dependent pension claims, bounty land warrants, "
            "combat casualties, POW internments, national cemetery burials, and valor awards."
        ),
        "test_path": "tests/test_gda/test_model/test_military",
        "quality_gate": "100.0% Statement & Branch Coverage",
    },
]


def extract_module_metadata(file_path: Path) -> dict[str, str]:
    """Parse a Python source file using AST to extract docstring and version."""
    metadata = {
        "description": "No description available.",
        "version": "Unversioned",
        "all_exports": "",
    }
    try:
        source = file_path.read_text(encoding="utf-8")
        parsed = ast.parse(source)

        doc = ast.get_docstring(parsed)
        if doc:
            clean_lines = [
                line.strip()
                for line in doc.splitlines()
                if line.strip() and not line.strip().startswith("Path:")
            ]
            if clean_lines:
                metadata["description"] = clean_lines[0]

        for node in parsed.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "__version__" and isinstance(
                            node.value, ast.Constant
                        ):
                            metadata["version"] = str(node.value.value)
                        elif target.id == "__all__" and isinstance(
                            node.value, ast.List
                        ):
                            names = [
                                elt.value
                                for elt in node.value.elts
                                if isinstance(elt, ast.Constant)
                            ]
                            metadata["all_exports"] = ", ".join(f"`{n}`" for n in names)
    except Exception as exc:
        metadata["description"] = f"Extraction error: {exc}"

    return metadata


def generate_package_readme(pkg_info: dict[str, str]) -> str:
    """Generate standardized Markdown documentation for a package folder."""
    pkg_dir = ROOT_ANCHOR / pkg_info["path"]
    py_files = sorted(
        [
            f
            for f in pkg_dir.glob("*.py")
            if f.is_file() and not f.name.startswith((".", "__"))
        ]
    )

    lines: list[str] = [
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

    subdirs = sorted(
        [
            d
            for d in pkg_dir.iterdir()
            if d.is_dir() and not d.name.startswith((".", "_"))
        ]
    )
    if subdirs:
        lines.append("## Subpackages")
        for subdir in subdirs:
            init_file = subdir / "__init__.py"
            desc = "Subpackage domain entities and enumerations."
            if init_file.exists():
                meta = extract_module_metadata(init_file)
                if meta["description"] != "No description available.":
                    desc = meta["description"]
            lines.append(f"- **`{subdir.name}/`**: {desc}")
        lines.append("")

    lines.extend(
        [
            "## Module Inventory & Descriptions",
            "| Module | Version | Canonical Description |",
            "| :--- | :--- | :--- |",
        ]
    )

    for py_file in py_files:
        meta = extract_module_metadata(py_file)
        lines.append(
            f"| `{py_file.name}` | `{meta['version']}` | {meta['description']} |"
        )

    lines.append("")
    lines.append("## Public Exports & Consumption Contract")
    init_file = pkg_dir / "__init__.py"
    if init_file.exists():
        init_meta = extract_module_metadata(init_file)
        if init_meta["all_exports"]:
            lines.append(f"Exports: {init_meta['all_exports']}.")
        else:
            lines.append(
                "Modules export public interfaces explicitly declared in `__all__`."
            )
    else:
        lines.append("Direct submodule imports supported.")

    lines.append("")
    lines.append("---")
    lines.append("Generated dynamically by `src/system/generate_readmes.py`.")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Generate README.md files for all completed packages or a targeted package."""
    parser = argparse.ArgumentParser(
        description="Dynamic package documentation generator for completed GDA framework modules."
    )
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        default=None,
        help="Optional package path to generate README for (e.g. 'src/gda/model/military').",
    )
    args = parser.parse_args()

    packages = COMPLETED_PACKAGES
    if args.target:
        target_norm = args.target.strip().replace("\\", "/").rstrip("/")
        packages = [p for p in COMPLETED_PACKAGES if p["path"] == target_norm]
        if not packages:
            print(
                f"[ERROR] Target package '{args.target}' not found in COMPLETED_PACKAGES registry."
            )
            return

    print("Beginning automated dynamic README generation...")
    for pkg in packages:
        target_dir = ROOT_ANCHOR / pkg["path"]
        if not target_dir.exists():
            print(f"[SKIP] Directory not found: {target_dir}")
            continue

        readme_content = generate_package_readme(pkg)
        readme_file = target_dir / "README.md"
        readme_file.write_text(readme_content, encoding="utf-8")
        print(f"[OK] Generated: {readme_file.relative_to(ROOT_ANCHOR)}")

    print("Dynamic README generation complete.")


if __name__ == "__main__":
    main()
