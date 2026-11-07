"""Keep HA alarm identities stable when the cloud replaces Event objects."""
from __future__ import annotations

from collections import Counter
from typing import Any
from uuid import uuid4

from homeassistant.core import CoreState, HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN


class AlarmIdentityStorageError(Exception):
    """The saved identity mapping cannot safely be loaded or committed."""


def alarm_identity_store(hass: HomeAssistant, entry_id: str) -> Store[dict[str, Any]]:
    """Use one atomic store per config entry; the data also checks the device."""
    return Store(hass, 1, f"{DOMAIN}.alarm_identity.{entry_id}", atomic_writes=True)


def alarm_snapshot(events: Any, remi_id: str) -> dict[str, dict[str, Any]] | None:
    """Validate a complete snapshot defensively before any identity changes."""
    if not isinstance(events, list):
        return None
    current: dict[str, dict[str, Any]] = {}
    for event in events:
        if not isinstance(event, dict):
            return None
        event_id = event.get("objectId")
        if not isinstance(event_id, str) or not event_id or event_id in current:
            return None
        if "remi" in event:
            owner = event["remi"]
            if (
                not isinstance(owner, dict)
                or owner.get("className") != "Remi"
                or owner.get("objectId") != remi_id
            ):
                return None
        current[event_id] = event
    return current


def _name(event: dict[str, Any]) -> str | None:
    """Match exact, nonblank cloud names, never translated or custom HA names."""
    name = event.get("name")
    return name if isinstance(name, str) and name.strip() else None


class AlarmIdentityMap:
    """Persist logical IDs independently of replaceable cloud object IDs.

    Initial logical IDs equal cloud IDs, preserving every pre-existing unique_id.
    Missing/corrupt storage never justifies deleting unexplained registry IDs.
    A genuine delete/recreate with the same unique name between two snapshots
    cannot be distinguished from a cloud rotation; no broader matching is used.
    """

    def __init__(
        self, remi_id: str, *, entry_id: str | None = None,
        store: Store[dict[str, Any]] | None = None,
    ) -> None:
        self.remi_id = remi_id
        self.entry_id = entry_id
        self._store = store
        self._records: dict[str, dict[str, str | None]] = {}
        self._unresolved_ids: set[str] = set()
        self._persisted = store is None

    async def async_load(self, registry_ids: set[str]) -> None:
        """Load before the first poll, protecting legacy IDs if storage is lost."""
        if self._store is None:
            return
        data = await self._store.async_load()
        if data is None:
            self._unresolved_ids = set(registry_ids)
            return
        if (
            not isinstance(data, dict)
            or data.get("remi_id") != self.remi_id
            or data.get("entry_id") != self.entry_id
            or not isinstance(data.get("records"), dict)
            or not isinstance(data.get("unresolved_ids"), list)
        ):
            raise AlarmIdentityStorageError("Invalid alarm identity storage")
        records = data["records"]
        cloud_ids: set[str] = set()
        for logical_id, record in records.items():
            if (
                not isinstance(logical_id, str) or not logical_id
                or not isinstance(record, dict)
                or not isinstance(record.get("cloud_id"), str) or not record["cloud_id"]
                or record["cloud_id"] in cloud_ids
                or (record.get("name") is not None and not isinstance(record["name"], str))
            ):
                raise AlarmIdentityStorageError("Invalid alarm identity record")
            cloud_ids.add(record["cloud_id"])
        unresolved = data["unresolved_ids"]
        if (
            any(not isinstance(key, str) or not key or key in records for key in unresolved)
            or len(set(unresolved)) != len(unresolved)
        ):
            raise AlarmIdentityStorageError("Invalid unresolved alarm identities")
        self._records = {key: dict(record) for key, record in records.items()}
        self._unresolved_ids = set(unresolved)
        self._persisted = True

    @property
    def retained_ids(self) -> set[str]:
        """IDs that registry cleanup must retain, including unresolvable legacy IDs."""
        return self._records.keys() | self._unresolved_ids

    def cloud_id(self, logical_id: str) -> str | None:
        """Resolve a command against the currently confirmed mapping."""
        record = self._records.get(logical_id)
        return record["cloud_id"] if record is not None else None

    def logical_snapshot(self, events: Any) -> dict[str, dict[str, Any]] | None:
        """Return only a snapshot whose complete mapping has been committed."""
        current = alarm_snapshot(events, self.remi_id)
        if current is None:
            return None
        by_cloud_id = {record["cloud_id"]: key for key, record in self._records.items()}
        if set(current) != set(by_cloud_id):
            return None
        return {by_cloud_id[key]: event for key, event in current.items()}

    async def async_reconcile(self, events: Any) -> bool:
        """Commit a complete valid snapshot before entities see the new mapping."""
        current = alarm_snapshot(events, self.remi_id)
        if current is None:
            return False
        previous_by_cloud = {record["cloud_id"]: key for key, record in self._records.items()}
        # Count ALL names, including unchanged IDs, to rule out hidden ambiguity.
        old_names = Counter(_name(record) for record in self._records.values())
        new_names = Counter(_name(event) for event in current.values())
        missing_by_name = {
            _name(record): key for key, record in self._records.items()
            if record["cloud_id"] not in current and _name(record) is not None
            and old_names[_name(record)] == 1
        }
        records: dict[str, dict[str, str | None]] = {}
        unresolved = set(self._unresolved_ids)
        reserved = self.retained_ids | set(current)
        for cloud_id, event in current.items():
            name = _name(event)
            logical_id = previous_by_cloud.get(cloud_id)
            if logical_id is None and name is not None and new_names[name] == 1:
                logical_id = missing_by_name.get(name)
            if logical_id is None:
                logical_id = cloud_id
                if logical_id in self._records:
                    # A cloud ID reused while its logical ID belongs to another
                    # generation must not hijack that entity or its automations.
                    logical_id = f"identity_{uuid4().hex}"
                    while logical_id in reserved:
                        logical_id = f"identity_{uuid4().hex}"
            reserved.add(logical_id)
            unresolved.discard(logical_id)
            records[logical_id] = {"cloud_id": cloud_id, "name": name}
        if records == self._records and unresolved == self._unresolved_ids and self._persisted:
            return True
        if self._store is not None:
            data = {
                "entry_id": self.entry_id, "remi_id": self.remi_id,
                "records": records, "unresolved_ids": sorted(unresolved),
            }
            if self._store.hass.state is CoreState.stopping:
                raise AlarmIdentityStorageError("Cannot commit alarm identities while stopping")
            await self._store.async_save(data)
            # HA Store logs some disk errors instead of raising them. Verify the
            # persisted data before allowing reconciliation to remove entities.
            if await self._store.async_load() != data:
                raise AlarmIdentityStorageError("Alarm identity storage write was not confirmed")
        self._records = records
        self._unresolved_ids = unresolved
        self._persisted = True
        return True
