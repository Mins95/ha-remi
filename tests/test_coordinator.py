"""Tests for the RemiDataUpdateCoordinator."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.urbanhello_remi_unofficial.api import RemiApiError
from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.coordinator import (
    RemiDataUpdateCoordinator,
)

from .conftest import (
    MOCK_CONFIG_DATA,
    MOCK_EVENT_DATA,
    MOCK_FACES_DATA,
    MOCK_REMI_DATA,
    mock_api_client,
)


@pytest.fixture
def coordinator(hass, mock_api_client):
    """Return a RemiDataUpdateCoordinator with a mock client."""
    return RemiDataUpdateCoordinator(hass, mock_api_client)


class TestCoordinatorProperties:
    """Tests for coordinator data properties."""

    def test_remi_returns_empty_when_no_data(self, coordinator):
        coordinator.data = None
        assert coordinator.remi == {}

    def test_remi_returns_remi_data(self, coordinator):
        coordinator.data = {"remi": MOCK_REMI_DATA, "events": []}
        assert coordinator.remi == MOCK_REMI_DATA

    def test_events_returns_empty_when_no_data(self, coordinator):
        coordinator.data = None
        assert coordinator.events == []

    def test_events_returns_event_list(self, coordinator):
        coordinator.data = {"remi": MOCK_REMI_DATA, "events": MOCK_EVENT_DATA}
        assert coordinator.events == MOCK_EVENT_DATA

    def test_latest_firmware_version_none_when_no_config(self, coordinator):
        coordinator.config_params = {}
        assert coordinator.latest_firmware_version is None

    def test_latest_firmware_version_from_config(self, coordinator):
        coordinator.config_params = {"default_firmware_update_version": 110}
        assert coordinator.latest_firmware_version == 110


class TestAsyncUpdateData:
    """Tests for _async_update_data."""

    async def test_update_data_success(self, coordinator, mock_api_client):
        result = await coordinator._async_update_data()

        assert result["remi"] == MOCK_REMI_DATA
        assert result["events"] == MOCK_EVENT_DATA
        mock_api_client.get_remi.assert_called_once()
        mock_api_client.get_events.assert_called_once()

    async def test_update_data_api_error_raises_update_failed(self, coordinator, mock_api_client):
        mock_api_client.get_remi.side_effect = RemiApiError("Connection refused")

        with pytest.raises(UpdateFailed) as raised:
            await coordinator._async_update_data()
        assert raised.value.translation_domain == DOMAIN
        assert raised.value.translation_key == "cannot_refresh_device"


class TestAsyncSetup:
    """Tests for async_setup."""

    async def test_face_catalogue_recovers_while_polling(self, coordinator, mock_api_client):
        mock_api_client.get_faces.side_effect = [RemiApiError("Offline"), MOCK_FACES_DATA]
        with patch("custom_components.urbanhello_remi_unofficial.coordinator.monotonic") as clock:
            clock.return_value = 0
            await coordinator.async_refresh()
            assert coordinator.faces == []
            assert coordinator.last_update_success
            assert coordinator.device_received_at is not None
            clock.return_value = 60
            await coordinator.async_refresh()
            mock_api_client.get_faces.assert_awaited_once()
            clock.return_value = 300
            await coordinator.async_refresh()
            assert coordinator.faces == MOCK_FACES_DATA
            assert mock_api_client.get_config.await_count == 1

    async def test_setup_fetches_faces_and_config(self, coordinator, mock_api_client):
        await coordinator.async_setup()

        assert coordinator.faces == MOCK_FACES_DATA
        assert coordinator.config_params == MOCK_CONFIG_DATA["params"]

    async def test_setup_handles_api_error_gracefully(self, coordinator, mock_api_client):
        mock_api_client.get_faces.side_effect = RemiApiError("Timeout")

        await coordinator.async_setup()

        assert coordinator.faces == []
        assert coordinator.config_params == MOCK_CONFIG_DATA["params"]
