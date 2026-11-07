"""Cloud history scope, decoding, independent availability and bounded caching."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.urbanhello_remi_unofficial.const import API_BASE_URL
from custom_components.urbanhello_remi_unofficial.history import (
    HISTORY_INTERVAL,
    RemiHistoryCoordinator,
    decode_history_series,
    parse_history_datetime,
    parse_sleep_info,
)
from custom_components.urbanhello_remi_unofficial.history_api import (
    MAX_HISTORY_FILE_BYTES,
    RemiHistoryApiMixin,
    RemiHistoryError,
    history_file_url,
)
from custom_components.urbanhello_remi_unofficial.history_sensor import (
    HISTORY_SENSOR_DESCRIPTIONS,
    RemiHistorySensor,
)
from custom_components.urbanhello_remi_unofficial.sensor import SENSOR_DESCRIPTIONS, RemiSensorEntity

REMI_ID = "own-device"
OWNER = {"__type": "Pointer", "className": "Remi", "objectId": REMI_ID}
FILE = {"__type": "File", "name": "sample.bin", "url": f"{API_BASE_URL}/parse/files/app/sample.bin"}
SLEEP = {
    "objectId": "sleep1", "remi": OWNER, "bedTime": [21, 7], "wakeUpTime": [7, 30],
    "sleepDuration": [10, 23], "score": 85,
    "sleepFaceTime": {"__type": "Date", "iso": "2026-11-05T20:00:00Z"},
}
LOG = {
    "objectId": "log1", "remi": OWNER,
    "timestamp": {"__type": "Date", "iso": "2026-11-06T10:00:00Z"},
    "sleepInfo": {"__type": "Pointer", "className": "SleepInfo", "objectId": "sleep1"},
    "tempData": FILE, "data": {**FILE, "name": "noise.bin", "url": FILE["url"].replace("sample", "noise")},
    "updatedAt": "2026-11-06T10:01:00Z",
}


class FakeClient(RemiHistoryApiMixin):
    def __init__(self):
        self._remi_id = REMI_ID
        self._request = AsyncMock()
        self._session = MagicMock()


@pytest.mark.parametrize("limit", [0, 3, -1, True, 1.0, "1", None])
async def test_invalid_limit_never_calls_api(limit):
    client = FakeClient()
    with pytest.raises(RemiHistoryError):
        await client.get_history_logs(limit)
    client._request.assert_not_called()


async def test_queries_are_owned_bounded_and_reference_only():
    client = FakeClient()
    client._request.return_value = {"results": [LOG]}
    assert await client.get_history_logs() == [LOG]
    payload = client._request.call_args.args[2]
    assert payload == {
        "_method": "GET", "limit": 2, "order": "-timestamp",
        "where": {"$or": [{"remi": OWNER}, {"remi": REMI_ID}]},
    }
    client._request.return_value = {"results": [SLEEP]}
    assert await client.get_history_sleep_info(["sleep1"]) == [SLEEP]
    payload = client._request.call_args.args[2]
    assert payload["where"]["objectId"] == {"$in": ["sleep1"]}
    assert payload["where"]["$or"] == [{"remi": OWNER}, {"remi": REMI_ID}]
    client._request.reset_mock()
    assert await client.get_history_sleep_info([]) == []
    client._request.assert_not_called()


@pytest.mark.parametrize("results", [
    None, {}, "bad", [None], [{**LOG, "remi": "other"}],
    [{**LOG, "objectId": ""}], [LOG, LOG], [LOG, LOG, LOG],
    [{**LOG, "remi": {"objectId": REMI_ID, "className": "Other"}}],
])
async def test_malformed_or_cross_device_records_rejected(results):
    client = FakeClient()
    client._request.return_value = {"results": results}
    with pytest.raises(RemiHistoryError):
        await client.get_history_logs()


async def test_unrequested_sleep_rejected():
    client = FakeClient()
    client._request.return_value = {"results": [SLEEP]}
    with pytest.raises(RemiHistoryError):
        await client.get_history_sleep_info(["different"])


@pytest.mark.parametrize("ids", [None, "sleep1", ["sleep1"] * 3, ["../private"], [1], [True]])
async def test_malformed_sleep_reference_rejected_before_api(ids):
    client = FakeClient()
    with pytest.raises(RemiHistoryError):
        await client.get_history_sleep_info(ids)
    client._request.assert_not_called()


@pytest.mark.parametrize("value", [None, "", "invalid", "2026-11-06", "2026-11-06T10:00:00", "0001-01-01T00:00:00+01:00", {}, {"iso": "2026-11-06T10:00:00Z"}])
def test_unknown_dates_do_not_gain_an_invented_timezone(value):
    assert parse_history_datetime(value) is None


def test_dates_normalize_utc_without_losing_instant():
    assert parse_history_datetime("2026-11-06T11:00:00+01:00") == datetime(2026, 11, 6, 10, tzinfo=timezone.utc)


def test_sleep_pairs_duration_and_zero_are_preserved():
    result = parse_sleep_info(SLEEP)
    assert result["sleep_bedtime"] == "21:07"
    assert result["sleep_wake_time"] == "07:30"
    assert result["sleep_duration"] == 623
    assert result["sleep_score"] == 85
    zero = parse_sleep_info({"bedTime": [0, 0], "sleepDuration": [0, 0], "score": 0})
    assert zero["sleep_bedtime"] == "00:00"
    assert zero["sleep_duration"] == zero["sleep_score"] == 0


@pytest.mark.parametrize("pair", [None, [], [0], [0, 0, 0], [24, 0], [0, 60], [-1, 0], [True, 0], [0, 1.0], "21:00"])
def test_malformed_sleep_pairs_are_unknown(pair):
    parsed = parse_sleep_info({"bedTime": pair, "wakeUpTime": pair, "sleepDuration": pair})
    assert parsed["sleep_bedtime"] is None
    assert parsed["sleep_wake_time"] is None
    assert parsed["sleep_duration"] is None


@pytest.mark.parametrize("score", [None, True, -1, 101, 4.2, "85"])
def test_malformed_score_is_unknown(score):
    assert parse_sleep_info({"score": score})["sleep_score"] is None


def test_decode_exact_chart_scale_without_inventing_sample_dates():
    body = bytes([0, 50, 160, 255]) + bytes(716)
    series = decode_history_series("temperature", body)
    assert series["unit"] == "°C"
    assert series["conversion"] == "raw * 50 / 255 - 10"
    assert series["samples"][2]["value"] == pytest.approx(21.3725)
    assert series["samples"][0]["value"] == -10
    assert series["samples"][3]["value"] == 40
    assert series["samples"][2]["raw_value"] == 160
    assert series["samples"][0]["clock"] == "12:00"
    assert series["samples"][-1]["clock"] == "11:58"
    assert series["samples"][-1]["minute_offset"] == 1438
    assert series["absolute_sample_timestamps"] is False
    assert all("timestamp" not in point for point in series["samples"])


def test_light_is_overlay_not_lux_and_noise_not_db():
    light = decode_history_series("light", bytes([0, 1, 7, 8, 255]) + bytes(715))
    assert [p["graph_value"] for p in light["samples"][:5]] == [0, 100, 100, 0, 0]
    assert [p["value"] for p in light["samples"][:5]] == [0, 1, 7, 8, 255]
    assert light["unit"] is None
    noise = decode_history_series("noise", bytes(720))
    assert noise["samples"][0]["value"] == 0
    assert noise["unit"] is None


@pytest.mark.parametrize("body", [bytes(1), bytes(719), bytes(721), bytes(2048), "bad", [0] * 720])
def test_invalid_binary_lengths_do_not_change_grid(body):
    with pytest.raises(RemiHistoryError):
        decode_history_series("temperature", body)


def test_empty_file_is_empty_not_720_zeroes():
    assert decode_history_series("temperature", b"") == {"status": "empty", "samples": []}


@pytest.mark.parametrize("url", [
    "http://remi2.urbanhello.com/parse/files/app/sample.bin",
    "https://evil.invalid/parse/files/app/sample.bin",
    "https://127.0.0.1/parse/files/app/sample.bin",
    "https://remi2.urbanhello.com.evil.invalid/parse/files/app/sample.bin",
    "https://user:password@remi2.urbanhello.com/parse/files/app/sample.bin",
    "https://remi2.urbanhello.com:444/parse/files/app/sample.bin",
    f"{API_BASE_URL}/parse/classes/sample.bin",
    f"{API_BASE_URL}/parse/files/../sample.bin",
    f"{API_BASE_URL}/parse/files/%2e%2e/sample.bin",
    f"{API_BASE_URL}/parse/files/%252e%252e/sample.bin",
    f"{FILE['url']}?token=private", f"{FILE['url']}#fragment",
    f"{API_BASE_URL}/parse/files/app/other.bin",
])
async def test_file_url_rejects_ssrf_and_never_opens_session(url):
    client = FakeClient()
    with pytest.raises(RemiHistoryError):
        await client.get_history_file({**FILE, "url": url})
    client._session.get.assert_not_called()


def test_valid_file_url():
    assert history_file_url(FILE) == FILE["url"]


def _response(client, chunks=(), status=200, length=None):
    response = MagicMock()
    response.status = status
    response.content_length = length
    async def iterate(_):
        for chunk in chunks:
            yield chunk
    response.content.iter_chunked = iterate
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=False)
    client._session.get.return_value = context
    return context


async def test_file_fragmentation_no_auth_headers_and_context_closed():
    client = FakeClient()
    context = _response(client, [bytes(100), bytes([160]) * 620])
    body = await client.get_history_file(FILE)
    assert len(body) == 720 and body[-1] == 160
    kwargs = client._session.get.call_args.kwargs
    assert kwargs["allow_redirects"] is False
    assert kwargs["headers"] == {"Accept": "application/octet-stream", "Accept-Encoding": "identity"}
    assert kwargs["auto_decompress"] is False
    context.__aexit__.assert_awaited_once()


@pytest.mark.parametrize("status,length,chunks", [
    (302, None, []), (500, None, []), (200, MAX_HISTORY_FILE_BYTES + 1, []),
    (200, None, [bytes(MAX_HISTORY_FILE_BYTES), b"x"]),
])
async def test_file_redirect_error_or_size_limit_closes_response(status, length, chunks):
    client = FakeClient()
    context = _response(client, chunks, status, length)
    with pytest.raises(RemiHistoryError):
        await client.get_history_file(FILE)
    context.__aexit__.assert_awaited_once()


@pytest.mark.parametrize("error", [TimeoutError(), aiohttp.ClientConnectionError("private URL")])
async def test_file_timeout_is_sanitized(hass, error):
    client = FakeClient()
    context = _response(client)
    context.__aenter__.side_effect = error
    with pytest.raises(RemiHistoryError) as caught:
        await client.get_history_file(FILE)
    assert caught.value.translation_key == "history_request_failed"
    assert "private" not in str(caught.value)


def _coordinator(hass):
    client = MagicMock()
    client.get_history_logs = AsyncMock(return_value=[deepcopy(LOG)])
    client.get_history_sleep_info = AsyncMock(return_value=[deepcopy(SLEEP)])
    client.get_history_file = AsyncMock(return_value=bytes([160]) * 720)
    device = MagicMock()
    device.remi = {"objectId": REMI_ID, "name": "Test REMI", "timezone": "Europe/Paris", "online": False}
    device.last_update_success = True
    return RemiHistoryCoordinator(hass, client, device)


async def test_metadata_poll_does_not_download_and_sleep_survives_device_offline(hass):
    coordinator = _coordinator(hass)
    await coordinator.async_refresh()
    coordinator.client.get_history_file.assert_not_called()
    description = next(d for d in HISTORY_SENSOR_DESCRIPTIONS if d.key == "sleep_duration")
    sensor = RemiHistorySensor(coordinator, description)
    assert sensor.native_value == 623
    assert sensor.available is True
    assert sensor.unique_id == f"{REMI_ID}_sleep_duration"
    assert sensor.extra_state_attributes["log_timestamp"] == "2026-11-06T10:00:00+00:00"


async def test_history_failure_does_not_disable_controls_or_relabel_old_data(hass):
    coordinator = _coordinator(hass)
    await coordinator.async_refresh()
    old_data = deepcopy(coordinator.data)
    coordinator.client.get_history_logs.side_effect = RemiHistoryError("test")
    await coordinator.async_refresh()
    assert coordinator.last_update_success is False
    assert coordinator.device_coordinator.last_update_success is True
    assert coordinator.data == old_data
    with pytest.raises(RemiHistoryError):
        await coordinator.async_get_history()


async def test_history_response_cache_missing_files_no_urls_or_retimestamps(hass):
    coordinator = _coordinator(hass)
    first = await coordinator.async_get_history()
    assert coordinator.client.get_history_file.await_count == 2
    assert first["absolute_sample_timestamps"] is False
    assert first["logs"][0]["series"]["light"]["status"] == "missing"
    assert "https://" not in repr(first)
    assert "objectId" not in repr(first)
    first["logs"][0]["sleep_duration"] = -1
    second = await coordinator.async_get_history()
    assert coordinator.client.get_history_file.await_count == 2
    assert second["logs"][0]["sleep_duration"] == 623


async def test_expired_failed_cache_is_not_returned_as_fresh(hass):
    coordinator = _coordinator(hass)
    await coordinator.async_get_history()
    coordinator._file_cache = type(coordinator._file_cache)(
        (key, (-HISTORY_INTERVAL.total_seconds(), value[1])) for key, value in coordinator._file_cache.items()
    )
    coordinator.client.get_history_file.side_effect = RemiHistoryError("test")
    result = await coordinator.async_get_history()
    assert result["logs"][0]["series"]["temperature"]["status"] == "unavailable"
    assert result["logs"][0]["sleep_duration"] == 623
    assert not coordinator._file_cache


async def test_empty_history_clears_previous_report(hass):
    coordinator = _coordinator(hass)
    await coordinator.async_refresh()
    coordinator.client.get_history_logs.return_value = []
    coordinator.client.get_history_sleep_info.return_value = []
    await coordinator.async_refresh()
    assert coordinator.latest_report == {}
    assert (await coordinator.async_get_history())["logs"] == []


async def test_aged_report_is_explicitly_stale(hass):
    coordinator = _coordinator(hass)
    await coordinator.async_refresh()
    coordinator.data["logs"][0]["log_timestamp"] = "2001-01-01T12:00:00+00:00"
    sensor = RemiHistorySensor(coordinator, HISTORY_SENSOR_DESCRIPTIONS[0])
    assert sensor.native_value == 623
    assert sensor.extra_state_attributes["stale"] is True
    assert sensor.extra_state_attributes["report_age_days"] > 2


@pytest.mark.parametrize("key,available", [("temperature", False), ("rssi", False), ("current_face", False), ("firmware_version", True), ("ip_address", True)])
def test_only_live_sensors_require_online_device(key, available):
    coordinator = MagicMock()
    coordinator.remi = {"objectId": REMI_ID, "online": False}
    coordinator.last_update_success = True
    sensor = RemiSensorEntity(coordinator, next(d for d in SENSOR_DESCRIPTIONS if d.key == key))
    assert sensor.available is available


@pytest.mark.parametrize("pointer", [None, True, "bad", [], 7, {"objectId": []}])
def test_malformed_face_is_unknown_not_a_sensor_crash(pointer):
    description = next(d for d in SENSOR_DESCRIPTIONS if d.key == "current_face")
    assert description.value_fn({"face": pointer}) is None
