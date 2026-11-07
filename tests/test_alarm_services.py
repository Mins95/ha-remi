"""Validate the app's event schema, including the weekday index conversion."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.urbanhello_remi_unofficial import _register_services
from custom_components.urbanhello_remi_unofficial.const import DOMAIN


@pytest.fixture
def coordinator(hass):
    coordinator = MagicMock(
        events=[{"objectId": "alarm"}], async_request_refresh=AsyncMock()
    )
    coordinator.client.create_event = AsyncMock()
    coordinator.client.update_event = AsyncMock()
    hass.data[DOMAIN] = {"entry": coordinator}
    _register_services(hass)
    return coordinator


async def test_create_uses_app_fields(hass, coordinator):
    await hass.services.async_call(DOMAIN, "create_alarm", {
        "name": "Week morning", "time": "07:30", "repeat": [1, 2, 3, 4, 5]
    }, blocking=True)
    coordinator.client.create_event.assert_awaited_once_with({
        "name": "Week morning", "event_time": [7, 30], "enabled": True,
        "recurrence": [1, 1, 1, 1, 1, 0, 0],
    })


async def test_update_weekend_and_time_without_overwriting_other_fields(hass, coordinator):
    await hass.services.async_call(DOMAIN, "update_alarm", {
        "event_id": "alarm", "time": "09:00:00", "repeat": [0, 6]
    }, blocking=True)
    coordinator.client.update_event.assert_awaited_once_with("alarm", {
        "event_time": [9, 0], "recurrence": [0, 0, 0, 0, 0, 1, 1],
    })


@pytest.mark.parametrize("face_define", ["awake", "FACE_DAY"])
async def test_create_face_selector_and_legacy_value(hass, coordinator, face_define):
    """Translated selectors and existing automations send the same cloud face."""
    await hass.services.async_call(DOMAIN, "create_alarm", {
        "name": "Morning", "time": "07:30", "face_define": face_define,
    }, blocking=True)
    coordinator.client.create_event.assert_awaited_once_with({
        "name": "Morning", "event_time": [7, 30], "enabled": True,
        "recurrence": [0, 0, 0, 0, 0, 0, 0],
        "face": {"__type": "Pointer", "className": "Face", "objectId": "fIjF0yWRxX"},
    })


@pytest.mark.parametrize("face_define", ["awake", "FACE_DAY"])
async def test_update_face_selector_and_legacy_value(hass, coordinator, face_define):
    """A translated face choice only updates the existing alarm's face."""
    await hass.services.async_call(DOMAIN, "update_alarm", {
        "event_id": "alarm", "face_define": face_define,
    }, blocking=True)
    coordinator.client.update_event.assert_awaited_once_with("alarm", {
        "face": {"__type": "Pointer", "className": "Face", "objectId": "fIjF0yWRxX"},
    })


@pytest.mark.parametrize("value", ["invalid", "24:00", "07:60", "07:30:15",
                                   "2026-02-20T07:00:00Z", "07:30+02:00"])
async def test_invalid_or_ambiguous_time_does_not_write(hass, coordinator, value):
    with pytest.raises(ServiceValidationError) as error:
        await hass.services.async_call(DOMAIN, "update_alarm", {
            "event_id": "alarm", "time": value
        }, blocking=True)
    assert error.value.translation_domain == DOMAIN
    assert error.value.translation_key == "invalid_alarm_clock_time"
    coordinator.client.update_event.assert_not_called()
