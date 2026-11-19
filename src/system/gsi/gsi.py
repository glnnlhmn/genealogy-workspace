"""Path: src/system/gsi/gsi.py

Genealogy Script Importer (GSI).

Provides hermetic intake automation for staged candidate files residing
within the configured download directory. GSI inspects candidate headers,
enforces Safe Backup protocols configured via TOML, documents operations to
a persistent log, and supports contextual execution and verification.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__version__ = "1.5.0+build.4"


def load_gsi_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load and parse the GSI TOML configuration file.

    Args:
        config_path: Optional path to the TOML configuration file.

    Returns:
        dict[str, Any]: Parsed configuration dictionary.
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "gsi_conf.toml"

    default_config: dict[str, Any] = {
        "workspace": {
            "root": ".",
            "download_dir": "download",
            "logs_dir": "logs",
            "reports_dir": "reports",
            "gtemp_dir": "gtemp",
            "archive_dir": "archive",
        },
        "logging": {
            "log_file": "logs/gsi.log",
            "log_level": "INFO",
        },
        "backup_routing": {
            "src/gda": "backups_gda",
            "tests/test_gda": "backups_gda",
            "src/ancestry_desk": "backups_ancestry_desk",
            "tests/test_ancestry_desk": "backups_ancestry_desk",
            "src/cli": "backups_cli",
            "tests/test_cli": "backups_cli",
            "src/system": "backups_system",
            "tests/test_system": "backups_system",
            "schemas": "backups_schemas",
            "data/setup": "backups_data_setup",
            "default": "backups_system",
        },
        "code_domains": {
            "protected_domains": ["src", "tests", "schemas", "data/setup"],
        },
    }

    if config_path.exists() and config_path.is_file():
        try:
            with open(config_path, "rb") as fh:
                loaded = tomllib.load(fh)
            for sec, vals in loaded.items():
                if sec in default_config and isinstance(vals, dict):
                    default_config[sec].update(vals)
                else:
                    default_config[sec] = vals
        except Exception as err:
            print(f"Warning: Failed to parse {config_path}: {err}. Using defaults.")

    return default_config


def get_workspace_root(config: dict[str, Any]) -> Path:
    """Resolve and return the canonical workspace root directory.

    Args:
        config: Parsed configuration dictionary.

    Returns:
        Path: Absolute path to the repository workspace root.
    """
    cfg_root = config.get("workspace", {}).get("root")
    if cfg_root and cfg_root != ".":
        root_path = Path(cfg_root).resolve()
        if root_path.is_dir():
            return root_path

    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        if (parent / "src").is_dir() and (parent / "archive").is_dir():
            return parent
        if (parent / "pyproject.toml").is_file():
            return parent

    return Path.cwd().resolve()


def setup_gsi_logger(root_dir: Path, config: dict[str, Any]) -> logging.Logger:
    """Configure standard GSI appending logger.

    Args:
        root_dir: Canonical workspace root directory.
        config: Parsed configuration dictionary.

    Returns:
        logging.Logger: Configured logger instance.
    """
    rel_log = config.get("logging", {}).get("log_file", "logs/gsi.log")
    log_path = root_dir / Path(rel_log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("gsi")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def parse_metadata_header(file_path: Path, root_dir: Path) -> tuple[str | None, Path | None]:
    """Extract destination filename and target path from candidate headers.

    Args:
        file_path: Staged file candidate inside download/.
        root_dir: Canonical repository root directory.

    Returns:
        tuple[str | None, Path | None]: (target_filename, resolved_destination_path).
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
            target_name = metadata.get("_name") or metadata.get("name") or nb_data.get("_name")
            target_path_str = metadata.get("_path") or metadata.get("path") or nb_data.get("_path")

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

    elif suffix in (".json", ".toml"):
        try:
            head_block = "\n".join(content.splitlines()[:25])
            name_m = re.search(r'["\']?_?name["\']?\s*[:=]\s*["\']([^"\']+)["\']', head_block)
            path_m = re.search(r'["\']?_?path["\']?\s*[:=]\s*["\']([^"\']+)["\']', head_block)
            if name_m:
                target_name = name_m.group(1).strip()
            if path_m:
                target_path_str = path_m.group(1).strip()
        except Exception:
            return None, None

    if not target_path_str:
        head_block = "\n".join(content.splitlines()[:25])
        docstring_path_m = re.search(
            r'^(?:"""|\'\'\')[ \t]*Path:[ \t]*["\']?([^\r\n"\']+)["\']?',
            head_block,
            re.MULTILINE | re.IGNORECASE,
        )
        if docstring_path_m:
            target_path_str = docstring_path_m.group(1).strip()
        else:
            generic_path_m = re.search(
                r"^[ \t]*(?:#|<!--|//|/\*|\*)*[ \t]*Path:[ \t]*[\"\']?([^\r\n>\"\*]+)[\"\']?",
                head_block,
                re.MULTILINE | re.IGNORECASE,
            )
            if generic_path_m:
                target_path_str = generic_path_m.group(1).strip()

        if not target_name:
            name_m = re.search(
                r"^[ \t]*(?:#|<!--|//|/\*|\*)*[ \t]*Name:[ \t]*[\"\']?([^\r\n>*/\"']+)[\"\']?",
                head_block,
                re.MULTILINE | re.IGNORECASE,
            )
            if name_m:
                target_name = name_m.group(1).strip()

    if not target_path_str:
        return None, None

    # Strip only trailing comment delimiters (""", ''', -->, */, or trailing XML comment markers --)
    target_path_str = (
        re.sub(r'(?:[\s\-]*-->|[\s\-]*\*/|\s*"""|\s*\'\'\'|--+)\s*$', "", target_path_str)
        .strip()
        .strip("\"'")
    )
    if target_name:
        target_name = (
            re.sub(r'(?:[\s\-]*-->|[\s\-]*\*/|\s*"""|\s*\'\'\'|--+)\s*$', "", target_name)
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


def _determine_backup_directory(dest_path: Path, root_dir: Path, config: dict[str, Any]) -> Path:
    """Determine the archive backup folder for a destination path using TOML rules.

    Args:
        dest_path: Canonical destination file path.
        root_dir: Canonical repository root directory.
        config: Parsed configuration dictionary.

    Returns:
        Path: Target directory under archive/ where the backup must be placed.
    """
    rel_path_str = dest_path.relative_to(root_dir).as_posix()
    routing = config.get("backup_routing", {})
    archive_dir_name = str(config.get("workspace", {}).get("archive_dir", "archive"))

    chosen_project: str | None = None
    for prefix, project in routing.items():
        if prefix != "default" and (
            rel_path_str == prefix or rel_path_str.startswith(f"{prefix}/")
        ):
            chosen_project = str(project)
            break

    if not chosen_project:
        chosen_project = str(routing.get("default", "backups_system"))

    parent_rel = dest_path.parent.relative_to(root_dir)
    return root_dir / archive_dir_name / chosen_project / parent_rel


def _backup_destination(
    dest_path: Path, root_dir: Path, config: dict[str, Any], logger: logging.Logger
) -> Path:
    """Create a timestamped backup of the destination file in the archive repository.

    Args:
        dest_path: Existing file about to be overwritten.
        root_dir: Canonical repository root directory.
        config: Parsed configuration dictionary.
        logger: Configured GSI logging instance.

    Returns:
        Path: Destination path of the created backup file.
    """
    backup_folder = _determine_backup_directory(dest_path, root_dir, config)
    backup_folder.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    candidate_name = f"{dest_path.name}.{ts}.bk"
    backup_file = backup_folder / candidate_name

    counter = 1
    while backup_file.exists():
        backup_file = backup_folder / f"{dest_path.name}.{ts}_{counter}.bk"
        counter += 1

    shutil.copy2(dest_path, backup_file)
    backup_rel_posix = backup_file.relative_to(root_dir).as_posix()
    logger.info(f"BACKUP_CREATED: {backup_rel_posix}")
    return backup_file


def _is_protected_domain(dest_path: Path, root_dir: Path, config: dict[str, Any]) -> bool:
    """Check if destination resides within configured protected domains.

    Args:
        dest_path: Destination path being evaluated.
        root_dir: Repository root directory.
        config: Parsed configuration dictionary.

    Returns:
        bool: True if destination requires automatic pre-write backup; False otherwise.
    """
    rel_posix = dest_path.relative_to(root_dir).as_posix()
    protected = config.get("code_domains", {}).get(
        "protected_domains", ["src", "tests", "schemas", "data/setup"]
    )
    return any(rel_posix == p or rel_posix.startswith(f"{p}/") for p in protected)


def _prompt_user_yes_no(question: str) -> bool:
    """Prompt user for interactive confirmation via standard input.

    Args:
        question: Message string displayed to the user.

    Returns:
        bool: True if user enters 'y' or 'yes'; False otherwise.
    """
    print(f"{question} (y/n): ", end="", flush=True)
    response = sys.stdin.readline().strip().lower()
    return response in ("y", "yes")


def _execute_python(path: Path, root_dir: Path) -> int:
    """Execute Python target or test."""
    name = path.name.lower()
    if name.startswith("test_") or name.endswith("_test.py"):
        cmd = [sys.executable, "-m", "pytest", str(path), "-v"]
    else:
        cmd = [sys.executable, str(path)]
    res = subprocess.run(cmd, cwd=str(root_dir))
    return res.returncode


def _execute_target(path: Path, root_dir: Path) -> int:
    """Dispatch file execution based on file extension."""
    ext = path.suffix.lower()
    if ext == ".py":
        return _execute_python(path, root_dir)
    if ext == ".ps1":
        return subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(path)],
            cwd=str(root_dir),
        ).returncode
    if ext == ".sh":
        return subprocess.run(["bash", str(path)], cwd=str(root_dir)).returncode

    print(f"Notice: Non-executable file type '{ext}' cannot be executed directly: {path.name}")
    return 0


