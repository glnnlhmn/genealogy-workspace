"""Path: src/system/gen_readme.py

Dynamic package documentation generator driven by external TOML configuration.

Operational Role:
    Inspects Python modules using AST parsing to extract canonical descriptions,
    PEP 440 build versions, and public symbols from module docstrings without
    side-effect imports. Emits standardized, up-to-date README.md files for all
    completed architectural packages or a specifically targeted package.
"""

from __future__ import annotations

import argparse
import ast
import sys
import tomllib
from pathlib import Path

__version__ = "1.0.0+build.3"

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "gen_readme.toml"


def load_configuration(config_file: Path) -> tuple[Path, list[dict[str, str]]]:
    """Load default root path and package definitions from TOML configuration."""
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    with config_file.open("rb") as f:
        data = tomllib.load(f)

    root_raw = data.get("default_root", ".")
    root_path = Path(root_raw)
    packages: list[dict[str, str]] = data.get("packages", [])
    return root_path, packages


def extract_module_metadata(file_path: Path) -> dict[str, str]:
    """Parse a Python source file using AST to extract docstring, version, and exports."""
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


def generate_package_readme(pkg_info: dict[str, str], root_path: Path) -> str:
    """Generate standardized Markdown documentation for a package directory."""
    pkg_dir = root_path / pkg_info["path"]
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
    lines.append("Generated dynamically by `src/system/gen_readme.py`.")
    lines.append("")

    return "\n".join(lines)


def prompt_overwrite(target_file: Path) -> str:
    """Prompt user for confirmation when a README.md already exists."""
    while True:
        try:
            choice = (
                input(
                    f"File '{target_file}' already exists. Overwrite? [y]es / [n]o / [a]ll / [q]uit: "
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


def run(
    target: str | None = None,
    force: bool = False,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> int:
    """Core execution engine for README generation."""
    try:
        root_path, all_packages = load_configuration(config_path)
    except Exception as exc:
        print(f"[ERROR] Failed to load configuration: {exc}")
        return 1

    packages = all_packages
    if target:
        target_norm = target.strip().replace("\\", "/").rstrip("/")
        packages = [p for p in all_packages if p["path"] == target_norm]
        if not packages:
            # Check if target is a path to an existing directory
            resolved_dir = Path(target_norm)
            if not resolved_dir.is_absolute():
                resolved_dir = root_path / target_norm

            if resolved_dir.is_dir():
                # Synthesize on-the-fly entry for an unconfigured directory
                rel_path = target_norm
                packages = [
                    {
                        "path": rel_path,
                        "title": f"Package Documentation ({rel_path})",
                        "role": "Architectural subsystem package.",
                        "test_path": f"tests/test_{Path(rel_path).name}",
                        "quality_gate": ">= 95.0% Statement & Branch Coverage",
                    }
                ]
            else:
                print(
                    f"[ERROR] Target package '{target}' not found in configuration or filesystem."
                )
                return 1

    overwrite_all = force
    print("Beginning automated dynamic README generation...")

    for pkg in packages:
        target_dir = root_path / pkg["path"]
        if not target_dir.exists():
            print(f"[SKIP] Directory not found: {target_dir}")
            continue

        readme_file = target_dir / "README.md"
        if readme_file.exists() and not overwrite_all:
            decision = prompt_overwrite(readme_file)
            if decision == "n":
                print(f"[SKIP] User declined overwrite: {readme_file}")
                continue
            if decision == "a":
                overwrite_all = True
            elif decision == "q":
                print("[ABORT] Documentation generation cancelled by user.")
                return 0

        readme_content = generate_package_readme(pkg, root_path)
        readme_file.write_text(readme_content, encoding="utf-8")
        print(f"[OK] Generated: {readme_file}")

    print("Dynamic README generation complete.")
    return 0


def main() -> None:
    """CLI orchestrator entrypoint."""
    parser = argparse.ArgumentParser(
        description="Dynamic package documentation generator driven by external TOML configuration."
    )
    parser.add_argument(
        "target_pos",
        nargs="?",
        default=None,
        help="Optional positional target package path (e.g. 'src/gda/model/xref').",
    )
    parser.add_argument(
        "-t",
        "--target",
        dest="target_opt",
        type=str,
        default=None,
        help="Optional named target package path.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force overwrite of all existing README.md files without interactive prompting.",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to custom TOML configuration file.",
    )
    args = parser.parse_args()

    target_selected = args.target_opt or args.target_pos
    exit_code = run(target=target_selected, force=args.force, config_path=args.config)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
