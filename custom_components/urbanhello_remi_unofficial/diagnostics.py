"""Share a small allowlist of diagnostics without account or household data."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .telemetry import parse_connection_telemetry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry,
) -> dict[str, Any]:
    """Export connection health without raw API records or config credentials."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    result: dict[str, Any] = {"loaded": coordinator is not None}
    if coordinator is None:
        return result
    remi = coordinator.remi
    telemetry = parse_connection_telemetry(remi.get("dataBundle"))
    history = getattr(coordinator, "history_coordinator", None)
    result.update({
        "cloud_read_successful": bool(coordinator.last_update_success),
        "alarm_read_successful": bool(coordinator.events_available),
        "device": {key: value for key in ("online", "alive")
                   if type(value := remi.get(key)) is bool},
        "connection_telemetry": telemetry,
        "telemetry_present": bool(telemetry),
        "units": {key: "s" if key.endswith("_s") else "count" if key == "day_reconnection_count" else "unconfirmed"
                  for key in telemetry},
        "history_read_successful": bool(history.last_update_success) if history is not None and history.data is not None else None,
    })
    return result
