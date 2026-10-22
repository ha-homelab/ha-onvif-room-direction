"""Exercise real sector validation, classification and confirmation offline."""

import json
import math
import sys
from pathlib import Path

import atheris

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
with atheris.instrument_imports():
    from custom_components.onvif_room_direction import core


def test_one_input(data):
    try:
        sectors = core.parse_sectors(data.decode("utf-8", errors="replace"))
    except ValueError:
        pass
    else:
        canonical = [{"area": s.area, "min": s.minimum, "max": s.maximum} for s in sectors]
        assert core.parse_sectors(json.dumps(canonical)) == sectors
        assert 1 <= len(sectors) <= 32
        for left, right in zip(sectors, sectors[1:], strict=False):
            assert left.maximum <= right.minimum
        for value in [True, False, None, math.inf, math.nan, -1.01, 1.01]:
            assert core.classify_pan(value, sectors) is None
        for sector in sectors:
            midpoint = sector.minimum + (sector.maximum - sector.minimum) / 2
            if sector.minimum < midpoint < sector.maximum:
                assert core.classify_pan(midpoint, sectors) == sector.area
    provider = atheris.FuzzedDataProvider(data)
    start = provider.ConsumeFloatInRange(-100000, 100000)
    interval = provider.ConsumeFloatInRange(0.5, 120)
    confirmation = core.RoomConfirmation(interval)
    assert confirmation.observe("zone_a", start) is None
    assert confirmation.observe("zone_a", start + interval / 2) is None
    assert confirmation.observe("zone_a", start + interval + 0.001) == "zone_a"
    assert confirmation.observe("zone_b", start + interval + 1) is None
    assert confirmation.observe("zone_b", start - 1) is None
    assert confirmation.observe(None, start + interval + 2) is None


if __name__ == "__main__":
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()
