# SPDX-License-Identifier: MIT
"""Read-only adapter for the Home Assistant 2026.10.3 ONVIF runtime.

Only create_ptz_service and GetStatus are invoked. An injected resolver makes
this module testable without Home Assistant or a camera.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .core import valid_pan


class ObservationError(ValueError):
    """A fixed diagnostic code, never an upstream exception or response."""


@dataclass(frozen=True)
class PanReading:
    """A validated camera observation and runtime generation."""

    pan: float
    timestamp: datetime
    generation: int


class OnvifPanReader:
    """Validate each camera response, including freshness and runtime identity."""

    def __init__(
        self,
        resolve: Callable[[], Any],
        *,
        max_age: float = 15,
        future_skew: float = 5,
        utcnow: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.resolve = resolve
        self.max_age = max_age
        self.future_skew = future_skew
        self.utcnow = utcnow
        self._device: Any = None
        self._stamp: datetime | None = None
        self.generation = 0

    async def read(self) -> PanReading:
        """Read one fresh position; no movement commands or stream operations."""
        device = self.resolve()
        if device is not self._device:
            self._device, self._stamp = device, None
            self.generation += 1
        if not getattr(device, "available", False):
            raise ObservationError("camera_unavailable")
        profiles = getattr(device, "profiles", ())
        profile = next((p for p in profiles if getattr(p, "ptz", None)), None)
        client = getattr(device, "device", None)
        if profile is None or not callable(getattr(client, "create_ptz_service", None)):
            raise ObservationError("unsupported_device")
        ptz = await client.create_ptz_service()
        status = await ptz.GetStatus({"ProfileToken": profile.token})
        if self.resolve() is not device:
            raise ObservationError("binding_changed")
        if getattr(status, "Error", None) not in (None, "", "0"):
            raise ObservationError("camera_error")
        stamp = getattr(status, "UtcTime", None)
        if not isinstance(stamp, datetime) or stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ObservationError("missing_timestamp")
        age = (self.utcnow() - stamp).total_seconds()
        if not -self.future_skew <= age <= self.max_age or (self._stamp is not None and stamp <= self._stamp):
            raise ObservationError("stale_position")
        position = getattr(status, "Position", None)
        pan_tilt = getattr(position, "PanTilt", None)
        pan = getattr(pan_tilt, "x", None)
        if not valid_pan(pan):
            raise ObservationError("invalid_position")
        space = getattr(pan_tilt, "space", None)
        if space not in (None, "", "http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace"):
            raise ObservationError("unsupported_coordinate_space")
        self._stamp = stamp
        return PanReading(float(pan), stamp, self.generation)
