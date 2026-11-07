"""Reconcile only validated cloud snapshots and preserve user-owned metadata."""
from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.entity import RemiEntity
from custom_components.urbanhello_remi_unofficial.switch import RemiAlarmSwitchEntity
from custom_components.urbanhello_remi_unofficial.switch import async_setup_entry as setup_switch
from custom_components.urbanhello_remi_unofficial.time import async_setup_entry as setup_time

from .conftest import MOCK_EVENT_DATA, MOCK_REMI_DATA, MOCK_REMI_ID


@pytest.fixture(autouse=True)
def enable_integration(enable_custom_integrations):
    yield


@pytest.mark.parametrize(
    ("data", "cloud_ok", "expected"),
    [({}, True, True), ({"online": True, "alive": True}, True, True),
     ({"online": False}, True, False), ({"alive": False}, True, False),
     ({"online": True, "alive": True}, False, False)],
)
def test_device_availability_does_not_change_cloud_availability(data, cloud_ok, expected):
    coordinator = MagicMock(remi={"objectId": MOCK_REMI_ID, **data}, last_update_success=cloud_ok)
    entity = RemiEntity(coordinator)
    assert entity.device_available is expected
    assert entity.available is cloud_ok


@pytest.mark.parametrize("setup, domain, suffix", [(setup_switch, "switch", ""), (setup_time, "time", "_time")])
@pytest.mark.parametrize("events, fresh", [(None, True), ({}, True), ([None], True), ([{"objectId": ""}], True), ([{"objectId": "a"}, {"objectId": "a"}], True), ([], False)])
async def test_bad_or_stale_snapshot_never_removes_registry_entries(hass, setup, domain, suffix, events, fresh):
    entry = MockConfigEntry(domain=DOMAIN, data={}, title="REMI")
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    old = registry.async_get_or_create(
        domain, DOMAIN, f"{MOCK_REMI_ID}_alarm_old{suffix}", config_entry=entry,
    )
    coordinator = MagicMock(
        remi=MOCK_REMI_DATA, events=events, last_update_success=True, events_available=fresh,
        client=MagicMock(remi_id=MOCK_REMI_ID),
    )
    hass.data[DOMAIN] = {entry.entry_id: coordinator}
    add = MagicMock()
    await setup(hass, entry, add)
    assert registry.async_get(old.entity_id) == old
    add.assert_not_called()


async def test_app_rename_and_offline_deletion_preserve_ids_and_user_names(
    hass, mock_api_client, mock_config_entry_data,
):
    hass.config.language = "fr"
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, unique_id=MOCK_REMI_ID)
    entry.add_to_hass(hass)
    other = MockConfigEntry(domain=DOMAIN, data={}, title="Other")
    other.add_to_hass(hass)
    registry = er.async_get(hass)
    protected = [
        registry.async_get_or_create("switch", DOMAIN, f"{MOCK_REMI_ID}_alarm_foreign", config_entry=other),
        registry.async_get_or_create("switch", DOMAIN, "other_remi_alarm_old", config_entry=entry),
        registry.async_get_or_create("number", DOMAIN, f"{MOCK_REMI_ID}_volume", config_entry=entry),
        registry.async_get_or_create("time", DOMAIN, f"{MOCK_REMI_ID}_unrelated", config_entry=entry),
    ]
    events = deepcopy(MOCK_EVENT_DATA)
    mock_api_client.get_events.return_value = events
    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        switch_id = registry.async_get_entity_id("switch", DOMAIN, f"{MOCK_REMI_ID}_alarm_event_id_1")
        time_id = registry.async_get_entity_id("time", DOMAIN, f"{MOCK_REMI_ID}_alarm_event_id_1_time")
        registry.async_update_entity(switch_id, name="Mon nom personnel")
        saved_switch = registry.async_get(switch_id)
        saved_time = registry.async_get(time_id)
        events[0]["name"] = "Réveil du week-end"
        events[0]["event_time"] = [9, 0]
        await hass.data[DOMAIN][entry.entry_id].async_refresh()
        await hass.async_block_till_done()
        assert registry.async_get(switch_id).id == saved_switch.id
        assert registry.async_get(time_id).id == saved_time.id
        assert registry.async_get(switch_id).original_name == "09:00 · Réveil du week-end"
        assert registry.async_get(switch_id).name == "Mon nom personnel"
        assert registry.async_get(time_id).original_name == "Heure de Réveil du week-end"
        assert hass.states.get(switch_id).attributes["friendly_name"] == "Remi Bedroom Mon nom personnel"

        assert await hass.config_entries.async_unload(entry.entry_id)
        mock_api_client.get_events.return_value = []  # Deleted in the app while HA was stopped.
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert registry.async_get(switch_id) is None
        assert registry.async_get(time_id) is None
        assert all(registry.async_get(entity.entity_id) is not None for entity in protected)
        mock_api_client.update_event.assert_not_awaited()
        mock_api_client.delete_event.assert_not_awaited()


@pytest.mark.parametrize("value", [[7, "30"], [24, 0], [7, 60], [7, 30, 0], [True, 0]])
def test_malformed_alarm_time_does_not_break_switch_state(value):
    event = {**MOCK_EVENT_DATA[0], "event_time": value}
    coordinator = MagicMock(remi=MOCK_REMI_DATA, events=[event])
    entity = RemiAlarmSwitchEntity(coordinator, event)
    assert "time" not in entity.extra_state_attributes


@pytest.mark.parametrize("command, expected", [(10, False), (11, False), (14, True), (15, True), (None, None), (True, None), (12, None), ("15", None)])
def test_alarm_card_fields_preserve_cloud_values(command, expected):
    event = {**MOCK_EVENT_DATA[0], "cmd": command, "music_path": "Music/lullaby.mp3"}
    coordinator = MagicMock(remi=MOCK_REMI_DATA, events=[event])
    entity = RemiAlarmSwitchEntity(coordinator, event)
    attrs = entity.extra_state_attributes
    assert attrs["alarm_name"] == event["name"]
    assert attrs["music_path"] == "Music/lullaby.mp3"
    assert attrs["play_button_enabled"] is expected
