"""Tests for the Remi light platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from copy import deepcopy

import pytest
from homeassistant.components.light import ATTR_RGB_COLOR
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.coordinator import (
    RemiDataUpdateCoordinator,
)
from custom_components.urbanhello_remi_unofficial.light import (
    RemiBackgroundLightEntity,
    async_setup_entry,
)

from .conftest import MOCK_REMI_DATA, MOCK_REMI_ID


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this module."""
    yield


@pytest.fixture
def mock_coordinator_with_lights():
    """Return a mock coordinator with RGB light data."""
    coordinator = MagicMock(spec=RemiDataUpdateCoordinator)
    coordinator.remi = {
        "objectId": MOCK_REMI_ID,
        "background_color": [0, 0, 255],
    }
    coordinator.client = MagicMock()
    coordinator.client.update_remi = AsyncMock(return_value={})
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    async def test_adds_only_app_background_light(self, hass: HomeAssistant, mock_coordinator_with_lights):
        added_entities = []

        def mock_add_entities(entities):
            added_entities.extend(entities)

        hass.data = {DOMAIN: {"entry_1": mock_coordinator_with_lights}}

        entry = MagicMock()
        entry.entry_id = "entry_1"
        entry.data = {"remi_id": MOCK_REMI_ID}

        await async_setup_entry(hass, entry, mock_add_entities)

        assert len(added_entities) == 1
        assert isinstance(added_entities[0], RemiBackgroundLightEntity)


class TestRemiBackgroundLightEntity:
    """Tests for RemiBackgroundLightEntity."""

    def test_unique_id(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        assert entity.unique_id == f"{MOCK_REMI_ID}_background_color"

    def test_name(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        assert entity.name == "App Background Color"

    def test_icon(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        assert entity.icon == "mdi:palette"

    def test_rgb_color_returns_tuple(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        assert entity.rgb_color == (0, 0, 255)

    async def test_turn_on_updates_background_color_field(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        await entity.async_turn_on(**{ATTR_RGB_COLOR: (255, 0, 128)})

        mock_coordinator_with_lights.client.update_remi.assert_awaited_once_with(
            {"background_color": [255, 0, 128]}
        )

    async def test_turn_off_sets_background_color_to_zero(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        await entity.async_turn_off()

        mock_coordinator_with_lights.client.update_remi.assert_awaited_once_with(
            {"background_color": [0, 0, 0]}
        )

    def test_invalid_color_is_unknown(self, mock_coordinator_with_lights):
        mock_coordinator_with_lights.remi["background_color"] = [255, 128]
        assert RemiBackgroundLightEntity(mock_coordinator_with_lights).rgb_color is None

    def test_is_on_and_off(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        assert entity.is_on is True
        mock_coordinator_with_lights.remi["background_color"] = [0, 0, 0]
        assert entity.is_on is False

    async def test_turn_on_without_rgb_uses_current(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        await entity.async_turn_on()
        mock_coordinator_with_lights.client.update_remi.assert_awaited_once_with(
            {"background_color": [0, 0, 255]}
        )
        mock_coordinator_with_lights.async_request_refresh.assert_awaited_once()

    async def test_turn_on_when_off_uses_white(self, mock_coordinator_with_lights):
        mock_coordinator_with_lights.remi["background_color"] = [0, 0, 0]
        await RemiBackgroundLightEntity(mock_coordinator_with_lights).async_turn_on()
        mock_coordinator_with_lights.client.update_remi.assert_awaited_once_with(
            {"background_color": [255, 255, 255]}
        )


@pytest.mark.parametrize("custom_name", [None, "My app color"])
async def test_setup_removes_only_night_light_and_preserves_background_identity(
    hass, mock_api_client, mock_config_entry_data, custom_name,
):
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, title="Test REMI")
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    legacy = registry.async_get_or_create("light", DOMAIN, f"{MOCK_REMI_ID}_night_light", config_entry=entry)
    background = registry.async_get_or_create(
        "light", DOMAIN, f"{MOCK_REMI_ID}_background_color", config_entry=entry,
        suggested_object_id="existing_background_color", original_name="Background Color",
    )
    if custom_name:
        registry.async_update_entity(background.entity_id, name=custom_name)
    other_entry = MockConfigEntry(domain=DOMAIN, data={}, title="Other", disabled_by=ConfigEntryDisabler.USER)
    other_entry.add_to_hass(hass)
    other = registry.async_get_or_create("light", DOMAIN, "other_night_light", config_entry=other_entry)
    unrelated = registry.async_get_or_create("number", DOMAIN, f"{MOCK_REMI_ID}_volume", config_entry=entry)
    original = deepcopy(MOCK_REMI_DATA)
    mock_api_client.get_remi.return_value = deepcopy(original)
    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert registry.async_get(legacy.entity_id) is None
        assert registry.async_get(other.entity_id) is not None
        assert registry.async_get(unrelated.entity_id) is not None
        assert registry.async_get_entity_id("light", DOMAIN, f"{MOCK_REMI_ID}_background_color") == background.entity_id
        updated = registry.async_get(background.entity_id)
        assert updated.unique_id == background.unique_id
        assert updated.name == custom_name
        assert updated.original_name == "App Background Color"
        assert hass.states.get(background.entity_id).attributes["friendly_name"].endswith(custom_name or "App Background Color")
        lights = [item for item in er.async_entries_for_config_entry(registry, entry.entry_id) if item.domain == "light"]
        assert [item.entity_id for item in lights] == [background.entity_id]
        mock_api_client.update_remi.assert_not_awaited()
        assert mock_api_client.get_remi.return_value == original
        await hass.services.async_call("light", "turn_on", {
            "entity_id": background.entity_id, "rgb_color": [10, 20, 30],
        }, blocking=True)
        mock_api_client.update_remi.assert_awaited_once_with({"background_color": [10, 20, 30]})
        await hass.services.async_call("light", "turn_off", {"entity_id": background.entity_id}, blocking=True)
        assert mock_api_client.update_remi.await_args.args == ({"background_color": [0, 0, 0]},)
        assert all("lightnight" not in call.args[0] for call in mock_api_client.update_remi.await_args_list)
