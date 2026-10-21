#!/usr/bin/env bash
# Path: bin/gen_readme.sh
# Shell wrapper orchestrating Python dynamic README generation

set -euo pipefail

# Ensure execution from repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Forward target and any additional CLI arguments to Python utility
python src/system/gen_readme.py "$@"