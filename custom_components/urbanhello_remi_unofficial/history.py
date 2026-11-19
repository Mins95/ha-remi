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
import hashlib
import logging
import time
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import FACE_DEFINE_TO_NAME
from .history_store import (
    CONF_HISTORY_NIGHTS, DEFAULT_HISTORY_NIGHTS, HISTORY_SAMPLES, NightArchive, history_store,
)
from .history_api import (
    MAX_HISTORY_LOGS,
    MAX_HISTORY_REPORTS,
    RemiHistoryError,
    history_error,
    history_file_url,
    validate_history_limit,
    validate_history_report_id,
    validate_report_limit,
)

_LOGGER = logging.getLogger(__name__)
HISTORY_INTERVAL = timedelta(minutes=20)
HISTORY_SYNC_DELAY = 12
HISTORY_SYNC_COOLDOWN = 60
MAX_HISTORY_FACE_EVENTS = 1440
_MAX_FACE_DATA_LENGTH = 65536
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
    minutes = duration[0] * 60 + duration[1] if duration is not None else 0
    # The app displays --:-- for 00:00, and -- for score 0. Midnight remains
    # a valid clock time; only the duration/score placeholders are suppressed.
    result["sleep_duration"] = minutes if minutes > 0 else None
    score = record.get("score")
    result["sleep_score"] = score if type(score) is int and 0 < score <= 100 else None
    for field, key in (("sleepFaceTime", "sleep_face_time"), ("wakeUpFaceTime", "wake_face_time")):
        stamp = parse_history_datetime(record.get(field))
        result[key] = stamp.isoformat() if stamp is not None and stamp.year > 1 else None
    result["sleep_status"] = "available" if minutes > 0 or result["sleep_score"] is not None else "unavailable"
    return result


def parse_history_face_events(value: Any, faces: Any) -> dict[str, Any]:
    """Read face changes independently of sleep estimates, matching the app.

    NoiseLogModel splits faceDataPsm into epoch_seconds:face_index tokens
    (0x8c6f34/0x8c7154). TrackGraphChart uses each epoch's UTC clock on its
    noon-to-noon grid (0x90bf40..0x90c06c). Do not reinterpret that clock in
    the device timezone or claim an absolute event/sleep timestamp.

    The app's map keeps the last value for a repeated epoch. Bound processing
    to 1440 tokens/64 KiB; invalid_entries counts only inspected tokens, and
    truncated explicitly reports an uninspected remainder.
    """
    result: dict[str, Any] = {
        "face_events": [],
        "face_events_source": "faceDataPsm",
        "face_events_time_basis": "app_utc_clock",
        "face_events_truncated": False,
        "face_events_invalid_entries": 0,
    }
    if value is None:
        return result
    if not isinstance(value, str):
        result["face_events_invalid_entries"] = 1
        return result
    prefix = value[:_MAX_FACE_DATA_LENGTH]
    if len(value) > _MAX_FACE_DATA_LENGTH:
        result["face_events_truncated"] = True
        # Never interpret the beginning of an overlong token as a complete
        # event. Retain all preceding complete tokens.
        if not prefix[-1].isspace() and not value[_MAX_FACE_DATA_LENGTH].isspace():
            parts = prefix.rsplit(maxsplit=1)
            prefix = parts[0] if len(parts) == 2 else ""
    tokens = prefix.split()
    if len(tokens) > MAX_HISTORY_FACE_EVENTS:
        result["face_events_truncated"] = True
        tokens = tokens[:MAX_HISTORY_FACE_EVENTS]
    face_names = {}
    if isinstance(faces, list):
        for face in faces:
            if (
                isinstance(face, dict)
                and type(face.get("index")) is int
                and 0 <= face["index"] <= 255
                and isinstance(face.get("define"), str)
            ):
                face_names[face["index"]] = FACE_DEFINE_TO_NAME.get(face["define"])
    events = {}
    for token in tokens:
        # Bound integer conversion and reject signs, fractions, extra fields,
        # Unicode digits and dates outside Python's representable range.
        parts = token.split(":")
        if (
            len(parts) != 2
            or not 1 <= len(parts[0]) <= 12
            or not 1 <= len(parts[1]) <= 3
            or not all(part.isascii() and part.isdecimal() for part in parts)
        ):
            result["face_events_invalid_entries"] += 1
            continue
        epoch, face_index = map(int, parts)
        if not 0 <= epoch <= 253402300799 or not 0 <= face_index <= 255:
            result["face_events_invalid_entries"] += 1
            continue
        try:
            clock = datetime.fromtimestamp(epoch, timezone.utc)
        except (OverflowError, OSError, ValueError):
            result["face_events_invalid_entries"] += 1
            continue
        events[epoch] = {
            "clock": f"{clock.hour:02d}:{clock.minute:02d}",
            "minute_offset": ((clock.hour - 12) % 24) * 60 + clock.minute,
            "face_index": face_index,
            "face": face_names.get(face_index),
        }
    result["face_events"] = sorted(events.values(), key=lambda event: event["minute_offset"])
    return result


