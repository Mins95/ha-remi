"""Editable alarm times in the REMI device's local time zone."""
from __future__ import annotations

from datetime import time
from typing import Any

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiAlarmEntity, retained_alarm_ids, valid_alarm_snapshot


def alarm_time(event: dict[str, Any]) -> time | None:
    """Decode the clock time without inventing a date or applying a UTC offset."""
    value = event.get("event_time")
    if not isinstance(value, list) or len(value) != 2:
        return None
    if not all(type(part) is int for part in value):
        return None
    try:
        return time(*value)
    except ValueError:
        return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Keep alarm time entities synchronized with the app's alarm list."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    known: set[str] = set()

    @callback
    def synchronize() -> None:
        current = valid_alarm_snapshot(coordinator)
        if current is None:
            return
        new = [RemiAlarmTime(coordinator, event, key) for key, event in current.items()
               if key not in known]
        if new:
            async_add_entities(new)
        registry = er.async_get(hass)
        retained = retained_alarm_ids(coordinator, set(current))
        remi_id = coordinator.client.remi_id
        if isinstance(remi_id, str) and remi_id:
            prefix = f"{remi_id}_alarm_"
            for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
                if entity.platform != DOMAIN or entity.domain != "time" or not entity.unique_id.startswith(prefix) or not entity.unique_id.endswith("_time"):
                    continue
                event_id = entity.unique_id[len(prefix):-len("_time")]
                if event_id and event_id not in retained:
                    registry.async_remove(entity.entity_id)
        known.clear()
        known.update(current)

    synchronize()
    entry.async_on_unload(coordinator.async_add_listener(synchronize))


class RemiAlarmTime(RemiAlarmEntity, TimeEntity):
    """Change the hour/minute of one existing alarm without changing its days."""

    _attr_icon = "mdi:alarm"
    _attr_translation_key = "alarm_time"

    def __init__(self, coordinator: RemiDataUpdateCoordinator, event: dict, logical_id: str | None = None) -> None:
        super().__init__(coordinator, event, logical_id)
        self._attr_unique_id = f"{self._remi_id}_alarm_{self._logical_id}_time"
        self._set_alarm_name("alarm_time", event.get("name") or self._logical_id)

    def _event(self) -> dict[str, Any]:
        return self._alarm_event()

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.events_available and bool(self._event())

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.coordinator.events_available and (event := self._event()):
            self._set_alarm_name("alarm_time", event.get("name") or self._logical_id)
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> time | None:
        return alarm_time(self._event())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"event_id": self._event().get("objectId")}

    async def async_set_value(self, value: time) -> None:
        if not self.coordinator.events_available or not (event := self._event()):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="alarm_not_found",
            )
        if value.second or value.microsecond or value.tzinfo is not None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_alarm_clock_time",
            )
        await self.coordinator.client.update_event(
            event["objectId"], {"event_time": [value.hour, value.minute]}
        )
        await self.coordinator.async_request_refresh()
