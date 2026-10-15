# SPDX-License-Identifier: MIT
"""Home Assistant room estimates from existing ONVIF pan and motion data.

Imports remain lazy so the core and adapter modules work without HA installed.
"""

from .const import DOMAIN


async def async_setup_entry(hass, entry):
    """Create one sensor per configured ONVIF camera."""
    from homeassistant.const import Platform

    from .core import config_from_mapping

    # Validate before registering any listeners or starting background tasks.
    config_from_mapping({**entry.data, **entry.options})
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    return True


async def _async_options_updated(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    """Unload sensors; entity cleanup cancels reads and expires state."""
    from homeassistant.const import Platform

    unloaded = await hass.config_entries.async_unload_platforms(entry, [Platform.SENSOR])
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded
