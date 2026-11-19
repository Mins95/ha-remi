"""Exercise an outage through HA's config entry, entity registry and services."""
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial.api import RemiApiError, RemiAuthError
from custom_components.urbanhello_remi_unofficial.const import API_BASE_URL, DOMAIN, FACE_DEFINE_TO_OBJECT_ID

from .conftest import MOCK_EVENT_DATA, MOCK_REMI_DATA, MOCK_REMI_ID


@pytest.fixture(autouse=True)
def enable_custom_components(enable_custom_integrations):
    yield


async def test_cached_startup_read_history_recover_and_remove(hass, hass_storage, mock_api_client, mock_config_entry_data):
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, unique_id=MOCK_REMI_ID)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    mock_api_client.get_remi.return_value = {**MOCK_REMI_DATA, "timezone": "Europe/Paris"}
    morning = MOCK_EVENT_DATA[0]
    evening = {
        **morning, "objectId": "evening", "name": "Bedtime", "event_time": [20, 15],
        "face": {"objectId": FACE_DEFINE_TO_OBJECT_ID["FACE_NIGHT"]},
    }
    mock_api_client.get_events.return_value = [morning, evening]
    timestamp = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    mock_api_client.get_history_logs.return_value = [{
        "objectId": "night", "timestamp": {"__type": "Date", "iso": timestamp},
        "updatedAt": timestamp, "tempData": {
            "__type": "File", "name": "sample.bin", "url": f"{API_BASE_URL}/parse/files/app/sample.bin",
        },
    }]
    mock_api_client.get_history_file.return_value = bytes([160]) * 720
    selected = {"remi_id": MOCK_REMI_ID, "report_id": "night", "include_series": True}
    with patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        response = await hass.services.async_call(DOMAIN, "get_history", selected, blocking=True, return_response=True)
        known_samples = response["logs"][0]["series"]["temperature"]["samples"]
        assert len(known_samples) == 720
        ids = {
            key: registry.async_get_entity_id(domain, DOMAIN, f"{MOCK_REMI_ID}_{key}")
            for domain, key in (
                ("sensor", "next_wake"), ("sensor", "next_bedtime"),
                ("sensor", "temperature"), ("number", "brightness"), ("switch", "alarm_event_id_1"),
            )
        }
        assert all(ids.values())
        first = hass.states.get(ids["next_wake"])
        assert first.state not in ("unknown", "unavailable")
        assert first.attributes["cached"] is False
        assert await hass.config_entries.async_unload(entry.entry_id)

        outage = RemiApiError("Simulated cloud outage")
        for read in (mock_api_client.get_events, mock_api_client.get_remi, mock_api_client.get_history_logs):
            read.side_effect = outage
        mock_api_client.get_history_file.reset_mock()
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED
        for key in ("next_wake", "next_bedtime"):
            forecast = hass.states.get(ids[key])
            assert forecast.attributes["cached"] is True
            assert forecast.state not in ("unknown", "unavailable")
            assert forecast.attributes["synced_at"] == first.attributes["synced_at"]
        assert hass.states.get(ids["next_wake"]).state == first.state
        for key in ("temperature", "brightness", "alarm_event_id_1"):
            state = hass.states.get(ids[key])
            assert state is None or state.state == "unavailable"
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(DOMAIN, "update_alarm", {"event_id": morning["objectId"], "enabled": False}, blocking=True)
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(DOMAIN, "create_alarm", {"name": "Offline", "time": "11:30"}, blocking=True)
        mock_api_client.update_event.assert_not_awaited()
        mock_api_client.create_event.assert_not_awaited()
        response = await hass.services.async_call(DOMAIN, "get_history", selected, blocking=True, return_response=True)
        series = response["logs"][0]["series"]["temperature"]
        assert series["source"] == "local_archive"
        assert series["samples"] == known_samples
        mock_api_client.get_history_file.assert_not_awaited()

        for read in (mock_api_client.get_remi, mock_api_client.get_history_logs, mock_api_client.get_events):
            read.side_effect = None
        mock_api_client.get_events.return_value = [{**morning, "name": "Updated in app"}, evening]
        await hass.data[DOMAIN][entry.entry_id].async_refresh()
        await hass.async_block_till_done()
        recovered = hass.states.get(ids["next_wake"])
        assert recovered.attributes["cached"] is False
        assert recovered.attributes["alarm_name"] == "Updated in app"
        assert hass.states.get(ids["alarm_event_id_1"]).state == "on"
        assert hass.states.get(ids["temperature"]).state != "unavailable"
        mock_api_client.create_event.assert_not_awaited()
        await hass.config_entries.async_remove(entry.entry_id)
        await hass.async_block_till_done()
        for store in ("alarm_identity", "schedule", "history"):
            assert f"{DOMAIN}.{store}.{entry.entry_id}" not in hass_storage


async def test_auth_rejection_even_with_confirmed_schedule(hass, mock_api_client, mock_config_entry_data):
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, unique_id=MOCK_REMI_ID)
    entry.add_to_hass(hass)
    with patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.data[DOMAIN][entry.entry_id].schedule_snapshot.synced_at is not None
        assert await hass.config_entries.async_unload(entry.entry_id)
        mock_api_client.get_remi.side_effect = RemiAuthError("Access revoked")
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert any(flow["context"]["source"] == "reauth" and flow["context"]["entry_id"] == entry.entry_id
               for flow in hass.config_entries.flow.async_progress())
