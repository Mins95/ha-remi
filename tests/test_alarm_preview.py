"""Test the live device command separately from the scheduled Event."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.urbanhello_remi_unofficial import _register_services
from custom_components.urbanhello_remi_unofficial.api import RemiApiClient, RemiApiError
from custom_components.urbanhello_remi_unofficial.const import DOMAIN


@pytest.fixture
def client():
    api = RemiApiClient("", "", MagicMock())
    api.set_remi_id("device1")
    api.get_remi = AsyncMock(return_value={"objectId": "device1", "online": True})
    api.get_events = AsyncMock(return_value=[{"objectId": "alarm1", "volume": 10}])
    api._request = AsyncMock(return_value={"updatedAt": "2026-11-27T10:00:00Z"})
    return api


async def test_service_uses_current_alarm_and_only_writes_live_device(hass, client, monkeypatch):
    face = {"__type": "Pointer", "className": "Face", "objectId": "rnAltoFwYC"}
    current_event = {"objectId": "alarm1", "enabled": False, "face": face, "brightness": 0,
                     "volume": 20, "music_path": "Music/goodnight.mp3", "length_min": 30, "cmd": 14}
    client.get_events.return_value = [current_event]
    coordinator = MagicMock(client=client, events=[{"objectId": "alarm1", "volume": 80}],
                            events_available=True, last_update_success=True)
    coordinator.async_request_refresh = AsyncMock()
    unrelated = MagicMock()
    unrelated.client.remi_id = "device2"
    hass.data[DOMAIN] = {"entry1": coordinator, "entry2": unrelated}
    _register_services(hass)
    monkeypatch.setattr("random.randrange", lambda _: 57)
    await hass.services.async_call(DOMAIN, "test_alarm", {"remi_id": "device1", "event_id": "alarm1"},
                                   blocking=True)
    client._request.assert_awaited_once_with("PUT", "/parse/classes/Remi/device1", {
        "face": face, "luminosity": 0, "volume": 20, "musicPath": "Music/goodnight.mp3:57"})
    coordinator.async_request_refresh.assert_awaited_once()
    unrelated.client.async_test_alarm.assert_not_called()
    assert not current_event["enabled"]


@pytest.mark.parametrize(("updates", "error"), [
    ({"face": {"className": "Remi", "objectId": "rnAltoFwYC"}}, "alarm_test_invalid_settings"),
    ({"volume": True}, "alarm_test_invalid_settings"),
    ({"brightness": 101}, "alarm_test_invalid_settings"),
    ({"music_path": "../track.mp3"}, "invalid_music_path"),
    ({"music_path": "stop"}, "invalid_music_path"),
    ({"volume": None, "music_path": ""}, "alarm_test_empty"),
    ({"objectId": "new_event_id"}, "alarm_not_found"),
])
async def test_invalid_or_replaced_event_sends_nothing(client, updates, error):
    client.get_events.return_value[0].update(updates)
    with pytest.raises(HomeAssistantError) as caught:
        await client.async_test_alarm("alarm1")
    assert caught.value.translation_key == error
    client._request.assert_not_awaited()


@pytest.mark.parametrize("connection", [{"online": False}, {}, {"online": True, "alive": False}])
async def test_offline_or_unknown_connection_sends_nothing(client, connection):
    client.get_remi.return_value = connection
    with pytest.raises(HomeAssistantError) as caught:
        await client.async_test_alarm("alarm1")
    assert caught.value.translation_key == "alarm_test_offline"
    client._request.assert_not_awaited()


async def test_double_call_during_preview_does_not_replay_command(client):
    started = asyncio.Event()
    finish = asyncio.Event()

    async def read_live_device():
        started.set()
        await finish.wait()
        return {"online": True}

    client.get_remi.side_effect = read_live_device
    first = asyncio.create_task(client.async_test_alarm("alarm1"))
    await started.wait()
    try:
        with pytest.raises(HomeAssistantError) as caught:
            await client.async_test_alarm("alarm1")
        assert caught.value.translation_key == "alarm_test_running"
    finally:
        finish.set()
        await first
    client._request.assert_awaited_once_with("PUT", "/parse/classes/Remi/device1", {"volume": 10})


async def test_failed_device_write_propagates_and_unlocks(client):
    client._request.side_effect = RemiApiError("write failed")
    with pytest.raises(RemiApiError):
        await client.async_test_alarm("alarm1")
    client._request.assert_awaited_once()
    client._request.side_effect = None
    await client.async_test_alarm("alarm1")
    assert client._request.await_count == 2
