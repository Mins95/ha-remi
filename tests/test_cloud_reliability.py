"""Complete alarm snapshots, partial cloud failures and actionable auth recovery."""
from __future__ import annotations

from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.urbanhello_remi_unofficial.api import RemiApiClient, RemiApiError, RemiAuthError
from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.coordinator import RemiDataUpdateCoordinator

from .conftest import MOCK_EVENT_DATA, MOCK_REMI_DATA, MOCK_REMI_ID


def _event(index: int) -> dict:
    return {
        "objectId": f"event{index:04d}", "name": f"Schedule {index}",
        "remi": {"__type": "Pointer", "className": "Remi", "objectId": MOCK_REMI_ID},
    }


def _client(*responses) -> RemiApiClient:
    client = RemiApiClient("test@example.invalid", "test", MagicMock())
    client.set_remi_id(MOCK_REMI_ID)
    client._request = AsyncMock(side_effect=responses)
    return client


async def test_alarm_pages_use_keyset_and_keep_every_owned_record():
    first = [_event(index) for index in range(100)]
    second = [_event(100), _event(101)]
    client = _client({"results": first}, {"results": second})

    assert await client.get_events() == first + second
    calls = client._request.await_args_list
    assert len(calls) == 2
    for call in calls:
        method, path, payload = call.args
        assert method == "POST" and path == "/parse/classes/Event"
        assert payload["_method"] == "GET"
        assert payload["limit"] == 100
        assert payload["order"] == "objectId"
        assert payload["where"]["remi"] == first[0]["remi"]
        assert "skip" not in payload
    assert "objectId" not in calls[0].args[2]["where"]
    assert calls[1].args[2]["where"]["objectId"] == {"$gt": "event0099"}


async def test_exactly_full_page_requires_an_empty_terminating_page():
    first = [_event(index) for index in range(100)]
    client = _client({"results": first}, {"results": []})
    assert await client.get_events() == first
    assert client._request.await_count == 2


async def test_empty_alarm_list_is_valid_and_does_not_request_more_pages():
    client = _client({"results": []})
    assert await client.get_events() == []
    assert client._request.await_count == 1


@pytest.mark.parametrize("owner", [
    "other-device", {"className": "Remi", "objectId": "other-device"},
    {"className": "Other", "objectId": MOCK_REMI_ID}, {}, True, [],
])
async def test_alarm_owner_mismatch_is_never_returned(owner):
    client = _client({"results": [{**_event(0), "remi": owner}]})
    with pytest.raises(RemiApiError) as error:
        await client.get_events()
    assert error.value.translation_key == "api_wrong_device"


async def test_legacy_alarm_without_expanded_owner_keeps_compatibility():
    record = {"objectId": "legacy", "name": "Existing alarm"}
    client = _client({"results": [record]})
    assert await client.get_events() == [record]


@pytest.mark.parametrize("response", [
    None, [], {}, {"results": None}, {"results": {}}, {"results": "bad"},
    {"results": [None]}, {"results": [True]}, {"results": [{}]},
    {"results": [{"objectId": ""}]}, {"results": [{"objectId": 1}]},
    {"results": [{"objectId": []}]}, {"results": [_event(0), _event(0)]},
    {"results": [_event(index) for index in range(101)]},
])
async def test_malformed_alarm_page_is_an_error_not_an_empty_snapshot(response):
    client = _client(response)
    with pytest.raises(RemiApiError) as error:
        await client.get_events()
    assert error.value.translation_key == "api_invalid_response"


@pytest.mark.parametrize("last_record", [_event(99), _event(1)])
async def test_duplicate_or_regressed_key_on_later_page_rejects_whole_snapshot(last_record):
    client = _client(
        {"results": [_event(index) for index in range(100)]},
        {"results": [last_record]},
    )
    with pytest.raises(RemiApiError) as error:
        await client.get_events()
    assert error.value.translation_key == "api_invalid_response"


async def test_second_page_failure_propagates_instead_of_returning_partial_alarms():
    failure = RemiApiError("Test read failed")
    client = _client({"results": [_event(index) for index in range(100)]}, failure)
    with pytest.raises(RemiApiError) as error:
        await client.get_events()
    assert error.value is failure
    assert client._request.await_count == 2


