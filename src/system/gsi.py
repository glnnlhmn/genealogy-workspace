"""Path: src/system/gsi.py

Genealogy Script Importer (GSI).

Provides hermetic, zero-dependency intake automation for staged candidate files
residing exclusively within the download/ staging directory. GSI inspects candidate
headers, enforces the Safe Backup Protocol into project-specific archive destinations,
prompts interactively for non-code assets, and supports optional contextual execution.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

__version__ = "1.4.0+build.r3"


def get_workspace_root() -> Path:
    """Resolve and return the canonical workspace root directory.

    Returns:
        Path: Absolute path to the repository workspace root.
    """
    script_path = Path(__file__).resolve()
    if len(script_path.parents) >= 3 and (script_path.parents[2] / "src").is_dir():
        return script_path.parents[2]
    return Path.cwd().resolve()


def parse_metadata_header(
    file_path: Path, root_dir: Path
) -> tuple[str | None, Path | None]:
    """Extract destination filename and target path from candidate headers.

    Supports the Single-Field Header & Docstring Architecture,
    Jupyter Notebook metadata, JSON envelope properties, and legacy top-level comment
    declarations (# Name:, # Path:).

    Args:
        file_path: Staged file candidate inside download/.
        root_dir: Canonical repository root directory.

    Returns:
        tuple[str | None, Path | None]: (target_filename, resolved_destination_path).
        Returns (None, None) if metadata is absent, malformed, or targets outside root.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None, None

    target_name: str | None = None
    target_path_str: str | None = None
    suffix = file_path.suffix.lower()

    if suffix == ".ipynb":
        try:
            nb_data = json.loads(content)
            metadata = nb_data.get("metadata", {})
            target_name = (
                metadata.get("_name") or metadata.get("name") or nb_data.get("_name")
            )
            target_path_str = (
                metadata.get("_path") or metadata.get("path") or nb_data.get("_path")
            )

            if not target_path_str:
                cells = nb_data.get("cells", [])
                if cells and cells[0].get("cell_type") in ("raw", "markdown", "code"):
                    first_cell = "".join(cells[0].get("source", []))
                    name_m = re.search(
                        r"(?:#|<!--)[ \t]*Name:[ \t]*([^\r\n>*/]+)",
                        first_cell,
                        re.IGNORECASE,
                    )
                    path_m = re.search(
                        r"(?:#|<!--)[ \t]*Path:[ \t]*([^\r\n>]+)",
                        first_cell,
                        re.IGNORECASE,
                    )
                    if name_m:
                        target_name = name_m.group(1).strip()
                    if path_m:
                        target_path_str = path_m.group(1).strip()
        except Exception:
            return None, None

    elif suffix == ".json":
        try:
            head_block = "\n".join(content.splitlines()[:20])
            name_json = re.search(
                r'"_?name"\s*:\s*"([^"]+)"', head_block, re.IGNORECASE
            )
            path_json = re.search(
                r'"_?path"\s*:\s*"([^"]+)"', head_block, re.IGNORECASE
            )
            if name_json:
                target_name = name_json.group(1).strip()
            if path_json:
                target_path_str = path_json.group(1).strip()
        except Exception:
            return None, None

    if not target_path_str:
        head_block = "\n".join(content.splitlines()[:20])

        docstring_path_m = re.search(
            r'^(?:"""|\'\'\')[ \t]*Path:[ \t]*["\']?([^\r\n"\']+)["\']?',
            head_block,
            re.MULTILINE | re.IGNORECASE,
        )
        if docstring_path_m:
            target_path_str = docstring_path_m.group(1).strip()
        else:
            generic_path_m = re.search(
                r"^[ \t]*(?:#|<!--|//|/\*|\*)*[ \t]*Path:[ \t]*[\"']?([^\r\n>\"*]+)[\"']?",
                head_block,
                re.MULTILINE | re.IGNORECASE,
            )
            if generic_path_m:
                target_path_str = generic_path_m.group(1).strip()

        if not target_name:
            name_m = re.search(
                r"^[ \t]*(?:#|<!--|//|/\*|\*)*[ \t]*Name:[ \t]*[\"']?([^\r\n>*/\"']+)[\"']?",
                head_block,
                re.MULTILINE | re.IGNORECASE,
            )
            if name_m:
                target_name = name_m.group(1).strip()

    if not target_path_str:
        return None, None

    target_path_str = (
        re.sub(r'[\s\-]*("""|\'\'\'|-->|\*/|-+).*$', "", target_path_str)
        .strip()
        .strip("\"'")
    )
    if target_name:
        target_name = (
            re.sub(r'[\s\-]*("""|\'\'\'|-->|\*/|-+).*$', "", target_name)
            .strip()
            .strip("\"'")
        )

    path_obj = Path(target_path_str)
    if not target_name:
        target_name = path_obj.name

    raw_dest = root_dir / path_obj
    if raw_dest.is_dir() or target_path_str.endswith(("/", "\\")):
        dest_path = (raw_dest / target_name).resolve()
    else:
        dest_path = raw_dest.resolve()

    try:
        dest_path.relative_to(root_dir)
    except ValueError:
        return None, None

    return target_name, dest_path


def _determine_backup_directory(dest_path: Path, root_dir: Path) -> Path:
    """Determine the isolated archive backup folder for a destination path.

    Args:
        dest_path: Canonical destination file path.
        root_dir: Canonical repository root directory.

    Returns:
        Path: Target directory under archive/ where the backup must be placed.
    """
    rel_parts = dest_path.relative_to(root_dir).parts
    top_seg = rel_parts[0] if rel_parts else ""
    sub_seg = rel_parts[1] if len(rel_parts) > 1 else ""

    if top_seg == "src":
        if sub_seg == "gda":
            project = "backups_gda"
        elif sub_seg == "ancestry_desk":
            project = "backups_ancestry_desk"
        elif sub_seg == "cli":
            project = "backups_cli"
        elif sub_seg in ("system", "sys"):
            project = "backups_system"
        else:
            project = f"backups_{sub_seg}"
    elif top_seg == "tests":
        if sub_seg == "test_gda":
            project = "backups_gda"
        elif sub_seg == "test_ancestry_desk":
            project = "backups_ancestry_desk"
        elif sub_seg == "test_cli":
            project = "backups_cli"
        else:
            project = "backups_system"
    else:
        project = "backups_system"

    parent_rel = dest_path.parent.relative_to(root_dir)
    return root_dir / "archive" / project / parent_rel


def _backup_destination(dest_path: Path, root_dir: Path) -> Path:
    """Create a timestamped backup of the destination file in the archive repository.

    Args:
        dest_path: Existing file about to be overwritten.
        root_dir: Canonical repository root directory.

    Returns:
        Path: Destination path of the created backup file.
    """
    backup_folder = _determine_backup_directory(dest_path, root_dir)
    backup_folder.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_folder / f"{dest_path.name}.{ts}.bk"
    shutil.copy2(dest_path, backup_file)
    return backup_file


def _is_code_domain(dest_path: Path, root_dir: Path) -> bool:
    """Check if destination resides within production code or test suites.

    Args:
        dest_path: Destination path being evaluated.
        root_dir: Repository root directory.

    Returns:
        bool: True if destination is under src/ or tests/; False otherwise.
    """
    rel = dest_path.relative_to(root_dir)
    return rel.parts[0] in ("src", "tests")


def _prompt_user_yes_no(question: str) -> bool:
    """Prompt user for interactive confirmation via standard input.

    Args:
        question: Message string displayed to the user.

    Returns:
        bool: True if user enters 'y' or 'yes' (case-insensitive); False otherwise.
    """
    print(f"{question} (y/n): ", end="", flush=True)
    response = sys.stdin.readline().strip().lower()
    return response in ("y", "yes")


def _execute_python(path: Path, root_dir: Path) -> int:
    """Execute a Python file or pytest target.

    Args:
        path: Absolute path to the Python target.
        root_dir: Repository root directory.

    Returns:
        int: Subprocess exit code.
    """
    name = path.name.lower()
    if name.startswith("test_") or name.endswith("_test.py"):
        cmd = [sys.executable, "-m", "pytest", str(path), "-v"]
    else:
        cmd = [sys.executable, str(path)]
    res = subprocess.run(cmd, cwd=str(root_dir))
    return res.returncode


def _execute_powershell(path: Path, root_dir: Path) -> int:
    """Execute a PowerShell script.

    Args:
        path: Absolute path to the PowerShell target.
        root_dir: Repository root directory.

    Returns:
        int: Subprocess exit code.
    """
    cmd = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(path)]
    res = subprocess.run(cmd, cwd=str(root_dir))
    return res.returncode


