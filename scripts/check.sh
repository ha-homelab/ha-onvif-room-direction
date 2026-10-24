#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
cd "$(dirname "$0")/.."
PYTHON=${PYTHON:-python3}
"$PYTHON" -c 'from homeassistant.const import __version__; assert __version__ == "2026.10.3", "Install the pinned ha-test extra"'
"$PYTHON" -m ruff check custom_components tests scripts/build-release.py scripts/build-demo.py
"$PYTHON" -m ruff format --check custom_components tests scripts/build-release.py scripts/build-demo.py
"$PYTHON" -m pytest -q
"$PYTHON" scripts/build-release.py
