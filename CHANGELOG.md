# Changelog

## [0.1.0] - Initial public beta

- Extract a reusable normalized-pan classifier and time-separated area confirmation API.
- Add a standalone Home Assistant config flow and options, with one helper per existing ONVIF device.
- Support configurable detection sources, non-overlapping area sectors, polling and freshness controls.
- Read existing ONVIF PTZ status without movement, additional streams or event subscriptions.
- Reject missing, repeated, stale and non-normalized positions; reset on runtime replacement and failures.
- Add cancellation-safe lifecycle handling, explicit expiry, sanitized diagnostics and an optional private installation guard.
- Include synthetic tests, offline replay, documentation and reproducible HACS-compatible ZIP packaging.

API baseline: Home Assistant Core 2026.10.0. Portable core API: 1. Physical camera compatibility is not certified by this beta.

### Upgrade

Install the published `onvif_room_direction.zip` into `custom_components/onvif_room_direction` on Home Assistant 2026.10.0 or the documented compatible version. Configure the built-in ONVIF integration first, restart Home Assistant after copying the files, and add this helper through Devices & services. Back up the previous integration folder before replacing it so that you can restore it and restart if an upgrade fails.

### Security

This helper only reads ONVIF PTZ status and does not issue camera movement commands. Camera credentials stay in the built-in ONVIF integration; diagnostics expose neither credentials nor raw transport errors. Treat this release as a beta and verify any automation using its estimates before relying on it. Development and CI dependencies use pytest 9.0.3 to address CVE-2025-71176.
