"""Number platform for the UrbanHello Remi integration."""
from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity


@dataclass(frozen=True, kw_only=True)
class RemiNumberEntityDescription(NumberEntityDescription):
    """Describes a Remi number entity."""

    field: str = ""
    value_fn: Any = None
    command_fn: Callable[[float], int] = int


def _luminosity_value(remi: dict[str, Any]) -> int | float | None:
    """Return the REMI brightness level, or None when the API value is unusable."""
    value = remi.get("luminosity")
    if type(value) in (int, float) and 0 <= value <= 100 and math.isfinite(value):
        return value
    return None


def _face_brightness_value(remi: dict[str, Any]) -> int | None:
    """Return the app's native night face level (1–10), if valid."""
    value = remi.get("light_min")
    if (
        type(value) in (int, float)
        and 1 <= value <= 10
        and math.isfinite(value)
        and value == int(value)
    ):
        return int(value)
    return None


def _face_brightness_command(value: float) -> int:
    """Reject invalid face levels before sending any command to REMI."""
    level = _face_brightness_value({"light_min": value})
    if level is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_face_brightness",
        )
    return level


NUMBER_DESCRIPTIONS: tuple[RemiNumberEntityDescription, ...] = (
    RemiNumberEntityDescription(
        key="volume",
        translation_key="volume",
        icon="mdi:volume-high",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        field="volume",
        value_fn=lambda remi: remi.get("volume", 50),
    ),
    RemiNumberEntityDescription(
        key="noise_threshold",
        translation_key="noise_threshold",
        icon="mdi:microphone",
        native_min_value=0,
        native_max_value=250,
        native_step=1,
        mode=NumberMode.SLIDER,
        field="noise_notification_threshold",
        value_fn=lambda remi: remi.get("noise_notification_threshold", 0),
    ),
    RemiNumberEntityDescription(
        key="brightness",
        translation_key="brightness",
        icon="mdi:brightness-6",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        field="luminosity",
        value_fn=_luminosity_value,
    ),
    RemiNumberEntityDescription(
        key="face_brightness",
        translation_key="face_brightness",
        icon="mdi:brightness-4",
        native_min_value=1,
        native_max_value=10,
        native_step=1,
        mode=NumberMode.SLIDER,
        field="light_min",
        value_fn=_face_brightness_value,
        command_fn=_face_brightness_command,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Remi number entities from a config entry."""
    coordinator: RemiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        RemiNumberEntity(coordinator, description)
        for description in NUMBER_DESCRIPTIONS
    )


class RemiNumberEntity(RemiEntity, NumberEntity):
    """Representation of a Remi number entity."""

    entity_description: RemiNumberEntityDescription

    def __init__(
        self,
        coordinator: RemiDataUpdateCoordinator,
        description: RemiNumberEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._remi_id}_{description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return self.entity_description.value_fn(self.coordinator.remi)

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        await self.coordinator.client.update_remi(
            {self.entity_description.field: self.entity_description.command_fn(value)}
        )
        await self.coordinator.async_request_refresh()
