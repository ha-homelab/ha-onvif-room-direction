# Compatibility and troubleshooting

## Exact API baseline

This beta targets **Home Assistant Core 2026.10.0**, Python **3.14.2+**. Its adapter has been checked against the upstream [ONVIF setup](https://github.com/home-assistant/core/blob/2026.10.0/homeassistant/components/onvif/__init__.py), [device](https://github.com/home-assistant/core/blob/2026.10.0/homeassistant/components/onvif/device.py), and [profile models](https://github.com/home-assistant/core/blob/2026.10.0/homeassistant/components/onvif/models.py).

It relies on the existing ONVIF config entry's `runtime_data`, `available`, `profiles[*].ptz`, `profiles[*].token` and `device.create_ptz_service()`. It selects the first PTZ-capable profile and calls only `GetStatus({"ProfileToken": token})`. This runtime interface belongs to another integration and is not a stable public Home Assistant extension API. Other Core releases are unverified; retest before upgrading.

The beta is tested offline against actual 2026.10.0 Home Assistant classes, event bus and configuration flows with synthetic camera responses. No physical camera model, full end-to-end ONVIF connection, or live Home Assistant deployment is certified by these tests. Compatible firmware must return valid normalized `Position.PanTilt.x` and strictly advancing timezone-aware `UtcTime`. If `PanTilt.space` is present, only ONVIF's generic normalized position space is accepted. Missing space metadata is accepted if the value is normalized.

## Setup and states

- **Camera is not selectable:** it must be an entity from the built-in ONVIF integration. A generic RTSP camera does not expose this runtime.
- **Already configured:** only one helper is allowed per ONVIF device, including devices with several camera profiles. Configure a different ONVIF device for each additional helper.
- **`unsupported_device` at setup:** no PTZ-capable profile is advertised. Fixed cameras and firmware without PTZ status are unsupported. No alternative protocol or movement probe is attempted.
- **`unknown` / `idle`:** no selected source is actively on, or an installation guard rejected the calibration. Restored states are ignored.
- **`unknown` / `unconfirmed`:** a reading is valid but it lies in an unassigned gap or has not passed confirmation yet. Check the pan attribute and the configured sectors.
- **`unavailable` / `camera_unavailable`:** the original ONVIF entry is disconnected, reloading or missing runtime data. It retries while detection remains active.
- **`unavailable` / `binding_changed`:** the camera was removed, replaced, or moved to another integration entry. Recreate the helper to establish a deliberate new binding. Renaming a registered camera is supported through its stable registry identifier.
- **`unavailable` / `missing_timestamp`:** the camera omitted time or returned a naive timestamp. This beta will not guess freshness.
- **`unavailable` / `stale_position`:** a timestamp repeats, moves backward, exceeds maximum age/future skew, or the last accepted reading expired. Correct time synchronization and confirm that status timestamps advance.
- **`unavailable` / `invalid_position`:** pan is missing, nonnumeric, nonfinite, or outside [-1, 1].
- **`unavailable` / `unsupported_coordinate_space`:** the camera reports a different position space. Values are not automatically converted.
- **`unavailable` / `camera_error`:** the status contains an ONVIF error. The original response is deliberately not published.
- **`unavailable` / `read_failed`:** timeout, unsupported GetStatus operation, or another upstream exception. Check the original ONVIF integration and camera documentation locally. Raw exception text is not logged or exported by this helper.

If a detection entity is renamed, update its selection in options. If a motion sensor stays on indefinitely, polling continues; fix the original detection source or disable the helper. If one source is unavailable while another is on, the active source still permits polling.

## What to include in a bug report

Include your Home Assistant version, this integration's version, the fixed reason, reproduction steps and sanitized diagnostics. State whether firmware reports advancing timestamps and normalized pan. Never attach credentials, full ONVIF responses, unredacted logs, screenshots of private areas, camera addresses, or exact home calibration. Use invented labels and sample coordinates to illustrate a problem.