async def test_second_page_wrong_device_invalidates_first_page_too():
    client = _client(
        {"results": [_event(index) for index in range(100)]},
        {"results": [{**_event(100), "remi": {"className": "Remi", "objectId": "other"}}]},
    )
    with pytest.raises(RemiApiError) as error:
        await client.get_events()
    assert error.value.translation_key == "api_wrong_device"


async def test_alarm_pagination_has_a_hard_budget_without_returning_truncation():
    client = _client(*[
        {"results": [_event(page * 100 + index) for index in range(100)]}
        for page in range(10)
    ])
    with pytest.raises(RemiApiError) as error:
        await client.get_events()
    assert error.value.translation_key == "api_invalid_response"
    assert client._request.await_count == 10


async def test_failed_alarm_read_keeps_snapshot_but_refreshes_live_device(hass, mock_api_client):
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    previous = deepcopy(MOCK_EVENT_DATA)
    coordinator.async_set_updated_data({"remi": deepcopy(MOCK_REMI_DATA), "events": previous})
    coordinator.events_available = True
    fresh_remi = {**MOCK_REMI_DATA, "temp": 160, "rssi": -50}
    mock_api_client.get_remi.return_value = fresh_remi
    mock_api_client.get_events.side_effect = RemiApiError("Alarm read failed")

    await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    assert coordinator.remi == fresh_remi
    assert coordinator.events is previous
    assert coordinator.events_available is False

    # A later successful empty snapshot is the point where deletion is real.
    mock_api_client.get_events.side_effect = None
    mock_api_client.get_events.return_value = []
    await coordinator.async_refresh()
    assert coordinator.last_update_success is True
    assert coordinator.events_available is True
    assert coordinator.events == []


async def test_initial_alarm_failure_still_loads_live_state_without_valid_empty_snapshot(hass, mock_api_client):
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    mock_api_client.get_events.side_effect = RemiApiError("Alarm read failed")
    await coordinator.async_refresh()
    assert coordinator.last_update_success is True
    assert coordinator.remi == MOCK_REMI_DATA
    assert coordinator.events == []
    assert coordinator.events_available is False


async def test_device_failure_cannot_make_previous_device_data_look_fresh(hass, mock_api_client):
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    previous = {"remi": deepcopy(MOCK_REMI_DATA), "events": deepcopy(MOCK_EVENT_DATA)}
    coordinator.async_set_updated_data(previous)
    mock_api_client.get_remi.side_effect = RemiApiError("Device read failed")
    await coordinator.async_refresh()
    assert coordinator.last_update_success is False
    assert coordinator.data == previous
    assert coordinator.events_available is False


@pytest.mark.parametrize("failing_method", ["get_remi", "get_events", "get_config"])
async def test_auth_failure_in_any_poll_requires_reauthentication(hass, mock_api_client, failing_method):
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    getattr(mock_api_client, failing_method).side_effect = RemiAuthError("Expired session")
    with pytest.raises(ConfigEntryAuthFailed) as error:
        await coordinator._async_update_data()
    assert error.value.translation_domain == DOMAIN
    assert error.value.translation_key == "reauth_required"


@pytest.mark.parametrize("failing_method", ["get_faces", "get_config"])
async def test_static_auth_failure_is_actionable_at_setup(hass, mock_api_client, failing_method):
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    getattr(mock_api_client, failing_method).side_effect = RemiAuthError("Expired session")
    with pytest.raises(ConfigEntryAuthFailed) as error:
        await coordinator.async_setup()
    assert error.value.translation_key == "reauth_required"


async def test_auth_failure_has_priority_over_other_read_failure(hass, mock_api_client):
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    mock_api_client.get_remi.side_effect = RemiApiError("Device unavailable")
    mock_api_client.get_events.side_effect = RemiAuthError("Expired session")
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()
    assert coordinator.events_available is False


async def test_firmware_metadata_failure_does_not_hide_fresh_device_or_alarms(hass, mock_api_client):
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    mock_api_client.get_config.side_effect = RemiApiError("Metadata unavailable")
    result = await coordinator._async_update_data()
    assert result["remi"] == MOCK_REMI_DATA
    assert result["events"] == MOCK_EVENT_DATA
    assert coordinator.events_available is True
