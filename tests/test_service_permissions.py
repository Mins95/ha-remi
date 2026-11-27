"""Exercise REMI's device-scoped actions with actual HA caller contexts."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import Context
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial import _register_services
from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.nap import async_register_nap_services


@pytest.fixture
def device(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    er.async_get(hass).async_get_or_create(
        "sensor", DOMAIN, "test_remi_temperature",
        suggested_object_id="test_remi_temperature", config_entry=entry,
    )
    coordinator = MagicMock(config_entry=entry)
    coordinator.client.remi_id = "test_remi"
    coordinator.client.get_naps = AsyncMock(return_value=[])
    coordinator.client.create_event = AsyncMock()
    coordinator.history_coordinator.async_get_history = AsyncMock(return_value={"logs": []})
    hass.data[DOMAIN] = {entry.entry_id: coordinator}
    _register_services(hass)
    async_register_nap_services(hass)
    return coordinator


async def test_read_only_user_can_view_nights_and_timers(hass, hass_read_only_user, device):
    for action in ("get_history", "list_naps"):
        await hass.services.async_call(DOMAIN, action, {}, blocking=True, return_response=True,
                                       context=Context(user_id=hass_read_only_user.id))
    device.history_coordinator.async_get_history.assert_awaited_once()
    device.client.get_naps.assert_awaited_once()


@pytest.mark.parametrize(("action", "data"), [
    ("create_alarm", {"name": "Morning", "time": "07:30"}),
    ("test_alarm", {"remi_id": "test_remi", "event_id": "event1"}),
    ("create_nap", {"name": "Nap", "duration_minutes": 10}),
    ("get_history", {"sync": True}),
])
async def test_read_only_user_cannot_send_commands(hass, hass_read_only_user, device, action, data):
    with pytest.raises(Unauthorized):
        await hass.services.async_call(DOMAIN, action, data, blocking=True,
                                       return_response=action == "get_history",
                                       context=Context(user_id=hass_read_only_user.id))
    device.history_coordinator.async_get_history.assert_not_called()
    device.client.create_event.assert_not_called()
    device.client.create_nap.assert_not_called()


async def test_restricted_reader_is_checked_against_selected_device(hass, device, monkeypatch):
    permissions = MagicMock()
    permissions.access_all_entities.return_value = False
    permissions.check_entity.return_value = False
    user = SimpleNamespace(is_admin=False, is_active=True, permissions=permissions)
    monkeypatch.setattr(hass.auth, "async_get_user", AsyncMock(return_value=user))
    async def request():
        await hass.services.async_call(DOMAIN, "get_history", {"remi_id": "test_remi"},
                                       blocking=True, return_response=True, context=Context(user_id="restricted"))
    with pytest.raises(Unauthorized):
        await request()
    device.history_coordinator.async_get_history.assert_not_called()
    sensor_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, "test_remi_temperature")
    permissions.check_entity.assert_called_once_with(sensor_id, "read")
    permissions.check_entity.return_value = True
    await request()
    device.history_coordinator.async_get_history.assert_awaited_once()


async def test_export_requires_read_access_even_with_control(hass, device, monkeypatch):
    permissions = MagicMock()
    permissions.access_all_entities.return_value = True
    permissions.check_entity.side_effect = lambda entity_id, policy: policy == "control"
    user = SimpleNamespace(is_admin=False, is_active=True, permissions=permissions)
    monkeypatch.setattr(hass.auth, "async_get_user", AsyncMock(return_value=user))
    with pytest.raises(Unauthorized):
        await hass.services.async_call(DOMAIN, "get_history", {"sync": True}, blocking=True,
                                       return_response=True, context=Context(user_id="restricted"))
    device.history_coordinator.async_get_history.assert_not_called()
