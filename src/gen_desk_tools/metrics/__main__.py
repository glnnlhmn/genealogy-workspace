"""Path: src/gen_desk_tools/metrics/__main__.py

Module execution entrypoint for `python -m gen_desk_tools.metrics`.
"""

from __future__ import annotations

from gen_desk_tools.metrics.cli import main

__version__ = "1.0.0+build.1"

if __name__ == "__main__":
    raise SystemExit(main())