def _execute_bash(path: Path, root_dir: Path) -> int:
    """Execute a Bash script.

    Args:
        path: Absolute path to the shell script target.
        root_dir: Repository root directory.

    Returns:
        int: Subprocess exit code.
    """
    cmd = ["bash", str(path)]
    res = subprocess.run(cmd, cwd=str(root_dir))
    return res.returncode


def _execute_target(path: Path, root_dir: Path) -> int:
    """Dispatch file execution based on file extension.

    Args:
        path: Absolute path to the relocated target.
        root_dir: Repository root directory.

    Returns:
        int: Subprocess exit code, or 0 if non-executable.
    """
    ext = path.suffix.lower()
    if ext == ".py":
        return _execute_python(path, root_dir)
    if ext == ".ps1":
        return _execute_powershell(path, root_dir)
    if ext == ".sh":
        return _execute_bash(path, root_dir)

    print(
        f"Notice: Non-executable file type '{ext}' cannot be executed directly: {path.name}"
    )
    return 0


def run_intake(
    force: bool = False,
    run_target: bool = False,
    clean: bool = False,
    prefix: str | None = None,
) -> int:
    """Execute the GSI intake workflow against download/ staged assets.

    Args:
        force: If True, bypass backups on code and bypass confirmation prompts.
        run_target: If True, invoke contextual execution on relocated targets.
        clean: If True, prompt to purge unparseable candidate files.
        prefix: Optional filename prefix filter (defaults to None, matching all files).

    Returns:
        int: Exit status code (0 for success, non-zero for failures).
    """
    root_dir = get_workspace_root()
    download_dir = root_dir / "download"

    if not download_dir.is_dir():
        print(f"Error: Download directory not found at {download_dir}")
        return 1

    candidates: list[Path] = [
        item
        for item in download_dir.iterdir()
        if item.is_file() and not item.name.startswith(".")
    ]

    if prefix:
        candidates = [
            c for c in candidates if c.name.lower().startswith(prefix.lower())
        ]

    if not candidates:
        print("No intake candidates found in download/.")
        return 0

    moved_files: list[str] = []

    for candidate in sorted(candidates):
        target_name, dest_path = parse_metadata_header(candidate, root_dir)

        if not target_name or not dest_path:
            if clean:
                confirmed = force or _prompt_user_yes_no(
                    f"Delete unparseable file '{candidate.name}' from download/?"
                )
                if confirmed:
                    candidate.unlink(missing_ok=True)
                    print(f"Purged: {candidate.name}")
            else:
                print(f"Skipping {candidate.name}: Missing valid metadata headers.")
            continue

        if dest_path.is_file():
            if _is_code_domain(dest_path, root_dir):
                if not force:
                    _backup_destination(dest_path, root_dir)
            else:
                if not force:
                    confirmed = _prompt_user_yes_no(
                        f"Overwrite destination '{dest_path.name}'?"
                    )
                    if not confirmed:
                        print(f"Skipped relocation: {candidate.name}")
                        continue

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(candidate), str(dest_path))
        rel_dest_display = str(dest_path.relative_to(root_dir))
        moved_files.append(rel_dest_display)

        if run_target:
            code = _execute_target(dest_path, root_dir)
            if code != 0:
                print(
                    f"Execution failed with non-zero exit code {code}: {dest_path.name}"
                )
                return code

    if moved_files:
        print("Intake completed successfully. Relocated files:")
        for mf in moved_files:
            print(f"  -> {mf}")
    else:
        print("No files were relocated.")

    return 0


def main(argv: list[str] | None = None) -> None:
    """Parse command-line arguments and run the GSI pipeline.

    Args:
        argv: Optional argument list override for testing. Defaults to sys.argv[1:].
    """
    parser = argparse.ArgumentParser(
        prog="gsi",
        description="Genealogy Script Importer (GSI) - Hermetic Intake Automation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Bypass pre-write backups for code and bypass interactive overwrite confirmations.",
    )
    parser.add_argument(
        "-r",
        "--run",
        action="store_true",
        default=False,
        help="Relocate files and immediately execute contextual verification (e.g. pytest).",
    )
    parser.add_argument(
        "-c",
        "--clean",
        action="store_true",
        default=False,
        help="Prompt to delete unparseable files lacking valid metadata headers from download/.",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        type=str,
        default=None,
        help="Optional prefix filter to only process files matching a specific prefix (e.g. 'gemini').",
    )

    args = parser.parse_args(argv)
    status = run_intake(
        force=args.force,
        run_target=args.run,
        clean=args.clean,
        prefix=args.prefix,
    )
    sys.exit(status)


if __name__ == "__main__":
    main()
