"""Path: src/system/gd_metrics/__main__.py

Module execution entrypoint for `python -m system.gd_metrics`.
"""

from __future__ import annotations

from system.gd_metrics.cli import main

__version__ = "1.0.0+build.1"

if __name__ == "__main__":
    raise SystemExit(main())
