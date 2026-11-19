"""Sensor platform for the UrbanHello Remi integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util

from .const import DOMAIN, FACE_OBJECT_ID_TO_DEFINE, FACE_DEFINE_TO_NAME
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity
from .history_sensor import HISTORY_SENSOR_DESCRIPTIONS, RemiHistorySensor
from .schedule_snapshot import ScheduleSnapshot, next_occurrence, schedule_rows
from .telemetry import parse_connection_telemetry


@dataclass(frozen=True, kw_only=True)
class RemiSensorEntityDescription(SensorEntityDescription):
    """Describes a Remi sensor entity."""

    value_fn: Any = None


def _temperature_value(remi: dict[str, Any]) -> float | None:
    """Use the app's Celsius scale while preserving fractional measurements.

    REMI Android 3.4.23: StoredPropertyTemperature at 0x651174 subtracts
    50, then divides by 5. Unlike the app, keep the decimal part instead of truncating it.
    See docs/protocol-3.4.23.json.
    """
    raw = remi.get("temp")
    if type(raw) not in (int, float):
        return None
    try:
        temperature = (raw - 50) / 5
    except OverflowError:
        return None
    return temperature if math.isfinite(temperature) else None


def _face_value(remi: dict[str, Any]) -> str | None:
    """A malformed cloud pointer must not break the other sensors."""
    face = remi.get("face")
    if not isinstance(face, dict) or not isinstance(face.get("objectId"), str):
        return None
    return FACE_DEFINE_TO_NAME.get(FACE_OBJECT_ID_TO_DEFINE.get(face["objectId"]))


SENSOR_DESCRIPTIONS: tuple[RemiSensorEntityDescription, ...] = (
    RemiSensorEntityDescription(
        key="daily_reconnections", translation_key="daily_reconnections",
        icon="mdi:wifi-refresh", entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda remi: parse_connection_telemetry(remi.get("dataBundle")).get("day_reconnection_count"),
    ),
    RemiSensorEntityDescription(
        key="reported_clock_shift", translation_key="reported_clock_shift",
        icon="mdi:clock-alert-outline", entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_registry_enabled_default=False,
        value_fn=lambda remi: parse_connection_telemetry(remi.get("dataBundle")).get("gettime_shift_s"),
    ),
    RemiSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_temperature_value,
    ),
    RemiSensorEntityDescription(
        key="rssi",
        translation_key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_registry_enabled_default=False,
        value_fn=lambda remi: remi.get("rssi"),
    ),
    RemiSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        icon="mdi:chip",
        value_fn=lambda remi: remi.get("current_firmware_version"),
    ),
    RemiSensorEntityDescription(
        key="ip_address",
        translation_key="ip_address",
        icon="mdi:ip-network",
        entity_registry_enabled_default=False,
        value_fn=lambda remi: remi.get("ipv4Address"),
    ),
    RemiSensorEntityDescription(
        key="current_face",
        translation_key="current_face",
        device_class=SensorDeviceClass.ENUM,
        options=list(FACE_DEFINE_TO_NAME.values()),
        icon="mdi:emoticon-outline",
        value_fn=_face_value,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Remi sensors from a config entry."""
    coordinator: RemiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        RemiSensorEntity(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )
    if isinstance(getattr(coordinator, "schedule_snapshot", None), ScheduleSnapshot):
        async_add_entities([
            RemiScheduleSensor(coordinator, "next_wake", "FACE_DAY"),
            RemiScheduleSensor(coordinator, "next_bedtime", "FACE_NIGHT"),
        ])
    if (history := getattr(coordinator, "history_coordinator", None)) is not None:
        async_add_entities(
            RemiHistorySensor(history, description)
            for description in HISTORY_SENSOR_DESCRIPTIONS
        )


class RemiSensorEntity(RemiEntity, SensorEntity):
    """Representation of a Remi sensor."""

    entity_description: RemiSensorEntityDescription
    _unrecorded_attributes = frozenset({"received_at"})

    def __init__(
        self,
        coordinator: RemiDataUpdateCoordinator,
        description: RemiSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._remi_id}_{description.key}"

    @property
    def available(self) -> bool:
        """Live readings cannot be trusted when REMI explicitly reports offline."""
        if self.entity_description.key in {"temperature", "rssi", "current_face", "daily_reconnections", "reported_clock_shift"}:
            return self.device_available
        return super().available

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.remi)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose the temperature input for checking future app discrepancies."""
        if self.entity_description.key != "temperature":
            return None
        remi = self.coordinator.remi
        received = getattr(self.coordinator, "device_received_at", None)
        valid_reading = _temperature_value(remi) is not None
        return {
            "raw_value": remi.get("temp") if valid_reading else None,
            "conversion": "(raw - 50) / 5",
            "received_at": received.isoformat() if valid_reading and isinstance(received, datetime) else None,
        }


class RemiScheduleSensor(RemiEntity, SensorEntity):
    """Next recurring face change derived from the confirmed device programme."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _unrecorded_attributes = frozenset({"synced_at", "schedules"})

    def __init__(self, coordinator: RemiDataUpdateCoordinator, key: str, face_define: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.remi_id}_{key}"
        self._attr_translation_key = key
        self._face_define = face_define
        self._snapshot = coordinator.schedule_snapshot
        self._cancel_clock: Callable[[], None] | None = None
        self._alarm_name: str | None = None
        self._scheduled: datetime | None = None

    @property
    def available(self) -> bool:
        """Saved programmes remain readable through coordinator failures."""
        return self._snapshot.synced_at is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        snapshot = self._snapshot
        attrs = {
            "synced_at": snapshot.synced_at.isoformat() if snapshot.synced_at else None,
            "source": "confirmed_schedule",
            "cached": not (self.coordinator.last_update_success and self.coordinator.events_available),
            "alarm_name": self._alarm_name,
            "timezone": snapshot.remi.get("timezone"),
        }
        if self._face_define == "FACE_DAY":
            attrs["schedules"] = schedule_rows(snapshot.events)
        return attrs

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._update_prediction(dt_util.utcnow())
        self.async_on_remove(self._cancel_timer)

    @callback
    def _cancel_timer(self) -> None:
        if self._cancel_clock is not None:
            self._cancel_clock()
            self._cancel_clock = None
        self._scheduled = None

    @callback
    def _update_prediction(self, now: datetime) -> None:
        next_time, self._alarm_name, check_at = next_occurrence(self._snapshot, self._face_define, now)
        self._attr_native_value = next_time
        if check_at != self._scheduled:
            self._cancel_timer()
            if check_at is not None:
                self._scheduled = check_at
                self._cancel_clock = async_track_point_in_utc_time(self.hass, self._on_timer, check_at)

    @callback
    def _on_timer(self, scheduled: datetime) -> None:
        self._cancel_clock = None
        self._scheduled = None
        self._update_prediction(max(scheduled, dt_util.utcnow()))
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_prediction(dt_util.utcnow())
        super()._handle_coordinator_update()
