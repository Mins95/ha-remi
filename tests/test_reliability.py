"""Regressions for real firmware metadata, cloud outages and integration reloads."""


import asyncio


from unittest.mock import AsyncMock, MagicMock, patch


import aiohttp


import pytest


from homeassistant.exceptions import HomeAssistantError


from custom_components.urbanhello_remi_unofficial import _register_services, async_unload_entry


from custom_components.urbanhello_remi_unofficial.api import RemiApiClient, RemiApiError


from custom_components.urbanhello_remi_unofficial.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS, RemiBinarySensorEntity,
)


from custom_components.urbanhello_remi_unofficial.button import RemiCheckFirmwareButton


from custom_components.urbanhello_remi_unofficial.const import DOMAIN


from custom_components.urbanhello_remi_unofficial.coordinator import RemiDataUpdateCoordinator


from custom_components.urbanhello_remi_unofficial.firmware import firmware_update_available


from .conftest import MOCK_LOGIN_RESPONSE, MOCK_REMI_DATA, MOCK_REMI_ID


from .test_api import _make_response


@pytest.mark.parametrize("device,expected", [
    ({"current_firmware_version": 332, "update_firmware_version": 332, "firmware_need_update": 0}, False),
    ({"current_firmware_version": 332, "update_firmware_version": 332}, False),
    ({"current_firmware_version": 332, "update_firmware_version": 333, "firmware_need_update": 1}, True),
    ({"current_firmware_version": 332, "update_firmware_version": 333}, True),
    ({"current_firmware_version": "332", "update_firmware_version": "333"}, True),
    ({"current_firmware_version": 332, "update_firmware_version": 332, "firmware_need_update": "1"}, True),
    ({"current_firmware_version": None}, None),
    ({"current_firmware_version": 332}, None),
    ({"current_firmware_version": True, "update_firmware_version": 333}, None),
    ({"current_firmware_version": "bad", "update_firmware_version": 333}, None),
    ({"current_firmware_version": 332, "update_firmware_version": 0}, None),
    ({"firmware_need_update": "0"}, False),
    ({"firmware_need_update": "unknown"}, None),
])
def test_firmware_uses_device_assignment(device, expected):
    assert firmware_update_available(device, 333) is expected


async def test_firmware_attributes_explain_global_default(hass, mock_api_client):
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    coordinator.data = {"remi": {**MOCK_REMI_DATA, "current_firmware_version": 332,
                                 "update_firmware_version": 332, "firmware_need_update": 0}}
    coordinator.config_params = {"default_firmware_update_version": 333}
    desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "firmware_update")
    entity = RemiBinarySensorEntity(coordinator, desc)
    assert entity.is_on is False
    assert entity.extra_state_attributes == {"installed_version": 332, "target_version": 332,
        "server_default_version": 333, "update_requested": False, "update_method": "automatic_wifi"}


async def test_firmware_button_performs_reads_only(hass, mock_api_client):
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    coordinator.data = {"remi": MOCK_REMI_DATA, "events": []}
    await RemiCheckFirmwareButton(coordinator).async_press()
    mock_api_client.get_config.assert_awaited_once()
    mock_api_client.get_remi.assert_awaited_once()
    mock_api_client.update_remi.assert_not_awaited()
    mock_api_client.create_event.assert_not_awaited()
    mock_api_client.update_event.assert_not_awaited()


async def test_firmware_button_reports_failed_read(hass, mock_api_client):
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    coordinator.data = {"remi": MOCK_REMI_DATA, "events": []}
    mock_api_client.get_config.side_effect = RemiApiError("unreachable")
    with pytest.raises(HomeAssistantError):
        await RemiCheckFirmwareButton(coordinator).async_press()


async def test_metadata_failure_does_not_discard_device_state(hass, mock_api_client):
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    mock_api_client.get_config.side_effect = RemiApiError("502")
    result = await coordinator._async_update_data()
    assert result["remi"] == MOCK_REMI_DATA
