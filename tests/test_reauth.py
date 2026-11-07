"""Recover credentials without replacing the selected REMI or its registry IDs."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial.api import RemiApiError, RemiAuthError
from custom_components.urbanhello_remi_unofficial.const import (
    CONF_INSTALLATION_ID, CONF_REMI_ID, CONF_SESSION_TOKEN, DOMAIN,
)
from .conftest import MOCK_REMI_ID


@pytest.fixture(autouse=True)
def enable_integration(enable_custom_integrations):
    yield


@pytest.fixture
def entry(hass, mock_config_entry_data):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MOCK_REMI_ID, title="Nom choisi",
        data=mock_config_entry_data, options={"kept": True},
    )
    entry.add_to_hass(hass)
    return entry


async def begin(hass, entry, source):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": source, "entry_id": entry.entry_id},
        data=dict(entry.data) if source == "reauth" else None,
    )


@pytest.mark.parametrize("source", ["reauth", "reconfigure"])
async def test_credentials_update_keeps_entry_selected_device_and_entities(hass, entry, source):
    registry = er.async_get(hass)
    saved = registry.async_get_or_create(
        "sensor", DOMAIN, f"{MOCK_REMI_ID}_temperature", config_entry=entry,
        suggested_object_id="my_temperature",
    )
    saved = registry.async_update_entity(saved.entity_id, name="Ma température")
    original_entry_id = entry.entry_id
    client = MagicMock()
    # The app's current REMI is another device: keep the one HA already owns.
    client.login = AsyncMock(return_value=("new-token", "other-remi", ["other-remi", MOCK_REMI_ID]))
    client.get_remi = AsyncMock(return_value={"objectId": MOCK_REMI_ID})
    with (
        patch("custom_components.urbanhello_remi_unofficial.config_flow.RemiApiClient", return_value=client) as constructor,
        patch.object(hass.config_entries, "async_reload", return_value=True) as reload_entry,
    ):
        result = await begin(hass, entry, source)
        assert result["type"] == FlowResultType.FORM
        password = next(key for key in result["data_schema"].schema if key.schema == "password")
        assert password.default is vol.UNDEFINED
        assert entry.data["password"] not in repr(result)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"username": "new@example.com", "password": "new-password"}
        )
        await hass.async_block_till_done()
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == f"{source}_successful"
    client.set_remi_id.assert_called_once_with(MOCK_REMI_ID)
    client.get_remi.assert_awaited_once()
    assert constructor.call_args.args[3] == entry.data[CONF_INSTALLATION_ID]
    assert entry.entry_id == original_entry_id
    assert entry.unique_id == MOCK_REMI_ID
    assert entry.data[CONF_REMI_ID] == MOCK_REMI_ID
    assert entry.title == "Nom choisi"
    assert entry.options == {"kept": True}
    assert entry.data[CONF_SESSION_TOKEN] == "new-token"
    assert entry.data["password"] == "new-password"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert registry.async_get(saved.entity_id) == saved
    reload_entry.assert_awaited_once_with(original_entry_id)


@pytest.mark.parametrize("source", ["reauth", "reconfigure"])
@pytest.mark.parametrize("failure", ["wrong_account", "wrong_device", "auth", "network"])
async def test_failed_credential_validation_keeps_original_data(hass, entry, source, failure):
    original = dict(entry.data)
    client = MagicMock()
    client.login = AsyncMock(return_value=("new-token", MOCK_REMI_ID, [MOCK_REMI_ID]))
    client.get_remi = AsyncMock(return_value={"objectId": MOCK_REMI_ID})
    expected = "device_not_in_account"
    if failure == "wrong_account":
        client.login.return_value = ("new-token", "other", ["other"])
    elif failure == "wrong_device":
        client.get_remi.return_value = {"objectId": "other"}
    elif failure == "auth":
        client.login.side_effect = RemiAuthError("Invalid credentials")
        expected = "invalid_auth"
    else:
        client.get_remi.side_effect = RemiApiError("Unavailable")
        expected = "cannot_connect"
    with (
        patch("custom_components.urbanhello_remi_unofficial.config_flow.RemiApiClient", return_value=client),
        patch.object(hass.config_entries, "async_reload", return_value=True) as reload_entry,
    ):
        result = await begin(hass, entry, source)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"username": "new@example.com", "password": "new-password"}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": expected}
    assert dict(entry.data) == original
    reload_entry.assert_not_awaited()
    assert "new-password" not in repr(result)


async def test_setup_auth_failure_starts_home_assistant_reauth(hass, entry, mock_api_client):
    mock_api_client.get_faces.side_effect = RemiAuthError("Expired credentials")
    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state == ConfigEntryState.SETUP_ERROR
    assert any(
        flow["context"]["source"] == "reauth" and flow["context"]["entry_id"] == entry.entry_id
        for flow in hass.config_entries.flow.async_progress()
    )
