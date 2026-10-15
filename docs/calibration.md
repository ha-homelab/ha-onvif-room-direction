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
