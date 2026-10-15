# SPDX-License-Identifier: MIT
"""Run a packaged integration in real HA, with a synthetic ONVIF boundary.

Invoked by test_package in an isolated interpreter so checkout imports cannot
hide missing ZIP files. Never start a real ONVIF connection or HA HTTP server.
"""

import asyncio
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from unittest.mock import AsyncMock, patch
from zipfile import ZipFile


def no_network(event, _args):
    if event in {
        "socket.connect",
        "socket.bind",
        "socket.getaddrinfo",
        "socket.gethostbyname",
        "socket.sendto",
    }:
        raise RuntimeError("Network is forbidden in the packaged HA canary")


async def verify(root):
    from homeassistant import config_entries, loader, setup
    from homeassistant.config_entries import ConfigEntries, ConfigEntry, ConfigEntryState
    from homeassistant.const import __version__
    from homeassistant.core import HomeAssistant, callback
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er
    from homeassistant.helpers.event import async_track_state_change_event

    from custom_components.onvif_room_direction import sensor
    from custom_components.onvif_room_direction.const import (
        DEFAULT_SECTORS,
        DOMAIN,
        TESTED_HA_VERSION,
        TIMING_DEFAULTS,
    )

    assert Path(sensor.__file__).is_relative_to(root)
    assert __version__ == TESTED_HA_VERSION
    hass = HomeAssistant(str(root))
    loader.async_setup(hass)
    dr.async_setup(hass)
    await dr.async_load(hass, load_empty=True)
    await er.async_load(hass, load_empty=True)
    registry = er.async_get(hass)
    hass.config_entries = ConfigEntries(hass, {})

    # The dependency is the only simulated integration. Its client has exactly
    # the two read-only methods our adapter is permitted to invoke.
    onvif = ConfigEntry(
        data={},
        domain="onvif",
        title="Synthetic camera",
        unique_id="synthetic-camera",
        source="user",
        version=1,
        minor_version=1,
        options={},
        discovery_keys=MappingProxyType({}),
        subentries_data=[],
    )
    get_status = AsyncMock(
        side_effect=lambda _: SimpleNamespace(
            Error=None,
            UtcTime=datetime.now(UTC),
            Position=SimpleNamespace(PanTilt=SimpleNamespace(x=0.6)),
        )
    )
    onvif.runtime_data = SimpleNamespace(
        available=True,
        profiles=[SimpleNamespace(ptz=True, token="synthetic-profile")],
        device=SimpleNamespace(
            create_ptz_service=AsyncMock(return_value=SimpleNamespace(GetStatus=get_status))
        ),
    )
    hass.config_entries._entries[onvif.entry_id] = onvif
    camera = registry.async_get_or_create("camera", "onvif", "synthetic-camera", config_entry=onvif)
    source = "binary_sensor.synthetic_motion"
    hass.states.async_set(source, "off")

    try:
        with (
            patch.object(setup, "async_process_deps_reqs", AsyncMock()),
            patch.object(config_entries, "async_process_deps_reqs", AsyncMock()),
        ):
            form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            result = await hass.config_entries.flow.async_configure(
                form["flow_id"],
                {
                    "name": "Synthetic direction",
                    "camera_entity_id": camera.entity_id,
                    "sources": [source],
                    "sectors": DEFAULT_SECTORS,
                },
            )
            assert result["type"] == "create_entry", result
            await hass.async_block_till_done()
            entry = result["result"]
            assert entry.state is ConfigEntryState.LOADED
            entity = hass.data[DOMAIN][entry.entry_id]
            entity_id = entity.entity_id
            assert hass.states.get(entity_id).state == "unknown"
            get_status.assert_not_awaited()

            async def save_options(enabled):
                form = await hass.config_entries.options.async_init(entry.entry_id)
                result = await hass.config_entries.options.async_configure(
                    form["flow_id"],
                    {
                        **TIMING_DEFAULTS,
                        "poll_interval": 0.5,
                        "confirmation_interval": 0.5,
                        "sources": [source],
                        "sectors": DEFAULT_SECTORS,
                        "enabled": enabled,
                    },
                )
                assert result["type"] == "create_entry", result
                await hass.async_block_till_done()
                assert entry.state is ConfigEntryState.LOADED
                return hass.data[DOMAIN][entry.entry_id]

            entity = await save_options(True)
            assert entity.entity_id == entity_id
            renamed = registry.async_update_entity(camera.entity_id, new_entity_id="camera.renamed_synthetic")
            assert renamed.id == camera.id
            assert entity._resolve_device() is onvif.runtime_data
            confirmed = asyncio.Event()

            @callback
            def observe(event):
                if (state := event.data["new_state"]) is not None and state.state == "zone_b":
                    confirmed.set()

            cancel = async_track_state_change_event(hass, [entity_id], observe)
            try:
                hass.states.async_set(source, "on")
                await asyncio.wait_for(confirmed.wait(), timeout=3)
            finally:
                cancel()
            assert get_status.await_count >= 2
            assert get_status.call_args.args == ({"ProfileToken": "synthetic-profile"},)

            old = entity
            entity = await save_options(False)
            assert old._stopped and not old._tasks
            assert entity.entity_id == entity_id
            assert hass.states.get(entity_id).state == "unknown"
            assert hass.states.get(entity_id).attributes["reason"] == "disabled"
            assert entity._task is None
            assert await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done()
            assert entity._stopped and not entity._tasks
            assert entry.entry_id not in hass.data[DOMAIN]
            assert hass.states.get(entity_id).state == "unavailable"
    finally:
        await hass.async_stop(force=True)

    print(
        json.dumps(
            {
                "status": "passed",
                "source": "extracted release ZIP",
                "homeassistant": __version__,
                "checks": [
                    "real config flow",
                    "idle without reads",
                    "real options reload",
                    "camera registry rename",
                    "synthetic GetStatus confirmation",
                    "disable cancels polling",
                    "stable entity ID",
                    "unload",
                ],
                "network": "connect, bind, DNS and sendto blocked by audit hook",
            }
        )
    )


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    sys.addaudithook(no_network)
    with tempfile.TemporaryDirectory(prefix="onvif-packaged-ha-") as directory:
        root = Path(directory)
        component = root / "custom_components" / "onvif_room_direction"
        component.mkdir(parents=True)
        (component.parent / "__init__.py").touch()
        with ZipFile(sys.argv[1]) as archive:
            for name in archive.namelist():
                assert not Path(name).is_absolute() and ".." not in Path(name).parts
            archive.extractall(component)
        sys.path.insert(0, str(root))
        asyncio.run(verify(root))
