"""Remember only brightness values observed in a successful device snapshot."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import TYPE_CHECKING, Any

from homeassistant.core import callback
from homeassistant.helpers.restore_state import ExtraStoredData

if TYPE_CHECKING:
    from .coordinator import RemiDataUpdateCoordinator

DEFAULT_BRIGHTNESS_PERCENT = 50


def valid_brightness_percent(value: Any) -> int | float | None:
    """Validate a cloud percentage without treating booleans as numbers."""
    if type(value) in (int, float) and 0 <= value <= 100 and math.isfinite(value):
        return value
    return None


@dataclass(frozen=True)
class BrightnessRestoreData(ExtraStoredData):
    """Store a confirmed nonzero level separately from the current light state."""

    remi_id: str
    last_nonzero: int | float | None

    def as_dict(self) -> dict[str, Any]:
        """Return a versioned, device-specific restore payload."""
        return {
            "version": 1,
            "remi_id": self.remi_id,
            "last_nonzero_luminosity": self.last_nonzero,
        }


class RemiBrightnessMemory:
    """Share confirmed brightness between controls using the same coordinator."""

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        self.coordinator = coordinator
        self.remi_id = coordinator.remi.get("objectId", "")
        self.last_nonzero: int | float | None = None

    @callback
    def observe(self) -> None:
        """Remember cloud reads, including changes made by the number entity."""
        remi = self.coordinator.remi
        if (
            not self.coordinator.last_update_success
            or not self.remi_id
            or remi.get("objectId") != self.remi_id
            or remi.get("online") is False
            or remi.get("alive") is False
        ):
            return
        value = valid_brightness_percent(remi.get("luminosity"))
        if value is not None and value > 0:
            self.last_nonzero = value

    @callback
    def restore(self, data: Any) -> None:
        """Use a saved level only when a current nonzero read has not superseded it."""
        if (
            self.last_nonzero is not None
            or not isinstance(data, dict)
            or type(data.get("version")) is not int
            or data.get("version") != 1
            or not self.remi_id
            or data.get("remi_id") != self.remi_id
        ):
            return
        value = valid_brightness_percent(data.get("last_nonzero_luminosity"))
        if value is not None and value > 0:
            self.last_nonzero = value

    @property
    def turn_on_percent(self) -> int:
        """Use the last known level, or a documented moderate first-use default."""
        value = self.last_nonzero
        return max(1, round(value)) if value is not None else DEFAULT_BRIGHTNESS_PERCENT


def get_brightness_memory(coordinator: RemiDataUpdateCoordinator) -> RemiBrightnessMemory:
    """Return one memory per coordinator, never a process-global device value."""
    memory = getattr(coordinator, "_remi_brightness_memory", None)
    if not isinstance(memory, RemiBrightnessMemory):
        memory = RemiBrightnessMemory(coordinator)
        coordinator._remi_brightness_memory = memory
    memory.observe()
    return memory
