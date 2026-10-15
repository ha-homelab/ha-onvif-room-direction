# SPDX-License-Identifier: MIT
"""Version 1 of the dependency-free room-direction API.

No network, Home Assistant, clock, or configuration-file access happens here.
Pan is a normalized ONVIF coordinate, not a physical angle.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any

API_VERSION = 1


def valid_pan(value: Any) -> bool:
    """Accept finite numeric normalized pan positions; explicitly reject bools."""
    return (
        not isinstance(value, bool)
        and isinstance(value, (float, int))
        and math.isfinite(value)
        and -1 <= value <= 1
    )


@dataclass(frozen=True)
class Sector:
    """A sector excluding inner edges; normalized limits -1/+1 are inclusive."""

    area: str
    minimum: float
    maximum: float

    def __post_init__(self) -> None:
        if not isinstance(self.area, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", self.area):
            raise ValueError("Area must be an identifier, at most 64 characters")
        if not valid_pan(self.minimum) or not valid_pan(self.maximum) or self.minimum >= self.maximum:
            raise ValueError("Sector requires -1 <= min < max <= 1")


def validate_sectors(sectors: tuple[Sector, ...]) -> tuple[Sector, ...]:
    """Reject ambiguity and return sectors ordered by lower bound."""
    if not 1 <= len(sectors) <= 32 or not all(isinstance(s, Sector) for s in sectors):
        raise ValueError("Provide between 1 and 32 sectors")
    ordered = tuple(sorted(sectors, key=lambda sector: sector.minimum))
    for left, right in zip(ordered, ordered[1:], strict=False):
        if left.maximum > right.minimum:
            raise ValueError("Sectors must not overlap")
    return ordered


def parse_sectors(raw: str | list[dict[str, Any]]) -> tuple[Sector, ...]:
    """Parse UI JSON. Repeated area labels allow separated/wrapped sectors."""
    try:
        values = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(values, list):
            raise ValueError
        sectors = []
        for value in values:
            if not isinstance(value, dict) or set(value) != {"area", "min", "max"}:
                raise ValueError
            sectors.append(Sector(value["area"], value["min"], value["max"]))
        return validate_sectors(tuple(sectors))
    except (ValueError, TypeError, KeyError) as err:
        raise ValueError("Invalid sectors: use area, min, max and non-overlapping ranges") from err


def classify_pan(pan: Any, sectors: tuple[Sector, ...]) -> str | None:
    """Return the unique matching area, or None for gaps/edges/invalid input.

    Validate sectors once at configuration time. Even an accidentally ambiguous
    direct caller fails closed rather than assigning an arbitrary room.
    """
    if not valid_pan(pan):
        return None
    matches = [
        sector.area
        for sector in sectors
        if sector.minimum < pan < sector.maximum or pan == sector.minimum == -1 or pan == sector.maximum == 1
    ]
    return matches[0] if len(matches) == 1 else None


class RoomConfirmation:
    """Require two observations of one area separated by a monotonic interval."""

    def __init__(self, interval: float = 2.0) -> None:
        if isinstance(interval, bool) or not math.isfinite(interval) or interval <= 0:
            raise ValueError("Confirmation interval must be positive and finite")
        self.interval = interval
        self.room: str | None = None
        self.since = 0.0
        self._last: float | None = None

    def observe(self, room: str | None, now: float) -> str | None:
        """Clear confirmation immediately on gaps, transitions, or clock reversal."""
        if isinstance(now, bool) or not math.isfinite(now):
            self.room, self._last = None, None
            return None
        if room != self.room or self._last is None or now < self._last:
            self.room, self.since = room, now
            self._last = now
            return None
        self._last = now
        return room if room and now - self.since >= self.interval else None


@dataclass(frozen=True)
class DirectionConfig:
    """Validated runtime settings shared by HA and compatibility adapters."""

    camera_entity_id: str
    onvif_entry_id: str
    sources: tuple[str, ...]
    sectors: tuple[Sector, ...]
    camera_registry_id: str | None = None
    poll_interval: float = 2.0
    confirmation_interval: float = 2.0
    failure_interval: float = 10.0
    timeout: float = 4.0
    max_age: float = 15.0
    future_skew: float = 5.0
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.camera_entity_id or not self.onvif_entry_id or not self.sources:
            raise ValueError("Camera, ONVIF entry and detection sources are required")
        if len(set(self.sources)) != len(self.sources):
            raise ValueError("Detection sources must be unique")
        if not all(
            isinstance(source, str) and source.startswith("binary_sensor.") for source in self.sources
        ):
            raise ValueError("Detection sources must be binary sensor entity IDs")
        object.__setattr__(self, "sectors", validate_sectors(self.sectors))
        for field, minimum, maximum in (
            ("poll_interval", 0.5, 60),
            ("confirmation_interval", 0.5, 120),
            ("failure_interval", 1, 300),
            ("timeout", 0.5, 30),
            ("max_age", 1, 120),
            ("future_skew", 0, 30),
        ):
            value = getattr(self, field)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not minimum <= value <= maximum
            ):
                raise ValueError(f"Invalid {field}")
        if self.failure_interval < self.poll_interval:
            raise ValueError("Failure interval must be at least the poll interval")
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be boolean")


def config_from_mapping(data: dict[str, Any]) -> DirectionConfig:
    """Convert a stored HA config-entry dictionary into the public API."""
    fields = {key: value for key, value in data.items() if key in DirectionConfig.__dataclass_fields__}
    fields["sources"] = tuple(data["sources"])
    fields["sectors"] = parse_sectors(data["sectors"])
    return DirectionConfig(**fields)
