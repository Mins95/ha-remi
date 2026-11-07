"""Bounded music-library reads and the app's cloud music-path commands."""
from __future__ import annotations

import asyncio
import random
import re
from typing import Any

from homeassistant.exceptions import ServiceValidationError

from .const import DOMAIN

MAX_MUSIC_ITEMS = 200
MAX_MUSIC_PATH_LENGTH = 512
_OBJECT_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")


def validation_error(key: str) -> ServiceValidationError:
    """Keep validation errors translatable and free of account data."""
    return ServiceValidationError(translation_domain=DOMAIN, translation_key=key)


def validate_music_path(value: Any, *, allow_empty: bool = True) -> str:
    """Validate a device-relative path, never a URL or serialized command."""
    if not isinstance(value, str):
        raise validation_error("invalid_music_path")
    if value == "" and allow_empty:
        return value
    if (
        not value or len(value) > MAX_MUSIC_PATH_LENGTH
        or value != value.strip() or value.startswith("/")
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
        or ":" in value or "\\" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or value in {"play", "pause", "stop"} or value.startswith("random_")
    ):
        raise validation_error("invalid_music_path")
    return value


def selected_remi_id(client: Any) -> str:
    """Require an explicit selected device before a scoped request."""
    remi_id = client.remi_id
    if not isinstance(remi_id, str) or not _OBJECT_ID.fullmatch(remi_id):
        raise validation_error("missing_remi_target")
    return remi_id


def validate_object_id(value: Any) -> str:
    """Prevent identifiers from escaping a Parse object endpoint."""
    if not isinstance(value, str) or not _OBJECT_ID.fullmatch(value):
        raise validation_error("invalid_profile_id")
    return value


def remi_pointer(remi_id: str) -> dict[str, str]:
    """Return a Parse device pointer."""
    return {"__type": "Pointer", "className": "Remi", "objectId": remi_id}


def owns_record(record: dict[str, Any], key: str, remi_id: str) -> bool:
    """Accept pointers and expanded objects only for the selected REMI."""
    owner = record.get(key)
    return (
        isinstance(owner, dict) and owner.get("className") == "Remi"
        and owner.get("objectId") == remi_id
    )


def invalid_response() -> Exception:
    """Import lazily: the main API client inherits this mixin."""
    from .api import RemiApiError

    return RemiApiError(translation_domain=DOMAIN, translation_key="invalid_cloud_response")


class RemiMediaApiMixin:
    """Music commands share the API client's authenticated request policy."""

    async def get_music_library(self) -> list[dict[str, Any]]:
        """Read at most 200 owned tracks, rejecting partial or malformed lists."""
        remi_id = selected_remi_id(self)
        result = await self._request("POST", "/parse/classes/Music", {
            # Match the app's whereMatchesKeyInQuery exactly. Music's uppercase
            # owner key must not be confused with Nap/Event's lowercase pointer.
            "where": {"REMI": {"$select": {
                "query": {"className": "Remi", "where": {"objectId": remi_id}},
                "key": "objectId",
            }}},
            "order": "index,objectId", "limit": MAX_MUSIC_ITEMS + 1,
            "_method": "GET",
        })
        records = result.get("results") if isinstance(result, dict) else None
        if not isinstance(records, list) or len(records) > MAX_MUSIC_ITEMS:
            raise invalid_response()
        tracks: list[dict[str, Any]] = []
        seen: set[str] = set()
        for record in records:
            if not isinstance(record, dict) or not (
                record.get("REMI") == remi_id or owns_record(record, "REMI", remi_id)
            ):
                raise invalid_response()
            object_id = record.get("objectId")
            path, file = record.get("path", ""), record.get("file")
            if (not isinstance(object_id, str) or not _OBJECT_ID.fullmatch(object_id)
                or object_id in seen or not isinstance(path, str)
                or not isinstance(file, str) or not file or "/" in file):
                raise invalid_response()
            try:
                full_path = validate_music_path(f"{path}/{file}" if path else file, allow_empty=False)
            except ServiceValidationError as err:
                raise invalid_response() from err
            seen.add(object_id)
            name = record.get("name")
            tracks.append({
                "object_id": object_id,
                "name": name if isinstance(name, str) and name else file,
                "path": path, "file": file, "full_path": full_path,
                "index": record.get("index") if type(record.get("index")) is int else None,
            })
        return tracks

    async def _async_send_music_path(self, value: str) -> dict[str, Any]:
        """Serialize and send once; never infer playback from a cloud ACK."""
        selected_remi_id(self)
        if not hasattr(self, "_music_command_lock"):
            self._music_command_lock = asyncio.Lock()
            self._last_music_nonce = None
        async with self._music_command_lock:
            nonce = random.randrange(1000)
            if nonce == self._last_music_nonce:
                nonce = (nonce + 1) % 1000
            self._last_music_nonce = nonce
            return await self.update_remi({"musicPath": f"{value}:{nonce}"})

    async def async_media_command(self, command: str) -> dict[str, Any]:
        """Only send command strings whose cloud setter is verified in the app."""
        if command not in {"pause", "stop"}:
            raise validation_error("unsupported_media_command")
        return await self._async_send_music_path(command)

    async def async_play_music(self, path: str) -> dict[str, Any]:
        """Select a device-relative track, using the same command serialization."""
        return await self._async_send_music_path(validate_music_path(path, allow_empty=False))
