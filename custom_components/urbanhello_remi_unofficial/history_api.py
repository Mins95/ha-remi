"""Bounded, device-scoped reads of REMI's cloud sleep reports and log files."""
from __future__ import annotations

import asyncio
import re
from typing import Any
from urllib.parse import unquote, urlsplit

import aiohttp
from homeassistant.exceptions import HomeAssistantError

from .const import API_BASE_URL, DOMAIN

MAX_HISTORY_LOGS = 2
MAX_HISTORY_FILE_BYTES = 1024 * 1024
_OBJECT_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")


class RemiHistoryError(HomeAssistantError):
    """A history read failed without affecting device control availability."""


def history_error() -> RemiHistoryError:
    """Return an error that cannot expose file URLs, identifiers or credentials."""
    return RemiHistoryError(
        translation_domain=DOMAIN, translation_key="history_request_failed"
    )


def validate_history_limit(limit: int) -> None:
    """Bound each read to the two most recent reports."""
    if type(limit) is not int or not 1 <= limit <= MAX_HISTORY_LOGS:
        raise history_error()


def _owned_by(record: dict[str, Any], remi_id: str) -> bool:
    owner = record.get("remi")
    return owner == remi_id or (
        isinstance(owner, dict)
        and owner.get("__type") == "Pointer"
        and owner.get("className") == "Remi"
        and owner.get("objectId") == remi_id
    )


def history_file_url(file: Any) -> str:
    """Only allow HTTPS Parse files from the configured, fixed cloud origin.

    File URLs are cloud data, never arbitrary URLs supplied by a service caller.
    Redirects are also refused at the request layer. No Parse auth headers are
    sent when downloading a file.
    """
    if not isinstance(file, dict) or file.get("__type") != "File":
        raise history_error()
    url, name = file.get("url"), file.get("name")
    if not isinstance(url, str) or len(url) > 2048 or not isinstance(name, str):
        raise history_error()
    try:
        parsed = urlsplit(url)
        path = unquote(parsed.path)
        valid = (
            parsed.scheme == "https"
            and parsed.hostname == urlsplit(API_BASE_URL).hostname
            and parsed.port in (None, 443)
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
            and path.startswith("/parse/files/")
            and not any(part in (".", "..") for part in path.split("/"))
            and "\\" not in path
            and "%" not in path
            and not any(ord(char) < 32 for char in url)
            and bool(name)
            and len(name) <= 512
            and path.rsplit("/", 1)[-1] == name
        )
    except ValueError:
        valid = False
    if not valid:
        raise history_error()
    return url


class RemiHistoryApiMixin:
    """Read helpers mixed into RemiApiClient, sharing its authenticated _request."""

    async def get_history_logs(self, limit: int = MAX_HISTORY_LOGS) -> list[dict[str, Any]]:
        """Read only logs belonging to the selected REMI."""
        validate_history_limit(limit)
        remi_id = self._remi_id
        if not isinstance(remi_id, str) or not remi_id:
            raise history_error()
        pointer = {"__type": "Pointer", "className": "Remi", "objectId": remi_id}
        data = await self._request(
            "POST", "/parse/classes/noise_logs",
            {"_method": "GET", "limit": limit, "order": "-timestamp",
             "where": {"$or": [{"remi": pointer}, {"remi": remi_id}]}},
        )
        return self._history_records(data, limit)

    async def get_history_sleep_info(self, ids: list[str]) -> list[dict[str, Any]]:
        """Resolve at most two sleep pointers, with an additional owner filter."""
        if not isinstance(ids, list) or len(ids) > MAX_HISTORY_LOGS or any(
            not isinstance(item, str) or not _OBJECT_ID.fullmatch(item) for item in ids
        ):
            raise history_error()
        if not ids:
            return []
        remi_id = self._remi_id
        if not isinstance(remi_id, str) or not remi_id:
            raise history_error()
        pointer = {"__type": "Pointer", "className": "Remi", "objectId": remi_id}
        data = await self._request(
            "POST", "/parse/classes/SleepInfo",
            {"_method": "GET", "limit": len(ids),
             "where": {"objectId": {"$in": list(dict.fromkeys(ids))},
                       "$or": [{"remi": pointer}, {"remi": remi_id}]}},
        )
        records = self._history_records(data, len(ids))
        if any(record["objectId"] not in ids for record in records):
            raise history_error()
        return records

    def _history_records(self, data: Any, limit: int) -> list[dict[str, Any]]:
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise history_error()
        records = data["results"]
        seen: set[str] = set()
        if len(records) > limit:
            raise history_error()
        for record in records:
            if not isinstance(record, dict) or not _owned_by(record, self._remi_id):
                raise history_error()
            object_id = record.get("objectId")
            if (
                not isinstance(object_id, str)
                or not _OBJECT_ID.fullmatch(object_id)
                or object_id in seen
            ):
                raise history_error()
            seen.add(object_id)
        return records

    async def get_history_file(self, file: dict[str, Any]) -> bytes:
        """Download a bounded binary log, never forwarding authentication."""
        url = history_file_url(file)
        try:
            async with asyncio.timeout(15):
                async with self._session.get(
                    url, allow_redirects=False,
                    headers={"Accept": "application/octet-stream", "Accept-Encoding": "identity"},
                    auto_decompress=False,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    if response.status != 200 or (
                        response.content_length is not None
                        and response.content_length > MAX_HISTORY_FILE_BYTES
                    ):
                        raise history_error()
                    body = bytearray()
                    async for chunk in response.content.iter_chunked(8192):
                        body.extend(chunk)
                        if len(body) > MAX_HISTORY_FILE_BYTES:
                            raise history_error()
                    return bytes(body)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise history_error() from err
