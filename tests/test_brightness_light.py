"""Physical brightness remembers cloud readings without changing the face."""
from __future__ import annotations

from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode
from homeassistant.core import State
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import async_get as async_get_restore_data
from pytest_homeassistant.common import MockConfigEntry, mock_restore_cache_with_extra_data

from custom_components.urbanhello_remi_unofficial.api import RemiApiError
from custom_components.urbanhello_remi_unofficial.brightness import (
    BrightnessRestoreData,
    get_brightness_memory,
)
from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.coordinator import RemiDataUpdateCoordinator
from custom_components.urbanhello_remi_unofficial.light import RemiBrightnessLightEntity, async_setup_entry
from custom_components.urbanhello_remi_unofficial.number import NUMBER_DESCRIPTIONS, RemiNumberEntity

from .conftest import MOCK_REMI_DATA, MOCK_REMI_ID


@pytest.fixture
def coordinator():
    """One successful cloud snapshot and non-optimistic write/read mocks."""
    coordinator = MagicMock(spec=RemiDataUpdateCoordinator)
    coordinator.remi = deepcopy(MOCK_REMI_DATA)
    coordinator.last_update_success = True
    coordinator.client = MagicMock()
    coordinator.client.update_remi = AsyncMock(return_value={})
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


def test_identity_defaults_and_units(coordinator):
    entity = RemiBrightnessLightEntity(coordinator)
    assert entity.unique_id == f"{MOCK_REMI_ID}_physical_brightness"
    assert entity.translation_key == "physical_brightness"
    assert entity.entity_registry_enabled_default is False
    assert entity.supported_color_modes == {ColorMode.BRIGHTNESS}
    assert entity.available is True
    assert entity.is_on is True
    assert entity.brightness == 107  # 42%, expressed on HA's 0–255 scale.


