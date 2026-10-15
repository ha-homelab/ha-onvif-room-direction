# Changelog

## 0.1.0b1 — Initial public beta

- Extract a reusable normalized-pan classifier and time-separated area confirmation API.
- Add a standalone Home Assistant config flow and options, with one helper per existing ONVIF device.
- Support configurable detection sources, non-overlapping area sectors, polling and freshness controls.
- Read existing ONVIF PTZ status without movement, additional streams or event subscriptions.
- Reject missing, repeated, stale and non-normalized positions; reset on runtime replacement and failures.
- Add cancellation-safe lifecycle handling, explicit expiry, sanitized diagnostics and an optional private installation guard.
- Include synthetic tests, offline replay, documentation and reproducible HACS-compatible ZIP packaging.

API baseline: Home Assistant Core 2026.10.0. Portable core API: 1. Physical camera compatibility is not certified by this beta.
