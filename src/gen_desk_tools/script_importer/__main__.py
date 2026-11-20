"""Path: src/gen_desk_tools/script_importer/__main__.py

Module execution entrypoint for python -m gen_desk_tools.script_importer.

Operational Role:
    Delegates package invocation directly to gen_desk_tools.script_importer.cli.main.
"""

from __future__ import annotations

from gen_desk_tools.script_importer.cli import main

__version__ = "1.0.0+build.2"

if __name__ == "__main__":
    main()
