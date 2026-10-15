# SPDX-License-Identifier: MIT
"""Synthetic boundary, configuration and confirmation regressions."""

import math

import pytest

from custom_components.onvif_room_direction.core import (
    API_VERSION,
    DirectionConfig,
    RoomConfirmation,
    Sector,
    classify_pan,
    parse_sectors,
)

SECTORS = (Sector("zone_a", -1, -0.2), Sector("zone_b", 0.2, 1))


@pytest.mark.parametrize("pan", [None, True, False, "0.5", math.nan, math.inf, -1.01, 1.01, -0.2, 0, 0.2])
def test_invalid_boundary_and_gap_positions_are_unknown(pan):
    assert classify_pan(pan, SECTORS) is None


def test_synthetic_classification():
    assert API_VERSION == 1
    assert classify_pan(-0.6, SECTORS) == "zone_a"
    assert classify_pan(0.6, SECTORS) == "zone_b"
    assert classify_pan(-1, SECTORS) == "zone_a"
    assert classify_pan(1, SECTORS) == "zone_b"
    assert classify_pan(0.5, (Sector("a", -1, 1), Sector("b", 0, 1))) is None


def test_confirmation_clears_gaps_transitions_and_clock_reversal():
    confirm = RoomConfirmation()
    assert confirm.observe("zone_a", 10) is None
    assert confirm.observe("zone_a", 11) is None
    assert confirm.observe("zone_a", 12) == "zone_a"
    assert confirm.observe(None, 14) is None
    assert confirm.observe("zone_a", 16) is None
    assert confirm.observe("zone_b", 18) is None
    assert confirm.observe("zone_b", 20) == "zone_b"
    assert confirm.observe("zone_b", 10) is None
    assert confirm.observe("zone_b", 12) == "zone_b"
    assert confirm.observe("zone_b", math.nan) is None
    assert confirm.observe("zone_b", 20) is None


@pytest.mark.parametrize(
    "raw",
    [
        "null",
        "{}",
        "[]",
        "no json",
        '[{"area":"bad label","min":-1,"max":1}]',
        '[{"area":"zone_a","min":false,"max":1}]',
        '[{"area":"zone_a","min":-2,"max":1}]',
        '[{"area":"zone_a","min":0.5,"max":0.2}]',
        '[{"area":"zone_a","min":-1,"max":1,"extra":0}]',
        '[{"area":"a","min":-1,"max":0.5},{"area":"b","min":0,"max":1}]',
    ],
)
def test_invalid_sectors_rejected(raw):
    with pytest.raises(ValueError):
        parse_sectors(raw)


def test_separated_ranges_can_share_an_area_and_touch_at_unknown_edge():
    sectors = parse_sectors('[{"area":"a","min":0,"max":1},{"area":"a","min":-1,"max":0}]')
    assert classify_pan(-0.5, sectors) == classify_pan(0.5, sectors) == "a"
    assert classify_pan(0, sectors) is None


@pytest.mark.parametrize(
    "option",
    [
        {"sources": ()},
        {"poll_interval": 0},
        {"timeout": math.nan},
        {"max_age": True},
        {"future_skew": -1},
        {"failure_interval": 1},
        {"enabled": 1},
        {"sources": ("sensor.demo",)},
    ],
)
def test_bad_runtime_config_fails_before_polling(option):
    args = dict(
        camera_entity_id="camera.demo",
        onvif_entry_id="synthetic",
        sources=("binary_sensor.demo_motion",),
        sectors=SECTORS,
    )
    with pytest.raises(ValueError):
        DirectionConfig(**(args | option))
