# Example use cases

## Highlight a direction on a floor plan

Map the sensor's configured area labels to visual highlights. Render `unknown` and `unavailable` explicitly so an old area never looks current. Use detection independently if the UI also needs to show that motion is active. The example uses synthetic labels and IDs:

```yaml
type: entities
title: Demo camera direction
entities:
  - entity: binary_sensor.demo_motion
    name: Detection
  - entity: sensor.demo_direction
    name: Estimated direction
```

## Annotate a detection notification

Combine your existing motion signal with a currently confirmed direction when composing a notification. If the helper is unknown, say the direction is unknown. Do not retain a previous area as a fallback.

## Compare tracking behavior

Inspect the helper's pan and confirmation behavior during a controlled test. It can reveal a gap that is too narrow or a camera whose timestamps stop advancing. The diagnostics export includes successful/failed read counts and the latest fixed reason code, without camera identifiers or calibration values.

## Use an estimate as a secondary automation input

A direction label can inform a noncritical visual or convenience automation alongside independent occupancy evidence. A camera facing an area does not prove anyone is there. Avoid using this estimate alone for safety functions, access control, or any decision that requires reliable person detection.

Multiple people, a stationary parked camera, camera motion without tracking, or an area outside the lens view can make the estimate misleading even when the pan reading is technically valid.
