# Calibrate for your camera and installation

Pan is a normalized ONVIF coordinate in [-1, 1], not degrees. Its physical meaning depends on the camera and mounting. This integration cannot provide universal room angles.

1. Confirm detection and PTZ status work in the built-in ONVIF integration. Configure the helper with your own chosen area labels. The initial JSON is only a synthetic example.
2. During a controlled detection, inspect the helper sensor's `pan` attribute in Home Assistant's Developer tools. Use the camera's existing interface or a naturally occurring tracking event to observe its direction; this helper has no movement controls.
3. Record several readings when the camera faces clearly inside each intended area. Include approaches from both sides and any tracking overshoot. Do not calibrate from a single point.
4. Choose conservative non-overlapping intervals. Leave gaps at entrances, shared sight lines, ambiguous directions and unstable tracking positions. Configure those intervals in the helper's options.
5. Repeat the controlled observation. The expected area should appear only after confirmation, and an ambiguous direction should immediately become unknown. Detection off should stop polling and clear the value.
6. If the mounting, camera orientation, coordinate convention or tracked areas change, disable the helper and recalibrate before enabling it again.

This public helper cannot know when a camera was physically moved. Installation adapters may supply an `eligibility` guard to invalidate calibration when a stored mounting or geometry binding changes; see the API document.

Use longer confirmation for noisy tracking and wider gaps for uncertain boundaries. A long confirmation interval may never confirm if the camera changes areas faster than that interval. Do not increase clock tolerance just to hide a broken camera timestamp. Set the camera's clock correctly using its own supported administration interface.

## Choosing bounds and testing edges

Keep your calibration notes local. For each intended area, record repeated interior readings and readings near the points where the direction becomes ambiguous. Use them to choose a conservative interior interval, not an interval that covers every observed value. The helper has no tilt or zoom model: if one pan coordinate can face different areas at different tilts, that direction cannot be assigned confidently by this helper alone.

The synthetic example `zone_a: (-1, -0.2)` and `zone_b: (0.2, 1)` classifies `-0.6` as `zone_a` and `0.6` as `zone_b`. The exact coordinates `-0.2` and `0.2`, and everything between them, are unknown. The outer coordinates `-1` and `1` are included. Even two touching sectors leave their shared endpoint unknown; a small gap is usually easier to reason about than a precision-sensitive boundary.

If one physical direction straddles the normalized wrap point, split it into two non-overlapping sectors with the same label, for example:

```json
[
  {"area": "wrapped_zone", "min": -1, "max": -0.8},
  {"area": "wrapped_zone", "min": 0.8, "max": 1}
]
```

Those values are invented. Do not express wrapping as `min > max`, and do not assume every camera wraps at the same physical direction. The valid label pattern is a letter followed by up to 63 letters, digits or underscores; labels are case-sensitive. Repeated labels are allowed, overlapping intervals are not.

## Timing expectations

Polling waits the configured interval **after** a completed read, so network latency adds to the time between samples. Confirmation measures elapsed monotonic time between valid observations of the same area, not a fixed number of polls. With the two-second defaults, the second qualifying sample can confirm; a brief detection that ends sooner remains unknown.

Each accepted sample must arrive within the maximum position age, with a timestamp newer than the previous accepted sample in that observation episode. Its expiry timer clears the estimate even if the next read stalls. Choose a polling interval and expected response latency comfortably below the freshness limit. A polling interval longer than the freshness window repeatedly expires confirmation; increasing confirmation duration does not solve that problem.

Changing sectors or timing through options reloads the helper and clears the old confirmation. A failed read, expired sample, gap, area transition or replacement ONVIF runtime also requires confirmation again. Identical successful samples update HA state reporting without changing the `observed_at` attribute; that attribute marks the last change to the published observation and is not the camera's latest timestamp. Use the current state/reason and diagnostic read counts when checking progress.
