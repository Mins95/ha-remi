"""Light platform for the UrbanHello Remi integration."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import ExtraStoredData, RestoreEntity

from .const import CONF_REMI_ID, DOMAIN
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Remi light entities from a config entry."""
    coordinator: RemiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    registry = er.async_get(hass)
    legacy_unique_id = f"{entry.data[CONF_REMI_ID]}_night_light"
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (
            entity.platform == DOMAIN
            and entity.domain == "light"
            and entity.unique_id == legacy_unique_id
        ):
            registry.async_remove(entity.entity_id)
    async_add_entities(
        [
            RemiBrightnessLightEntity(coordinator),
            RemiBackgroundLightEntity(coordinator),
        ]
    )


def _valid_luminosity(value: Any) -> bool:
    """Accept only finite numeric API levels on the REMI scale."""
    return type(value) in (int, float) and 0 <= value <= 100 and math.isfinite(value)


@dataclass
class RemiBrightnessExtraData(ExtraStoredData):
    """Keep the last nonzero REMI level even when the light is off."""

    last_luminosity: int | float | None

    def as_dict(self) -> dict[str, Any]:
        return {"last_luminosity": self.last_luminosity}


class RemiBrightnessLightEntity(RemiEntity, LightEntity, RestoreEntity):
    """The dimmable upper light, controlled by the API luminosity field."""

    _attr_name = "Brightness"
    _attr_translation_key = "brightness"
    _attr_icon = "mdi:brightness-6"
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._remi_id}_brightness"
        self._last_luminosity: int | float | None = None
        self._remember_luminosity()

    @property
    def _luminosity(self) -> int | float | None:
        value = self.coordinator.remi.get("luminosity")
        return value if _valid_luminosity(value) else None

    def _remember_luminosity(self) -> None:
        if (value := self._luminosity) is not None and value > 0:
            self._last_luminosity = value

    @property
    def available(self) -> bool:
        return super().available and self._luminosity is not None

    @property
    def is_on(self) -> bool | None:
        value = self._luminosity
        return value > 0 if value is not None else None

    @property
    def brightness(self) -> int | None:
        value = self._luminosity
        if value is None:
            return None
        return max(1, round(value * 255 / 100)) if value > 0 else 0

    @property
    def extra_restore_state_data(self) -> RemiBrightnessExtraData:
        return RemiBrightnessExtraData(self._last_luminosity)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self._last_luminosity is None and (data := await self.async_get_last_extra_data()):
            value = data.as_dict().get("last_luminosity")
            if _valid_luminosity(value) and value > 0:
                self._last_luminosity = value

    @callback
    def _handle_coordinator_update(self) -> None:
        self._remember_luminosity()
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            if type(brightness) is not int or not 0 <= brightness <= 255:
                raise ValueError("Brightness must be an integer between 0 and 255")
            level = max(1, round(brightness * 100 / 255)) if brightness else 0
        else:
            self._remember_luminosity()
            level = max(1, round(self._last_luminosity)) if self._last_luminosity else 100
        await self._async_set_luminosity(level)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._remember_luminosity()
        await self._async_set_luminosity(0)

    async def _async_set_luminosity(self, level: int) -> None:
        await self.coordinator.client.update_remi({"luminosity": level})
        if level > 0:
            self._last_luminosity = level
        # Request refreshes may be debounced. Reflect a successful command now,
        # preserving all other data until the normal cloud refresh confirms it.
        self.coordinator.async_set_updated_data({
            **self.coordinator.data,
            "remi": {**self.coordinator.remi, "luminosity": level},
        })
        await self.coordinator.async_request_refresh()


class RemiRgbLightEntity(RemiEntity, LightEntity):
    """Base class for Remi RGB light entities."""

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    _field: str = ""

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)

    def _get_rgb(self) -> list[int]:
        return self.coordinator.remi.get(self._field, [255, 255, 255])

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the current RGB color."""
        rgb = self._get_rgb()
        if isinstance(rgb, list) and len(rgb) == 3:
            return (rgb[0], rgb[1], rgb[2])
        return None

    @property
    def is_on(self) -> bool:
        """Return true if the light is on (any non-zero channel)."""
        rgb = self._get_rgb()
        return any(v > 0 for v in rgb)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light, optionally setting RGB color."""
        rgb = kwargs.get(ATTR_RGB_COLOR)
        if rgb is None:
            current = self._get_rgb()
            if all(v == 0 for v in current):
                rgb = (255, 255, 255)
            else:
                rgb = tuple(current)
        await self.coordinator.client.update_remi(
            {self._field: list(rgb)}
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light by setting RGB to [0, 0, 0]."""
        await self.coordinator.client.update_remi(
            {self._field: [0, 0, 0]}
        )
        await self.coordinator.async_request_refresh()


class RemiBackgroundLightEntity(RemiRgbLightEntity):
    """Color associated with the Remi in the official app."""

    _attr_name = "App Background Color"
    _attr_icon = "mdi:palette"
    _field = "background_color"

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._remi_id}_background_color"
