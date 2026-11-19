"""Offline forecasts use only a complete programme confirmed for this device."""
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from custom_components.urbanhello_remi_unofficial.const import FACE_DEFINE_TO_OBJECT_ID
from custom_components.urbanhello_remi_unofficial.schedule_snapshot import (
    ScheduleSnapshot, next_occurrence, schedule_rows,
)
from custom_components.urbanhello_remi_unofficial.sensor import RemiScheduleSensor

DEVICE = {"objectId": "device1", "name": "Rémi", "timezone": "Europe/Paris"}
SUNDAY = [0, 0, 0, 0, 0, 0, 1]


def alarm(hour, minute, *, face="FACE_DAY", days=None, name="Weekend", enabled=True):
    return {
        "objectId": name, "name": name, "event_time": [hour, minute], "enabled": enabled,
        "recurrence": days if days is not None else SUNDAY,
        "face": {"objectId": FACE_DEFINE_TO_OBJECT_ID[face]},
    }


async def test_persistence_scoping_and_local_purge(hass, hass_storage):
    snapshot = ScheduleSnapshot(hass, "test_entry", DEVICE["objectId"])
    device = {**DEVICE, "sessionToken": "private", "online": True}
    event = {**alarm(9, 0), "music_path": "private"}
    await snapshot.async_confirm(device, [event])
    first_sync = snapshot.synced_at
    restored = ScheduleSnapshot(hass, "test_entry", DEVICE["objectId"])
    await restored.async_load()
    assert restored.remi == DEVICE
    assert restored.events == [alarm(9, 0)]
    assert restored.synced_at == first_sync
    assert schedule_rows(restored.events) == [{
        "name": "Weekend", "time": "09:00", "days": ["sun"], "face": "awake", "enabled": True,
    }]
    await restored.async_confirm(device, [alarm(8, 30), alarm(9, 0)])  # duplicate IDs
    assert restored.events == [alarm(9, 0)]
    other = ScheduleSnapshot(hass, "test_entry", "other_device")
    await other.async_load()
    assert other.synced_at is None
    await restored.async_confirm(device, [])
    await snapshot.async_load()
    assert snapshot.events == [] and snapshot.synced_at is not None
    await snapshot.async_remove()
    fresh = ScheduleSnapshot(hass, "test_entry", DEVICE["objectId"])
    await fresh.async_load()
    assert fresh.synced_at is None


async def test_no_disk_writes_each_poll(hass, hass_storage):
    snapshot = ScheduleSnapshot(hass, "entry", DEVICE["objectId"])
    events = [alarm(9, 0)]
    start = datetime(2026, 11, 19, 8, tzinfo=UTC)
    clock = [start + timedelta(minutes=n) for n in (0, 1, 60, 61)]
    with patch("custom_components.urbanhello_remi_unofficial.schedule_snapshot.dt_util.utcnow", side_effect=clock):
        for instant in clock:
            await snapshot.async_confirm(DEVICE, events)
            assert snapshot.synced_at == instant
    restored = ScheduleSnapshot(hass, "entry", DEVICE["objectId"])
    await restored.async_load()
    assert restored.synced_at == clock[2]


async def test_forecast_local_time_sunday_and_filters(hass, hass_storage):
    snapshot = ScheduleSnapshot(hass, "forecasts", DEVICE["objectId"])
    events = [
        alarm(9, 0), alarm(20, 15, face="FACE_NIGHT", name="Soir"),
        alarm(2, 0, enabled=False, name="Off"),
        alarm(3, 0, days=[0] * 7, name="Undated"),
        alarm(4, 0, days=[0, 0, 1], name="Invalid mask"),
        alarm(5, 0, face="FACE_SMILY", name="Unrelated expression"),
    ]
    await snapshot.async_confirm(DEVICE, events)
    # Saturday evening UTC; the two confirmed Sunday clock times are UTC+1.
    saturday = datetime(2026, 11, 21, 19, 0, tzinfo=UTC)
    wake = datetime(2026, 11, 22, 8, 0, tzinfo=UTC)
    bed = datetime(2026, 11, 22, 19, 15, tzinfo=UTC)
    assert next_occurrence(snapshot, "FACE_DAY", saturday) == (wake, "Weekend", wake)
    assert next_occurrence(snapshot, "FACE_NIGHT", saturday) == (bed, "Soir", bed)
    assert next_occurrence(snapshot, "FACE_DAY", wake)[0] == wake + timedelta(weeks=1)
    assert next_occurrence(snapshot, "FACE_DAY", datetime(2026, 8, 1, 12, tzinfo=UTC))[0] == datetime(2026, 8, 2, 7, tzinfo=UTC)
    await snapshot.async_confirm({**DEVICE, "timezone": "invalid/zone"}, events)
    assert next_occurrence(snapshot, "FACE_DAY", saturday) == (None, None, None)


@pytest.mark.parametrize(("now", "resume_at"), [
    (datetime(2026, 3, 28, 12, tzinfo=UTC), datetime(2026, 3, 29, 1, 30, tzinfo=UTC)),
    (datetime(2026, 10, 25, 1, tzinfo=UTC), datetime(2026, 10, 25, 1, 30, tzinfo=UTC)),
])
async def test_dst_gap_or_fold_is_unknown(hass, hass_storage, now, resume_at):
    snapshot = ScheduleSnapshot(hass, "dst", DEVICE["objectId"])
    await snapshot.async_confirm(DEVICE, [alarm(2, 30)])
    assert next_occurrence(snapshot, "FACE_DAY", now) == (None, None, resume_at)
    assert next_occurrence(snapshot, "FACE_DAY", resume_at)[0] > resume_at


async def test_offline_sensor_advances_on_local_timer(hass, hass_storage):
    coordinator = MagicMock()
    coordinator.client.remi_id = DEVICE["objectId"]
    coordinator.remi = DEVICE
    coordinator.last_update_success = coordinator.events_available = False
    snapshot = coordinator.schedule_snapshot = ScheduleSnapshot(hass, "due", DEVICE["objectId"])
    entity = RemiScheduleSensor(coordinator, "next_wake", "FACE_DAY")
    entity.hass = hass
    assert not entity.available
    await snapshot.async_confirm(DEVICE, [alarm(9, 0)])
    now = datetime(2026, 11, 21, 12, tzinfo=UTC)
    with (
        patch("custom_components.urbanhello_remi_unofficial.sensor.dt_util.utcnow", return_value=now),
        patch("custom_components.urbanhello_remi_unofficial.sensor.async_track_point_in_utc_time") as schedule,
        patch.object(entity, "async_write_ha_state"),
    ):
        await entity.async_added_to_hass()
        assert entity.available and entity.extra_state_attributes["cached"]
        due = entity.native_value
        schedule.assert_called_once_with(hass, entity._on_timer, due)
        entity._on_timer(due)
        assert entity.native_value == due + timedelta(weeks=1)
        assert schedule.call_count == 2
