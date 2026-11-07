"""Switch platform for the UrbanHello Remi integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DAYS_OF_WEEK, DOMAIN, FACE_OBJECT_ID_TO_DEFINE, FACE_DEFINE_TO_NAME
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity, valid_alarm_snapshot
from .time import alarm_time


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Remi alarm switch entities from a config entry."""
    coordinator: RemiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    known_event_ids: set[str] = set()

    @callback
    def _add_new_alarms() -> None:
        """Add switch entities for any events not yet tracked."""
        current = valid_alarm_snapshot(coordinator)
        if current is None:
            return
        new_entities = []
        for event_id, event in current.items():
            if event_id not in known_event_ids:
                known_event_ids.add(event_id)
                new_entities.append(RemiAlarmSwitchEntity(coordinator, event))
        if new_entities:
            async_add_entities(new_entities)

        _remove_stale_alarms(set(current))

    def _remove_stale_alarms(current_ids: set[str]) -> None:
        """Remove switch entities for events that no longer exist."""
        ent_registry = er.async_get(hass)
        remi_id = coordinator.client.remi_id
        if not isinstance(remi_id, str) or not remi_id:
            return
        prefix = f"{remi_id}_alarm_"
        for entity in er.async_entries_for_config_entry(ent_registry, entry.entry_id):
            if entity.platform != DOMAIN or entity.domain != "switch" or not entity.unique_id.startswith(prefix):
                continue
            event_id = entity.unique_id[len(prefix):]
            if event_id and event_id not in current_ids:
                ent_registry.async_remove(entity.entity_id)
        known_event_ids.intersection_update(current_ids)

    _add_new_alarms()
    entry.async_on_unload(coordinator.async_add_listener(lambda: _add_new_alarms()))


class RemiAlarmSwitchEntity(RemiEntity, SwitchEntity):
    """Switch entity representing a single Remi alarm (Event)."""

    _attr_icon = "mdi:alarm"

    def __init__(
        self,
        coordinator: RemiDataUpdateCoordinator,
        event: dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self._event_id: str = event["objectId"]
        self._attr_unique_id = f"{self._remi_id}_alarm_{self._event_id}"
        self._update_alarm_name(event)

    @callback
    def _update_alarm_name(self, event: dict[str, Any]) -> None:
        """Include the current clock time while retaining the cloud alarm name."""
        value = alarm_time(event)
        self._set_alarm_name(
            "alarm" if event.get("name") else "unnamed_alarm",
            event.get("name") or self._event_id,
            value.strftime("%H:%M") if value is not None else "--:--",
        )

    def _get_event(self) -> dict[str, Any]:
        """Return the current event data from the coordinator."""
        events = self.coordinator.events
        if not isinstance(events, list):
            return {}
        for event in events:
            if isinstance(event, dict) and event.get("objectId") == self._event_id:
                return event
        return {}

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.events_available and bool(self._get_event())

    @callback
    def _handle_coordinator_update(self) -> None:
        """Follow app renames; HA retains any user-supplied entity name."""
        if self.coordinator.events_available and (event := self._get_event()):
            self._update_alarm_name(event)
        super()._handle_coordinator_update()

    @property
    def is_on(self) -> bool:
        """Return true if the alarm is enabled."""
        return self._get_event().get("enabled", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return alarm details as state attributes."""
        event = self._get_event()
        attrs: dict[str, Any] = {}
        if isinstance(event.get("name"), str):
            attrs["alarm_name"] = event["name"]
        if isinstance(event.get("music_path"), str):
            attrs["music_path"] = event["music_path"]
        command = event.get("cmd")
        attrs["play_button_enabled"] = (
            command in (14, 15) if type(command) is int and command in (10, 11, 14, 15) else None
        )

        if (value := alarm_time(event)) is not None:
            attrs["time"] = value.strftime("%H:%M")

        recurrence = event.get("recurrence")
        if isinstance(recurrence, list):
            attrs["recurrence"] = [
                DAYS_OF_WEEK[i]
                for i, active in enumerate(recurrence)
                if active and i < len(DAYS_OF_WEEK)
            ]

        for field in ("brightness", "volume", "length_min"):
            value = event.get(field)
            if value is not None:
                attrs[field] = value

        face_ptr = event.get("face") or {}
        if isinstance(face_ptr, dict):
            face_object_id = face_ptr.get("objectId", "")
            define = FACE_OBJECT_ID_TO_DEFINE.get(face_object_id, "")
            face_name = FACE_DEFINE_TO_NAME.get(define)
            if face_name:
                attrs["face"] = face_name

        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the alarm."""
        if not self._get_event():
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="alarm_not_found")
        await self.coordinator.client.update_event(self._event_id, {"enabled": True})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the alarm."""
        if not self._get_event():
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="alarm_not_found")
        await self.coordinator.client.update_event(self._event_id, {"enabled": False})
        await self.coordinator.async_request_refresh()
