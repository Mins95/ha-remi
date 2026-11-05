"""Brightness scaling, restoration, commands and legacy registry migration."""
from __future__ import annotations

from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.core import State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import RestoredExtraData
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache_with_extra_data,
)

from custom_components.urbanhello_remi_unofficial.api import RemiApiError
from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.coordinator import RemiDataUpdateCoordinator
from custom_components.urbanhello_remi_unofficial.light import RemiBrightnessLightEntity

from .conftest import MOCK_REMI_DATA, MOCK_REMI_ID


@pytest.fixture
def coordinator():
    coordinator = MagicMock(spec=RemiDataUpdateCoordinator)
    coordinator.remi = {"objectId": MOCK_REMI_ID, "luminosity": 42}
    coordinator.last_update_success = True
    coordinator.data = {"remi": coordinator.remi, "events": []}

    def set_updated_data(data):
        coordinator.data = data
        coordinator.remi = data["remi"]

    coordinator.async_set_updated_data.side_effect = set_updated_data
    coordinator.client = MagicMock()
    coordinator.client.update_remi = AsyncMock(return_value={})
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.mark.parametrize("level,brightness", [(0, 0), (1, 3), (42, 107), (50, 128), (100, 255)])
def test_api_scale(coordinator, level, brightness):
    coordinator.remi["luminosity"] = level
    entity = RemiBrightnessLightEntity(coordinator)
    assert entity.unique_id == f"{MOCK_REMI_ID}_brightness"
    assert entity.supported_color_modes == {ColorMode.BRIGHTNESS}
    assert entity.brightness == brightness
    assert entity.is_on is (level > 0)
    assert entity.available is True


@pytest.mark.parametrize("raw", [None, True, False, "42", "", [], {}, -1, 101, float("nan"), float("inf"), 10**1000])
def test_invalid_api_values_are_unavailable(coordinator, raw):
    coordinator.remi["luminosity"] = raw
    entity = RemiBrightnessLightEntity(coordinator)
    assert entity.available is False
    assert entity.brightness is None
    assert entity.is_on is None


def test_missing_value_and_coordinator_failure(coordinator):
    coordinator.remi.pop("luminosity")
    entity = RemiBrightnessLightEntity(coordinator)
    assert entity.available is False
    coordinator.remi["luminosity"] = 50
    coordinator.last_update_success = False
    assert entity.available is False


@pytest.mark.parametrize("brightness,level", [(0, 0), (1, 1), (2, 1), (3, 1), (107, 42), (128, 50), (254, 100), (255, 100)])
async def test_turn_on_scale(coordinator, brightness, level):
    entity = RemiBrightnessLightEntity(coordinator)
    await entity.async_turn_on(**{ATTR_BRIGHTNESS: brightness})
    coordinator.client.update_remi.assert_awaited_once_with({"luminosity": level})
    coordinator.async_request_refresh.assert_awaited_once()


async def test_turn_off_and_restore_last_level(coordinator):
    entity = RemiBrightnessLightEntity(coordinator)
    await entity.async_turn_off()
    coordinator.client.update_remi.assert_awaited_once_with({"luminosity": 0})
    coordinator.remi["luminosity"] = 0
    await entity.async_turn_on()
    assert coordinator.client.update_remi.await_args.kwargs == {}
    assert coordinator.client.update_remi.await_args.args == ({"luminosity": 42},)


async def test_fast_dimming_off_on_preserves_new_level_and_other_data(coordinator):
    coordinator.remi["volume"] = 25
    coordinator.data["events"] = [{"enabled": True}]
    entity = RemiBrightnessLightEntity(coordinator)
    await entity.async_turn_on(**{ATTR_BRIGHTNESS: 153})
    assert entity.brightness == 153
    await entity.async_turn_off()
    assert entity.is_on is False
    await entity.async_turn_on()
    assert entity.brightness == 153
    assert coordinator.client.update_remi.await_args.args == ({"luminosity": 60},)
    assert coordinator.remi["volume"] == 25
    assert coordinator.data["events"] == [{"enabled": True}]


async def test_first_turn_on_defaults_to_maximum(coordinator):
    coordinator.remi["luminosity"] = 0
    entity = RemiBrightnessLightEntity(coordinator)
    await entity.async_turn_on()
    coordinator.client.update_remi.assert_awaited_once_with({"luminosity": 100})


async def test_external_level_is_remembered_before_off(coordinator):
    entity = RemiBrightnessLightEntity(coordinator)
    with patch.object(entity, "async_write_ha_state"):
        coordinator.remi["luminosity"] = 73
        entity._handle_coordinator_update()
        coordinator.remi["luminosity"] = 0
        entity._handle_coordinator_update()
    await entity.async_turn_on()
    coordinator.client.update_remi.assert_awaited_once_with({"luminosity": 73})


