"""Regressions discovered while preparing the input corpus."""

import pytest

from custom_components.onvif_room_direction.core import parse_sectors


def test_deep_sector_json_is_a_validation_error():
    with pytest.raises(ValueError, match="Invalid sectors"):
        parse_sectors("[" * 1200 + "0" + "]" * 1200)