def run_intake(
    force: bool = False,
    run_target: bool = False,
    clean: bool = False,
    prefix: str | None = None,
    config_path: Path | None = None,
) -> int:
    """Execute the GSI intake workflow against configured download staged assets.

    Args:
        force: If True, bypass backups and prompts, logging force mode execution.
        run_target: If True, invoke contextual execution on relocated targets.
        clean: If True, prompt to purge unparseable candidate files in download.
        prefix: Optional filename prefix filter.
        config_path: Optional path to custom gsi_conf.toml.

    Returns:
        int: Exit status code (0 for success, non-zero for failure).
    """
    config = load_gsi_config(config_path)
    root_dir = get_workspace_root(config)
    logger = setup_gsi_logger(root_dir, config)

    if force:
        logger.warning("EXECUTION_MODE: FORCE=TRUE (Backups bypassed for protected domains)")

    download_dir_name = config.get("workspace", {}).get("download_dir", "download")
    download_dir = root_dir / download_dir_name

    if not download_dir.is_dir():
        print(f"Error: Download directory not found at {download_dir}")
        return 1

    candidates: list[Path] = [
        item for item in download_dir.iterdir() if item.is_file() and not item.name.startswith(".")
    ]

    if prefix:
        candidates = [c for c in candidates if c.name.lower().startswith(prefix.lower())]

    if not candidates:
        print("No intake candidates found in download/.")
        return 0

    moved_files: list[str] = []

    for candidate in sorted(candidates):
        target_name, dest_path = parse_metadata_header(candidate, root_dir)

        if not target_name or not dest_path:
            if clean:
                confirmed = force or _prompt_user_yes_no(
                    f"Delete unparseable file '{candidate.name}' from {download_dir_name}/?"
                )
                if confirmed:
                    candidate.unlink(missing_ok=True)
                    print(f"Purged: {candidate.name}")
            else:
                print(f"Skipping {candidate.name}: Missing valid metadata headers.")
            continue

        if dest_path.is_file():
            if _is_protected_domain(dest_path, root_dir, config):
                if not force:
                    _backup_destination(dest_path, root_dir, config, logger)
            else:
                if not force:
                    confirmed = _prompt_user_yes_no(f"Overwrite destination '{dest_path.name}'?")
                    if not confirmed:
                        print(f"Skipped relocation: {candidate.name}")
                        continue

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(candidate), str(dest_path))
        rel_dest_posix = dest_path.relative_to(root_dir).as_posix()
        moved_files.append(rel_dest_posix)
        logger.info(f"FILE_CREATED: {rel_dest_posix}")

        if run_target:
            code = _execute_target(dest_path, root_dir)
            if code != 0:
                print(f"Execution failed with non-zero exit code {code}: {dest_path.name}")
                return code

    if moved_files:
        print("Intake completed successfully. Relocated files:")
        for mf in moved_files:
            print(f" -> {mf}")
    else:
        print("No files were relocated.")

    return 0


def main(argv: list[str] | None = None) -> None:
    """Parse command-line arguments and run the GSI pipeline."""
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
        help="Optional prefix filter to only process files matching a specific prefix.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to custom gsi_conf.toml configuration file.",
    )

    args = parser.parse_args(argv)
    status = run_intake(
        force=args.force,
        run_target=args.run,
        clean=args.clean,
        prefix=args.prefix,
        config_path=args.config,
    )
    sys.exit(status)


if __name__ == "__main__":
    main()
