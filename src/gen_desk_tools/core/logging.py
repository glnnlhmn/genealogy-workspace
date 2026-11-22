"""Path: src/gen_desk_tools/core/logging.py

Standardized 4-tier dual-handler UTF-8 logging setup for GenDesk Tools (GDT).

Operational Role:
    Registers the custom VERBOSE (15) logging level and configures a persistent
    appending UTF-8 file handler under logs/<tool>.log alongside a stdout
    stream handler whose verbosity responds to -v/--verbose and --debug flags.

Constants:
    VERBOSE: Custom logging level (15) sitting between DEBUG (10) and INFO (20).

Functions:
    setup_tool_logger: Configure and return a dual-handler tool logger.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

__version__ = "1.0.0+build.2"

__all__ = [
    "VERBOSE",
    "setup_tool_logger",
]

VERBOSE: int = 15
logging.addLevelName(VERBOSE, "VERBOSE")


def setup_tool_logger(
    name: str,
    root_dir: Path,
    cfg: dict[str, Any],
    *,
    verbose: bool = False,
    debug: bool = False,
) -> logging.Logger:
    """Configure a dual-handler logger routing to logs/<name>.log and stdout.

    Closes and removes any existing handlers on the named logger to prevent
    duplicate log lines or Windows file-lock leaks across repeated calls.

    Args:
        name: Logger name and log file stem under the configured logs directory.
        root_dir: Workspace root directory used to resolve relative log paths.
        cfg: Merged GDT configuration dictionary.
        verbose: Lower stdout threshold to VERBOSE (15).
        debug: Lower both file and stdout thresholds to DEBUG (10).

    Returns:
        Configured logging.Logger instance with file and stdout handlers.
    """
    # --- Resolve Log Destination & Thresholds ---
    logs_rel: str = cfg.get("workspace", {}).get("logs_dir", "logs")
    logs_dir = root_dir.resolve() / logs_rel
    logs_dir.mkdir(parents=True, exist_ok=True)

    level_name: str = str(cfg.get("logging", {}).get("log_level", "INFO")).upper()
    configured_level: int = logging.getLevelNamesMapping().get(level_name, logging.INFO)
    file_level = logging.DEBUG if debug else configured_level

    if debug:
        console_level = logging.DEBUG
    elif verbose:
        console_level = VERBOSE
    else:
        console_level = logging.WARNING

    # --- Reset Logger & Attach Handlers ---
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    for existing in list(logger.handlers):
        existing.close()
        logger.removeHandler(existing)

    file_handler = logging.FileHandler(
        logs_dir / f"{name}.log",
        mode="a",
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