async def test_memory_observes_cloud_while_optional_light_is_disabled(hass, mock_api_client):
    """Platform observation must not depend on adding the optional light to HA."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    coordinator.async_set_updated_data({"remi": deepcopy(MOCK_REMI_DATA), "events": []})
    entry = MagicMock(entry_id="entry", data={"remi_id": MOCK_REMI_ID})
    hass.data[DOMAIN] = {entry.entry_id: coordinator}
    added = MagicMock()
    await async_setup_entry(hass, entry, added)
    physical = added.call_args.args[0][1]
    assert physical.entity_registry_enabled_default is False
    memory = get_brightness_memory(coordinator)
    for level in (73, 0):
        coordinator.async_set_updated_data({
            "remi": {**MOCK_REMI_DATA, "luminosity": level}, "events": [],
        })
    assert memory.last_nonzero == 73
    # The platform listener belongs to the config entry and is removed on unload.
    entry.async_on_unload.call_args.args[0]()
    coordinator.async_set_updated_data({
        "remi": {**MOCK_REMI_DATA, "luminosity": 15}, "events": [],
    })
    assert memory.last_nonzero == 73


async def test_number_then_off_then_on_restores_cloud_level(coordinator):
    """The existing number shares its confirmed level with the optional light."""
    entity = RemiBrightnessLightEntity(coordinator)
    number = RemiNumberEntity(
        coordinator, next(item for item in NUMBER_DESCRIPTIONS if item.key == "brightness")
    )
    pending = {}

    async def write(payload):
        pending.update(payload)

    async def read():
        coordinator.remi.update(pending)
        pending.clear()
        get_brightness_memory(coordinator).observe()

    coordinator.client.update_remi.side_effect = write
    coordinator.async_request_refresh.side_effect = read
    await number.async_set_native_value(73)
    await entity.async_turn_off()
    assert entity.is_on is False
    assert entity.extra_restore_state_data.as_dict()["last_nonzero_luminosity"] == 73
    await entity.async_turn_on()
    assert entity.is_on is True
    assert [call.args[0] for call in coordinator.client.update_remi.await_args_list] == [
        {"luminosity": 73}, {"luminosity": 0}, {"luminosity": 73},
    ]
    assert coordinator.remi["face"] == MOCK_REMI_DATA["face"]


async def test_no_memory_defaults_to_fifty_without_claiming_confirmation(coordinator):
    coordinator.remi["luminosity"] = 0
    entity = RemiBrightnessLightEntity(coordinator)
    await entity.async_turn_on()
    coordinator.client.update_remi.assert_awaited_once_with({"luminosity": 50})
    assert entity.is_on is False
    assert entity.brightness == 0
    assert entity.extra_restore_state_data.as_dict()["last_nonzero_luminosity"] is None


@pytest.mark.parametrize("brightness,expected", [(0, 0), (1, 1), (128, 50), (255, 100)])
async def test_explicit_brightness_only_changes_luminosity(coordinator, brightness, expected):
    entity = RemiBrightnessLightEntity(coordinator)
    await entity.async_turn_on(**{ATTR_BRIGHTNESS: brightness})
    coordinator.client.update_remi.assert_awaited_once_with({"luminosity": expected})
    assert entity.brightness == 107  # No fabricated post-write value.
    assert entity.extra_restore_state_data.as_dict()["last_nonzero_luminosity"] == 42


@pytest.mark.parametrize("value", [None, True, "25", -1, 256, float("nan"), float("inf")])
async def test_invalid_command_is_rejected_before_write(coordinator, value):
    entity = RemiBrightnessLightEntity(coordinator)
    with pytest.raises(ServiceValidationError) as error:
        await entity.async_turn_on(**{ATTR_BRIGHTNESS: value})
    assert error.value.translation_key == "invalid_brightness"
    coordinator.client.update_remi.assert_not_awaited()


@pytest.mark.parametrize("value", [None, True, "42", -1, 101, float("nan"), float("inf")])
async def test_invalid_cloud_value_is_unknown_and_does_not_replace_memory(coordinator, value):
    entity = RemiBrightnessLightEntity(coordinator)
    coordinator.remi["luminosity"] = value
    get_brightness_memory(coordinator).observe()
    assert entity.is_on is None
    assert entity.brightness is None
    assert entity.available is False
    assert entity.extra_restore_state_data.as_dict()["last_nonzero_luminosity"] == 42
    with pytest.raises(HomeAssistantError):
        await entity.async_turn_on()
    coordinator.client.update_remi.assert_not_awaited()


async def test_missing_cloud_value_is_unknown(coordinator):
    coordinator.remi.pop("luminosity")
    entity = RemiBrightnessLightEntity(coordinator)
    assert entity.available is False
    assert entity.brightness is None
    assert entity.extra_restore_state_data.as_dict()["last_nonzero_luminosity"] is None


@pytest.mark.parametrize("flag", ["online", "alive", "cloud"])
async def test_unavailable_device_cannot_replace_memory_or_receive_commands(coordinator, flag):
    entity = RemiBrightnessLightEntity(coordinator)
    coordinator.remi["luminosity"] = 99
    if flag == "cloud":
        coordinator.last_update_success = False
    else:
        coordinator.remi[flag] = False
    get_brightness_memory(coordinator).observe()
    assert entity.available is False
    assert entity.extra_restore_state_data.as_dict()["last_nonzero_luminosity"] == 42
    with pytest.raises(HomeAssistantError) as error:
        await entity.async_turn_off()
    assert error.value.translation_key == "device_unavailable"
    coordinator.client.update_remi.assert_not_awaited()


async def test_write_error_preserves_state_and_memory(coordinator):
    entity = RemiBrightnessLightEntity(coordinator)
    coordinator.client.update_remi.side_effect = RemiApiError("write failed")
    with pytest.raises(RemiApiError):
        await entity.async_turn_off()
    assert entity.brightness == 107
    assert entity.extra_restore_state_data.as_dict()["last_nonzero_luminosity"] == 42
    coordinator.async_request_refresh.assert_not_awaited()


async def test_failed_refresh_does_not_confirm_requested_level(coordinator):
    entity = RemiBrightnessLightEntity(coordinator)

    async def failed_read():
        coordinator.last_update_success = False

    coordinator.async_request_refresh.side_effect = failed_read
    with pytest.raises(HomeAssistantError) as error:
        await entity.async_turn_on(**{ATTR_BRIGHTNESS: 255})
    assert error.value.translation_key == "cannot_refresh_device"
    assert entity.available is False
    assert entity.extra_restore_state_data.as_dict()["last_nonzero_luminosity"] == 42


@pytest.mark.parametrize("saved", [0, -1, 101, None, True, "73", float("nan")])
def test_invalid_restored_level_is_ignored(coordinator, saved):
    coordinator.remi["luminosity"] = 0
    memory = get_brightness_memory(coordinator)
    memory.restore(BrightnessRestoreData(MOCK_REMI_ID, saved).as_dict())
    assert memory.last_nonzero is None
    assert memory.turn_on_percent == 50


def test_memories_are_device_specific_and_current_read_wins(coordinator):
    memory = get_brightness_memory(coordinator)
    memory.restore(BrightnessRestoreData(MOCK_REMI_ID, 73).as_dict())
    assert memory.last_nonzero == 42
    other = MagicMock(spec=RemiDataUpdateCoordinator)
    other.remi = {"objectId": "other", "luminosity": 0}
    other.last_update_success = True
    other_memory = get_brightness_memory(other)
    other_memory.restore(BrightnessRestoreData(MOCK_REMI_ID, 73).as_dict())
    assert other_memory.last_nonzero is None
    other.remi["luminosity"] = 17
    other_memory.observe()
    assert other_memory.last_nonzero == 17
    assert memory.last_nonzero == 42
    coordinator.remi = {"objectId": "other", "luminosity": 91}
    memory.observe()
    assert memory.last_nonzero == 42


async def test_enabled_light_restores_memory_and_saves_it_while_off(
    hass, enable_custom_integrations, mock_api_client, mock_config_entry_data,
):
    """Exercise HA's real entity registry and RestoreEntity storage integration."""
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, title="Test REMI")
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    physical = registry.async_get_or_create(
        "light", DOMAIN, f"{MOCK_REMI_ID}_physical_brightness", config_entry=entry,
        suggested_object_id="remi_physical_light", disabled_by=None,
    )
    mock_restore_cache_with_extra_data(hass, [(
        State(physical.entity_id, "on", {"brightness": 186}),
        BrightnessRestoreData(MOCK_REMI_ID, 73).as_dict(),
    )])
    data = deepcopy(MOCK_REMI_DATA)
    data["luminosity"] = 0
    mock_api_client.get_remi.return_value = data
    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get(physical.entity_id).state == "off"
        await hass.services.async_call("light", "turn_on", {"entity_id": physical.entity_id}, blocking=True)
        mock_api_client.update_remi.assert_awaited_once_with({"luminosity": 73})
        assert hass.states.get(physical.entity_id).state == "off"
        stored = next(
            item for item in async_get_restore_data(hass).async_get_stored_states()
            if item.state.entity_id == physical.entity_id
        )
        assert stored.extra_data.as_dict()["last_nonzero_luminosity"] == 73
        assert stored.state.state == "off"
        # Unload/reload uses the normal RestoreEntity removal cache, with a new coordinator.
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        mock_api_client.update_remi.reset_mock()
        await hass.services.async_call("light", "turn_on", {"entity_id": physical.entity_id}, blocking=True)
        mock_api_client.update_remi.assert_awaited_once_with({"luminosity": 73})
        assert hass.states.get(physical.entity_id).state == "off"
