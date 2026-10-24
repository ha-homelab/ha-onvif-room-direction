# Changelog

## [0.1.4] - Unreleased

### Changed

- Record Home Assistant 2026.10.3 as the tested diagnostic baseline and validate with its compatible uv 0.13.5 dependency. The supported minimum version is unchanged.
- Update the pinned release signer module overlay to chi v5.4.0 while retaining the existing Cosign source revision.

### Upgrade

Install the verified integration ZIP using the existing procedure and restart Home Assistant. Retain sector configuration and the previous package for rollback. No configuration migration is required.

### Security

The signer dependency update resolves the reported chi advisory in release tooling. Home Assistant still requires Pillow 12.3.0 in the isolated test environment; the separate upstream constraint remains open. The helper keeps its read-only camera behavior, and simulated checks do not qualify a physical camera or establish sensing accuracy.

## [0.1.3] - 2026-10-24

### Changed

- Add bounded, offline production-boundary fuzzing to public release candidates, with source-bound reports and committed regression seeds.
- Reject deeply nested sector JSON with the documented validation error instead of leaking a recursion exception.

### Upgrade

Install the verified release package using the existing procedure. Retain configuration and the previous package for rollback; no configuration migration is required.

### Security

The shared fuzz job uses no credentials or live household data and runs target mutation without network access. Passing synthetic checks does not establish physical-device compatibility or sensing accuracy.

## [0.1.2] - 2026-10-18

### Changed

- Restore Dependabot approval automation by routing default-branch dependency PR metadata through the trusted target workflow. Trusted-author, draft and opt-in label checks remain enforced; the approval job does not execute PR code.
- Synchronize package version fields for this CI maintenance release.

### Upgrade

Install the verified integration ZIP using the documented procedure, then restart Home Assistant. Retain sector configuration and the previous package for rollback.

### Security

The helper continues to read existing ONVIF status without camera movement or additional streams. Synthetic tests do not qualify a physical camera.

## [0.1.1] - 2026-10-17

### Changed

- Document supported security reporting, governance, maintenance and the limits of the OpenSSF self-assessment and synthetic Home Assistant verification.
- Synchronize the distribution, integration manifest and runtime version for this documentation maintenance release.

### Upgrade

Install the verified integration ZIP using the existing procedure and restart Home Assistant. Existing detection sources, sector configuration and read-only ONVIF behavior remain unchanged. Keep the previous package for rollback.

### Security

This release does not add camera movement, streams, network permissions or live-device qualification. Existing freshness, cancellation and bounded-input checks remain in place.

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
