"""Optional telemetry stays numeric, missing-aware and safe to share."""
from types import SimpleNamespace
import json

import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.diagnostics import async_get_config_entry_diagnostics
from custom_components.urbanhello_remi_unofficial.sensor import SENSOR_DESCRIPTIONS
from custom_components.urbanhello_remi_unofficial.telemetry import parse_connection_telemetry


def test_supported_formats_and_real_zeroes():
    expected = {"day_reconnection_count": 0, "gettime_shift_s": -1.25}
    assert parse_connection_telemetry("day_reconnection_count:0 gettime_shift_s:-1.25 account:private") == expected
    assert parse_connection_telemetry({**expected, "account": "private"}) == expected


@pytest.mark.parametrize("value", [None, [], True, "x" * 8193, {str(i): i for i in range(129)}])
def test_missing_or_oversized_bundle(value):
    assert parse_connection_telemetry(value) == {}


@pytest.mark.parametrize("value", [True, False, None, [], {}, float("nan"), float("inf"), 10**400, -1, 1.5, "1e2", "NaN", "1 2", "-2"])
def test_invalid_reconnection_count(value):
    assert parse_connection_telemetry({"day_reconnection_count": value}) == {}


def test_duplicate_known_keys_are_ambiguous():
    assert parse_connection_telemetry("day_reconnection_count:2 day_reconnection_count:3 gettime_shift_s:0") == {"gettime_shift_s": 0}


def test_unconfirmed_disconnection_unit_is_not_invented():
    assert parse_connection_telemetry({"day_disconnection_time": 42}) == {"day_disconnection_time": 42}


def test_optional_sensors_do_not_claim_missing_zeroes():
    for description in SENSOR_DESCRIPTIONS:
        if description.key in {"daily_reconnections", "reported_clock_shift"}:
            assert description.value_fn({}) is None
            assert description.entity_registry_enabled_default is False
            assert description.entity_category.value == "diagnostic"


async def test_diagnostics_allowlist_excludes_credentials_and_household_data(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"username": "SECRET", "password": "SECRET", "session_token": "SECRET"})
    remi = {key: "SECRET" for key in ("name", "objectId", "ipv4Address", "uniqueID", "token", "timezone")}
    remi.update(online=True, alive=False, dataBundle={"day_reconnection_count": 3, "day_disconnection_time": 7, "unknown": "SECRET"})
    hass.data[DOMAIN] = {entry.entry_id: SimpleNamespace(remi=remi, last_update_success=False, events_available=True, history_coordinator=None)}
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert "SECRET" not in json.dumps(result)
    assert result["connection_telemetry"]["day_reconnection_count"] == 3
    assert result["units"]["day_disconnection_time"] == "unconfirmed"
    assert result["device"] == {"online": True, "alive": False}
    assert result["cloud_read_successful"] is False


async def test_diagnostics_of_unloaded_entry(hass):
    result = await async_get_config_entry_diagnostics(hass, MockConfigEntry(domain=DOMAIN))
    assert result == {"loaded": False}


async def test_history_not_yet_read_does_not_claim_success(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    history = SimpleNamespace(data=None, last_update_success=True)
    hass.data[DOMAIN] = {entry.entry_id: SimpleNamespace(remi={}, last_update_success=True, events_available=True, history_coordinator=history)}
    assert (await async_get_config_entry_diagnostics(hass, entry))["history_read_successful"] is None
    history.data = {"logs": []}
    assert (await async_get_config_entry_diagnostics(hass, entry))["history_read_successful"] is True
    history.last_update_success = False
    assert (await async_get_config_entry_diagnostics(hass, entry))["history_read_successful"] is False
