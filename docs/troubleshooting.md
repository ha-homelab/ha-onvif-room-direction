# Compatibility and troubleshooting

## Exact API baseline

The tested baseline is **Home Assistant Core 2026.10.3**, Python **3.14.2+**. Its adapter has been checked against the upstream [ONVIF setup](https://github.com/home-assistant/core/blob/2026.10.3/homeassistant/components/onvif/__init__.py), [device](https://github.com/home-assistant/core/blob/2026.10.3/homeassistant/components/onvif/device.py), and [profile models](https://github.com/home-assistant/core/blob/2026.10.3/homeassistant/components/onvif/models.py).

It relies on the existing ONVIF config entry's `runtime_data`, `available`, `profiles[*].ptz`, `profiles[*].token` and `device.create_ptz_service()`. It selects the first PTZ-capable profile and calls only `GetStatus({"ProfileToken": token})`. This runtime interface belongs to another integration and is not a stable public Home Assistant extension API. Other Core releases are unverified; retest before upgrading.

The integration is tested offline against actual 2026.10.3 Home Assistant classes, event bus and configuration flows with synthetic camera responses, including installation of its ZIP in an isolated interpreter. No physical camera model, full end-to-end ONVIF connection, or live Home Assistant deployment is certified by these tests. Compatible firmware must return valid normalized `Position.PanTilt.x` and strictly advancing timezone-aware `UtcTime`. If `PanTilt.space` is present, only ONVIF's generic normalized position space is accepted. Missing space metadata is accepted if the value is normalized. See [validation scope](validation.md).

## Integration does not appear or fails to load

Check the [installation layout](installation.md) first: `custom_components/onvif_room_direction/manifest.json` must exist directly in the HA configuration directory. Restart HA after changing files, and refresh the browser if Add integration still shows an old list. Do not install the repository source ZIP as though it were the integration ZIP. HACS downloads the integration files but you still configure the helper under Devices & services.

Check the installed Home Assistant version and the release notes before changing dependencies manually. The helper relies on the built-in ONVIF integration and has no separately configured camera credentials. Configure and load that integration first. A camera whose video works but whose firmware lacks readable PTZ status remains unsupported.

## Setup and states

- **Camera is not selectable:** it must be an entity from the built-in ONVIF integration. A generic RTSP camera does not expose this runtime.
- **Already configured:** only one helper is allowed per ONVIF device, including devices with several camera profiles. Configure a different ONVIF device for each additional helper.
- **`unsupported_device` at setup:** no PTZ-capable profile is advertised. Fixed cameras and firmware without PTZ status are unsupported. No alternative protocol or movement probe is attempted.
- **`unknown` / `idle`:** no selected source is actively on, or an installation guard rejected the calibration. Restored states are ignored.
- **`unknown` / `unconfirmed`:** a reading is valid but it lies in an unassigned gap or has not passed confirmation yet. Check the pan attribute and the configured sectors.
- **`unavailable` / `camera_unavailable`:** the original ONVIF entry is disconnected, reloading or missing runtime data. It retries while detection remains active.
- **`unavailable` / `binding_changed`:** the camera was removed, replaced, or moved to another integration entry. Recreate the helper to establish a deliberate new binding. Renaming a registered camera is supported through its stable registry identifier.
- **`unavailable` / `missing_timestamp`:** the camera omitted time or returned a naive timestamp. The helper will not guess freshness.
- **`unavailable` / `stale_position`:** a timestamp repeats, moves backward, exceeds maximum age/future skew, or the last accepted reading expired. Correct time synchronization and confirm that status timestamps advance.
- **`unavailable` / `invalid_position`:** pan is missing, nonnumeric, nonfinite, or outside [-1, 1].
- **`unavailable` / `unsupported_coordinate_space`:** the camera reports a different position space. Values are not automatically converted.
- **`unavailable` / `camera_error`:** the status contains an ONVIF error. The original response is deliberately not published.
- **`unavailable` / `read_failed`:** timeout, unsupported GetStatus operation, or another upstream exception. Check the original ONVIF integration and camera documentation locally. Raw exception text is not logged or exported by this helper.

If a detection entity is renamed, update its selection in options. If a motion sensor stays on indefinitely, polling continues; fix the original detection source or disable the helper. If one source is unavailable while another is on, the active source still permits polling.

## Recovery and timing

Failures discard the area and use the configured retry interval while any selected source remains on. A successful retry first becomes unconfirmed; a later qualifying sample can confirm. Switching all sources off clears the failure state to `unknown`/`idle` and stops the episode. Enabling a disabled helper during an active detection starts a new episode without restoring the old area.

A reloading ONVIF entry may temporarily report `camera_unavailable`, `binding_changed`, or `read_failed`, depending on when the shared runtime changes or closes. Wait for that integration to recover. A replacement runtime clears confirmation; permanent removal/recreation of its config entry requires a new helper binding.

Only one read per sensor proceeds at a time, even if a previous transport coroutine is slow to honour cancellation. A new detection may therefore wait for a cancelled read to finish. A response returned after the read timeout is discarded. The helper does not close the shared ONVIF client to force cancellation, because other ONVIF entities use it. If the upstream client remains stuck, investigate the built-in ONVIF integration and use the [recovery procedure](installation.md#upgrade-rollback-and-removal).

On unload, cleanup waits at most the configured read timeout plus one second for this sensor's tasks. A third-party transport that completely ignores cancellation may outlive that wait; Python cannot force it to terminate safely. Its eventual result cannot publish state after unload. The per-sensor serialization guarantee does not coordinate independent sensor instances or a new instance created by reloading after that cleanup limit.

If `observed_at` is unchanged while the area and pan are unchanged, that alone is not a stalled poller. Identical samples retain attributes to avoid Recorder churn; diagnostics expose read counters. If the state repeatedly expires between valid responses, reduce polling latency/interval or revisit the configured freshness window rather than treating an old area as current.

## What to include in a bug report

Include your Home Assistant version, this integration's version, the fixed reason, reproduction steps and sanitized diagnostics. State whether firmware reports advancing timestamps and normalized pan. Never attach credentials, full ONVIF responses, unredacted logs, screenshots of private areas, camera addresses, or exact home calibration. Use invented labels and sample coordinates to illustrate a problem.
