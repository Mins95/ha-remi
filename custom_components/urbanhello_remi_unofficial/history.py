"""Separate cloud history polling and on-demand environmental series.

REMI Android 3.4.23 reads Uint8List logs directly (TrackLogsService.getBinFileData),
with 720 positions, 2 minutes each, displayed from 12:00 to 11:58. The
timestamp-to-sample offset is not established, so no absolute sample timestamps
are invented. The cloud report timestamp and the app's clock grid stay separate.
"""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import logging
import time
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .history_api import (
    MAX_HISTORY_LOGS,
    RemiHistoryError,
    history_error,
    history_file_url,
    validate_history_limit,
)

_LOGGER = logging.getLogger(__name__)
HISTORY_INTERVAL = timedelta(minutes=20)
HISTORY_SAMPLES = 720
_SERIES_FIELDS = {"temperature": "tempData", "noise": "data", "light": "lightData"}


def parse_history_datetime(value: Any) -> datetime | None:
    """Accept only timezone-aware server dates, without guessing a timezone."""
    if isinstance(value, dict):
        value = value.get("iso") if value.get("__type") == "Date" else None
    if not isinstance(value, str) or len(value) > 64:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if result.tzinfo is None or result.utcoffset() is None:
        return None
    try:
        return result.astimezone(timezone.utc)
    except OverflowError:
        return None


def _clock_pair(value: Any) -> tuple[int, int] | None:
    """Match SerializationService.listIntToTime, including its 24h bound."""
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(type(item) is not int for item in value)
        or not 0 <= value[0] < 24
        or not 0 <= value[1] < 60
    ):
        return None
    return value[0], value[1]


def parse_sleep_info(record: Any) -> dict[str, Any]:
    """Keep cloud-derived times, estimates and duration without reinterpreting dates."""
    if not isinstance(record, dict):
        record = {}
    result: dict[str, Any] = {}
    for field, key in (("bedTime", "sleep_bedtime"), ("wakeUpTime", "sleep_wake_time")):
        pair = _clock_pair(record.get(field))
        result[key] = f"{pair[0]:02d}:{pair[1]:02d}" if pair is not None else None
    duration = _clock_pair(record.get("sleepDuration"))
    result["sleep_duration"] = duration[0] * 60 + duration[1] if duration is not None else None
    score = record.get("score")
    result["sleep_score"] = score if type(score) is int and 0 <= score <= 100 else None
    for field, key in (("sleepFaceTime", "sleep_face_time"), ("wakeUpFaceTime", "wake_face_time")):
        stamp = parse_history_datetime(record.get(field))
        result[key] = stamp.isoformat() if stamp is not None else None
    return result


def decode_history_series(kind: str, body: bytes) -> dict[str, Any]:
    """Decode the app's byte arrays; physical units are only known for its °C axis.

    TrackGraphChart: temperature/noise Y=raw*100/255 (0x90ac60/0x90b3a8).
    Celsius axis Y/2-10 (0x90cab8..0x90cacc, °C label 0x90cbac).
    Light overlay is 100 for raw 1..7, otherwise 0 (0x90b63c..0x90b678).
    Boundary bytes are retained; absence versus saturation is not established.
    This reproduces the app's chart scale, not a sensor calibration.
    """
    if kind not in _SERIES_FIELDS or not isinstance(body, bytes):
        raise history_error()
    if not body:
        return {"status": "empty", "samples": []}
    if len(body) != HISTORY_SAMPLES:
        raise history_error()
    samples = []
    for index, raw in enumerate(body):
        minute = (12 * 60 + index * 2) % (24 * 60)
        graph = 100 if 1 <= raw <= 7 else 0
        if kind != "light":
            graph = round(raw * 100 / 255, 4)
        value = raw
        if kind == "temperature":
            value = round(raw * 50 / 255 - 10, 4)
        samples.append({
            "index": index,
            "minute_offset": index * 2,
            "clock": f"{minute // 60:02d}:{minute % 60:02d}",
            "value": value,
            "raw_value": raw,
            "graph_value": graph,
        })
    result = {
        "status": "available", "unit": "°C" if kind == "temperature" else None,
        "encoding": "uint8", "sample_interval_seconds": 120,
        "absolute_sample_timestamps": False,
        "samples": samples,
    }
    if kind == "temperature":
        result.update({"conversion": "raw * 50 / 255 - 10", "source": "app_chart_axis",
                       "boundary_values_not_calibrated": [0, 255]})
    else:
        result["conversion"] = "raw (no physical unit established)"
    result["graph_conversion"] = (
        "100 if 1 <= raw <= 7 else 0" if kind == "light" else "raw * 100 / 255"
    )
    return result


class RemiHistoryCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll small metadata independently; fetch binary files only on request."""

    def __init__(self, hass: HomeAssistant, client: Any, device_coordinator: Any) -> None:
        super().__init__(hass, _LOGGER, name="REMI history", update_interval=HISTORY_INTERVAL)
        self.client = client
        self.device_coordinator = device_coordinator
        self._logs: list[dict[str, Any]] = []
        self._fetched_monotonic: float | None = None
        self._file_cache: OrderedDict[tuple[str, str], tuple[float, bytes]] = OrderedDict()
        self._history_lock = asyncio.Lock()

    @property
    def remi(self) -> dict[str, Any]:
        """Share device identity, never live availability, with history entities."""
        return self.device_coordinator.remi

    @property
    def latest_report(self) -> dict[str, Any]:
        """The latest published report, which may be older than the last night."""
        logs = (self.data or {}).get("logs", [])
        return logs[0] if logs else {}

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            logs = await self.client.get_history_logs(limit=MAX_HISTORY_LOGS)
            ids = list(dict.fromkeys(
                log["sleepInfo"]["objectId"] for log in logs
                if isinstance(log.get("sleepInfo"), dict)
                and log["sleepInfo"].get("__type") == "Pointer"
                and log["sleepInfo"].get("className") == "SleepInfo"
                and isinstance(log["sleepInfo"].get("objectId"), str)
            ))
            sleep = await self.client.get_history_sleep_info(ids)
        except (HomeAssistantError, aiohttp.ClientError, TimeoutError) as err:
            # The parent coordinator and device controls remain untouched.
            raise UpdateFailed("Unable to read REMI history") from err
        sleep_by_id = {record["objectId"]: record for record in sleep}
        summaries = []
        for log in logs:
            stamp = parse_history_datetime(log.get("timestamp"))
            ref = log.get("sleepInfo")
            ref_id = ref.get("objectId") if isinstance(ref, dict) else None
            summaries.append({
                "log_timestamp": stamp.isoformat() if stamp is not None else None,
                **parse_sleep_info(sleep_by_id.get(ref_id)),
            })
        self._logs = deepcopy(logs)
        self._fetched_monotonic = time.monotonic()
        return {"logs": summaries, "fetched_at": datetime.now(timezone.utc).isoformat()}

    async def _cached_file(self, file: dict[str, Any], revision: str) -> bytes:
        key = (history_file_url(file), revision)
        now = time.monotonic()
        cached = self._file_cache.get(key)
        if cached is not None and now - cached[0] < HISTORY_INTERVAL.total_seconds():
            self._file_cache.move_to_end(key)
            return cached[1]
        # A failed refresh never makes an expired file appear newly fetched.
        self._file_cache.pop(key, None)
        body = await self.client.get_history_file(file)
        if not isinstance(body, bytes) or len(body) not in (0, HISTORY_SAMPLES):
            raise history_error()
        self._file_cache[key] = (time.monotonic(), body)
        while len(self._file_cache) > MAX_HISTORY_LOGS * len(_SERIES_FIELDS):
            self._file_cache.popitem(last=False)
        return body

    async def async_get_history(self, limit: int = MAX_HISTORY_LOGS) -> dict[str, Any]:
        """Return bounded chart data; no recorder backfill or credentials/URLs."""
        validate_history_limit(limit)
        async with self._history_lock:
            if (
                self._fetched_monotonic is None
                or not self.last_update_success
                or time.monotonic() - self._fetched_monotonic >= HISTORY_INTERVAL.total_seconds()
            ):
                await self.async_refresh()
            if not self.last_update_success or self.data is None:
                raise history_error()
            # Snapshot once: a metadata poll cannot mix reports and file pointers.
            logs = deepcopy(self._logs[:limit])
            result = deepcopy(self.data)
            result["logs"] = result["logs"][:limit]
            result["timezone"] = self.remi.get("timezone")
            result["time_basis"] = "app_clock_grid_only"
            result["clock_start"] = "12:00"
            result["absolute_sample_timestamps"] = False
            for log, summary in zip(logs, result["logs"], strict=True):
                stamp = parse_history_datetime(summary["log_timestamp"])
                age = (datetime.now(timezone.utc) - stamp).total_seconds() if stamp else None
                summary["report_age_days"] = round(age / 86400, 2) if age is not None else None
                summary["stale"] = age is None or age < 0 or age > 48 * 3600
                # At most three file reads in flight; each has its own 15s deadline.
                series = await asyncio.gather(*(
                    self._load_series(kind, log) for kind in _SERIES_FIELDS
                ))
                summary["series"] = dict(zip(_SERIES_FIELDS, series, strict=True))
            return result

    async def _load_series(self, kind: str, log: dict[str, Any]) -> dict[str, Any]:
        file = log.get(_SERIES_FIELDS[kind])
        if file is None:
            return {"status": "missing", "samples": []}
        try:
            body = await self._cached_file(file, str(log.get("updatedAt", "")))
            return decode_history_series(kind, body)
        except (RemiHistoryError, aiohttp.ClientError, TimeoutError):
            return {"status": "unavailable", "samples": []}
