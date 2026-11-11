"""Firmware metadata failures must not flood the cloud or hide live state."""
from __future__ import annotations

from copy import deepcopy
from unittest.mock import patch

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError

from custom_components.urbanhello_remi_unofficial.api import RemiApiError, RemiAuthError
from custom_components.urbanhello_remi_unofficial.button import RemiCheckFirmwareButton
from custom_components.urbanhello_remi_unofficial.coordinator import RemiDataUpdateCoordinator

from .conftest import MOCK_CONFIG_DATA, MOCK_EVENT_DATA, MOCK_REMI_DATA


@pytest.fixture
def clock():
    """Control only the coordinator's monotonic clock without sleeping."""
    with patch(
        "custom_components.urbanhello_remi_unofficial.coordinator.monotonic",
        return_value=1000.0,
    ) as value:
        yield value


@pytest.mark.parametrize("had_config", [False, True])
async def test_failed_metadata_waits_five_minutes_without_delaying_live_polls(
    hass, mock_api_client, clock, had_config,
):
    """Initial and expired metadata failures retain old config and fresh state."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    previous = {"default_firmware_update_version": 333} if had_config else {}
    coordinator.config_params = previous
    if had_config:
        coordinator._config_checked_at = clock.return_value - 3600
    mock_api_client.get_config.side_effect = RemiApiError("Metadata unavailable")

    await coordinator.async_refresh()
    assert mock_api_client.get_config.await_count == 1
    assert coordinator.config_params is previous

    for timestamp in (1060, 1120, 1299.999):
        clock.return_value = timestamp
        fresh_remi = {**MOCK_REMI_DATA, "rssi": -50}
        fresh_events = [{**event, "name": "Updated alarm"} for event in MOCK_EVENT_DATA]
        mock_api_client.get_remi.return_value = fresh_remi
        mock_api_client.get_events.return_value = fresh_events
        await coordinator.async_refresh()
        assert coordinator.last_update_success is True
        assert coordinator.remi == fresh_remi
        assert coordinator.events == fresh_events
        assert coordinator.events_available is True
        assert coordinator.config_params is previous
        assert mock_api_client.get_config.await_count == 1

    # Ordinary polls did not move the deadline: retry at exactly 300 seconds.
    clock.return_value = 1300
    await coordinator.async_refresh()
    assert mock_api_client.get_config.await_count == 2
    assert coordinator.config_params is previous
    assert mock_api_client.get_remi.await_count == 5
    assert mock_api_client.get_events.await_count == 5

    # Another real failure starts another five-minute pause.
    clock.return_value = 1599.999
    await coordinator.async_refresh()
    assert mock_api_client.get_config.await_count == 2
    clock.return_value = 1600
    await coordinator.async_refresh()
    assert mock_api_client.get_config.await_count == 3


async def test_success_after_retry_restores_hourly_metadata_refresh(hass, mock_api_client, clock):
    """A successful retry clears the failure deadline and starts a full hour."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    mock_api_client.get_config.side_effect = RemiApiError("Metadata unavailable")
    await coordinator.async_refresh()

    clock.return_value = 1300
    mock_api_client.get_config.side_effect = None
    mock_api_client.get_config.return_value = deepcopy(MOCK_CONFIG_DATA)
    await coordinator.async_refresh()
    assert mock_api_client.get_config.await_count == 2
    assert coordinator.config_params == MOCK_CONFIG_DATA["params"]

    for timestamp in (1600, 4899.999):
        clock.return_value = timestamp
        await coordinator.async_refresh()
        assert mock_api_client.get_config.await_count == 2
    clock.return_value = 4900
    await coordinator.async_refresh()
    assert mock_api_client.get_config.await_count == 3


async def test_setup_metadata_failure_does_not_retry_on_first_device_refresh(hass, mock_api_client, clock):
    """Setup and regular polling share the same failed-read deadline."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    mock_api_client.get_config.side_effect = RemiApiError("Metadata unavailable")
    await coordinator.async_setup()
    await coordinator.async_refresh()
    assert coordinator.last_update_success is True
    assert mock_api_client.get_config.await_count == 1
    clock.return_value = 1300
    await coordinator.async_refresh()
    assert mock_api_client.get_config.await_count == 2


async def test_manual_check_bypasses_failure_deadline_and_clears_it_on_success(hass, mock_api_client, clock):
    """The button reads immediately; its success also restores hourly polling."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    mock_api_client.get_config.side_effect = RemiApiError("Metadata unavailable")
    await coordinator.async_refresh()

    clock.return_value = 1060
    mock_api_client.get_config.side_effect = None
    await RemiCheckFirmwareButton(coordinator).async_press()
    assert mock_api_client.get_config.await_count == 2
    assert coordinator.last_update_success is True
    assert coordinator.config_params == MOCK_CONFIG_DATA["params"]
    mock_api_client.update_remi.assert_not_awaited()

    for timestamp in (1300, 4659.999):
        clock.return_value = timestamp
        await coordinator.async_refresh()
        assert mock_api_client.get_config.await_count == 2
    clock.return_value = 4660
    await coordinator.async_refresh()
    assert mock_api_client.get_config.await_count == 3


async def test_failed_manual_check_retries_after_five_minutes_even_with_recent_cache(hass, mock_api_client, clock):
    """A manual failure does not discard config or defer recovery for an hour."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    await coordinator.async_setup()
    previous = coordinator.config_params

    clock.return_value = 1060
    mock_api_client.get_config.side_effect = RemiApiError("Metadata unavailable")
    with pytest.raises(HomeAssistantError) as error:
        await RemiCheckFirmwareButton(coordinator).async_press()
    assert error.value.translation_key == "cannot_check_firmware"
    assert coordinator.config_params is previous
    assert mock_api_client.get_config.await_count == 2

    clock.return_value = 1359.999
    await coordinator.async_refresh()
    assert coordinator.last_update_success is True
    assert mock_api_client.get_config.await_count == 2
    clock.return_value = 1360
    await coordinator.async_refresh()
    assert mock_api_client.get_config.await_count == 3
    assert coordinator.config_params is previous


@pytest.mark.parametrize("operation", ["poll", "setup", "manual"])
async def test_metadata_auth_error_requires_reauthentication_without_cooldown(
    hass, mock_api_client, clock, operation,
):
    """Authentication errors remain actionable in every metadata entry point."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    failure = RemiAuthError("Rejected credentials")
    mock_api_client.get_config.side_effect = failure
    action = {
        "poll": coordinator._async_update_data,
        "setup": coordinator.async_setup,
        "manual": RemiCheckFirmwareButton(coordinator).async_press,
    }[operation]
    for _ in range(2):
        with pytest.raises(ConfigEntryAuthFailed) as error:
            await action()
        assert error.value.translation_key == "reauth_required"
        assert error.value.__cause__ is failure
    assert mock_api_client.get_config.await_count == 2


@pytest.mark.parametrize("method", ["get_remi", "get_events"])
async def test_live_auth_errors_remain_visible_during_metadata_cooldown(hass, mock_api_client, clock, method):
    """Pausing metadata never pauses device reads or their auth failures."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    mock_api_client.get_config.side_effect = RemiApiError("Metadata unavailable")
    await coordinator.async_refresh()

    clock.return_value = 1060
    getattr(mock_api_client, method).side_effect = RemiAuthError("Rejected credentials")
    with pytest.raises(ConfigEntryAuthFailed) as error:
        await coordinator._async_update_data()
    assert error.value.translation_key == "reauth_required"
    assert mock_api_client.get_config.await_count == 1
