# Validation scope

The automated baseline is **Home Assistant Core 2026.10.3**. Tests use invented entities, labels, timestamps and ONVIF responses. They do not connect to Home Assistant servers or cameras, move hardware, open streams, or certify firmware.

`PYTHON=.venv/bin/python ./scripts/check.sh` covers:

- Core classification: normalized limits, excluded inner edges, gaps, overlap rejection, wrapped/disjoint labels, invalid numbers and time-separated confirmation resets.
- Adapter behavior: the exact `GetStatus` call, timestamp freshness and order, fixed error codes, missing data, unsupported coordinate spaces and runtime replacement.
- HA lifecycle: real event subscriptions, active-source gating, cancellation ownership, non-overlapping reads when cancellation is delayed, timeout rejection, expiry, retries, options validation and diagnostics.
- Installation: a deterministic ZIP is extracted into a temporary configuration directory, then loaded in a separate Python interpreter. Real HA configuration and options managers create and reload the helper; a synthetic ONVIF client supplies readings; the sensor confirms, survives a camera registry rename, disables and unloads. Socket connections, binds, DNS and datagrams are blocked by a Python audit hook. Only dependency startup and the existing camera client are simulated.
- Packaging: expected integration-root files, matching version fields and English strings, no local/test files, and byte-for-byte repeatability of two ZIP builds in the same environment.

These checks establish software behavior at the tested interfaces. They do **not** prove a successful HACS UI download, live authentication to any camera, physical direction accuracy, all Python/platform combinations, or compatibility with other HA versions. ZIP repeatability in one environment does not claim identical compressed bytes across all zlib versions. Release signature verification is a separate publication check described in [release signatures](release-signatures.md).

When changing the Home Assistant baseline, rerun the entire suite and review the built-in ONVIF runtime interface. When changing camera firmware, mounting or calibration, repeat the local [first-run checks](installation.md#first-run-acceptance). Keep software release status separate from hardware qualification.
