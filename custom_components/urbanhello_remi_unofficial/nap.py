"""Home Assistant actions for stored REMI nap/timer profiles."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, callback
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, FACE_DEFINE_TO_NAME, FACE_DEFINE_TO_OBJECT_ID
from .media_api import invalid_response, validate_music_path, validate_object_id, validation_error
from .nap_api import strict_integer

NAP_SERVICES = ("list_naps", "create_nap", "update_nap", "delete_nap")
_FIELD_MAP = {
    "name": "name", "brightness": "brightness",
    "music_path_start": "musicPathStart", "music_path_end": "musicPathEnd",
    "volume_start": "volumeStart", "volume_end": "volumeEnd",
    "music_duration_start_minutes": "lengthStart", "music_duration_end_minutes": "lengthEnd",
}
_FACE_NAMES = {name: define for define, name in FACE_DEFINE_TO_NAME.items()}
_FACE_IDS = {FACE_DEFINE_TO_OBJECT_ID[define]: name for define, name in FACE_DEFINE_TO_NAME.items()}


def _integer(minimum: int, maximum: int):
    return lambda value: strict_integer(value, minimum, maximum)


_FIELDS = {
    vol.Optional("name"): cv.string,
    vol.Optional("duration_minutes"): _integer(1, 1439),
    vol.Optional("face"): vol.In(_FACE_NAMES),
    vol.Optional("brightness"): _integer(0, 100),
    vol.Optional("sleep_aid"): vol.Boolean(),
    vol.Optional("music_path_start"): validate_music_path,
    vol.Optional("music_path_end"): validate_music_path,
    vol.Optional("volume_start"): _integer(0, 100),
    vol.Optional("volume_end"): _integer(0, 100),
    vol.Optional("music_duration_start_minutes"): _integer(0, 1440),
    vol.Optional("music_duration_end_minutes"): _integer(0, 1440),
}
_TARGET = {vol.Optional("remi_id"): validate_object_id}
LIST_NAPS_SCHEMA = vol.Schema(_TARGET)
CREATE_NAP_SCHEMA = vol.Schema({
    **_TARGET, **{key: value for key, value in _FIELDS.items() if key.schema not in {"name", "duration_minutes"}},
    vol.Required("name"): cv.string,
    vol.Required("duration_minutes"): _integer(1, 1439),
})
UPDATE_NAP_SCHEMA = vol.Schema({**_TARGET, **_FIELDS, vol.Required("nap_id"): validate_object_id})
DELETE_NAP_SCHEMA = vol.Schema({**_TARGET, vol.Required("nap_id"): validate_object_id})


def _payload(data: dict[str, Any], *, create: bool) -> dict[str, Any]:
    values: dict[str, Any] = {}
    if create:
        values = {
            "face": "sleepy", "brightness": 0, "sleep_aid": False,
            "music_path_start": "", "music_path_end": "",
            "volume_start": 50, "volume_end": 50,
            "music_duration_start_minutes": 0, "music_duration_end_minutes": 0,
        }
    values.update(data)
    result = {_FIELD_MAP[key]: value for key, value in values.items() if key in _FIELD_MAP}
    if "duration_minutes" in values:
        result["duration"] = list(divmod(values["duration_minutes"], 60))
    if "sleep_aid" in values:
        result["sleepAid"] = int(values["sleep_aid"])
    if "face" in values:
        result["face"] = {
            "__type": "Pointer", "className": "Face",
            "objectId": FACE_DEFINE_TO_OBJECT_ID[_FACE_NAMES[values["face"]]],
        }
    if not result:
        raise validation_error("empty_nap_update")
    return result


def _profile(record: dict[str, Any]) -> dict[str, Any]:
    """Return only documented fields, never ACLs, owners, or account data."""
    result = {"nap_id": record["objectId"]}
    for field, cloud_field in _FIELD_MAP.items():
        value = record.get(cloud_field)
        if field in {"name", "music_path_start", "music_path_end"}:
            result[field] = value if isinstance(value, str) else None
        else:
            maximum = 1440 if field.startswith("music_duration") else 100
            result[field] = value if type(value) is int and 0 <= value <= maximum else None
    duration = record.get("duration")
    result["duration_minutes"] = (
        duration[0] * 60 + duration[1]
        if isinstance(duration, list) and len(duration) == 2
        and type(duration[0]) is int and 0 <= duration[0] <= 23
        and type(duration[1]) is int and 0 <= duration[1] <= 59 else None
    )
    face = record.get("face")
    result["face"] = _FACE_IDS.get(face.get("objectId")) if isinstance(face, dict) else None
    value = record.get("sleepAid")
    result["sleep_aid"] = bool(value) if type(value) is int and value in (0, 1) else None
    return result


@callback
def async_register_nap_services(hass: HomeAssistant) -> None:
    """Register once; resolve live config entries on every action."""
    if hass.services.has_service(DOMAIN, "list_naps"):
        return

    def resolve(call: ServiceCall):
        coordinators = [value for value in hass.data.get(DOMAIN, {}).values() if hasattr(value, "client")]
        if remi_id := call.data.get("remi_id"):
            coordinators = [value for value in coordinators if value.client.remi_id == remi_id]
        if len(coordinators) != 1:
            raise validation_error("nap_target_not_unique")
        return coordinators[0]

    async def list_naps(call: ServiceCall) -> dict[str, Any]:
        records = await resolve(call).client.get_naps()
        return {"profiles": [_profile(record) for record in records]}

    async def create_nap(call: ServiceCall) -> dict[str, Any]:
        response = await resolve(call).client.create_nap(_payload(dict(call.data), create=True))
        if not isinstance(response, dict) or not isinstance(response.get("objectId"), str):
            raise invalid_response()
        return {"nap_id": response["objectId"]}

    async def update_nap(call: ServiceCall) -> None:
        await resolve(call).client.update_nap(call.data["nap_id"], _payload(dict(call.data), create=False))

    async def delete_nap(call: ServiceCall) -> None:
        await resolve(call).client.delete_nap(call.data["nap_id"])

    hass.services.async_register(DOMAIN, "list_naps", list_naps, schema=LIST_NAPS_SCHEMA, supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "create_nap", create_nap, schema=CREATE_NAP_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, "update_nap", update_nap, schema=UPDATE_NAP_SCHEMA)
    hass.services.async_register(DOMAIN, "delete_nap", delete_nap, schema=DELETE_NAP_SCHEMA)


@callback
def async_unregister_nap_services(hass: HomeAssistant) -> None:
    """Call only after the final REMI config entry is unloaded."""
    for service in NAP_SERVICES:
        hass.services.async_remove(DOMAIN, service)
