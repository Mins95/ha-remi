"""Base entity for the UrbanHello Remi integration."""
from __future__ import annotations

from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RemiDataUpdateCoordinator
from .alarm_identity import AlarmIdentityMap, alarm_snapshot


class RemiEntity(CoordinatorEntity[RemiDataUpdateCoordinator]):
    """Base class for all Remi entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        remi = coordinator.remi
        self._remi_id = remi.get("objectId", "")

    @property
    def device_available(self) -> bool:
        """Distinguish a reachable cloud from an explicitly offline REMI."""
        return (
            super().available
            and self.coordinator.remi.get("online") is not False
            and self.coordinator.remi.get("alive") is not False
        )

    @callback
    def _set_alarm_name(self, translation_key: str, name: str, clock_time: str | None = None) -> None:
        """Refresh translated alarm names without touching registry overrides."""
        placeholders = {"name": name}
        if clock_time is not None:
            placeholders["time"] = clock_time
        if self.translation_key == translation_key and self.translation_placeholders == placeholders:
            return
        self._attr_translation_key = translation_key
        self._attr_translation_placeholders = placeholders
        # HA caches the translated name separately from its key/placeholders.
        # Its next state write updates original_name while retaining user names.
        self.__dict__.pop("_name_translation_key", None)
        self.__dict__.pop("name", None)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this Remi."""
        remi = self.coordinator.remi
        return DeviceInfo(
            identifiers={(DOMAIN, self._remi_id)},
            name=remi.get("name", "Remi"),
            manufacturer="UrbanHello",
            model="Remi",
            sw_version=str(remi.get("current_firmware_version", "")),
            serial_number=remi.get("uniqueID"),
            configuration_url=f"http://{remi.get('ipv4Address', '')}",
        )


def valid_alarm_snapshot(coordinator: RemiDataUpdateCoordinator) -> dict[str, dict[str, Any]] | None:
    """Only reconcile entities after a complete, successful alarm snapshot."""
    if not coordinator.last_update_success or not coordinator.events_available:
        return None
    identities = getattr(coordinator, "alarm_identities", None)
    if isinstance(identities, AlarmIdentityMap):
        return identities.logical_snapshot(coordinator.events)
    return alarm_snapshot(coordinator.events, coordinator.client.remi_id)


def retained_alarm_ids(coordinator: RemiDataUpdateCoordinator, current: set[str]) -> set[str]:
    """Protect unresolvable legacy registry IDs when identity storage is missing."""
    identities = getattr(coordinator, "alarm_identities", None)
    return identities.retained_ids if isinstance(identities, AlarmIdentityMap) else current


class RemiAlarmEntity(RemiEntity):
    """Share immutable HA identity and current cloud event resolution."""

    def __init__(
        self, coordinator: RemiDataUpdateCoordinator, event: dict[str, Any],
        logical_id: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._logical_id = logical_id if logical_id is not None else event["objectId"]

    def _alarm_event(self) -> dict[str, Any]:
        identities = getattr(self.coordinator, "alarm_identities", None)
        cloud_id = (
            identities.cloud_id(self._logical_id)
            if isinstance(identities, AlarmIdentityMap) else self._logical_id
        )
        if not isinstance(self.coordinator.events, list):
            return {}
        return next((event for event in self.coordinator.events
                     if isinstance(event, dict) and event.get("objectId") == cloud_id), {})
