# SPDX-License-Identifier: MIT
"""Configure local entities and calibration without opening a camera connection."""

import json

import probatio as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import DEFAULT_SECTORS, DOMAIN, TIMING_DEFAULTS
from .core import config_from_mapping, parse_sectors


def _schema(values, *, initial):
    fields = {}
    if initial:
        fields[vol.Required("name", default=values.get("name", "Motion direction"))] = str
        fields[vol.Required("camera_entity_id", default=values.get("camera_entity_id", vol.UNDEFINED))] = (
            selector.EntitySelector({"filter": [{"domain": "camera", "integration": "onvif"}]})
        )
    fields[vol.Required("sources", default=values.get("sources", []))] = selector.EntitySelector(
        {"filter": [{"domain": "binary_sensor"}], "multiple": True}
    )
    fields[vol.Required("sectors", default=values.get("sectors", DEFAULT_SECTORS))] = selector.TextSelector(
        {"multiline": True}
    )
    if not initial:
        fields[vol.Required("enabled", default=values.get("enabled", True))] = bool
        for key, default in TIMING_DEFAULTS.items():
            fields[vol.Required(key, default=values.get(key, default))] = vol.Coerce(float)
    return vol.Schema(fields)


def _normalize(data):
    sectors = parse_sectors(data["sectors"])
    return {
        **data,
        "sectors": json.dumps([{"area": s.area, "min": s.minimum, "max": s.maximum} for s in sectors]),
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """One configuration per existing ONVIF device, across all its profiles."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            registry = er.async_get(self.hass)
            source = registry.async_get(user_input["camera_entity_id"])
            entry = (
                self.hass.config_entries.async_get_entry(source.config_entry_id)
                if source and source.config_entry_id
                else None
            )
            if (
                not source
                or source.platform != "onvif"
                or not source.entity_id.startswith("camera.")
                or not entry
                or entry.domain != "onvif"
            ):
                errors["base"] = "invalid_camera"
            else:
                device = getattr(entry, "runtime_data", None)
                if device is None or not getattr(device, "available", False):
                    errors["base"] = "camera_unavailable"
                elif not any(getattr(profile, "ptz", None) for profile in getattr(device, "profiles", ())):
                    errors["base"] = "unsupported_device"
                else:
                    try:
                        data = _normalize(
                            {**user_input, "onvif_entry_id": entry.entry_id, "camera_registry_id": source.id}
                        )
                        config_from_mapping(data)
                        if not data["name"].strip():
                            raise ValueError("Name required")
                    except (ValueError, TypeError, KeyError):
                        errors["base"] = "invalid_config"
                    else:
                        await self.async_set_unique_id(entry.entry_id)
                        self._abort_if_unique_id_configured()
                        return self.async_create_entry(title=data.pop("name").strip(), data=data)
        return self.async_show_form(
            step_id="user", data_schema=_schema(user_input or {}, initial=True), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlow()


class OptionsFlow(config_entries.OptionsFlow):
    """Change detection sources, sectors and timing, then reload the entry."""

    async def async_step_init(self, user_input=None):
        errors = {}
        values = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            try:
                normalized = _normalize(user_input)
                config_from_mapping({**values, **normalized})
            except (ValueError, TypeError, KeyError):
                errors["base"] = "invalid_config"
            else:
                return self.async_create_entry(title="", data=normalized)
            values.update(user_input)
        return self.async_show_form(step_id="init", data_schema=_schema(values, initial=False), errors=errors)
