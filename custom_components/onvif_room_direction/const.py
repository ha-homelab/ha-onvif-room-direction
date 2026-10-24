# SPDX-License-Identifier: MIT
"""Integration constants."""

DOMAIN = "onvif_room_direction"
VERSION = "0.1.3"
TESTED_HA_VERSION = "2026.10.3"
DEFAULT_SECTORS = '[{"area":"zone_a","min":-1,"max":-0.2},{"area":"zone_b","min":0.2,"max":1}]'
TIMING_DEFAULTS = {
    "poll_interval": 2.0,
    "confirmation_interval": 2.0,
    "failure_interval": 10.0,
    "timeout": 4.0,
    "max_age": 15.0,
    "future_skew": 5.0,
}
