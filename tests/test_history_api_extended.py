"""Bound history catalogues and explicit exports without contacting a REMI."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.translation import async_get_translations

from custom_components.urbanhello_remi_unofficial import _register_services
from custom_components.urbanhello_remi_unofficial.api import (
    RemiApiClient,
    RemiApiError,
    _TransientApiError,
)
from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.history_api import (
    MAX_HISTORY_LOGS,
    MAX_HISTORY_REPORTS,
    RemiHistoryApiMixin,
    RemiHistoryError,
    validate_history_limit,
    validate_history_report_id,
    validate_report_limit,
)

REMI_ID = "test-remi"
OWNER = {"__type": "Pointer", "className": "Remi", "objectId": REMI_ID}


class FakeClient(RemiHistoryApiMixin):
    def __init__(self):
        self._remi_id = REMI_ID
        self._request = AsyncMock(return_value={"results": []})
        self.update_remi = AsyncMock(return_value={"updatedAt": "2026-11-01T12:00:00Z"})


async def test_sixty_metadata_records_keep_scope_and_default_budget():
    client = FakeClient()
    records = [{"objectId": f"report-{index}", "remi": OWNER} for index in range(60)]
    client._request.return_value = {"results": records}
    assert await client.get_history_logs(MAX_HISTORY_REPORTS) == records
    client._request.assert_awaited_once_with("POST", "/parse/classes/noise_logs", {
        "_method": "GET", "limit": 60, "order": "-timestamp",
        "where": {"$or": [{"remi": OWNER}, {"remi": REMI_ID}]},
    })
    client._request.return_value = {"results": []}
    await client.get_history_logs()
    assert client._request.call_args.args[2]["limit"] == MAX_HISTORY_LOGS == 2
    client.update_remi.assert_not_awaited()


@pytest.mark.parametrize("limit", [0, 61, -1, True, 1.0, "60", None])
async def test_metadata_budget_rejects_bad_inputs_before_request(limit):
    client = FakeClient()
    with pytest.raises(RemiHistoryError):
        await client.get_history_logs(limit)
    client._request.assert_not_awaited()


def test_chart_budget_stays_separate_from_metadata_budget():
    validate_report_limit(60)
    validate_history_limit(2)
    with pytest.raises(RemiHistoryError):
        validate_history_limit(3)


@pytest.mark.parametrize("kind", ["foreign_owner", "duplicate", "oversized"])
async def test_larger_catalogue_does_not_relax_response_validation(kind):
    client = FakeClient()
    records = [{"objectId": f"report-{index}", "remi": OWNER} for index in range(60)]
    if kind == "foreign_owner":
        records[-1] = {**records[-1], "remi": "another-device"}
    elif kind == "duplicate":
        records[-1] = records[0]
    else:
        records.append({"objectId": "extra", "remi": OWNER})
    client._request.return_value = {"results": records}
    with pytest.raises(RemiHistoryError):
        await client.get_history_logs(60)


async def test_sixty_sleep_references_are_filtered_by_owner_and_ids():
    client = FakeClient()
    ids = [f"sleep-{index}" for index in range(60)]
    records = [{"objectId": identifier, "remi": OWNER} for identifier in ids]
    client._request.return_value = {"results": records}
    assert await client.get_history_sleep_info(ids) == records
    client._request.assert_awaited_once_with("POST", "/parse/classes/SleepInfo", {
        "_method": "GET", "limit": 60,
        "where": {"objectId": {"$in": ids},
                  "$or": [{"remi": OWNER}, {"remi": REMI_ID}]},
    })
    client._request.return_value = {"results": [{"objectId": "unrequested", "remi": OWNER}]}
    with pytest.raises(RemiHistoryError):
        await client.get_history_sleep_info(ids)


@pytest.mark.parametrize("ids", [[f"sleep-{i}" for i in range(61)], ["../sleep"], [True]])
async def test_sleep_reference_budget_and_syntax_checked_before_request(ids):
    client = FakeClient()
    with pytest.raises(RemiHistoryError):
        await client.get_history_sleep_info(ids)
    client._request.assert_not_awaited()


async def test_duplicate_sleep_references_only_query_unique_records():
    client = FakeClient()
    await client.get_history_sleep_info(["sleep-1", "sleep-1"])
    payload = client._request.call_args.args[2]
    assert payload["limit"] == 1
    assert payload["where"]["objectId"] == {"$in": ["sleep-1"]}


@pytest.mark.parametrize("identifier", [None, True, 1, "", "../report", "report/1", "x" * 129, "report\n"])
def test_report_identifier_validation(identifier):
    with pytest.raises(RemiHistoryError):
        validate_history_report_id(identifier)


@pytest.mark.parametrize("nonce", [0, 999])
async def test_explicit_export_uses_the_app_command_once(nonce):
    client = FakeClient()
    with patch("custom_components.urbanhello_remi_unofficial.history_api.random.randrange", return_value=nonce):
        response = await client.request_history_sync()
    assert response == client.update_remi.return_value
    client.update_remi.assert_awaited_once_with({"cmd": f"push_logs:{nonce}"})
    client._request.assert_not_awaited()


async def test_consecutive_exports_do_not_reuse_the_same_nonce():
    client = FakeClient()
    with patch("custom_components.urbanhello_remi_unofficial.history_api.random.randrange", return_value=999):
        await client.request_history_sync()
        await client.request_history_sync()
    assert [call.args[0] for call in client.update_remi.await_args_list] == [
        {"cmd": "push_logs:999"}, {"cmd": "push_logs:0"},
    ]


@pytest.mark.parametrize("identifier", [None, "", "../another-device"])
async def test_export_requires_a_valid_selected_device(identifier):
    client = FakeClient()
    client._remi_id = identifier
    with pytest.raises(RemiHistoryError):
        await client.request_history_sync()
    client.update_remi.assert_not_awaited()


@pytest.mark.parametrize("error", [TimeoutError(), _TransientApiError("temporary")])
async def test_export_is_not_retried_by_the_real_api_client(error):
    client = RemiApiClient("example", "example", MagicMock())
    client.set_remi_id(REMI_ID)
    client._request_once = AsyncMock(side_effect=error)
    with patch("custom_components.urbanhello_remi_unofficial.history_api.random.randrange", return_value=5):
        with pytest.raises(RemiApiError):
            await client.request_history_sync()
    client._request_once.assert_awaited_once_with(
        "PUT", f"/parse/classes/Remi/{REMI_ID}", {"cmd": "push_logs:5"}, True,
    )


@pytest.fixture
def coordinator(hass):
    coordinator = MagicMock()
    coordinator.client.remi_id = REMI_ID
    coordinator.history_coordinator.async_get_history = AsyncMock(return_value={"logs": []})
    hass.data[DOMAIN] = {"entry": coordinator}
    _register_services(hass)
    return coordinator


async def test_history_service_keeps_non_writing_defaults(hass, coordinator):
    response = await hass.services.async_call(
        DOMAIN, "get_history", {}, blocking=True, return_response=True,
    )
    assert response == {"logs": []}
    coordinator.history_coordinator.async_get_history.assert_awaited_once_with(
        2, report_id=None, include_series=True, refresh=False, sync=False,
    )


@pytest.mark.parametrize("data,expected", [
    ({"limit": 60, "include_series": False}, (60, None, False, False, False)),
    ({"report_id": "report-1", "refresh": True}, (2, "report-1", True, True, False)),
    ({"limit": 1, "sync": True}, (1, None, True, False, True)),
])
async def test_history_service_forwards_explicit_options(hass, coordinator, data, expected):
    await hass.services.async_call(DOMAIN, "get_history", data, blocking=True, return_response=True)
    limit, report_id, include_series, refresh, sync = expected
    coordinator.history_coordinator.async_get_history.assert_awaited_once_with(
        limit, report_id=report_id, include_series=include_series, refresh=refresh, sync=sync,
    )


@pytest.mark.parametrize("data", [
    {"limit": 61}, {"limit": 1.5}, {"limit": True},
    {"report_id": "../report", "sync": True}, {"report_id": True},
    {"sync": "unexpected"}, {"refresh": {}}, {"include_series": []},
])
async def test_invalid_service_inputs_cannot_reach_a_sync(hass, coordinator, data):
    with pytest.raises((vol.Invalid, HomeAssistantError)):
        await hass.services.async_call(DOMAIN, "get_history", data, blocking=True, return_response=True)
    coordinator.history_coordinator.async_get_history.assert_not_awaited()


async def test_history_service_routes_the_selected_device(hass, coordinator):
    other = MagicMock()
    other.client.remi_id = "other-device"
    other.history_coordinator.async_get_history = AsyncMock(return_value={"logs": []})
    hass.data[DOMAIN]["other"] = other
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN, "get_history", {"sync": True}, blocking=True, return_response=True,
        )
    await hass.services.async_call(
        DOMAIN, "get_history", {"remi_id": "other-device", "sync": True},
        blocking=True, return_response=True,
    )
    coordinator.history_coordinator.async_get_history.assert_not_awaited()
    other.history_coordinator.async_get_history.assert_awaited_once_with(
        2, report_id=None, include_series=True, refresh=False, sync=True,
    )


@pytest.mark.parametrize("language", ["en", "fr"])
async def test_new_history_action_fields_are_translated(hass, enable_custom_integrations, language):
    resources = await async_get_translations(hass, language, "services", {DOMAIN})
    prefix = f"component.{DOMAIN}.services.get_history.fields"
    for field in ("report_id", "include_series", "refresh", "sync"):
        assert resources[f"{prefix}.{field}.name"]
        assert resources[f"{prefix}.{field}.description"]
    assert "12" in resources[f"{prefix}.sync.description"]
    assert "60" in resources[f"{prefix}.limit.description"]
