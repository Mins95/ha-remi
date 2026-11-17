"""Historical face changes are chart annotations, not sleep estimates."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.urbanhello_remi_unofficial.history import (
    MAX_HISTORY_FACE_EVENTS,
    RemiHistoryCoordinator,
    parse_history_face_events,
)

FACES = [
    {"index": 0, "define": "FACE_OFF"},
    {"index": 1, "define": "FACE_DAY"},
    {"index": 2, "define": "FACE_NIGHT"},
    {"index": 3, "define": "FACE_SEMI_AWAKE"},
    {"index": 4, "define": "FACE_SMILY"},
]


def epoch(hour: int, minute: int = 0) -> int:
    """Use synthetic dates; only the UTC clock belongs in the result."""
    return int(datetime(2000, 1, 2, hour, minute, tzinfo=timezone.utc).timestamp())


def test_face_events_follow_app_utc_clock_and_noon_grid():
    parsed = parse_history_face_events(
        f"{epoch(8, 40)}:1 {epoch(21, 45)}:2 {epoch(12)}:0 ", FACES,
    )
    assert parsed == {
        "face_events": [
            {"clock": "12:00", "minute_offset": 0, "face_index": 0, "face": "off"},
            {"clock": "21:45", "minute_offset": 585, "face_index": 2, "face": "sleepy"},
            {"clock": "08:40", "minute_offset": 1240, "face_index": 1, "face": "awake"},
        ],
        "face_events_source": "faceDataPsm",
        "face_events_time_basis": "app_utc_clock",
        "face_events_truncated": False,
        "face_events_invalid_entries": 0,
    }
    # An encoded epoch does not establish an absolute timestamp or bedtime.
    assert all(set(event) == {"clock", "minute_offset", "face_index", "face"}
               for event in parsed["face_events"])


def test_duplicate_epoch_keeps_last_valid_change_like_app_map():
    parsed = parse_history_face_events(f"{epoch(21)}:2 {epoch(21)}:4", FACES)
    assert parsed["face_events"] == [
        {"clock": "21:00", "minute_offset": 540, "face_index": 4, "face": "smiley"},
    ]


@pytest.mark.parametrize("token", [
    "bad", "1:", ":1", "1:2:3", "-1:2", "+1:2", "1:-1", "1:true",
    "1:256", "1:1000", "1:1.0", "253402300800:1", "9999999999999:1",
    "١:2", "1:٢", "1e3:2",
])
def test_malformed_tokens_do_not_hide_other_face_changes(token):
    parsed = parse_history_face_events(f"{epoch(20)}:2 {token} {epoch(8)}:1", FACES)
    assert len(parsed["face_events"]) == 2
    assert parsed["face_events_invalid_entries"] == 1
    assert not parsed["face_events_truncated"]


@pytest.mark.parametrize("value,count", [(None, 0), ("", 0), (" \t\n", 0), ({}, 1), ([], 1), (True, 1)])
def test_missing_or_invalid_field_remains_empty(value, count):
    parsed = parse_history_face_events(value, FACES)
    assert parsed["face_events"] == []
    assert parsed["face_events_invalid_entries"] == count


def test_unknown_index_preserved_without_inventing_a_face():
    parsed = parse_history_face_events(f"{epoch(23, 59)}:255", FACES)
    assert parsed["face_events"] == [
        {"clock": "23:59", "minute_offset": 719, "face_index": 255, "face": None},
    ]
    assert parsed["face_events_invalid_entries"] == 0


@pytest.mark.parametrize("faces", [None, {}, [None, {"index": True, "define": "FACE_DAY"}],
                                        [{"index": 1, "define": []}]])
def test_invalid_reference_mapping_does_not_fabricate_a_face(faces):
    parsed = parse_history_face_events(f"{epoch(0)}:1", faces)
    assert parsed["face_events"][0]["face"] is None
    assert parsed["face_events"][0]["minute_offset"] == 720


def test_mapping_is_supplied_per_device_not_global_mutable_state():
    source = f"{epoch(11, 59)}:8"
    first = parse_history_face_events(source, [{"index": 8, "define": "FACE_NIGHT"}])
    second = parse_history_face_events(source, [{"index": 8, "define": "FACE_DAY"}])
    assert first["face_events"][0]["face"] == "sleepy"
    assert second["face_events"][0]["face"] == "awake"
    assert first["face_events"][0]["minute_offset"] == 1439


def test_token_limit_keeps_prefix_and_explicitly_marks_truncation():
    parsed = parse_history_face_events(
        " ".join(f"{epoch(12) + index}:1" for index in range(MAX_HISTORY_FACE_EVENTS + 1)), FACES,
    )
    assert len(parsed["face_events"]) == MAX_HISTORY_FACE_EVENTS
    assert parsed["face_events_truncated"]
    assert parsed["face_events_invalid_entries"] == 0


def test_character_limit_never_interprets_a_cut_token():
    parsed = parse_history_face_events(f"{epoch(20)}:2 " + "1" * 70000 + ":1", FACES)
    assert len(parsed["face_events"]) == 1
    assert parsed["face_events"][0]["face"] == "sleepy"
    assert parsed["face_events_truncated"]
    assert parsed["face_events_invalid_entries"] == 0


async def test_catalogue_contains_markers_without_sleep_or_file_download(hass):
    client = SimpleNamespace(
        get_history_logs=AsyncMock(return_value=[{
            "objectId": "testlog1",
            "timestamp": {"__type": "Date", "iso": "2000-01-03T10:00:00Z"},
            "faceDataPsm": f"{epoch(21, 45)}:2 {epoch(8, 40)}:1",
        }]),
        get_history_sleep_info=AsyncMock(return_value=[]),
        get_history_file=AsyncMock(),
        request_history_sync=AsyncMock(),
    )
    device = SimpleNamespace(remi={"timezone": "Europe/Paris"}, faces=FACES)
    coordinator = RemiHistoryCoordinator(hass, client, device)
    result = await coordinator.async_get_history(limit=60, include_series=False)
    report = result["logs"][0]
    assert report["sleep_status"] == "unavailable"
    assert report["sleep_duration"] is report["sleep_bedtime"] is report["sleep_wake_time"] is None
    assert report["sleep_face_time"] is report["wake_face_time"] is None
    assert [event["clock"] for event in report["face_events"]] == ["21:45", "08:40"]
    assert "faceDataPsm" not in report and "series" not in report
    client.get_history_file.assert_not_called()
    client.request_history_sync.assert_not_called()
    # Service callers cannot mutate the coordinator's cached annotations.
    report["face_events"][0]["clock"] = "invalid"
    assert coordinator.data["logs"][0]["face_events"][0]["clock"] == "21:45"