@pytest.mark.parametrize("restored,expected", [(37, 37), (0, 100), (-1, 100), (101, 100), ("37", 100), (None, 100), (True, 100)])
async def test_restart_restores_extra_data_while_off(coordinator, restored, expected):
    coordinator.remi["luminosity"] = 0
    entity = RemiBrightnessLightEntity(coordinator)
    with (
        patch.object(entity, "async_on_remove"),
        patch.object(entity, "async_get_last_extra_data", return_value=RestoredExtraData({"last_luminosity": restored})),
    ):
        await entity.async_added_to_hass()
    assert entity.is_on is False
    assert entity.brightness == 0
    await entity.async_turn_on()
    coordinator.client.update_remi.assert_awaited_once_with({"luminosity": expected})
    assert entity.extra_restore_state_data.as_dict() == {"last_luminosity": expected}


async def test_current_cloud_level_takes_precedence_over_restored_level(coordinator):
    entity = RemiBrightnessLightEntity(coordinator)
    with patch.object(entity, "async_on_remove"), patch.object(entity, "async_get_last_extra_data") as restore:
        await entity.async_added_to_hass()
    restore.assert_not_awaited()
    await entity.async_turn_on()
    coordinator.client.update_remi.assert_awaited_once_with({"luminosity": 42})


async def test_failed_command_does_not_remember_requested_level(coordinator):
    entity = RemiBrightnessLightEntity(coordinator)
    coordinator.client.update_remi.side_effect = RemiApiError("failed")
    with pytest.raises(RemiApiError):
        await entity.async_turn_on(**{ATTR_BRIGHTNESS: 255})
    coordinator.async_request_refresh.assert_not_awaited()
    assert entity.extra_restore_state_data.as_dict() == {"last_luminosity": 42}


@pytest.mark.parametrize("raw", [None, True, -1, 256, "128", float("nan")])
async def test_invalid_command_does_not_write(coordinator, raw):
    entity = RemiBrightnessLightEntity(coordinator)
    with pytest.raises(ValueError):
        await entity.async_turn_on(**{ATTR_BRIGHTNESS: raw})
    coordinator.client.update_remi.assert_not_awaited()


async def test_real_setup_registry_cleanup_and_light_services(
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
    cloud = deepcopy(MOCK_REMI_DATA)
    mock_api_client.get_remi.side_effect = lambda: deepcopy(cloud)

    def update(fields):
        cloud.update(fields)
        return {}

    mock_api_client.update_remi.side_effect = update
    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert all(registry.async_get(item.entity_id) is None for item in legacy)
        assert registry.async_get(unrelated.entity_id) is not None
        assert registry.async_get(other.entity_id) is not None
        entity_id = registry.async_get_entity_id("light", DOMAIN, f"{MOCK_REMI_ID}_brightness")
        assert entity_id is not None
        mock_api_client.update_remi.assert_not_awaited()
        await hass.services.async_call("light", "turn_on", {"entity_id": entity_id, "brightness_pct": 60}, blocking=True)
        await hass.async_block_till_done()
        assert mock_api_client.update_remi.await_args.args == ({"luminosity": 60},)
        assert hass.states.get(entity_id).attributes["brightness"] == 153
        await hass.services.async_call("light", "turn_off", {"entity_id": entity_id}, blocking=True)
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).state == "off"
        await hass.services.async_call("light", "turn_on", {"entity_id": entity_id}, blocking=True)
        await hass.async_block_till_done()
        assert mock_api_client.update_remi.await_args.args == ({"luminosity": 60},)
        assert hass.states.get(entity_id).state == "on"


async def test_real_setup_restores_nonzero_level_from_previous_off_state(
    hass, enable_custom_integrations, mock_api_client, mock_config_entry_data,
):
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, title="Test REMI")
    entry.add_to_hass(hass)
    registered = er.async_get(hass).async_get_or_create(
        "light", DOMAIN, f"{MOCK_REMI_ID}_brightness", config_entry=entry,
    )
    mock_restore_cache_with_extra_data(hass, [
        (State(registered.entity_id, "off"), {"last_luminosity": 37}),
    ])
    mock_api_client.get_remi.return_value = {**MOCK_REMI_DATA, "luminosity": 0}
    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get(registered.entity_id).state == "off"
        mock_api_client.update_remi.assert_not_awaited()
        await hass.services.async_call("light", "turn_on", {"entity_id": registered.entity_id}, blocking=True)
        mock_api_client.update_remi.assert_awaited_once_with({"luminosity": 37})
