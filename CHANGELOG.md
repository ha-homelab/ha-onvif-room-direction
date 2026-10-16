# Changelog

## Unreleased

- Document current support, private security reporting, project governance and
  the limits of the OpenSSF self-assessment and synthetic HA verification.


## [0.1.0] - Initial public beta

- Serialize reads across cancelled detection episodes and reject late responses when a transport suppresses timeout cancellation.
- Reject oversized numeric pan/sector/timing inputs without leaking conversion errors.
- Exercise the installable ZIP through real Home Assistant configuration, options reload, synthetic confirmation, camera rename, disable and unload with network access blocked.
- Expand installation, calibration, timing, troubleshooting, upgrade and rollback guidance; distinguish release status from hardware qualification.
- Extract a reusable normalized-pan classifier and time-separated area confirmation API.
- Add a standalone Home Assistant config flow and options, with one helper per existing ONVIF device.
- Support configurable detection sources, non-overlapping area sectors, polling and freshness controls.
- Read existing ONVIF PTZ status without movement, additional streams or event subscriptions.
- Reject missing, repeated, stale and non-normalized positions; reset on runtime replacement and failures.
- Add cancellation-safe lifecycle handling, explicit expiry, sanitized diagnostics and an optional private installation guard.
- Include synthetic tests, offline replay, documentation and reproducible HACS-compatible ZIP packaging.

API baseline: Home Assistant Core 2026.10.0. Portable core API: 1. Physical camera compatibility is not certified by these offline tests.

### Upgrade

Verify the published release and install `onvif_room_direction.zip` into `custom_components/onvif_room_direction` on Home Assistant 2026.10.0 or the documented compatible version. Configure the built-in ONVIF integration first, restart Home Assistant after replacing the files, and add this helper through Devices & services. Retain a Home Assistant backup, your private calibration settings and the previous verified release before upgrading. Existing 0.1.0 prerelease config entries keep their schema and identity; no removal/recreation is needed for these fixes. See [installation and recovery](docs/installation.md).

### Security

This helper only reads ONVIF PTZ status and does not issue camera movement commands. Camera credentials stay in the built-in ONVIF integration; diagnostics expose neither credentials nor raw transport errors. Verify any automation using its estimates before relying on it, irrespective of release channel. Development and CI dependencies use pytest 9.0.3 to address CVE-2025-71176.