def report_timing(report: dict[str, Any], device_timezone: Any, now: datetime | None = None) -> dict[str, Any]:
    """Separate the app's date range from the actual cloud export time.

    The app labels a log using its UTC calendar date, minus one day through
    that date. Its timestamp hour is not the time of the latest measurement.
    """
    now = now or datetime.now(timezone.utc)
    stamp = parse_history_datetime(report.get("log_timestamp"))
    updated = parse_history_datetime(report.get("updated_at"))
    age = (now - updated).total_seconds() if updated else None
    valid_age = age is not None and age >= -300
    result = {
        "period_start": None, "period_end": None, "report_status": "unknown",
        "report_age_days": round(max(0, age) / 86400, 2) if valid_age else None,
        "stale": age > 48 * 3600 if valid_age else None,
    }
    if stamp is None or stamp.year < 1970:
        return result
    end = stamp.date()
    start = end - timedelta(days=1)
    result.update(period_start=start.isoformat(), period_end=end.isoformat())
    try:
        zone = ZoneInfo(device_timezone) if isinstance(device_timezone, str) else None
    except (ZoneInfoNotFoundError, ValueError):
        zone = None
    if zone is not None:
        local = now.astimezone(zone)
        # The app's clock grid runs from noon to the following noon. Keep
        # this period status separate from unestablished sample timestamps.
        start_noon = datetime(start.year, start.month, start.day, 12, tzinfo=zone)
        end_noon = datetime(end.year, end.month, end.day, 12, tzinfo=zone)
        if start_noon <= local < end_noon:
            result["report_status"] = "in_progress"
        elif local >= end_noon:
            result["report_status"] = "completed"
    return result


