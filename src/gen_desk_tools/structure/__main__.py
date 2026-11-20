"""Path: src/gen_desk_tools/structure/__main__.py

Module execution entrypoint for python -m gen_desk_tools.structure.

Operational Role:
    Delegates package invocation directly to gen_desk_tools.structure.cli.main.
"""

from __future__ import annotations

from gen_desk_tools.structure.cli import main

__version__ = "1.0.0+build.1"

if __name__ == "__main__":
    main()
