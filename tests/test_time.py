"""Alarm time edits preserve the rest of the REMI schedule."""
from datetime import time, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.time import (
    RemiAlarmTime, alarm_time, async_setup_entry,
)
from .conftest import MOCK_EVENT_DATA, MOCK_REMI_DATA, MOCK_REMI_ID


@pytest.fixture
def coordinator(hass, mock_api_client):
    return MagicMock(
        hass=hass, client=mock_api_client, remi=MOCK_REMI_DATA,
        events=[dict(MOCK_EVENT_DATA[0])], last_update_success=True, events_available=True,
        async_request_refresh=AsyncMock(),
    )


@pytest.mark.parametrize("value", [None, [], [7], [24, 0], [7, 60],
                                        [True, 30], [7, "30"], [7, 30, 0]])
def test_bad_cloud_time_is_unknown(value):
    assert alarm_time({"event_time": value}) is None


async def test_edit_changes_only_clock_time(coordinator):
    entity = RemiAlarmTime(coordinator, coordinator.events[0])
    assert entity.native_value == time(7, 30)
    assert entity.unique_id == f"{MOCK_REMI_ID}_alarm_event_id_1_time"
    assert entity.available
    await entity.async_set_value(time(8, 15))
    coordinator.client.update_event.assert_awaited_once_with(
        "event_id_1", {"event_time": [8, 15]}
    )
    coordinator.async_request_refresh.assert_awaited_once()
    # No optimistic value: retain the last confirmed reading until the refresh.
    assert entity.native_value == time(7, 30)


async def test_missing_alarm_cannot_be_edited(coordinator):
    entity = RemiAlarmTime(coordinator, coordinator.events[0])
    coordinator.events = []
    assert not entity.available
    with pytest.raises(ServiceValidationError) as error:
        await entity.async_set_value(time(8))
    assert error.value.translation_domain == DOMAIN
    assert error.value.translation_key == "alarm_not_found"
    coordinator.client.update_event.assert_not_called()


@pytest.mark.parametrize("value", [time(8, 0, 1), time(8, tzinfo=timezone.utc)])
async def test_precision_or_timezone_not_silently_discarded(coordinator, value):
    entity = RemiAlarmTime(coordinator, coordinator.events[0])
    with pytest.raises(ServiceValidationError) as error:
        await entity.async_set_value(value)
    assert error.value.translation_domain == DOMAIN
    assert error.value.translation_key == "invalid_alarm_clock_time"
    coordinator.client.update_event.assert_not_called()


async def test_alarm_lifecycle_and_failed_poll(hass, coordinator):
    entry = MockConfigEntry(domain=DOMAIN, data={}, title="REMI")
    entry.add_to_hass(hass)
    hass.data[DOMAIN] = {entry.entry_id: coordinator}
    add = MagicMock()
    await async_setup_entry(hass, entry, add)
    assert len(add.call_args.args[0]) == 1
    listener = coordinator.async_add_listener.call_args.args[0]
    listener()
    assert add.call_count == 1
    registry = er.async_get(hass)
    registered = registry.async_get_or_create(
        "time", DOMAIN, f"{MOCK_REMI_ID}_alarm_event_id_1_time", config_entry=entry
    )
    coordinator.events = []
    coordinator.last_update_success = False
    listener()
    assert registry.async_get(registered.entity_id) is not None
    coordinator.last_update_success = True
    listener()
    assert registry.async_get(registered.entity_id) is None
    coordinator.events = [dict(MOCK_EVENT_DATA[0])]
    listener()
    assert add.call_count == 2
