# Contributing

Use English for code, comments and documentation. Include `SPDX-License-Identifier: MIT` in source files. Keep examples entirely synthetic; no real room layout, calibration, camera identifiers, addresses, credentials or personal data belong in issues or tests.

Create a feature branch and a focused pull request. Do not introduce camera movement or extra streams/subscriptions into this read-only helper. Preserve immediate clearing, timestamp validation, confirmation reset, single-poller behavior, runtime binding and cancellation ownership. Add tests for behavioral fixes, particularly failure and recovery paths.

With Python 3.14.2+:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,ha-test,demo]'
PYTHON=.venv/bin/python ./scripts/check.sh
.venv/bin/python -m playwright install chromium
.venv/bin/python scripts/build-demo.py --screenshot
```

The screenshot command renders the included synthetic HTML locally using Chromium. It does not open a live Home Assistant or camera page. Commit `docs/demo.html` and `docs/synthetic-demo.png` when the replay changes. Label it as a synthetic replay in every use; do not present it as the real HA UI.

`scripts/build-release.py` writes `dist/onvif_room_direction.zip` with integration files at the archive root, plus `dist/SHA256SUMS`. ZIP entries use fixed timestamps, file modes and ordering. It includes only explicit Python/JSON integration files and the license, never workspaces or configuration. The packaging test builds twice and compares bytes.

Before a release, synchronize `version`, `pyproject.toml`, `manifest.json` and `const.VERSION`, update the changelog, run checks, inspect the archive and test installation in an isolated HA instance. Tag `v<version>` and publish the archive and checksum as a prerelease. Do not claim a device model is supported based only on synthetic tests. Shared CI workflows are maintained by the organization and should be pinned to full commit SHAs.
