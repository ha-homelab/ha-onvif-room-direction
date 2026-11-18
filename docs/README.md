# Documentation

Guides for the event-gated Home Assistant sensor that estimates which calibrated area
an ONVIF camera points toward. It reuses the existing ONVIF integration's authenticated
client, reads PTZ status while a detection sensor is on, and never moves a camera.

## Install and use

- [Installation and recovery](installation.md) — the tested Core baseline, the ONVIF and detection prerequisites, and the backup before upgrading.
- [Calibrate for your camera and installation](calibration.md) — recording normalized pan readings per area and why a single sample is not calibration.
- [Example use cases](use-cases.md) — mapping area labels onto a floor plan and rendering unknown or unavailable explicitly.
- [Compatibility and troubleshooting](troubleshooting.md) — the exact ONVIF runtime interface relied on and the failures when it differs.

## Design and API

- [Extension API v1](api.md) — the importable core types and `API_VERSION` a dependent custom integration builds against.
- [Architecture and security boundaries](security-design.md) — how the classifier and adapter split, and which states they reject.
- [Validation scope](validation.md) — what the offline synthetic tests cover and what remains untested.
- [Release-candidate fuzz testing](fuzzing.md) — the sector parsing and confirmation state machine targets and when they run.
