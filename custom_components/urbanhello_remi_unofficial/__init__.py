"""The UrbanHello Remi integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er
import homeassistant.helpers.config_validation as cv

from .api import RemiApiClient
from .alarm_identity import AlarmIdentityMap, AlarmIdentityStorageError, alarm_identity_store
from .const import (
    CONF_INSTALLATION_ID,
    CONF_REMI_ID,
    CONF_SESSION_TOKEN,
    DOMAIN,
    FACE_DEFINE_TO_NAME,
    FACE_DEFINE_TO_OBJECT_ID,
)
from .coordinator import RemiDataUpdateCoordinator
from .history import RemiHistoryCoordinator
from .history_api import MAX_HISTORY_REPORTS, validate_history_report_id
from .nap import async_register_nap_services, async_unregister_nap_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.LIGHT,
    Platform.MEDIA_PLAYER,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TIME,
]

SERVICE_CREATE_ALARM = "create_alarm"
SERVICE_UPDATE_ALARM = "update_alarm"
SERVICE_DELETE_ALARM = "delete_alarm"
ALARM_FACE_NAME_TO_DEFINE = {
    name: define for define, name in FACE_DEFINE_TO_NAME.items()
}
ALARM_FACE_VALUES = set(ALARM_FACE_NAME_TO_DEFINE) | set(FACE_DEFINE_TO_OBJECT_ID)


def _alarm_integer(value: Any) -> int:
    """Accept whole-number service input without silently truncating a setting."""
    if type(value) is int:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        return int(value)
    raise vol.Invalid("Expected a whole number")


def _alarm_music_path(value: str) -> str:
    """Validate an SD-card path; an empty path removes the scheduled music."""
    from .media_api import validate_music_path

    return validate_music_path(value, allow_empty=True)


def _alarm_play_command(current: int | None, enabled: bool, *, creating: bool) -> int:
    """Update only Play in the app's known command format, preserving Wi-Fi.

    APK 3.4.23 EventModel: bit 0 = wifiOn, bit 2 = playOn.
    saveEvent emits 10/11/14/15. Other formats cannot be safely reconstructed.
    New events use the app's Wi-Fi-on default; existing unknown flags are refused.
    """
    if creating:
        current = 15
    if type(current) is not int or current not in (10, 11, 14, 15):
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="unknown_alarm_play_settings"
        )
    return (current & ~4) | (4 if enabled else 0)


def _alarm_clock_time(value: str) -> list[int]:
    """Validate a minute-precision local clock time, without an invented date."""
    match = re.fullmatch(r"([01][0-9]|2[0-3]):([0-5][0-9])(?::00)?", value)
    if match is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_alarm_clock_time",
        )
    return [int(match[1]), int(match[2])]


def _alarm_recurrence(days: list[int]) -> list[int]:
    """Keep the documented service numbering (Sunday=0); cloud starts Monday."""
    return [int((index + 1) % 7 in days) for index in range(7)]


SERVICE_CREATE_ALARM_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Required("time"): vol.All(cv.string, _alarm_clock_time),
        vol.Optional("enabled", default=True): cv.boolean,
        vol.Optional("repeat", default=[]): vol.All(
            cv.ensure_list, [vol.In(range(7))]
        ),
        vol.Optional("face_define"): vol.All(cv.string, vol.In(ALARM_FACE_VALUES)),
        vol.Optional("volume"): vol.All(_alarm_integer, vol.Range(min=0, max=100)),
        vol.Optional("brightness"): vol.All(_alarm_integer, vol.Range(min=0, max=100)),
        vol.Optional("music_path"): vol.All(cv.string, _alarm_music_path),
        vol.Optional("music_duration_minutes"): vol.All(_alarm_integer, vol.Range(min=0, max=1440)),
        vol.Optional("play_button_enabled"): cv.boolean,
        vol.Optional("remi_id"): cv.string,
    }
)

SERVICE_UPDATE_ALARM_SCHEMA = vol.Schema(
    {
        vol.Required("event_id"): cv.string,
        vol.Optional("name"): cv.string,
        vol.Optional("time"): vol.All(cv.string, _alarm_clock_time),
        vol.Optional("enabled"): cv.boolean,
        vol.Optional("repeat"): vol.All(cv.ensure_list, [vol.In(range(7))]),
        vol.Optional("face_define"): vol.All(cv.string, vol.In(ALARM_FACE_VALUES)),
        vol.Optional("volume"): vol.All(_alarm_integer, vol.Range(min=0, max=100)),
        vol.Optional("brightness"): vol.All(_alarm_integer, vol.Range(min=0, max=100)),
        vol.Optional("music_path"): vol.All(cv.string, _alarm_music_path),
        vol.Optional("music_duration_minutes"): vol.All(_alarm_integer, vol.Range(min=0, max=1440)),
        vol.Optional("play_button_enabled"): cv.boolean,
        vol.Optional("remi_id"): cv.string,
    }
)

SERVICE_DELETE_ALARM_SCHEMA = vol.Schema(
    {
        vol.Required("event_id"): cv.string,
        vol.Optional("remi_id"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Remi from a config entry."""
    session = async_get_clientsession(hass)
    client = RemiApiClient(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        session,
        entry.data.get(CONF_INSTALLATION_ID, ""),
    )
    client._session_token = entry.data.get(CONF_SESSION_TOKEN)
    client._remi_id = entry.data[CONF_REMI_ID]

    coordinator = RemiDataUpdateCoordinator(hass, client)
    registry = er.async_get(hass)
    prefix = f"{entry.data[CONF_REMI_ID]}_alarm_"
    registry_alarm_ids: set[str] = set()
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.platform != DOMAIN or not entity.unique_id.startswith(prefix):
            continue
        if entity.domain == "switch":
            logical_id = entity.unique_id[len(prefix):]
        elif entity.domain == "time" and entity.unique_id.endswith("_time"):
            logical_id = entity.unique_id[len(prefix):-len("_time")]
        else:
            continue
        if logical_id:
            registry_alarm_ids.add(logical_id)
    coordinator.alarm_identities = AlarmIdentityMap(
        entry.data[CONF_REMI_ID], entry_id=entry.entry_id,
        store=alarm_identity_store(hass, entry.entry_id),
    )
    try:
        await coordinator.alarm_identities.async_load(registry_alarm_ids)
    except (AlarmIdentityStorageError, HomeAssistantError, OSError) as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="alarm_identity_storage_invalid"
        ) from err
    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    coordinator.history_coordinator = RemiHistoryCoordinator(hass, client, coordinator)

    # Remove only obsolete entities owned by this config entry. Automation
    # references are intentionally left for the user to migrate.
    legacy_unique_id = f"{entry.data[CONF_REMI_ID]}_luminosity"
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (
            entity.platform == DOMAIN
            and entity.domain in {"sensor", "number"}
            and entity.unique_id == legacy_unique_id
        ):
            registry.async_remove(entity.entity_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Optional history must neither delay startup nor block live device controls.
    entry.async_create_background_task(
        hass, coordinator.history_coordinator.async_refresh(), "REMI initial history refresh"
    )

    from .frontend import async_setup_frontend
    await async_setup_frontend(hass)

    _register_services(hass)
    async_register_nap_services(hass)

    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Discard the identity store only when its config entry is removed."""
    await alarm_identity_store(hass, entry.entry_id).async_remove()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if coordinator is not None and getattr(coordinator, "history_coordinator", None) is not None:
            await coordinator.history_coordinator.async_shutdown()
        if not hass.data.get(DOMAIN):
            for service in (SERVICE_CREATE_ALARM, SERVICE_UPDATE_ALARM, SERVICE_DELETE_ALARM, "get_history"):
                hass.services.async_remove(DOMAIN, service)
            async_unregister_nap_services(hass)
    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    """Register alarm CRUD services."""

    def resolve_coordinator(event_id=None, remi_id=None):
        """Resolve currently loaded entries instead of retaining an unloaded client."""
        coordinators = list(hass.data.get(DOMAIN, {}).values())
        if remi_id is not None:
            coordinators = [c for c in coordinators if c.client.remi_id == remi_id]
        if event_id is not None:
            coordinators = [c for c in coordinators
                            if c.last_update_success and c.events_available
                            and any(e.get("objectId") == event_id for e in c.events)]
        if len(coordinators) != 1:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="alarm_target_not_unique",
            )
        return coordinators[0]

    async def handle_create_alarm(call: ServiceCall) -> None:
        """Handle create_alarm service call."""
        coordinator = resolve_coordinator(remi_id=call.data.get("remi_id"))
        event_data: dict[str, Any] = {
            "name": call.data["name"],
            "event_time": call.data["time"],
            "enabled": call.data.get("enabled", True),
            "recurrence": _alarm_recurrence(call.data.get("repeat", [])),
        }
        face_define = call.data.get("face_define")
        face_define = ALARM_FACE_NAME_TO_DEFINE.get(face_define, face_define)
        if face_define and face_define in FACE_DEFINE_TO_OBJECT_ID:
            event_data["face"] = {
                "__type": "Pointer",
                "className": "Face",
                "objectId": FACE_DEFINE_TO_OBJECT_ID[face_define],
            }
        if "volume" in call.data:
            event_data["volume"] = call.data["volume"]
        for field in ("brightness", "music_path"):
            if field in call.data:
                event_data[field] = call.data[field]
        if "music_duration_minutes" in call.data:
            event_data["length_min"] = call.data["music_duration_minutes"]
        if "play_button_enabled" in call.data:
            event_data["cmd"] = _alarm_play_command(None, call.data["play_button_enabled"], creating=True)

        await coordinator.client.create_event(event_data)
        await coordinator.async_request_refresh()

    async def handle_update_alarm(call: ServiceCall) -> None:
        """Handle update_alarm service call."""
        event_id = call.data["event_id"]
        coordinator = resolve_coordinator(event_id, call.data.get("remi_id"))
        fields: dict[str, Any] = {}

        if "name" in call.data:
            fields["name"] = call.data["name"]
        if "time" in call.data:
            fields["event_time"] = call.data["time"]
        if "enabled" in call.data:
            fields["enabled"] = call.data["enabled"]
        if "repeat" in call.data:
            fields["recurrence"] = _alarm_recurrence(call.data["repeat"])
        if "volume" in call.data:
            fields["volume"] = call.data["volume"]
        for field in ("brightness", "music_path"):
            if field in call.data:
                fields[field] = call.data[field]
        if "music_duration_minutes" in call.data:
            fields["length_min"] = call.data["music_duration_minutes"]
        if "play_button_enabled" in call.data:
            # Re-read flags before a partial change; an app may have edited them
            # since the last regular poll. Never reconstruct unknown Wi-Fi flags.
            events = await coordinator.client.get_events()
            current = next((e for e in events if e.get("objectId") == event_id), None)
            if current is None:
                raise ServiceValidationError(
                    translation_domain=DOMAIN, translation_key="alarm_not_found"
                )
            fields["cmd"] = _alarm_play_command(current.get("cmd"), call.data["play_button_enabled"], creating=False)
        face_define = call.data.get("face_define")
        face_define = ALARM_FACE_NAME_TO_DEFINE.get(face_define, face_define)
        if face_define and face_define in FACE_DEFINE_TO_OBJECT_ID:
            fields["face"] = {
                "__type": "Pointer",
                "className": "Face",
                "objectId": FACE_DEFINE_TO_OBJECT_ID[face_define],
            }

        await coordinator.client.update_event(event_id, fields)
        await coordinator.async_request_refresh()

    async def handle_delete_alarm(call: ServiceCall) -> None:
        """Handle delete_alarm service call."""
        coordinator = resolve_coordinator(call.data["event_id"], call.data.get("remi_id"))
        await coordinator.client.delete_event(call.data["event_id"])
        await coordinator.async_request_refresh()

    async def handle_history(call: ServiceCall) -> dict[str, Any]:
        """Read history, with a device export only when explicitly requested."""
        coordinator = resolve_coordinator(remi_id=call.data.get("remi_id"))
        return await coordinator.history_coordinator.async_get_history(
            call.data["limit"],
            report_id=call.data.get("report_id"),
            include_series=call.data["include_series"],
            refresh=call.data["refresh"],
            sync=call.data["sync"],
        )

    if not hass.services.has_service(DOMAIN, "get_history"):
        hass.services.async_register(
            DOMAIN, "get_history", handle_history,
            schema=vol.Schema({
                vol.Optional("remi_id"): cv.string,
                vol.Optional("limit", default=2): vol.All(
                    _alarm_integer, vol.Range(min=1, max=MAX_HISTORY_REPORTS)
                ),
                vol.Optional("report_id"): validate_history_report_id,
                vol.Optional("include_series", default=True): cv.boolean,
                vol.Optional("refresh", default=False): cv.boolean,
                vol.Optional("sync", default=False): cv.boolean,
            }),
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CREATE_ALARM):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CREATE_ALARM,
            handle_create_alarm,
            schema=SERVICE_CREATE_ALARM_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_UPDATE_ALARM):
        hass.services.async_register(
            DOMAIN,
            SERVICE_UPDATE_ALARM,
            handle_update_alarm,
            schema=SERVICE_UPDATE_ALARM_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_DELETE_ALARM):
        hass.services.async_register(
            DOMAIN,
            SERVICE_DELETE_ALARM,
            handle_delete_alarm,
            schema=SERVICE_DELETE_ALARM_SCHEMA,
        )
