# Extension API v1

`custom_components.onvif_room_direction.core.API_VERSION == 1`. The core and adapter import without Home Assistant installed; neither reads files, environment variables, credentials or network state at import. Keep the integration installed alongside a dependent private custom integration. Do not copy its algorithms into another project.

```python
from custom_components.onvif_room_direction.core import (
    DirectionConfig, RoomConfirmation, Sector, classify_pan,
)

sectors = (Sector("zone_a", -1, -0.2), Sector("zone_b", 0.2, 1))
assert classify_pan(-0.6, sectors) == "zone_a"
assert classify_pan(0, sectors) is None
confirmation = RoomConfirmation(interval=2)
assert confirmation.observe("zone_a", 10) is None
assert confirmation.observe("zone_a", 12) == "zone_a"
```

`Sector(area, minimum, maximum)` validates a case-sensitive area identifier and finite normalized bounds. Inner edges and gaps are unknown; -1 and +1 are included if a sector extends to them. `parse_sectors(str_or_list)` checks overlap and normalizes order. `classify_pan(pan, sectors)` returns a unique area or `None`, including for invalid and ambiguous input. Direct callers should validate a sector set once before use.

`RoomConfirmation(interval=2.0).observe(area_or_none, monotonic_seconds)` needs at least two valid observations separated by the interval. A changed area, gap, invalid clock, or reversed clock resets it. Fresh camera timestamp checks are the caller's responsibility; `adapter.OnvifPanReader` supplies them.

`DirectionConfig(camera_entity_id, onvif_entry_id, sources, sectors, camera_registry_id=None, poll_interval=2, confirmation_interval=2, failure_interval=10, timeout=4, max_age=15, future_skew=5, enabled=True)` is immutable and validates timing, sources and sectors. Sources and sectors are tuples. The optional registry identifier preserves camera binding across renames. Without it, `camera_entity_id` is looked up by its current entity ID; private adapters may bind another ONVIF entity from the same config entry.

```python
from custom_components.onvif_room_direction.sensor import DirectionSensor

config = DirectionConfig(
    camera_entity_id="camera.demo",
    onvif_entry_id="synthetic_onvif_entry",
    sources=("binary_sensor.demo_motion",),
    sectors=sectors,
)
entity = DirectionSensor(
    config,
    unique_id="stable_private_adapter_id",
    name="Demo direction",
    eligibility=lambda: True,  # Replace with your local calibration-binding check.
)
```

`DirectionSensor` is the supported Home Assistant extension class. Use the normal `async_add_entities` callback to add it. Preserve the old entity ID and unique ID when replacing an existing private implementation. An optional `eligibility` callback must be synchronous, cheap and side-effect-free. False or an exception prevents observation. The guard is checked before and after reads; call public `reconcile()` immediately when your external geometry/configuration changes, so an old estimate clears without waiting for a poll.

The class manages its own event subscriptions, task cancellation, expiry timer and shutdown. Never call its internal `_observe` directly. Underscore-prefixed fields and methods are internal and can change. It creates no movement services and never takes ownership of the shared ONVIF client.

Reads are serialized within a sensor, including across cancelled detection episodes. An old transport that delays cancellation can delay the next read, but its result cannot update the new episode. Results returned after the read timeout are rejected even when a transport suppresses cancellation. The shared client is never forcibly closed by this helper.

Unload waits at most `timeout + 1` seconds for outstanding tasks. Fully noncooperative third-party I/O may outlive that wait, with its result blocked from publication. The lock is per sensor, not a global lock on the shared ONVIF client; it does not serialize separate sensor instances or a replacement instance created after a bounded unload.

`adapter.OnvifPanReader(resolve, max_age=15, future_skew=5, utcnow=...)` accepts a synchronous runtime resolver. `await reader.read()` returns `PanReading(pan, timestamp, generation)`. Generation changes when the resolved object changes. Clear confirmation after a generation change or any exception. Upstream exceptions may contain private values; do not print them. `ObservationError` contains a fixed reason defined by this package; the HA sensor sanitizes other exceptions.

Breaking changes will update `API_VERSION` and the changelog. Check the selected release's channel and notes when depending on this contract. The public HA domain is stable; the manifest version, packaged distribution version and root `version` file must remain synchronized.
