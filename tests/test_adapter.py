# SPDX-License-Identifier: MIT
"""Only synthetic ONVIF objects. No camera/network fixtures are used."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import pytest

from custom_components.onvif_room_direction.adapter import ObservationError, OnvifPanReader

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def status(pan=0.6, stamp=NOW, error="0", space=None):
    return NS(Error=error, UtcTime=stamp, Position=NS(PanTilt=NS(x=pan, space=space)))


def camera(response=None):
    ptz = NS(GetStatus=AsyncMock(return_value=response or status()))
    device = NS(
        available=True,
        profiles=[NS(token="synthetic-profile", ptz=True)],
        device=NS(create_ptz_service=AsyncMock(return_value=ptz)),
    )
    return device, ptz


async def test_read_only_calls_and_duplicate_timestamps():
    device, ptz = camera()
    reader = OnvifPanReader(lambda: device, utcnow=lambda: NOW)
    reading = await reader.read()
    assert reading.pan == 0.6 and reading.generation == 1
    ptz.GetStatus.assert_awaited_once_with({"ProfileToken": "synthetic-profile"})
    with pytest.raises(ObservationError, match="stale_position"):
        await reader.read()


@pytest.mark.parametrize(
    "response, reason",
    [
        (status(stamp=NOW - timedelta(seconds=16)), "stale_position"),
        (status(stamp=NOW + timedelta(seconds=6)), "stale_position"),
        (status(stamp=NOW.replace(tzinfo=None)), "missing_timestamp"),
        (status(stamp=None), "missing_timestamp"),
        (status(pan=True), "invalid_position"),
        (status(pan=float("nan")), "invalid_position"),
        (status(error="upstream sensitive error"), "camera_error"),
        (status(space="urn:other-space"), "unsupported_coordinate_space"),
        (NS(Error=None, UtcTime=NOW, Position=None), "invalid_position"),
    ],
)
async def test_rejections_are_fixed_diagnostic_codes(response, reason):
    device, _ = camera(response)
    with pytest.raises(ObservationError, match=reason):
        await OnvifPanReader(lambda: device, utcnow=lambda: NOW).read()


async def test_runtime_replacement_during_request_is_rejected():
    device, ptz = camera()
    current = device

    async def replace(_):
        nonlocal current
        current = camera()[0]
        return status()

    ptz.GetStatus.side_effect = replace
    reader = OnvifPanReader(lambda: current, utcnow=lambda: NOW)
    with pytest.raises(ObservationError, match="binding_changed"):
        await reader.read()
    assert (await reader.read()).generation == 2


@pytest.mark.parametrize(
    "mutation,reason",
    [
        (lambda d: setattr(d, "available", False), "camera_unavailable"),
        (lambda d: setattr(d, "profiles", []), "unsupported_device"),
        (lambda d: setattr(d, "device", None), "unsupported_device"),
    ],
)
async def test_unavailable_and_unsupported_cameras(mutation, reason):
    device, ptz = camera()
    mutation(device)
    with pytest.raises(ObservationError, match=reason):
        await OnvifPanReader(lambda: device).read()
    ptz.GetStatus.assert_not_awaited()
