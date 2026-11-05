"""Tests for the Remi number platform."""
from __future__ import annotations

from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.number import NumberMode
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.coordinator import (
    RemiDataUpdateCoordinator,
)
from custom_components.urbanhello_remi_unofficial.number import (
    NUMBER_DESCRIPTIONS,
    RemiNumberEntity,
    async_setup_entry,
)

from .conftest import MOCK_REMI_DATA, MOCK_REMI_ID


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this module."""
    yield


@pytest.fixture
def mock_coordinator():
    """Return a mock coordinator with number data."""
    coordinator = MagicMock(spec=RemiDataUpdateCoordinator)
    coordinator.remi = {
        "objectId": MOCK_REMI_ID,
        "volume": 75,
        "luminosity": 60,
        "noise_notification_threshold": 30,
    }
    coordinator.client = MagicMock()
    coordinator.client.update_remi = AsyncMock(return_value={})
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.mark.skip(reason="Requires full HA platform setup - covered by other tests")
    async def test_adds_all_number_entities(self, hass: HomeAssistant, mock_coordinator):
        added_entities = []

        async def mock_add_entities(entities):
            added_entities.extend(entities)

        hass.data = {DOMAIN: {"entry_1": mock_coordinator}}

        entry = MagicMock()
        entry.entry_id = "entry_1"

        await async_setup_entry(hass, entry, mock_add_entities)

        assert len(added_entities) == 3
        for entity in added_entities:
            assert isinstance(entity, RemiNumberEntity)


class TestRemiNumberEntity:
    """Tests for RemiNumberEntity."""

    def test_volume_entity_unique_id(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[0])
        assert entity.unique_id == f"{MOCK_REMI_ID}_volume"

    def test_volume_entity_properties(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[0])
        assert entity.entity_description.name == "Volume"
        assert entity.icon == "mdi:volume-high"
        assert entity.native_min_value == 0
        assert entity.native_max_value == 100
        assert entity.native_step == 1

    def test_volume_native_value(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[0])
        assert entity.native_value == 75

    def test_volume_default_value_when_missing(self, mock_coordinator):
        mock_coordinator.remi.pop("volume")
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[0])
        assert entity.native_value == 50

    async def test_volume_set_value(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[0])
        await entity.async_set_native_value(80)

        mock_coordinator.client.update_remi.assert_awaited_once_with({"volume": 80})
        mock_coordinator.async_request_refresh.assert_awaited_once()

    def test_noise_threshold_entity_properties(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[1])
        assert entity.entity_description.name == "Noise Alert Threshold"
        assert entity.icon == "mdi:microphone"
        assert entity.native_min_value == 0
        assert entity.native_max_value == 250
        assert entity.native_step == 1

    @pytest.mark.parametrize("value", [0, 30, 101, 250])
    def test_noise_threshold_native_value(self, mock_coordinator, value):
        mock_coordinator.remi["noise_notification_threshold"] = value
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[1])
        assert entity.native_value == value

    def test_noise_threshold_default_value_when_missing(self, mock_coordinator):
        mock_coordinator.remi.pop("noise_notification_threshold")
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[1])
        assert entity.native_value == 0

    @pytest.mark.parametrize("value", [0, 45, 100, 101, 250])
    async def test_noise_threshold_set_value(self, mock_coordinator, value):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[1])
        await entity.async_set_native_value(value)

        mock_coordinator.client.update_remi.assert_awaited_once_with(
            {"noise_notification_threshold": value}
        )


def test_brightness_number_replaces_the_removed_luminosity_number():
    assert all(description.key != "luminosity" for description in NUMBER_DESCRIPTIONS)
    assert any(description.key == "brightness" for description in NUMBER_DESCRIPTIONS)


class TestRemiBrightnessNumber:
    """Tests for the Brightness number entity."""

    def test_brightness_entity_unique_id(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[2])
        assert entity.unique_id == f"{MOCK_REMI_ID}_brightness"

    def test_brightness_entity_properties(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[2])
        assert entity.entity_description.name == "Brightness"
        assert entity.icon == "mdi:brightness-6"
        assert entity.mode == NumberMode.SLIDER
        assert entity.native_min_value == 0
        assert entity.native_max_value == 100
        assert entity.native_step == 1

    def test_brightness_native_value(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[2])
        assert entity.native_value == 60

    @pytest.mark.parametrize(
        "raw", [None, True, False, "60", "", [], {}, -1, 101, float("nan"), float("inf")]
    )
    def test_brightness_invalid_api_value_is_unknown(self, mock_coordinator, raw):
        mock_coordinator.remi["luminosity"] = raw
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[2])
        assert entity.native_value is None

    async def test_brightness_set_value(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[2])
        await entity.async_set_native_value(40)

        mock_coordinator.client.update_remi.assert_awaited_once_with({"luminosity": 40})
        mock_coordinator.async_request_refresh.assert_awaited_once()


async def test_real_setup_removes_legacy_luminosity_entities(
    hass, enable_custom_integrations, mock_api_client, mock_config_entry_data,
):
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, title="Test REMI")
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    legacy = [
        registry.async_get_or_create(domain, DOMAIN, f"{MOCK_REMI_ID}_luminosity", config_entry=entry)
        for domain in ("number", "sensor")
    ]
    unrelated = registry.async_get_or_create("number", DOMAIN, f"{MOCK_REMI_ID}_volume", config_entry=entry)
    other_entry = MockConfigEntry(domain=DOMAIN, data={}, title="Other REMI", disabled_by=ConfigEntryDisabler.USER)
    other_entry.add_to_hass(hass)
    other = registry.async_get_or_create("number", DOMAIN, "other_luminosity", config_entry=other_entry)
    mock_api_client.get_remi.return_value = deepcopy(MOCK_REMI_DATA)
    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert all(registry.async_get(item.entity_id) is None for item in legacy)
        assert registry.async_get(unrelated.entity_id) is not None
        assert registry.async_get(other.entity_id) is not None
        entity_id = registry.async_get_entity_id("number", DOMAIN, f"{MOCK_REMI_ID}_brightness")
        assert entity_id is not None
        assert hass.states.get(entity_id).state == "42"
        mock_api_client.update_remi.assert_not_awaited()
        await hass.services.async_call(
            "number", "set_value", {"entity_id": entity_id, "value": 60}, blocking=True
        )
        await hass.async_block_till_done()
        assert mock_api_client.update_remi.await_args.args == ({"luminosity": 60},)