def decode_history_series(kind: str, body: bytes) -> dict[str, Any]:
    """Decode the app's byte arrays; physical units are only known for its °C axis.

    TrackGraphChart: temperature/noise Y=raw*100/255 (0x90ac60/0x90b3a8).
    Celsius axis Y/2-10 (0x90cab8..0x90cacc, °C label 0x90cbac).
    Light overlay is 100 for raw 1..7, otherwise 0 (0x90b63c..0x90b678).
    A temperature zero byte is ambiguous (unfilled slot or chart floor): keep
    it in raw_value but do not assert a physical -10°C measurement. Noise and
    light zeroes remain valid; silence and darkness must not become gaps.
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
            value = round(raw * 50 / 255 - 10, 4) if raw else None
            if not raw:
                graph = None
        samples.append({
            "index": index,
            "minute_offset": index * 2,
            "clock": f"{minute // 60:02d}:{minute % 60:02d}",
            "value": value,
            "raw_value": raw,
            "graph_value": graph,
            "valid": value is not None,
        })
    result = {
        "status": "available", "unit": "°C" if kind == "temperature" else None,
        "encoding": "uint8", "sample_interval_seconds": 120,
        "absolute_sample_timestamps": False,
        "samples": samples,
    }
    if kind == "temperature":
        result.update({"conversion": "raw * 50 / 255 - 10", "source": "app_chart_axis",
                       "boundary_values_not_calibrated": [0, 255],
                       "uninterpreted_raw_values": [0]})
    else:
        result["conversion"] = "raw (no physical unit established)"
    result["graph_conversion"] = (
        "100 if 1 <= raw <= 7 else 0" if kind == "light" else "raw * 100 / 255"
    )
    return result


class RemiHistoryCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll metadata and incrementally archive environmental measurements."""

    def __init__(self, hass: HomeAssistant, client: Any, device_coordinator: Any, *, entry: ConfigEntry | None = None) -> None:
        super().__init__(hass, _LOGGER, name="REMI history", update_interval=HISTORY_INTERVAL)
        self.client = client
        self.device_coordinator = device_coordinator
        self._logs: list[dict[str, Any]] = []
        self._fetched_monotonic: float | None = None
        self._file_cache: OrderedDict[tuple[str, str], tuple[float, tuple[bytes, str]]] = OrderedDict()
        self._history_lock = asyncio.Lock()
        self._file_locks = {kind: asyncio.Lock() for kind in _SERIES_FIELDS}
        self._last_sync_attempt: float | None = None
        self._archive = NightArchive(
            history_store(hass, entry.entry_id), client.remi_id,
            entry.options.get(CONF_HISTORY_NIGHTS, DEFAULT_HISTORY_NIGHTS),
        ) if entry is not None else None
        self._entry = entry
        self._backfill: asyncio.Task | None = None
        self._last_backfill: dict[str, float] = {}
        self._closing = False
        self._unsubscribe_archive = None

    async def async_load_archive(self) -> bool:
        """Restore existing reports before the first cloud read."""
        if self._archive is None:
            return False
        try:
            await self._archive.async_load()
        except (OSError, HomeAssistantError):
            _LOGGER.warning("Could not read the local REMI sleep archive")
        if not self._archive.reports:
            return False
        self.data = self._archived_data()
        return True

    def _archived_data(self) -> dict[str, Any]:
        return {"logs": self._archive.summaries(), "fetched_at": self._archive.fetched_at,
                "source": "local_archive"}

    @callback
    def async_start(self) -> None:
        """Poll for archiving even if every historical sensor has been disabled."""
        if self._archive and self._archive.nights:
            self._unsubscribe_archive = self.async_add_listener(lambda: None)
        self._entry.async_create_background_task(self.hass, self.async_refresh(), "REMI initial history refresh")

    async def async_shutdown(self) -> None:
        self._closing = True
        if self._unsubscribe_archive:
            self._unsubscribe_archive()
            self._unsubscribe_archive = None
        await super().async_shutdown()
        if self._backfill:
            self._backfill.cancel()
            await asyncio.gather(self._backfill, return_exceptions=True)
        if self._archive:
            await self._archive.async_close()

    @property
    def remi(self) -> dict[str, Any]:
        """Share device identity, never live availability, with history entities."""
        return self.device_coordinator.remi

    @property
    def latest_report(self) -> dict[str, Any]:
        """The latest published report, which may be older than the last night."""
        logs = (self.data or {}).get("logs", [])
        # A new empty/current period must not replace a real completed sleep
        # report in the native sensors. The card can still inspect all periods.
        undated = None
        for report in logs:
            if report.get("sleep_status") != "available":
                continue
            status = report_timing(report, self.remi.get("timezone"))["report_status"]
            if status == "completed":
                return report
            if status == "unknown" and undated is None:
                undated = report
        if undated is not None:
            return undated
        return logs[0] if logs else {}

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            logs = await self.client.get_history_logs(limit=MAX_HISTORY_REPORTS)
            ids = list(dict.fromkeys(
                log["sleepInfo"]["objectId"] for log in logs
                if isinstance(log.get("sleepInfo"), dict)
                and log["sleepInfo"].get("__type") == "Pointer"
                and log["sleepInfo"].get("className") == "SleepInfo"
                and isinstance(log["sleepInfo"].get("objectId"), str)
            ))
            sleep = await self.client.get_history_sleep_info(ids)
        except (HomeAssistantError, aiohttp.ClientError, TimeoutError) as err:
            if self._archive:
                self._archive.prune()
                await self._archive.async_save()
                if self._archive.reports:
                    self._logs = []
                    self._fetched_monotonic = time.monotonic()
                    return self._archived_data()
            # The parent coordinator and device controls remain untouched.
            raise UpdateFailed("Unable to read REMI history") from err
        sleep_by_id = {record["objectId"]: record for record in sleep}
        summaries = []
        for log in logs:
            stamp = parse_history_datetime(log.get("timestamp"))
            ref = log.get("sleepInfo")
            ref_id = ref.get("objectId") if isinstance(ref, dict) else None
            info = sleep_by_id.get(ref_id)
            updated = parse_history_datetime(log.get("updatedAt"))
            sleep_updated = parse_history_datetime(info.get("updatedAt")) if info else None
            summary = {
                "report_id": log["objectId"],
                "source": "cloud",
                "series_available": any(log.get(field) is not None for field in _SERIES_FIELDS.values()),
                "log_timestamp": stamp.isoformat() if stamp is not None else None,
                "updated_at": updated.isoformat() if updated is not None else None,
                "sleep_updated_at": sleep_updated.isoformat() if sleep_updated is not None else None,
                **parse_sleep_info(info),
                **parse_history_face_events(log.get("faceDataPsm"), getattr(self.device_coordinator, "faces", None)),
            }
            summary.update(report_timing(summary, self.remi.get("timezone")))
            summaries.append(summary)
        fetched_at = datetime.now(timezone.utc).isoformat()
        if self._archive and self._archive.nights:
            self._archive.update_reports(summaries, fetched_at)
            live_ids = {log["objectId"] for log in logs}
            for log in logs:
                record = self._archive.reports.get(log["objectId"])
                if record is None:
                    continue
                revisions = {}
                for kind, field in _SERIES_FIELDS.items():
                    if log.get(field) is None:
                        continue
                    try:
                        revisions[kind] = self._revision(log[field], log)
                    except RemiHistoryError:
                        continue
                record["revisions"] = revisions
            for summary in summaries:
                record = self._archive.reports.get(summary["report_id"])
                if record and record["files"]:
                    summary["series_available"] = True
            archived = [s for s in self._archive.summaries() if s["report_id"] not in live_ids]
            if archived:
                summaries.extend(archived)
                summaries.sort(key=lambda report: report.get("log_timestamp") or "", reverse=True)
                del summaries[MAX_HISTORY_REPORTS:]
            await self._archive.async_save()
        # Publish pointers and summaries together. Do not suspend between here
        # and the coordinator installing the result as its current data.
        self._logs = deepcopy(logs)
        if (not self._closing and self._archive and self._archive.nights
                and (self._backfill is None or self._backfill.done())):
            self._backfill = self._entry.async_create_background_task(
                self.hass, self._backfill_series(), "REMI archive environmental history", eager_start=False,
            )
        self._fetched_monotonic = time.monotonic()
        return {"logs": summaries, "fetched_at": fetched_at, "source": "cloud"}

    def _revision(self, file: dict[str, Any], log: dict[str, Any]) -> str:
        """A cloud file reference stays in memory; only its fingerprint is saved."""
        url = history_file_url(file)
        return hashlib.sha256(f"{url}\n{log.get('updatedAt', '')}".encode()).hexdigest()

    async def _backfill_series(self) -> None:
        """Catch up two recent/missing nights per successful poll, without exporting."""
        logs = [log for log in self._logs if log["objectId"] in self._archive.reports]
        # Rotate retries so one continuously failing file cannot starve older nights.
        self._last_backfill = {key: value for key, value in self._last_backfill.items()
                               if key in self._archive.reports}
        logs.sort(key=lambda log: self._last_backfill.get(log["objectId"], 0.0))
        attempted = 0
        for log in logs:
            key = log["objectId"]
            missing = []
            for kind, field in _SERIES_FIELDS.items():
                if log.get(field) is None:
                    continue
                try:
                    revision = self._revision(log[field], log)
                except RemiHistoryError:
                    continue
                archived = self._archive.file(key, kind)
                if archived is None or archived.revision != revision:
                    missing.append(kind)
            if missing:
                self._last_backfill[key] = time.monotonic()
                await asyncio.gather(*(self._read_body(kind, log) for kind in missing))
                await self._archive.async_save()
                attempted += 1
                if attempted >= MAX_HISTORY_LOGS:
                    break

    async def _cached_file(
        self, file: dict[str, Any], revision: str, *, force: bool = False,
    ) -> tuple[bytes, str]:
        key = (history_file_url(file), revision)
        now = time.monotonic()
        cached = self._file_cache.get(key)
        if not force and cached is not None and now - cached[0] < HISTORY_INTERVAL.total_seconds():
            self._file_cache.move_to_end(key)
            return cached[1]
        # A failed refresh never makes an expired file appear newly fetched.
        self._file_cache.pop(key, None)
        body = await self.client.get_history_file(file)
        if not isinstance(body, bytes) or len(body) not in (0, HISTORY_SAMPLES):
            raise history_error()
        downloaded = (body, datetime.now(timezone.utc).isoformat())
        self._file_cache[key] = (time.monotonic(), downloaded)
        while len(self._file_cache) > MAX_HISTORY_LOGS * len(_SERIES_FIELDS):
            self._file_cache.popitem(last=False)
        return downloaded

    async def async_get_history(
        self, limit: int = MAX_HISTORY_LOGS, *, report_id: str | None = None,
        include_series: bool = True, refresh: bool = False, sync: bool = False,
    ) -> dict[str, Any]:
        """Return bounded chart data; no recorder backfill or credentials/URLs."""
        validate_report_limit(limit)
        if any(type(value) is not bool for value in (include_series, refresh, sync)):
            raise history_error()
        if report_id is not None:
            validate_history_report_id(report_id)
        elif include_series:
            validate_history_limit(limit)
        async with self._history_lock:
            if self._closing:
                raise history_error()
            if report_id is not None and sync:
                if not self._logs or not self.last_update_success:
                    await self.async_refresh()
                if not any(log.get("objectId") == report_id for log in self._logs):
                    # An explicit export requires current online ownership.
                    raise history_error()
            sync_status = None
            if sync:
                now = time.monotonic()
                if self._last_sync_attempt is None or now - self._last_sync_attempt >= HISTORY_SYNC_COOLDOWN:
                    # Mark the attempt before the write: an ambiguous failure
                    # must not cause an automatic replay of a device command.
                    self._last_sync_attempt = now
                    try:
                        await self.client.request_history_sync()
                    except (HomeAssistantError, aiohttp.ClientError, TimeoutError):
                        if not self._archive or not self._archive.reports:
                            raise
                        sync_status = "failed"
                    else:
                        await asyncio.sleep(HISTORY_SYNC_DELAY)
                        sync_status = "requested"
                else:
                    sync_status = "cooldown"
                refresh = True
            restored = self.data is not None and self.data.get("source") == "local_archive"
            if (
                refresh or (self._fetched_monotonic is None and not restored)
                or not self.last_update_success
                or (self._fetched_monotonic is not None
                    and time.monotonic() - self._fetched_monotonic >= HISTORY_INTERVAL.total_seconds())
            ):
                await self.async_refresh()
            if not self.last_update_success or self.data is None:
                raise history_error()
            # Snapshot once: a metadata poll cannot mix reports and file pointers.
            result = deepcopy(self.data)
            live_logs = {log["objectId"]: log for log in self._logs}
            pairs = [(live_logs.get(summary["report_id"]), summary) for summary in result["logs"]]
            if report_id is not None:
                pairs = [(log, summary) for log, summary in pairs if summary.get("report_id") == report_id]
                if not pairs:
                    # Never look up an arbitrary object supplied by the caller.
                    raise history_error()
            else:
                pairs = pairs[:limit]
            result["logs"] = [summary for _, summary in pairs]
            result["sync_status"] = sync_status
            result["timezone"] = self.remi.get("timezone")
            result["time_basis"] = "app_clock_grid_only"
            result["clock_start"] = "12:00"
            result["absolute_sample_timestamps"] = False
            for log, summary in pairs:
                summary.update(report_timing(summary, self.remi.get("timezone")))
                if not include_series:
                    continue
                # At most three file reads in flight; each has its own 15s deadline.
                series = await asyncio.gather(*(
                    self._load_series(kind, summary["report_id"], log, force=refresh) for kind in _SERIES_FIELDS
                ))
                summary["series"] = dict(zip(_SERIES_FIELDS, series, strict=True))
            if self._archive:
                await self._archive.async_save()
            return result

    async def _read_body(self, kind: str, log: dict, *, force: bool = False) -> tuple[bytes, str] | None:
        """Refresh a single file and retain the last good version on failure."""
        key = log["objectId"]
        file = log.get(_SERIES_FIELDS[kind])
        async with self._file_locks[kind]:
            try:
                revision = self._revision(file, log)
                saved = self._archive.file(key, kind) if self._archive else None
                if not force and saved and saved.revision == revision and log.get("updatedAt"):
                    return saved.body, "local_archive"
                body, received_at = await self._cached_file(file, revision, force=force)
                # Empty files can be transient while a new export is being
                # published. Retry next poll and retain any usable older curve.
                if not body and saved:
                    return None
                if self._archive and body:
                    record = self._archive.reports.get(key)
                    if record and record["revisions"].get(kind) == revision:
                        self._archive.save_file(key, kind, revision, body, received_at)
                return body, "cloud"
            except (RemiHistoryError, aiohttp.ClientError, TimeoutError):
                return None

    async def _load_series(self, kind: str, key: str, log: dict | None, *, force: bool) -> dict:
        has_reference = log is not None and log.get(_SERIES_FIELDS[kind]) is not None
        if has_reference:
            current = await self._read_body(kind, log, force=force)
            if current is not None:
                body, source = current
                return dict(decode_history_series(kind, body), source=source)
        record = self._archive.reports.get(key) if self._archive else None
        saved = self._archive.file(key, kind) if record else None
        if saved is not None:
            return dict(decode_history_series(kind, saved.body), source="local_archive",
                        updated_at=saved.updated_at, received_at=saved.received_at,
                        outdated=record.get("revisions", {}).get(kind) != saved.revision)
        status = "unavailable" if has_reference or (record and kind in record.get("revisions", {})) else "missing"
        return {"status": status, "samples": []}
