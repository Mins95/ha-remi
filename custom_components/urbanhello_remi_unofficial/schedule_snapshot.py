"""Read-only local copy of the last complete alarm programme."""
from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .alarm_identity import alarm_snapshot
from .const import DAYS_OF_WEEK, DOMAIN, FACE_DEFINE_TO_NAME, FACE_OBJECT_ID_TO_DEFINE


def alarm_time(event: dict[str, Any]) -> time | None:
    """Decode the device's wall time without assigning a date or UTC offset."""
    value = event.get("event_time")
    if not isinstance(value, list) or len(value) != 2 or not all(type(n) is int for n in value):
        return None
    try:
        return time(*value)
    except ValueError:
        return None


def _safe_event(event: dict[str, Any]) -> dict[str, Any]:
    """Allowlist schedule fields, never save associated media or other device settings."""
    row = {"objectId": event["objectId"]}
    if isinstance(event.get("name"), str):
        row["name"] = event["name"]
    if isinstance(event.get("enabled"), bool):
        row["enabled"] = event["enabled"]
    if alarm_time(event) is not None:
        row["event_time"] = list(event["event_time"])
    repeat = event.get("recurrence")
    if isinstance(repeat, list) and len(repeat) == 7 and all(type(n) in (bool, int) and n in (0, 1) for n in repeat):
        row["recurrence"] = [int(n) for n in repeat]
    face = event.get("face")
    if isinstance(face, dict) and isinstance(face.get("objectId"), str) and face["objectId"] in FACE_OBJECT_ID_TO_DEFINE:
        row["face"] = {"objectId": face["objectId"]}
    return row


def schedule_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Provide the card with read-only controls and no cloud action targets."""
    rows = []
    for event in events:
        value = alarm_time(event)
        repeat = event.get("recurrence", [])
        define = FACE_OBJECT_ID_TO_DEFINE.get(event.get("face", {}).get("objectId"))
        rows.append({
            "name": event.get("name"),
            "time": value.strftime("%H:%M") if value else None,
            "days": [day for day, enabled in zip(DAYS_OF_WEEK, repeat) if enabled],
            "enabled": event.get("enabled"),
            "face": FACE_DEFINE_TO_NAME.get(define),
        })
    return rows


class ScheduleSnapshot:
    """An entry-bound schedule, separate from live command availability."""

    def __init__(self, hass: HomeAssistant, entry_id: str, remi_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass, 1, f"{DOMAIN}.schedule.{entry_id}", private=True, atomic_writes=True
        )
        self._remi_id = remi_id
        self.remi: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []
        self.synced_at: datetime | None = None
        self.zone: ZoneInfo | None = None
        self._saved_at: datetime | None = None

    async def async_load(self) -> None:
        """Ignore incomplete or unrelated storage rather than displaying it."""
        data = await self._store.async_load()
        if not isinstance(data, dict):
            return
        remi = data.get("remi")
        events = data.get("events")
        timestamp = data.get("synced_at")
        if not isinstance(remi, dict) or remi.get("objectId") != self._remi_id or not isinstance(timestamp, str):
            return
        try:
            confirmed = datetime.fromisoformat(timestamp)
        except ValueError:
            return
        if confirmed.tzinfo is None or alarm_snapshot(events, self._remi_id) is None:
            return
        await self._set_snapshot(remi, events, confirmed.astimezone(UTC))
        self._saved_at = self.synced_at

    async def _set_snapshot(self, remi: dict[str, Any], events: list[dict[str, Any]], now: datetime) -> bool:
        device = {"objectId": self._remi_id}
        device.update({key: remi[key] for key in ("name", "timezone") if isinstance(remi.get(key), str)})
        if device.get("timezone") != self.remi.get("timezone"):
            self.zone = await dt_util.async_get_time_zone(device["timezone"]) if device.get("timezone") else None
        rows = sorted((_safe_event(e) for e in events), key=lambda row: row["objectId"])
        changed = device != self.remi or rows != self.events
        self.remi, self.events, self.synced_at = device, rows, now
        return changed

    async def async_confirm(self, remi: dict[str, Any], events: list[dict[str, Any]]) -> None:
        """Persist changes immediately, checkpoint unchanged sync times at most hourly."""
        if remi.get("objectId") != self._remi_id or alarm_snapshot(events, self._remi_id) is None:
            return
        now = dt_util.utcnow()
        changed = await self._set_snapshot(remi, events, now)
        if changed or self._saved_at is None or now - self._saved_at >= timedelta(hours=1):
            self._saved_at = None  # Retry a failed save on the next successful poll.
            await self._store.async_save({"remi": self.remi, "events": self.events, "synced_at": now.isoformat()})
            self._saved_at = now

    async def async_remove(self) -> None:
        """Remove the device's schedule when its config entry is removed."""
        await self._store.async_remove()


def next_occurrence(
    snapshot: ScheduleSnapshot, face_define: str, now: datetime
) -> tuple[datetime | None, str | None, datetime | None]:
    """Return next predicted UTC time, alarm name and next local recalculation time.

    A doubled or missing wall time has no verified REMI-specific DST rule.
    Keep that prediction unknown until the affected interval passes.
    """
    if (zone := snapshot.zone) is None:
        return None, None, None
    today = now.astimezone(zone).date()
    choices: list[tuple[datetime, datetime, str | None]] = []
    for event in snapshot.events:
        face_id = event.get("face", {}).get("objectId")
        if event.get("enabled") is not True or FACE_OBJECT_ID_TO_DEFINE.get(face_id) != face_define:
            continue
        clock = alarm_time(event)
        days = event.get("recurrence")
        if clock is None or not days or not any(days):
            continue  # One-off alarms without a confirmed date cannot be placed.
        for offset in range(8):
            date = today + timedelta(days=offset)
            if not days[date.weekday()]:
                continue
            wall = datetime.combine(date, clock, tzinfo=zone)
            first, last = sorted((wall.astimezone(UTC), wall.replace(fold=1).astimezone(UTC)))
            if last > now:
                choices.append((first, last, event.get("name")))
                break
    if not choices:
        return None, None, None
    first, last, name = min(choices, key=lambda item: item[0])
    if first != last:
        return None, None, last
    return first, name, first
