"""Real HA service registry tests for stored nap profiles."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import voluptuous as vol
from homeassistant.exceptions import ServiceValidationError

from custom_components.urbanhello_remi_unofficial.const import DOMAIN, FACE_DEFINE_TO_OBJECT_ID
from custom_components.urbanhello_remi_unofficial.nap import (
    CREATE_NAP_SCHEMA, async_register_nap_services, async_unregister_nap_services,
)


@pytest.fixture
def coordinator(hass):
    client = MagicMock(remi_id="remi1")
    client.get_naps = AsyncMock(return_value=[{
        "objectId": "nap1", "name": "Afternoon", "duration": [1, 15],
        "face": {"objectId": FACE_DEFINE_TO_OBJECT_ID["FACE_NIGHT"]},
        "brightness": 30, "sleepAid": 1, "volumeStart": 40,
        "lengthStart": 10, "ACL": {"private": True}, "secret": "not returned",
    }])
    client.create_nap = AsyncMock(return_value={"objectId": "new"})
    client.update_nap = AsyncMock(return_value={})
    client.delete_nap = AsyncMock(return_value={})
    coordinator = MagicMock(client=client)
    hass.data[DOMAIN] = {"entry1": coordinator}
    async_register_nap_services(hass)
    return coordinator


async def test_list_response_sanitized_and_minutes(hass, coordinator):
    result = await hass.services.async_call(DOMAIN, "list_naps", {}, blocking=True, return_response=True)
    profile = result["profiles"][0]
    assert profile["nap_id"] == "nap1"
    assert profile["duration_minutes"] == 75
    assert profile["music_duration_start_minutes"] == 10
    assert profile["face"] == "sleepy"
    assert profile["sleep_aid"] is True
    assert "ACL" not in profile and "secret" not in profile
    assert "remaining" not in profile and "running" not in profile


async def test_create_maps_app_fields_and_response(hass, coordinator):
    result = await hass.services.async_call(DOMAIN, "create_nap", {
        "name": "Nap", "duration_minutes": 95, "face": "sleepy",
        "music_path_start": "Music/a.mp3", "volume_start": 25,
        "music_duration_start_minutes": 12, "sleep_aid": True,
    }, blocking=True, return_response=True)
    payload = coordinator.client.create_nap.call_args.args[0]
    assert payload["duration"] == [1, 35]
    assert payload["lengthStart"] == 12
    assert payload["volumeStart"] == 25
    assert payload["musicPathStart"] == "Music/a.mp3"
    assert payload["face"]["objectId"] == FACE_DEFINE_TO_OBJECT_ID["FACE_NIGHT"]
    assert payload["sleepAid"] == 1
    assert result == {"nap_id": "new"}


async def test_update_only_supplied_fields_and_no_countdown(hass, coordinator):
    await hass.services.async_call(DOMAIN, "update_nap", {"nap_id": "nap1", "duration_minutes": 40}, blocking=True)
    coordinator.client.update_nap.assert_awaited_once_with("nap1", {"duration": [0, 40]})
    assert not hass.services.has_service(DOMAIN, "start_nap")
    assert not hass.services.has_service(DOMAIN, "stop_nap")


async def test_empty_update_refused(hass, coordinator):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "update_nap", {"nap_id": "nap1"}, blocking=True)
    coordinator.client.update_nap.assert_not_called()


async def test_multi_device_requires_target_and_resolves_current_entry(hass, coordinator):
    other = MagicMock(client=MagicMock(remi_id="remi2"))
    other.client.get_naps = AsyncMock(return_value=[])
    hass.data[DOMAIN]["entry2"] = other
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "list_naps", {}, blocking=True, return_response=True)
    result = await hass.services.async_call(DOMAIN, "list_naps", {"remi_id": "remi2"}, blocking=True, return_response=True)
    assert result == {"profiles": []}
    coordinator.client.get_naps.assert_not_called()
    del hass.data[DOMAIN]["entry2"]
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "list_naps", {"remi_id": "remi2"}, blocking=True, return_response=True)


async def test_unregister_after_unload(hass, coordinator):
    async_unregister_nap_services(hass)
    assert not hass.services.has_service(DOMAIN, "list_naps")
    assert not hass.services.has_service(DOMAIN, "create_nap")


@pytest.mark.parametrize("data", [{}, {"name": "Nap"}, {"duration_minutes": 40}])
def test_creation_requires_name_and_duration(data):
    with pytest.raises(vol.Invalid):
        CREATE_NAP_SCHEMA(data)
