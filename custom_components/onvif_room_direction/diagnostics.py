# SPDX-License-Identifier: MIT
"""Allowlisted diagnostics: no identifiers, room labels, pan or credentials."""

from .const import DOMAIN, TESTED_HA_VERSION, VERSION
from .core import API_VERSION, config_from_mapping


async def async_get_config_entry_diagnostics(hass, entry):
    config = config_from_mapping({**entry.data, **entry.options})
    sensor = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    return {
        "integration_version": VERSION,
        "core_api_version": API_VERSION,
        "tested_ha_version": TESTED_HA_VERSION,
        "enabled": config.enabled,
        "source_count": len(config.sources),
        "sector_count": len(config.sectors),
        "timing_seconds": {
            key: getattr(config, key)
            for key in (
                "poll_interval",
                "confirmation_interval",
                "failure_interval",
                "timeout",
                "max_age",
                "future_skew",
            )
        },
        "runtime": sensor.diagnostic_summary() if sensor else {"reason": "not_loaded"},
    }
