"""Path: src/gen_desk_tools/__main__.py

Module execution entrypoint for python -m gen_desk_tools.

Operational Role:
    Launches the layered GenDesk Tools interactive menu (gd-menu).
"""

from __future__ import annotations

from gen_desk_tools.menu import main

__version__ = "1.0.0+build.1"

if __name__ == "__main__":
    main()
