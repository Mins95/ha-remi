"""Light platform for the UrbanHello Remi integration."""
from __future__ import annotations

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
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import ExtraStoredData, RestoreEntity

from .brightness import (
    BrightnessRestoreData,
    get_brightness_memory,
    valid_brightness_percent,
)
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
    remi_id = entry.data[CONF_REMI_ID]
    # Night Light was removed, brightness moved to the number platform.
    legacy_unique_ids = {f"{remi_id}_night_light", f"{remi_id}_brightness"}
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (
            entity.platform == DOMAIN
            and entity.domain == "light"
            and entity.unique_id in legacy_unique_ids
        ):
            registry.async_remove(entity.entity_id)
    # Observe the shared cloud snapshot even if the optional light is disabled.
    # Number changes are picked up by their normal coordinator refresh.
    memory = get_brightness_memory(coordinator)
    entry.async_on_unload(coordinator.async_add_listener(memory.observe))
    async_add_entities(
        [RemiBackgroundLightEntity(coordinator), RemiBrightnessLightEntity(coordinator)]
    )


class RemiBrightnessLightEntity(RemiEntity, LightEntity, RestoreEntity):
    """Optional standard HA light for the physical lamp, independent of its face."""

    _attr_translation_key = "physical_brightness"
    _attr_icon = "mdi:lightbulb-night-outline"
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._remi_id}_physical_brightness"
        self._memory = get_brightness_memory(coordinator)

    async def async_added_to_hass(self) -> None:
        """Restore brightness memory without restoring a stale on/off state."""
        await super().async_added_to_hass()
        if (data := await self.async_get_last_extra_data()) is not None:
            self._memory.restore(data.as_dict())
        self._memory.observe()

    @property
    def extra_restore_state_data(self) -> ExtraStoredData:
        """Keep the nonzero level even when the current state is off/unavailable."""
        return BrightnessRestoreData(self._remi_id, self._memory.last_nonzero)

    @property
    def available(self) -> bool:
        """Require a valid, available REMI snapshot for this physical control."""
        return (
            self.device_available
            and self.coordinator.remi.get("objectId") == self._remi_id
            and self._percent is not None
        )

    @property
    def _percent(self) -> int | float | None:
        return valid_brightness_percent(self.coordinator.remi.get("luminosity"))

    @property
    def brightness(self) -> int | None:
        """Convert the native percentage to Home Assistant's 0–255 scale."""
        value = self._percent
        if value is None:
            return None
        return max(1, round(value * 255 / 100)) if value > 0 else 0

    @property
    def is_on(self) -> bool | None:
        """Read the cloud state; a successful write is not a device confirmation."""
        value = self._percent
        return value > 0 if value is not None else None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._memory.observe()
        super()._handle_coordinator_update()

    async def _async_set_percent(self, value: int) -> None:
        if not self.available:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="device_unavailable"
            )
        self._memory.observe()
        await self.coordinator.client.update_remi({"luminosity": value})
        await self.coordinator.async_request_refresh()
        if not self.coordinator.last_update_success:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="cannot_refresh_device"
            )
        self._memory.observe()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set an explicit level, or restore the last observed nonzero level."""
        self._memory.observe()
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            if (
                type(brightness) not in (int, float)
                or not 0 <= brightness <= 255
                or not math.isfinite(brightness)
            ):
                raise ServiceValidationError(
                    translation_domain=DOMAIN, translation_key="invalid_brightness"
                )
            value = max(1, round(brightness * 100 / 255)) if brightness > 0 else 0
        else:
            value = self._memory.turn_on_percent
        await self._async_set_percent(value)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Set only the lamp brightness to zero, retaining the previous level."""
        await self._async_set_percent(0)


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

    _attr_translation_key = "background_color"
    _attr_icon = "mdi:palette"
    _field = "background_color"

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._remi_id}_background_color"
