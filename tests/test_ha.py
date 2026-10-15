# SPDX-License-Identifier: MIT
"""Real HA classes and event bus, with mocked registry/device boundaries.

These tests do not bootstrap ONVIF, open sockets, or use user configuration.
"""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock, patch

import pytest

pytest.importorskip("homeassistant")

from homeassistant.config_entries import ConfigEntries  # noqa: E402
from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.data_entry_flow import AbortFlow  # noqa: E402

from custom_components.onvif_room_direction import (  # noqa: E402  # noqa: E402
    async_setup_entry,
    async_unload_entry,
    config_flow,
    sensor,
)
from custom_components.onvif_room_direction.adapter import PanReading  # noqa: E402
from custom_components.onvif_room_direction.const import DEFAULT_SECTORS, DOMAIN  # noqa: E402
from custom_components.onvif_room_direction.core import DirectionConfig, Sector  # noqa: E402
from custom_components.onvif_room_direction.diagnostics import (
    async_get_config_entry_diagnostics,  # noqa: E402
)

pytestmark = pytest.mark.ha


@pytest.fixture
async def env(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    hass.config_entries = ConfigEntries(hass, {})
    config = DirectionConfig(
        camera_entity_id="camera.demo",
        onvif_entry_id="synthetic-onvif",
        sources=("binary_sensor.demo_motion",),
        sectors=(Sector("zone_a", -1, -0.2), Sector("zone_b", 0.2, 1)),
    )
    entity = sensor.DirectionSensor(config, unique_id="synthetic-direction")
    entity.hass = hass
    entity.entity_id = "sensor.demo_direction"
    entity.async_write_ha_state = Mock()
    hass.states.async_set("binary_sensor.demo_motion", "on")
    yield hass, entity
    entity._stop()
    if entity._tasks:
        await asyncio.gather(*entity._tasks, return_exceptions=True)
    await hass.async_stop(force=True)


def reading(pan=0.6, generation=1):
    return PanReading(pan, datetime.now(UTC), generation)


async def test_identical_polls_refresh_ha_without_attribute_churn(env):
    _, entity = env
    entity._publish("zone_a", -0.6)
    attrs = entity._attr_extra_state_attributes.copy()
    for _ in range(10):
        entity._publish("zone_a", -0.6)
    assert entity._attr_extra_state_attributes == attrs
    assert entity.async_write_ha_state.call_count == 11
    entity._publish(None, available=False, reason="read_failed")
    assert entity._attr_native_value is None and not entity._attr_available
    assert entity._attr_extra_state_attributes["pan"] is None


async def test_real_ha_event_subscription_and_removal(env):
    hass, entity = env
    started = asyncio.Event()
    blocked = asyncio.Event()

    async def read(_self):
        started.set()
        await blocked.wait()
        return reading()

    with patch.object(sensor.OnvifPanReader, "read", read):
        await entity.async_added_to_hass()
        await started.wait()
        task = entity._task
        for _ in range(8):
            entity.reconcile()
        assert entity._task is task
        hass.states.async_set("binary_sensor.demo_motion", "off")
        await hass.async_block_till_done()
        assert entity._task is None
        assert entity._attr_native_value is None
        await entity.async_will_remove_from_hass()
        entity._call_on_remove_callbacks()
        assert entity._stopped


async def test_restored_disabled_and_guarded_entities_do_not_poll(env):
    hass, entity = env
    hass.states.async_set("binary_sensor.demo_motion", "on", {"restored": True})
    entity.reconcile()
    assert entity._task is None
    hass.states.async_set("binary_sensor.demo_motion", "on")
    entity._eligibility = lambda: False
    entity.reconcile()
    assert entity._task is None


async def test_confirm_fail_recover_and_runtime_replacement(env):
    _, entity = env
    observations, delays = [], []
    results = [
        reading(),
        reading(),
        RuntimeError("never publish this secret"),
        reading(),
        reading(),
        reading(generation=2),
        reading(generation=2),
    ]
    entity.async_write_ha_state = lambda: observations.append(
        (entity._attr_native_value, entity._attr_available)
    )

    async def sleep(delay):
        delays.append(delay)
        if len(delays) == len(results):
            entity._stopped = True

    with (
        patch.object(sensor.OnvifPanReader, "read", AsyncMock(side_effect=results)),
        patch.object(sensor.asyncio, "sleep", sleep),
        patch.object(sensor, "monotonic", side_effect=[10, 12, 20, 22, 30, 32]),
    ):
        entity.reconcile()
        await entity._task
    assert observations == [
        (None, True),
        ("zone_b", True),
        (None, False),
        (None, True),
        ("zone_b", True),
        (None, True),
        ("zone_b", True),
    ]
    assert delays == [2, 2, 10, 2, 2, 2, 2]
    assert "secret" not in str(entity._attr_extra_state_attributes)


async def test_old_cancelled_response_cannot_replace_new_task(env):
    _, entity = env
    gate = asyncio.Event()
    started = asyncio.Event()

    async def late(_self):
        started.set()
        try:
            await gate.wait()
        except asyncio.CancelledError:
            await gate.wait()
        return reading()

    with patch.object(sensor.OnvifPanReader, "read", late):
        entity.reconcile()
        old = entity._task
        await started.wait()
        entity._cancel()
        entity.reconcile()
        current = entity._task
        gate.set()
        await old
        assert entity._task is current
        assert not entity._stopped


async def test_expiry_clears_a_confirmed_result_during_blocked_poll(env):
    _, entity = env
    entity._task = asyncio.current_task()
    confirm = sensor.RoomConfirmation()
    entity._publish("zone_b", 0.6)
    with patch.object(sensor, "async_call_later") as later:
        entity._arm_expiry(reading(), confirm, entity._task)
        later.call_args.args[2](None)
    assert not entity._attr_available
    assert entity._attr_native_value is None
    entity._task = None


async def test_binding_checks_and_stable_registry_identifier(env):
    hass, entity = env
    device = NS(available=True)
    source = NS(platform="onvif", config_entry_id="synthetic-onvif")
    entry = NS(domain="onvif", runtime_data=device)
    with (
        patch.object(sensor.er, "async_get", return_value=NS(async_get=lambda _: source)),
        patch.object(hass.config_entries, "async_get_entry", return_value=entry),
    ):
        assert entity._resolve_device() is device
        source.config_entry_id = "replaced"
        with pytest.raises(ValueError, match="binding_changed"):
            entity._resolve_device()


async def test_flow_validation_duplicate_and_options(env):
    hass, _ = env
    source = NS(
        platform="onvif", entity_id="camera.demo", config_entry_id="synthetic-onvif", id="synthetic-registry"
    )
    onvif = NS(
        entry_id="synthetic-onvif", domain="onvif", runtime_data=NS(available=True, profiles=[NS(ptz=True)])
    )
    flow = config_flow.ConfigFlow()
    flow.hass = hass
    flow.context = {"source": "user"}
    flow.handler = DOMAIN
    user_input = {
        "name": "Demo direction",
        "camera_entity_id": "camera.demo",
        "sources": ["binary_sensor.demo_motion"],
        "sectors": DEFAULT_SECTORS,
    }
    with (
        patch.object(config_flow.er, "async_get", return_value=NS(async_get=lambda _: source)),
        patch.object(hass.config_entries, "async_get_entry", return_value=onvif),
    ):
        result = await flow.async_step_user()
        assert result["type"] == "form"
        assert result["data_schema"](user_input) == user_input
        invalid = await flow.async_step_user(user_input | {"sectors": "[]"})
        assert invalid["errors"] == {"base": "invalid_config"}
        result = await flow.async_step_user(user_input)
        assert result["type"] == "create_entry"
        assert result["data"]["camera_registry_id"] == source.id
        with patch.object(
            hass.config_entries, "async_entry_for_domain_unique_id", return_value=NS(source="user")
        ):
            with pytest.raises(AbortFlow, match="already_configured"):
                await flow.async_step_user(user_input)
    entry = NS(data=result["data"], options={})
    options = config_flow.OptionsFlow()
    options.hass = hass
    options.handler = "synthetic-direction"
    with patch.object(hass.config_entries, "async_get_known_entry", return_value=entry):
        result = await options.async_step_init()
        values = result["data_schema"]({"sources": user_input["sources"], "sectors": DEFAULT_SECTORS})
        assert (await options.async_step_init(values))["type"] == "create_entry"
        assert (await options.async_step_init(values | {"timeout": -1}))["errors"]


async def test_diagnostics_and_entry_lifecycle(env):
    hass, entity = env
    data = {
        "camera_entity_id": "camera.demo",
        "onvif_entry_id": "synthetic-onvif",
        "sources": ["binary_sensor.demo_motion"],
        "sectors": DEFAULT_SECTORS,
    }
    entry = NS(
        entry_id="synthetic-direction",
        data=data,
        options={},
        async_on_unload=Mock(),
        add_update_listener=Mock(),
    )
    hass.data[DOMAIN] = {entry.entry_id: entity}
    diagnostic = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostic["source_count"] == 1
    assert "camera.demo" not in str(diagnostic)
    assert "zone_a" not in str(diagnostic)
    with (
        patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()) as setup,
        patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)),
    ):
        assert await async_setup_entry(hass, entry)
        setup.assert_awaited_once()
        assert await async_unload_entry(hass, entry)
        assert entry.entry_id not in hass.data[DOMAIN]
