"""Tests for the Remi number platform."""
from __future__ import annotations

from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.number import NumberMode
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial.api import RemiApiError
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

        assert len(added_entities) == 4
        for entity in added_entities:
            assert isinstance(entity, RemiNumberEntity)


class TestRemiNumberEntity:
    """Tests for RemiNumberEntity."""

    def test_volume_entity_unique_id(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[0])
        assert entity.unique_id == f"{MOCK_REMI_ID}_volume"

    def test_volume_entity_properties(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[0])
        assert entity.translation_key == "volume"
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
        assert entity.translation_key == "noise_threshold"
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
        assert entity.translation_key == "brightness"
        assert entity.icon == "mdi:brightness-6"
        assert entity.mode == NumberMode.SLIDER
        assert entity.native_min_value == 0
        assert entity.native_max_value == 100
        assert entity.native_step == 1

    @pytest.mark.parametrize("raw", [0, 60, 100])
    def test_brightness_native_value(self, mock_coordinator, raw):
        mock_coordinator.remi["luminosity"] = raw
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[2])
        assert entity.native_value == raw

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


class TestRemiFaceBrightnessNumber:
    """The night face control uses light_min, independently from luminosity."""

    @pytest.fixture
    def entity(self, mock_coordinator):
        description = next(
            item for item in NUMBER_DESCRIPTIONS if item.key == "face_brightness"
        )
        return RemiNumberEntity(mock_coordinator, description)

    def test_native_app_scale_and_identity(self, entity):
        assert entity.unique_id == f"{MOCK_REMI_ID}_face_brightness"
        assert entity.entity_description.translation_key == "face_brightness"
        assert entity.native_min_value == 1
        assert entity.native_max_value == 10
        assert entity.native_step == 1
        assert entity.native_unit_of_measurement is None
        assert entity.mode == NumberMode.SLIDER

    @pytest.mark.parametrize("value", [1, 5, 10, 7.0])
    def test_native_value_without_conversion(self, entity, mock_coordinator, value):
        mock_coordinator.remi["light_min"] = value
        assert entity.native_value == value

    def test_missing_field_is_unknown(self, entity):
        assert entity.native_value is None

    @pytest.mark.parametrize(
        "value",
        [None, True, False, "7", "", [], {}, 0, 11, 10**1000, 5.5, float("nan"), float("inf")],
    )
    def test_invalid_value_is_unknown(self, entity, mock_coordinator, value):
        mock_coordinator.remi["light_min"] = value
        assert entity.native_value is None

    @pytest.mark.parametrize("value", [1, 5, 10, 7.0])
    async def test_only_updates_light_min(self, entity, mock_coordinator, value):
        await entity.async_set_native_value(value)
        mock_coordinator.client.update_remi.assert_awaited_once_with(
            {"light_min": int(value)}
        )
        mock_coordinator.async_request_refresh.assert_awaited_once()

    @pytest.mark.parametrize(
        "value",
        [None, True, False, "7", 0, -1, 11, 10**1000, 5.5, float("nan"), float("inf")],
    )
    async def test_rejects_invalid_commands_before_cloud_write(
        self, entity, mock_coordinator, value,
    ):
        with pytest.raises(ServiceValidationError) as raised:
            await entity.async_set_native_value(value)
        assert raised.value.translation_key == "invalid_face_brightness"
        mock_coordinator.client.update_remi.assert_not_awaited()
        mock_coordinator.async_request_refresh.assert_not_awaited()


    async def test_cloud_error_is_propagated_without_refresh(self, entity, mock_coordinator):
        mock_coordinator.client.update_remi.side_effect = RemiApiError("Cloud unavailable")
        with pytest.raises(RemiApiError, match="Cloud unavailable"):
            await entity.async_set_native_value(7)
        mock_coordinator.async_request_refresh.assert_not_awaited()


async def test_real_setup_adds_face_brightness_and_retains_existing_brightness(
    hass, enable_custom_integrations, mock_api_client, mock_config_entry_data,
):
    """A real HA service updates only the face level and refreshes its state."""
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, title="Test REMI")
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    brightness = registry.async_get_or_create(
        "number", DOMAIN, f"{MOCK_REMI_ID}_brightness",
        config_entry=entry, suggested_object_id="retained_brightness",
    )
    data = deepcopy(MOCK_REMI_DATA)
    data["light_min"] = 7
    mock_api_client.get_remi.return_value = data

    async def update_remi(payload):
        data.update(payload)
        return {}

    mock_api_client.update_remi.side_effect = update_remi
    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert registry.async_get_entity_id(
            "number", DOMAIN, f"{MOCK_REMI_ID}_brightness"
        ) == brightness.entity_id
        face_id = registry.async_get_entity_id(
            "number", DOMAIN, f"{MOCK_REMI_ID}_face_brightness"
        )
        assert face_id is not None
        face = hass.states.get(face_id)
        assert face.state == "7"
        assert face.attributes["min"] == 1
        assert face.attributes["max"] == 10
        assert face.attributes["step"] == 1
        assert "unit_of_measurement" not in face.attributes
        assert hass.states.get(brightness.entity_id).state == "42"
        mock_api_client.update_remi.assert_not_awaited()

        await hass.services.async_call(
            "number", "set_value", {"entity_id": face_id, "value": 8}, blocking=True
        )
        await hass.async_block_till_done()
        mock_api_client.update_remi.assert_awaited_once_with({"light_min": 8})
        assert hass.states.get(face_id).state == "8"
        assert hass.states.get(brightness.entity_id).state == "42"


async def test_real_setup_removes_legacy_luminosity_entities(
    hass, enable_custom_integrations, mock_api_client, mock_config_entry_data,
):
    """Obsolete luminosity number and sensor entries are removed on load."""
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
