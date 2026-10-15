# SPDX-License-Identifier: MIT
"""Event-gated direction sensor, with an optional private installation guard."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from time import monotonic

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.util import dt as dt_util

from .adapter import ObservationError, OnvifPanReader, PanReading
from .const import DOMAIN
from .core import DirectionConfig, RoomConfirmation, classify_pan, config_from_mapping


async def async_setup_entry(hass, entry, async_add_entities):
    config = config_from_mapping({**entry.data, **entry.options})
    sensor = DirectionSensor(config, unique_id=entry.entry_id, name=entry.title)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = sensor
    async_add_entities([sensor])


class DirectionSensor(SensorEntity):
    """Estimate an area, never occupancy or the identity of a person.

    ``eligibility`` is an optional synchronous guard for installation-specific
    calibration bindings. It is rechecked before and after every network read.
    Adapters should call ``reconcile()`` immediately when their binding changes.
    """

    _attr_icon = "mdi:compass-outline"
    _attr_should_poll = False
    _attr_native_value = None
    _attr_available = True

    def __init__(
        self,
        config: DirectionConfig,
        *,
        unique_id: str,
        name: str = "Motion direction",
        eligibility: Callable[[], bool] | None = None,
    ) -> None:
        self.config = config
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._eligibility = eligibility
        self._task: asyncio.Task | None = None
        self._tasks: set[asyncio.Task] = set()
        # Cancellation is cooperative: a transport may finish an old request
        # after a new detection episode starts. Keep those reads serialized.
        self._read_lock = asyncio.Lock()
        self._stopped = False
        self._published = None
        self._cancel_expiry: Callable[[], None] | None = None
        self._attr_extra_state_attributes = {"method": "Camera direction estimate", "reason": "idle"}
        self._successes = 0
        self._failures = 0

    async def async_added_to_hass(self):
        self.async_on_remove(async_track_state_change_event(self.hass, self.config.sources, self.reconcile))
        self.async_on_remove(self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self._stop))
        self.async_on_remove(self._stop)
        self.reconcile()

    async def async_will_remove_from_hass(self):
        self._stop()
        if self._tasks:
            await asyncio.wait(tuple(self._tasks), timeout=self.config.timeout + 1)

    def _active(self) -> bool:
        if not self.config.enabled:
            return False
        try:
            if self._eligibility is not None and not self._eligibility():
                return False
        except Exception:
            return False
        return any(
            state is not None and state.state == "on" and not state.attributes.get("restored")
            for source in self.config.sources
            if (state := self.hass.states.get(source)) is not None
        )

    @callback
    def reconcile(self, event=None):
        """Start one polling task or immediately clear an inactive estimate."""
        if self._stopped:
            return
        if not self._active():
            self._cancel()
            self._publish(None, reason="idle" if self.config.enabled else "disabled")
        elif self._task is None:
            task = self.hass.async_create_background_task(
                self._observe(), "ONVIF room direction", eager_start=False
            )
            self._task = task
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    @callback
    def _clear_expiry(self):
        if self._cancel_expiry:
            self._cancel_expiry()
            self._cancel_expiry = None

    @callback
    def _cancel(self):
        self._clear_expiry()
        if self._task is not None:
            self._task.cancel()
            self._task = None

    @callback
    def _stop(self, event=None):
        self._stopped = True
        self._cancel()

    def _publish(self, room, pan=None, available=True, reason="observing"):
        self._attr_native_value = room
        self._attr_available = available
        observation = (room, pan, available, reason)
        if observation != self._published:
            self._published = observation
            self._attr_extra_state_attributes = {
                "method": "Camera direction estimate",
                "pan": pan,
                "reason": reason,
                "observed_at": dt_util.utcnow().isoformat(),
            }
        # Report unchanged samples too, but retain attributes to avoid Recorder churn.
        self.async_write_ha_state()

    def _resolve_device(self):
        registry = er.async_get(self.hass)
        if self.config.camera_registry_id:
            source = registry.async_get(self.config.camera_registry_id)
        else:
            source = registry.async_get(self.config.camera_entity_id)
        if (
            source is None
            or source.platform != "onvif"
            or source.config_entry_id != self.config.onvif_entry_id
        ):
            raise ObservationError("binding_changed")
        entry = self.hass.config_entries.async_get_entry(self.config.onvif_entry_id)
        if entry is None or entry.domain != "onvif":
            raise ObservationError("binding_changed")
        device = getattr(entry, "runtime_data", None)
        if device is None or not getattr(device, "available", False):
            raise ObservationError("camera_unavailable")
        return device

    def _arm_expiry(self, reading: PanReading, confirmation: RoomConfirmation, task):
        self._clear_expiry()
        remaining = max(0, self.config.max_age - (dt_util.utcnow() - reading.timestamp).total_seconds())

        @callback
        def expire(_now):
            if self._task is task and not self._stopped:
                confirmation.observe(None, monotonic())
                self._publish(None, available=False, reason="stale_position")

        self._cancel_expiry = async_call_later(self.hass, remaining, expire)

    async def _observe(self):
        task = asyncio.current_task()
        reader = OnvifPanReader(
            self._resolve_device, max_age=self.config.max_age, future_skew=self.config.future_skew
        )
        confirmation = RoomConfirmation(self.config.confirmation_interval)
        generation = None
        try:
            while self._task is task and not self._stopped and self._active():
                delay = self.config.poll_interval
                try:
                    async with self._read_lock:
                        async with asyncio.timeout(self.config.timeout) as deadline:
                            reading = await reader.read()
                        # A transport may catch CancelledError and return a late
                        # result instead of propagating the timeout cancellation.
                        if deadline.expired():
                            raise TimeoutError
                    if self._task is not task or self._stopped or not self._active():
                        break
                    if reading.generation != generation:
                        confirmation = RoomConfirmation(self.config.confirmation_interval)
                        generation = reading.generation
                    room = confirmation.observe(classify_pan(reading.pan, self.config.sectors), monotonic())
                    self._successes += 1
                    self._publish(room, reading.pan, reason="confirmed" if room else "unconfirmed")
                    self._arm_expiry(reading, confirmation, task)
                except Exception as err:
                    if self._task is not task or self._stopped:
                        break
                    confirmation = RoomConfirmation(self.config.confirmation_interval)
                    self._clear_expiry()
                    self._failures += 1
                    # Only our own fixed codes cross the adapter boundary.
                    reason = str(err) if type(err) is ObservationError else "read_failed"
                    self._publish(None, available=False, reason=reason)
                    delay = self.config.failure_interval
                await asyncio.sleep(delay)
        finally:
            # Cancelled reads from an earlier detection cannot touch a new episode.
            if self._task is task:
                self._task = None
                self._clear_expiry()
                if not self._stopped:
                    self._publish(None, reason="idle")

    def diagnostic_summary(self):
        """Return counts and fixed reasons only; no labels, coordinates or IDs."""
        return {
            "active": self._active() and not self._stopped,
            "poller_running": self._task is not None,
            "successful_reads": self._successes,
            "failed_reads": self._failures,
            "reason": self._attr_extra_state_attributes.get("reason"),
        }
