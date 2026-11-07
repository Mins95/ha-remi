"""Exercise new public actions without contacting or changing a physical REMI."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from custom_components.urbanhello_remi_unofficial import (
    _register_services, async_unload_entry,
)
from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.nap import async_register_nap_services


def make_coordinator(remi_id, event_id="alarm"):
    result = MagicMock(events=[{"objectId": event_id}], async_request_refresh=AsyncMock())
    result.client.remi_id = remi_id
    result.client.create_event = AsyncMock()
    result.client.update_event = AsyncMock()
    result.client.delete_event = AsyncMock()
    result.client.get_events = AsyncMock(return_value=[{"objectId": event_id, "cmd": 15}])
    result.history_coordinator.async_get_history = AsyncMock(return_value={"reports": []})
    result.history_coordinator.async_shutdown = AsyncMock()
    return result


@pytest.fixture
def coordinator(hass):
    result = make_coordinator("remi-one")
    hass.data[DOMAIN] = {"one": result}
    _register_services(hass)
    return result


async def test_create_extended_alarm_uses_minutes_and_default_flags(hass, coordinator):
    await hass.services.async_call(DOMAIN, "create_alarm", {
        "name": "Bedtime", "time": "20:15", "repeat": [0, 1, 2, 3, 4],
        "brightness": 12, "volume": 20, "music_path": "Music/lullaby.mp3",
        "music_duration_minutes": 15, "play_button_enabled": False, "remi_id": "remi-one",
    }, blocking=True)
    coordinator.client.create_event.assert_awaited_once_with({
        "name": "Bedtime", "event_time": [20, 15], "enabled": True,
        "recurrence": [1, 1, 1, 1, 0, 0, 1], "brightness": 12, "volume": 20,
        "music_path": "Music/lullaby.mp3", "length_min": 15, "cmd": 11,
    })


@pytest.mark.parametrize("command,enabled,expected", [
    (10, True, 14), (11, True, 15), (14, False, 10), (15, False, 11),
])
async def test_play_change_preserves_latest_other_flags(hass, coordinator, command, enabled, expected):
    coordinator.events = [{"objectId": "alarm", "cmd": 15}]
    coordinator.client.get_events.return_value = [{"objectId": "alarm", "cmd": command}]
    await hass.services.async_call(DOMAIN, "update_alarm", {
        "event_id": "alarm", "play_button_enabled": enabled,
    }, blocking=True)
    coordinator.client.get_events.assert_awaited_once()
    coordinator.client.update_event.assert_awaited_once_with("alarm", {"cmd": expected})


@pytest.mark.parametrize("command", [None, 0, 1, 20, "15", True])
async def test_unknown_play_flags_do_not_write_or_change_other_settings(hass, coordinator, command):
    coordinator.client.get_events.return_value = [{"objectId": "alarm", "cmd": command}]
    with pytest.raises(ServiceValidationError) as error:
        await hass.services.async_call(DOMAIN, "update_alarm", {
            "event_id": "alarm", "play_button_enabled": True, "brightness": 20,
        }, blocking=True)
    assert error.value.translation_key == "unknown_alarm_play_settings"
    coordinator.client.update_event.assert_not_awaited()


async def test_alarm_deleted_in_app_during_play_edit_is_not_recreated(hass, coordinator):
    coordinator.client.get_events.return_value = []
    with pytest.raises(ServiceValidationError) as error:
        await hass.services.async_call(DOMAIN, "update_alarm", {
            "event_id": "alarm", "play_button_enabled": True,
        }, blocking=True)
    assert error.value.translation_key == "alarm_not_found"
    coordinator.client.update_event.assert_not_awaited()


async def test_partial_music_edit_does_not_reconstruct_alarm(hass, coordinator):
    await hass.services.async_call(DOMAIN, "update_alarm", {
        "event_id": "alarm", "music_path": "", "music_duration_minutes": 0,
    }, blocking=True)
    coordinator.client.get_events.assert_not_awaited()
    coordinator.client.update_event.assert_awaited_once_with("alarm", {"music_path": "", "length_min": 0})


@pytest.mark.parametrize("field,value", [
    ("brightness", -1), ("brightness", 101), ("brightness", 12.7),
    ("volume", True), ("music_duration_minutes", 1441), ("music_duration_minutes", 0.5),
    ("music_path", "https://example.invalid/audio.mp3"), ("music_path", "../private"),
    ("music_path", "pause:123"), ("face_define", "unknown"),
])
async def test_invalid_alarm_fields_cannot_produce_partial_writes(hass, coordinator, field, value):
    with pytest.raises((vol.Invalid, HomeAssistantError)):
        await hass.services.async_call(DOMAIN, "update_alarm", {
            "event_id": "alarm", field: value,
        }, blocking=True)
    coordinator.client.update_event.assert_not_awaited()


async def test_multiple_devices_require_and_respect_explicit_create_target(hass, coordinator):
    second = make_coordinator("remi-two", "alarm-two")
    hass.data[DOMAIN]["two"] = second
    data = {"name": "Morning", "time": "07:30"}
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "create_alarm", data, blocking=True)
    coordinator.client.create_event.assert_not_awaited()
    second.client.create_event.assert_not_awaited()
    await hass.services.async_call(DOMAIN, "create_alarm", {**data, "remi_id": "remi-two"}, blocking=True)
    second.client.create_event.assert_awaited_once()
    coordinator.client.create_event.assert_not_awaited()
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "delete_alarm", {
            "event_id": "alarm-two", "remi_id": "remi-one",
        }, blocking=True)
    second.client.delete_event.assert_not_awaited()


async def test_get_history_response_targets_one_remi_and_never_writes(hass, coordinator):
    response = await hass.services.async_call(DOMAIN, "get_history", {
        "remi_id": "remi-one", "limit": 1,
    }, blocking=True, return_response=True)
    assert response == {"reports": []}
    coordinator.history_coordinator.async_get_history.assert_awaited_once_with(1)
    coordinator.client.update_event.assert_not_awaited()
    coordinator.client.create_event.assert_not_awaited()


@pytest.mark.parametrize("limit", [0, 3, 1.5, True])
async def test_history_rejects_out_of_budget_or_fractional_limits(hass, coordinator, limit):
    with pytest.raises((vol.Invalid, HomeAssistantError)):
        await hass.services.async_call(DOMAIN, "get_history", {"limit": limit},
                                       blocking=True, return_response=True)
    coordinator.history_coordinator.async_get_history.assert_not_awaited()


async def test_unload_stops_history_and_removes_services_only_after_last_entry(hass, coordinator):
    second = make_coordinator("remi-two", "alarm-two")
    hass.data[DOMAIN]["two"] = second
    async_register_nap_services(hass)
    with patch.object(hass.config_entries, "async_unload_platforms", return_value=True):
        assert await async_unload_entry(hass, MagicMock(entry_id="one"))
        coordinator.history_coordinator.async_shutdown.assert_awaited_once()
        assert hass.services.has_service(DOMAIN, "get_history")
        assert hass.services.has_service(DOMAIN, "list_naps")
        assert await async_unload_entry(hass, MagicMock(entry_id="two"))
        second.history_coordinator.async_shutdown.assert_awaited_once()
    for service in ("get_history", "create_alarm", "update_alarm", "delete_alarm", "list_naps", "create_nap", "update_nap", "delete_nap"):
        assert not hass.services.has_service(DOMAIN, service)
