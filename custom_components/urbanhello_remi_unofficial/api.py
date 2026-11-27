"""API client for the UrbanHello Remi integration."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError

from .const import (
    API_APP_BUILD_VERSION,
    API_APP_DISPLAY_VERSION,
    API_APP_ID,
    API_BASE_URL,
    API_CLIENT_VERSION,
    API_OS_VERSION,
    API_USER_AGENT,
    DOMAIN,
    FACE_OBJECT_ID_TO_DEFINE,
)
from .history_api import RemiHistoryApiMixin
from .media_api import RemiMediaApiMixin, selected_remi_id, validate_music_path, validation_error
from .nap_api import RemiNapApiMixin

_LOGGER = logging.getLogger(__name__)
_MAX_JSON_BYTES = 8 * 1024 * 1024


class RemiApiError(HomeAssistantError):
    """Raised when an API call fails."""


class RemiAuthError(RemiApiError):
    """Raised when authentication fails."""


class _TransientApiError(RemiApiError):
    """A transient response that may only be retried for read operations."""


async def _read_json_object(response: aiohttp.ClientResponse) -> dict[str, Any]:
    """Bound decompressed bytes, including chunked responses without a length."""
    media_type = response.content_type
    if media_type != "application/json" and not media_type.endswith("+json"):
        raise RemiApiError(translation_domain=DOMAIN, translation_key="api_invalid_response")
    body = bytearray()
    async for chunk in response.content.iter_chunked(64 * 1024):
        if len(body) + len(chunk) > _MAX_JSON_BYTES:
            raise RemiApiError(translation_domain=DOMAIN, translation_key="api_invalid_response")
        body.extend(chunk)
    try:
        data = json.loads(body)
    except (ValueError, RecursionError) as err:
        raise RemiApiError(translation_domain=DOMAIN, translation_key="api_invalid_response") from err
    if not isinstance(data, dict):
        raise RemiApiError(translation_domain=DOMAIN, translation_key="api_invalid_response")
    return data


class RemiApiClient(RemiHistoryApiMixin, RemiMediaApiMixin, RemiNapApiMixin):
    """Client for the UrbanHello Remi Parse Server API."""

    def __init__(self, username: str, password: str, session: aiohttp.ClientSession, installation_id: str = "") -> None:
        self._username = username
        self._password = password
        self._session = session
        self._installation_id = installation_id
        self._session_token: str | None = None
        self._remi_id: str | None = None
        self._auth_lock = asyncio.Lock()
        self._alarm_test_lock = asyncio.Lock()
        self._timeout = aiohttp.ClientTimeout(total=15)

    @property
    def remi_id(self) -> str | None:
        return self._remi_id

    @property
    def session_token(self) -> str | None:
        return self._session_token

    def _base_headers(self, authenticated: bool = True) -> dict[str, str]:
        headers = {
            "X-Parse-Client-Version": API_CLIENT_VERSION,
            "X-Parse-Application-Id": API_APP_ID,
            "X-Parse-Installation-Id": self._installation_id,
            "X-Parse-OS-Version": API_OS_VERSION,
            "X-Parse-App-Build-Version": API_APP_BUILD_VERSION,
            "X-Parse-App-Display-Version": API_APP_DISPLAY_VERSION,
            "Accept": "*/*",
            "Accept-Language": "en-gb",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": API_USER_AGENT,
            "Connection": "keep-alive",
        }
        if authenticated and self._session_token:
            headers["X-Parse-Session-Token"] = self._session_token
        return headers

    def set_remi_id(self, remi_id: str) -> None:
        """Set the active Remi device ID."""
        self._remi_id = remi_id

    async def login(self) -> tuple[str, str, list[str]]:
        """Authenticate and return (session_token, current_remi_id, all_remi_ids)."""
        url = f"{API_BASE_URL}/parse/login"
        payload = {
            "_method": "GET",
            "username": self._username,
            "password": self._password,
        }
        async with self._session.post(
            url, json=payload, headers=self._base_headers(authenticated=False),
            timeout=self._timeout, allow_redirects=False,
        ) as resp:
            if resp.status == 401:
                raise RemiAuthError(
                    translation_domain=DOMAIN,
                    translation_key="api_invalid_auth",
                )
            if resp.status != 200:
                raise RemiApiError(
                    translation_domain=DOMAIN,
                    translation_key="api_login_failed",
                    translation_placeholders={"status": str(resp.status)},
                )
            data = await _read_json_object(resp)

        session_token = data.get("sessionToken")
        current_remi = data.get("currentRemi", {})
        current_remi_id = current_remi.get("objectId") if isinstance(current_remi, dict) else None
        all_remi_ids = data.get("remis", [])
        if (
            not isinstance(session_token, str) or not session_token.isascii()
            or not session_token.isprintable() or not session_token.strip()
            or not isinstance(all_remi_ids, list)
        ):
            raise RemiApiError(
                translation_domain=DOMAIN,
                translation_key="api_invalid_login_response",
            )
        self._validate_object_id(current_remi_id)
        for remi_id in all_remi_ids:
            self._validate_object_id(remi_id)

        if not all_remi_ids:
            all_remi_ids = [current_remi_id]

        self._session_token = session_token
        if self._remi_id is None:
            self._remi_id = current_remi_id
        return session_token, current_remi_id, all_remi_ids

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        retry_auth: bool = True,
    ) -> Any:
        """Retry transient read failures, without replaying device commands."""
        is_read = method.upper() == "GET" or (
            method.upper() == "POST" and (payload or {}).get("_method") == "GET"
        )
        for attempt in range(3 if is_read else 1):
            try:
                return await self._request_once(method, path, payload, retry_auth)
            except (_TransientApiError, aiohttp.ClientError, TimeoutError) as err:
                if not is_read or attempt == 2:
                    raise RemiApiError(
                        translation_domain=DOMAIN,
                        translation_key="api_request_failed",
                    ) from err
                await asyncio.sleep(0.5 * (attempt + 1))

    async def _request_once(self, method, path, payload, retry_auth):
        """Perform one request and at most one authentication recovery."""
        url = f"{API_BASE_URL}{path}"
        token_used = self._session_token
        async with self._session.request(
            method, url, json=payload, headers=self._base_headers(), timeout=self._timeout,
            allow_redirects=False,
        ) as resp:
            status = resp.status
            if status != 401:
                if status in (500, 502, 503, 504):
                    raise _TransientApiError(
                        translation_domain=DOMAIN,
                        translation_key="api_http_error",
                        translation_placeholders={"status": str(status)},
                    )
                if status not in (200, 201):
                    raise RemiApiError(
                        translation_domain=DOMAIN,
                        translation_key="api_http_error",
                        translation_placeholders={"status": str(status)},
                    )
                return await _read_json_object(resp)
        # Release the response before logging in; concurrent expired reads share
        # one refreshed session instead of racing two logins against each other.
        if not retry_auth:
            raise RemiAuthError(
                translation_domain=DOMAIN,
                translation_key="api_reauthentication_failed",
            )
        async with self._auth_lock:
            if self._session_token == token_used:
                await self.login()
        return await self._request_once(method, path, payload, False)

    async def get_remi(self) -> dict[str, Any]:
        """Fetch the Remi device state."""
        data = await self._request(
            "POST",
            "/parse/classes/Remi",
            {
                "limit": "1",
                "where": {"objectId": self._remi_id},
                "_method": "GET",
            },
        )
        results = data.get("results") if isinstance(data, dict) else None
        if not isinstance(results, list) or any(not isinstance(item, dict) for item in results):
            raise RemiApiError(translation_domain=DOMAIN, translation_key="api_invalid_response")
        if not results:
            raise RemiApiError(
                translation_domain=DOMAIN,
                translation_key="api_device_not_found",
            )
        if len(results) != 1 or results[0].get("objectId") != self._remi_id:
            raise RemiApiError(
                translation_domain=DOMAIN,
                translation_key="api_wrong_device",
            )
        return results[0]

    async def update_remi(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Update Remi device fields via PUT."""
        return await self._request(
            "PUT",
            f"/parse/classes/Remi/{self._remi_id}",
            fields,
        )

    async def get_faces(self) -> list[dict[str, Any]]:
        """Fetch all available clock faces."""
        data = await self._request(
            "POST",
            "/parse/classes/Face",
            {"order": "index", "_method": "GET"},
        )
        faces = data.get("results")
        if not isinstance(faces, list) or any(not isinstance(face, dict) for face in faces):
            raise RemiApiError(translation_domain=DOMAIN, translation_key="api_invalid_response")
        return faces

    async def get_config(self) -> dict[str, Any]:
        """Fetch server config (used for firmware update version)."""
        config = await self._request("GET", "/parse/config")
        if not isinstance(config.get("params", {}), dict):
            raise RemiApiError(translation_domain=DOMAIN, translation_key="api_invalid_response")
        return config

    async def get_events(self) -> list[dict[str, Any]]:
        """Return a complete, validated alarm snapshot before registry cleanup.

        Keyset pagination avoids skipping an existing alarm if an earlier page
        changes during the read. A malformed or oversized result is an error,
        never an empty snapshot that could remove the user's entities.
        """
        events: list[dict[str, Any]] = []
        seen: set[str] = set()
        cursor: str | None = None
        for _ in range(10):
            where: dict[str, Any] = {"remi": {
                "__type": "Pointer", "className": "Remi", "objectId": self._remi_id,
            }}
            if cursor is not None:
                where["objectId"] = {"$gt": cursor}
            data = await self._request("POST", "/parse/classes/Event", {
                "where": where, "order": "objectId", "limit": 100, "_method": "GET",
            })
            page = data.get("results") if isinstance(data, dict) else None
            if not isinstance(page, list) or len(page) > 100:
                raise RemiApiError(translation_domain=DOMAIN, translation_key="api_invalid_response")
            for event in page:
                event_id = event.get("objectId") if isinstance(event, dict) else None
                if not isinstance(event_id, str) or not event_id or event_id in seen:
                    raise RemiApiError(translation_domain=DOMAIN, translation_key="api_invalid_response")
                if cursor is not None and event_id <= cursor:
                    raise RemiApiError(translation_domain=DOMAIN, translation_key="api_invalid_response")
                owner = event.get("remi")
                if owner is not None and not (
                    isinstance(owner, dict) and owner.get("className") == "Remi"
                    and owner.get("objectId") == self._remi_id
                ):
                    raise RemiApiError(translation_domain=DOMAIN, translation_key="api_wrong_device")
                seen.add(event_id)
                events.append(event)
            if len(page) < 100:
                return events
            cursor = max(event["objectId"] for event in page)
        raise RemiApiError(translation_domain=DOMAIN, translation_key="api_invalid_response")

    async def async_test_alarm(self, event_id: str) -> None:
        """Apply the event's current output settings in one device update."""
        selected_remi_id(self)
        self._validate_object_id(event_id)
        if self._alarm_test_lock.locked():
            raise validation_error("alarm_test_running")
        async with self._alarm_test_lock:
            events = await self.get_events()
            event = next((item for item in events if item["objectId"] == event_id), None)
            if event is None:
                raise validation_error("alarm_not_found")

            fields: dict[str, Any] = {}
            face = event.get("face")
            if face is not None:
                if (
                    not isinstance(face, dict)
                    or face.get("className", "Face") != "Face"
                    or not isinstance(face.get("objectId"), str)
                    or face["objectId"] not in FACE_OBJECT_ID_TO_DEFINE
                ):
                    raise validation_error("alarm_test_invalid_settings")
                fields["face"] = {
                    "__type": "Pointer", "className": "Face", "objectId": face["objectId"],
                }
            for setting, device_field in (("volume", "volume"), ("brightness", "luminosity")):
                value = event.get(setting)
                if value is not None:
                    if type(value) is not int or not 0 <= value <= 100:
                        raise validation_error("alarm_test_invalid_settings")
                    fields[device_field] = value
            path = event.get("music_path")
            if path is not None:
                path = validate_music_path(path)
            if not fields and not path:
                raise validation_error("alarm_test_empty")

            remi = await self.get_remi()
            if remi.get("online") is not True or remi.get("alive") is False:
                raise validation_error("alarm_test_offline")
            if path:
                await self._async_send_music_path(path, device_fields=fields)
            else:
                await self.update_remi(fields)

    async def create_event(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new alarm event."""
        payload = {
            **event_data,
            "remi": {
                "__type": "Pointer",
                "className": "Remi",
                "objectId": self._remi_id,
            },
        }
        return await self._request("POST", "/parse/classes/Event", payload)

    async def update_event(self, event_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Update an existing alarm event."""
        self._validate_object_id(event_id)
        return await self._request("PUT", f"/parse/classes/Event/{event_id}", fields)

    async def delete_event(self, event_id: str) -> None:
        """Delete an alarm event."""
        self._validate_object_id(event_id)
        await self._request("DELETE", f"/parse/classes/Event/{event_id}")

    @staticmethod
    def _validate_object_id(object_id: str) -> None:
        """Keep object identifiers inside their intended API path segment."""
        if not isinstance(object_id, str) or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", object_id) is None:
            raise RemiApiError(translation_domain=DOMAIN, translation_key="api_invalid_response")
