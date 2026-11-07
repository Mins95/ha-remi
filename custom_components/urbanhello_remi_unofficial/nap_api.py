"""Cloud storage for REMI nap profiles, with device ownership checks."""
from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.exceptions import ServiceValidationError

from .const import FACE_DEFINE_TO_OBJECT_ID
from .media_api import (
    invalid_response, owns_record, remi_pointer, selected_remi_id,
    validate_music_path, validate_object_id, validation_error,
)

MAX_NAP_PROFILES = 5
_MAX_NAP_READ = 100
_NAP_FIELDS = frozenset({
    "name", "face", "brightness", "duration", "sleepAid", "musicPathStart",
    "musicPathEnd", "volumeStart", "volumeEnd", "lengthStart", "lengthEnd",
})


def strict_integer(value: Any, minimum: int, maximum: int) -> int:
    """Do not truncate fractions or accept booleans as timer values."""
    if type(value) is not int or not minimum <= value <= maximum:
        raise validation_error("invalid_nap_value")
    return value


def validate_nap_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """Validate the app's Nap fields; all music lengths are minutes."""
    if not isinstance(fields, dict) or not fields or not fields.keys() <= _NAP_FIELDS:
        raise validation_error("invalid_nap_value")
    result = dict(fields)
    for key, value in fields.items():
        if key == "name":
            if not isinstance(value, str) or not value.strip() or len(value) > 100 or any(ord(c) < 32 for c in value):
                raise validation_error("invalid_nap_value")
        elif key == "duration":
            if not isinstance(value, list) or len(value) != 2:
                raise validation_error("invalid_nap_value")
            result[key] = [strict_integer(value[0], 0, 23), strict_integer(value[1], 0, 59)]
        elif key in {"brightness", "volumeStart", "volumeEnd"}:
            strict_integer(value, 0, 100)
        elif key in {"lengthStart", "lengthEnd"}:
            strict_integer(value, 0, 1440)
        elif key == "sleepAid":
            strict_integer(value, 0, 1)
        elif key.startswith("musicPath"):
            validate_music_path(value)
        elif key == "face":
            if (not isinstance(value, dict) or value.get("__type") != "Pointer"
                or value.get("className") != "Face"
                or value.get("objectId") not in FACE_DEFINE_TO_OBJECT_ID.values()
                or set(value) != {"__type", "className", "objectId"}):
                raise validation_error("invalid_nap_value")
            result[key] = dict(value)
    return result


class RemiNapApiMixin:
    """Create and edit profiles without inventing a remote timer command."""

    def _get_nap_lock(self) -> asyncio.Lock:
        if not hasattr(self, "_nap_lock"):
            self._nap_lock = asyncio.Lock()
        return self._nap_lock

    async def get_naps(self) -> list[dict[str, Any]]:
        """Read a bounded complete profile list belonging to the selected REMI."""
        remi_id = selected_remi_id(self)
        result = await self._request("POST", "/parse/classes/Nap", {
            "where": {"remi": remi_pointer(remi_id)},
            "order": "createdAt,objectId", "limit": _MAX_NAP_READ + 1, "_method": "GET",
        })
        records = result.get("results") if isinstance(result, dict) else None
        if not isinstance(records, list) or len(records) > _MAX_NAP_READ:
            raise invalid_response()
        seen: set[str] = set()
        for record in records:
            if not isinstance(record, dict) or not owns_record(record, "remi", remi_id):
                raise invalid_response()
            try:
                nap_id = validate_object_id(record.get("objectId"))
            except ServiceValidationError as err:
                raise invalid_response() from err
            if nap_id in seen:
                raise invalid_response()
            seen.add(nap_id)
        return records

    async def _assert_owned_nap(self, nap_id: str) -> None:
        remi_id = selected_remi_id(self)
        nap_id = validate_object_id(nap_id)
        result = await self._request("POST", "/parse/classes/Nap", {
            "where": {"remi": remi_pointer(remi_id), "objectId": nap_id},
            "limit": 2, "_method": "GET",
        })
        records = result.get("results") if isinstance(result, dict) else None
        if not isinstance(records, list):
            raise invalid_response()
        if not records:
            raise validation_error("nap_not_found")
        if (len(records) != 1 or not isinstance(records[0], dict)
            or records[0].get("objectId") != nap_id
            or not owns_record(records[0], "remi", remi_id)):
            raise invalid_response()

    async def create_nap(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Create a stored profile; serialize creation to respect the five-profile limit."""
        fields = validate_nap_fields(fields)
        if not {"name", "duration"} <= fields.keys():
            raise validation_error("invalid_nap_value")
        remi_id = selected_remi_id(self)
        async with self._get_nap_lock():
            if len(await self.get_naps()) >= MAX_NAP_PROFILES:
                raise validation_error("nap_profile_limit")
            return await self._request("POST", "/parse/classes/Nap", {
                **fields, "remi": remi_pointer(remi_id),
            })

    async def update_nap(self, nap_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Patch known fields only after proving ownership of this profile."""
        fields = validate_nap_fields(fields)
        nap_id = validate_object_id(nap_id)
        async with self._get_nap_lock():
            await self._assert_owned_nap(nap_id)
            return await self._request("PUT", f"/parse/classes/Nap/{nap_id}", fields)

    async def delete_nap(self, nap_id: str) -> dict[str, Any]:
        """Delete only a profile belonging to the selected device."""
        nap_id = validate_object_id(nap_id)
        async with self._get_nap_lock():
            await self._assert_owned_nap(nap_id)
            return await self._request("DELETE", f"/parse/classes/Nap/{nap_id}")
