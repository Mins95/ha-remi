"""Device-scoped archive of sleep estimates and environmental measurements."""
from __future__ import annotations

import asyncio
import base64
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .history_api import MAX_HISTORY_REPORTS

_LOGGER = logging.getLogger(__name__)
CONF_HISTORY_NIGHTS = "history_nights"
DEFAULT_HISTORY_NIGHTS = 30
HISTORY_SAMPLES = 720


def history_store(hass: HomeAssistant, entry_id: str) -> Store:
    """Use the private HA storage area, separately for every config entry."""
    return Store(hass, 1, f"{DOMAIN}.history.{entry_id}", private=True,
                 atomic_writes=True, serialize_in_event_loop=False)


@dataclass(frozen=True)
class ArchivedSeries:
    revision: str
    body: bytes
    updated_at: str | None
    received_at: str | None


class NightArchive:
    """Persist normalized reports and compact chart samples, without cloud URLs."""

    def __init__(self, store: Store, remi_id: str, nights: int) -> None:
        self.store = store
        self.remi_id = remi_id
        self.nights = nights if type(nights) is int and 0 <= nights <= MAX_HISTORY_REPORTS else DEFAULT_HISTORY_NIGHTS
        self.reports: dict[str, dict] = {}
        self.fetched_at: str | None = None
        self._dirty = False
        self._save_lock = asyncio.Lock()
        self._closed = False

    async def async_load(self) -> None:
        """Apply shorter retention and the opt-out immediately, even offline."""
        if not self.nights:
            await self.store.async_remove()
            return
        data = await self.store.async_load()
        if not isinstance(data, dict) or data.get("remi_id") != self.remi_id:
            return
        if not isinstance(data.get("reports"), dict):
            return
        self.fetched_at = data.get("fetched_at")
        self.reports = {
            key: item for key, item in data["reports"].items()
            if isinstance(item, dict) and isinstance(item.get("summary"), dict)
            and item["summary"].get("report_id") == key and isinstance(item.get("files"), dict)
        }
        self.prune()
        await self.async_save()

    def prune(self) -> None:
        """Keep dated nights only, at most one record per day and N in total."""
        # The cloud's UTC date labels the night ending that day, including
        # tomorrow's label while the current recording is in progress.
        today = datetime.now(timezone.utc).date()
        oldest = today - timedelta(days=self.nights - 1)
        latest = today + timedelta(days=1)
        retained: dict[str, dict] = {}
        seen: set[date] = set()
        for key, item in sorted(self.reports.items(), key=lambda pair: (
            str(pair[1]["summary"].get("period_end") or ""),
            str(pair[1]["summary"].get("updated_at") or ""),
        ), reverse=True):
            try:
                day = date.fromisoformat(item["summary"]["period_end"])
            except (KeyError, TypeError, ValueError):
                continue
            if oldest <= day <= latest and day not in seen and len(seen) < self.nights:
                retained[key] = item
                seen.add(day)
        if self.reports.keys() != retained.keys():
            self._dirty = True
        self.reports = retained

    def update_reports(self, reports: list[dict], fetched_at: str) -> None:
        """Keep a successful metadata read without expiring earlier owned nights."""
        if not self.nights:
            return
        for summary in reports:
            key = summary["report_id"]
            item = self.reports.setdefault(key, {"files": {}, "revisions": {}})
            item["summary"] = deepcopy(summary)
        self.fetched_at = fetched_at
        self._dirty = True
        self.prune()

    def summaries(self) -> list[dict]:
        """Return local metadata in the same order as the cloud catalogue."""
        return [dict(item["summary"], source="local_archive", series_available=bool(item["files"]))
                for item in self.reports.values()]

    def file(self, key: str, kind: str) -> ArchivedSeries | None:
        record = self.reports.get(key, {}).get("files", {}).get(kind)
        if not isinstance(record, dict) or not isinstance(record.get("samples"), str):
            return None
        if len(record["samples"]) > HISTORY_SAMPLES * 4 // 3 or not isinstance(record.get("revision"), str):
            return None
        try:
            body = base64.b64decode(record["samples"], validate=True)
        except ValueError:
            return None
        if len(body) != HISTORY_SAMPLES:
            return None
        return ArchivedSeries(record["revision"], body, record.get("updated_at"), record.get("received_at"))

    def save_file(self, key: str, kind: str, revision: str, body: bytes, received_at: str) -> None:
        if key in self.reports:
            record = self.reports[key]
            record["files"][kind] = {
                "revision": revision, "samples": base64.b64encode(body).decode("ascii"),
                "updated_at": record["summary"].get("updated_at"),
                "received_at": received_at,
            }
            self._dirty = True

    async def async_save(self) -> None:
        async with self._save_lock:
            if not self._dirty or self._closed:
                return
            self._dirty = False
            try:
                await self.store.async_save({
                    "remi_id": self.remi_id, "fetched_at": self.fetched_at,
                    "reports": deepcopy(self.reports),
                })
            except (HomeAssistantError, OSError):
                self._dirty = True
                _LOGGER.warning("Could not save the local REMI sleep history")
            except asyncio.CancelledError:
                self._dirty = True
                raise

    async def async_close(self) -> None:
        """Drain pending saves before the entry may be reloaded or deleted."""
        await self.async_save()
        self._closed = True
