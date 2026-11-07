"""Sensor platform for the UrbanHello Remi integration."""
from __future__ import annotations

from dataclasses import dataclass
import math
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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, FACE_OBJECT_ID_TO_DEFINE, FACE_DEFINE_TO_NAME
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity
from .history_sensor import HISTORY_SENSOR_DESCRIPTIONS, RemiHistorySensor
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
    if (history := getattr(coordinator, "history_coordinator", None)) is not None:
        async_add_entities(
            RemiHistorySensor(history, description)
            for description in HISTORY_SENSOR_DESCRIPTIONS
        )


class RemiSensorEntity(RemiEntity, SensorEntity):
    """Representation of a Remi sensor."""

    entity_description: RemiSensorEntityDescription

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
        return {
            "raw_value": remi.get("temp") if _temperature_value(remi) is not None else None,
            "conversion": "(raw - 50) / 5",
        }
