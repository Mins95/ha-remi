"""Stable alarm entities without guessing across ambiguous cloud replacements."""
from __future__ import annotations

from copy import deepcopy
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial.alarm_identity import (
    AlarmIdentityMap, AlarmIdentityStorageError, alarm_identity_store,
)
from custom_components.urbanhello_remi_unofficial.const import DOMAIN

from .conftest import MOCK_EVENT_DATA, MOCK_REMI_ID


@pytest.fixture(autouse=True)
def enable_integration(enable_custom_integrations):
    yield


def event(cloud_id, name="Morning"):
    return {"objectId": cloud_id, "name": name}


@pytest.mark.parametrize("before, after, expected", [
    ([event("old")], [event("new")], {"old": "new"}),
    ([event("same")], [event("same", "Renamed")], {"same": "same"}),
    # Duplicates among unchanged IDs count, not just the missing/new candidates.
    ([event("old"), event("kept")], [event("new"), event("kept")], {"new": "new", "kept": "kept"}),
    ([event("old"), event("other")], [event("new")], {"new": "new"}),
    ([event("old")], [event("new"), event("other")], {"new": "new", "other": "other"}),
    ([event("old")], [event("old"), event("new")], {"old": "old", "new": "new"}),
    ([event("old")], [event("new", "Renamed")], {"new": "new"}),
    ([event("old")], [event("new", "morning")], {"new": "new"}),
    ([event("old")], [event("new", "Morning ")], {"new": "new"}),
    ([event("old", "")], [event("new", "")], {"new": "new"}),
    ([event("old", " ")], [event("new", " ")], {"new": "new"}),
    ([event("old", None)], [event("new", None)], {"new": "new"}),
])
async def test_only_unique_exact_names_with_missing_old_ids_match(before, after, expected):
    identities = AlarmIdentityMap(MOCK_REMI_ID)
    assert await identities.async_reconcile(before)
    assert await identities.async_reconcile(after)
    assert {key: value["objectId"] for key, value in identities.logical_snapshot(after).items()} == expected


async def test_rename_with_same_id_is_remembered_for_the_next_rotation():
    identities = AlarmIdentityMap(MOCK_REMI_ID)
    for events in ([event("first")], [event("first", "Weekend")], [event("second", "Weekend")]):
        assert await identities.async_reconcile(events)
    assert identities.cloud_id("first") == "second"
    assert identities.retained_ids == {"first"}


async def test_reused_cloud_id_cannot_hijack_an_existing_logical_identity():
    identities = AlarmIdentityMap(MOCK_REMI_ID)
    await identities.async_reconcile([event("first")])
    await identities.async_reconcile([event("second")])
    current = [event("second"), event("first", "A different alarm")]
    await identities.async_reconcile(current)
    mapped = identities.logical_snapshot(current)
    assert mapped["first"]["objectId"] == "second"
    assert len(mapped) == 2
    new_key = next(key for key in mapped if key != "first")
    assert mapped[new_key]["objectId"] == "first"


@pytest.mark.parametrize("invalid", [
    None, {}, [None], [{"objectId": ""}], [event("duplicate"), event("duplicate")],
    [{**event("new"), "remi": {"className": "Remi", "objectId": "other-device"}}],
    [{**event("new"), "remi": {"className": "Other", "objectId": MOCK_REMI_ID}}],
    [{**event("new"), "remi": MOCK_REMI_ID}],
])
async def test_invalid_snapshot_cannot_change_or_delete_mappings(invalid):
    identities = AlarmIdentityMap(MOCK_REMI_ID)
    await identities.async_reconcile([event("old")])
    assert await identities.async_reconcile(invalid) is False
    assert identities.cloud_id("old") == "old"
    assert identities.retained_ids == {"old"}


async def test_store_survives_new_manager_and_keeps_unknown_legacy_ids(hass, hass_storage):
    store = alarm_identity_store(hass, "entry-one")
    identities = AlarmIdentityMap(MOCK_REMI_ID, entry_id="entry-one", store=store)
    await identities.async_load({"original", "unresolvable_legacy"})
    await identities.async_reconcile([event("original")])
    await identities.async_reconcile([event("replacement")])
    loaded = AlarmIdentityMap(MOCK_REMI_ID, entry_id="entry-one", store=alarm_identity_store(hass, "entry-one"))
    await loaded.async_load(set())
    await loaded.async_reconcile([event("third")])
    assert loaded.cloud_id("original") == "third"
    assert loaded.retained_ids == {"original", "unresolvable_legacy"}
    assert hass_storage[store.key]["data"]["records"]["original"]["cloud_id"] == "third"
    # Real deletion is still reconciled, but unexplained pre-store IDs are safe.
    await loaded.async_reconcile([])
    assert loaded.retained_ids == {"unresolvable_legacy"}


@pytest.mark.parametrize("change", [
    {"remi_id": "other-device"}, {"entry_id": "other-entry"}, {"records": []},
    {"records": {"a": {"cloud_id": "same", "name": "A"}, "b": {"cloud_id": "same", "name": "B"}}},
    {"records": {"a": {"cloud_id": "", "name": "A"}}},
    {"unresolved_ids": ["duplicate", "duplicate"]}, {"unresolved_ids": [[]]},
])
async def test_corrupt_or_wrong_scope_store_is_never_silently_replaced(hass, hass_storage, change):
    store = alarm_identity_store(hass, "entry-one")
    payload = {"entry_id": "entry-one", "remi_id": MOCK_REMI_ID, "records": {}, "unresolved_ids": [], **change}
    await store.async_save(payload)
    identities = AlarmIdentityMap(MOCK_REMI_ID, entry_id="entry-one", store=store)
    with pytest.raises(AlarmIdentityStorageError):
        await identities.async_load(set())
    assert hass_storage[store.key]["data"] == payload


async def test_silently_failed_store_write_never_publishes_new_identity(hass):
    store = alarm_identity_store(hass, "entry-one")
    identities = AlarmIdentityMap(MOCK_REMI_ID, entry_id="entry-one", store=store)
    await identities.async_load(set())
    await identities.async_reconcile([event("original")])
    with patch.object(store, "async_save", AsyncMock()):
        with pytest.raises(AlarmIdentityStorageError):
            await identities.async_reconcile([event("replacement")])
    assert identities.cloud_id("original") == "original"
    assert identities.logical_snapshot([event("replacement")]) is None
    # A later successful commit is enough to recover without changing identity.
    await identities.async_reconcile([event("replacement")])
    assert identities.cloud_id("original") == "replacement"


async def test_unchanged_snapshots_do_not_rewrite_storage(hass):
    store = alarm_identity_store(hass, "entry-one")
    identities = AlarmIdentityMap(MOCK_REMI_ID, entry_id="entry-one", store=store)
    await identities.async_load(set())
    await identities.async_reconcile([event("original")])
    with patch.object(store, "async_save", AsyncMock()) as save:
        await identities.async_reconcile([event("original")])
    save.assert_not_awaited()


def alarm_registry_ids(registry):
    return {
        domain: registry.async_get_entity_id(domain, DOMAIN, f"{MOCK_REMI_ID}_alarm_event_id_1{suffix}")
        for domain, suffix in (("switch", ""), ("time", "_time"))
    }


async def test_live_and_offline_rotations_preserve_registry_ids_names_and_commands(
    hass, mock_api_client, mock_config_entry_data, hass_storage,
):
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, unique_id=MOCK_REMI_ID)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    events = deepcopy(MOCK_EVENT_DATA)
    mock_api_client.get_events.return_value = events
    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        ids = alarm_registry_ids(registry)
        for domain, entity_id in ids.items():
            registry.async_update_entity(entity_id, name=f"My {domain}")
        originals = {domain: registry.async_get(entity_id) for domain, entity_id in ids.items()}
        events = [{**events[0], "objectId": "second_generation", "event_time": [8, 15]}]
        mock_api_client.get_events.return_value = events
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        for domain, entity_id in ids.items():
            assert registry.async_get(entity_id).id == originals[domain].id
            assert registry.async_get(entity_id).unique_id == originals[domain].unique_id
            assert registry.async_get(entity_id).name == f"My {domain}"
            assert hass.states.get(entity_id).attributes["event_id"] == "second_generation"
        assert registry.async_get(ids["switch"]).original_name == "08:15 · Morning Alarm"
        await hass.services.async_call("switch", "turn_off", {"entity_id": ids["switch"]}, blocking=True)
        mock_api_client.update_event.assert_awaited_with("second_generation", {"enabled": False})
        await hass.services.async_call("time", "set_value", {"entity_id": ids["time"], "time": "09:00:00"}, blocking=True)
        mock_api_client.update_event.assert_awaited_with("second_generation", {"event_time": [9, 0]})
        await hass.async_block_till_done()

        assert await hass.config_entries.async_unload(entry.entry_id)
        mock_api_client.get_events.return_value = [{**events[0], "objectId": "third_generation"}]
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert alarm_registry_ids(registry) == ids
        for domain, entity_id in ids.items():
            assert registry.async_get(entity_id).id == originals[domain].id
            assert registry.async_get(entity_id).name == f"My {domain}"
            assert hass.states.get(entity_id).attributes["event_id"] == "third_generation"
        alarms = [item for item in er.async_entries_for_config_entry(registry, entry.entry_id) if item.domain in {"switch", "time"}]
        assert len(alarms) == 2

        mock_api_client.get_events.return_value = []
        await hass.data[DOMAIN][entry.entry_id].async_refresh()
        await hass.async_block_till_done()
        assert all(registry.async_get(entity_id) is None for entity_id in ids.values())


async def test_failed_snapshot_or_persistence_never_cleans_up_entities(
    hass, mock_api_client, mock_config_entry_data,
):
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, unique_id=MOCK_REMI_ID)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        ids = alarm_registry_ids(registry)
        coordinator = hass.data[DOMAIN][entry.entry_id]
        original = coordinator.events
        mock_api_client.get_events.return_value = [event("bad"), event("bad")]
        await coordinator.async_refresh()
        assert not coordinator.events_available
        assert coordinator.events is original
        mock_api_client.get_events.return_value = []
        with patch.object(coordinator.alarm_identities._store, "async_save", AsyncMock()):
            await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert not coordinator.events_available
        assert all(registry.async_get(entity_id) is not None for entity_id in ids.values())
        assert all(hass.states.get(entity_id).state == "unavailable" for entity_id in ids.values())
        assert coordinator.alarm_identities.cloud_id("event_id_1") == "event_id_1"
        for service in ("update_alarm", "delete_alarm"):
            with pytest.raises(HomeAssistantError):
                await hass.services.async_call(DOMAIN, service, {"event_id": "event_id_1"}, blocking=True)
        mock_api_client.update_event.assert_not_awaited()
        mock_api_client.delete_event.assert_not_awaited()


async def test_missing_store_protects_unresolvable_existing_registry_entities(
    hass, mock_api_client, mock_config_entry_data,
):
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, unique_id=MOCK_REMI_ID)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    old = registry.async_get_or_create("switch", DOMAIN, f"{MOCK_REMI_ID}_alarm_lost_mapping", config_entry=entry)
    registry.async_update_entity(old.entity_id, name="Do not delete my automation target")
    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert registry.async_get(old.entity_id).id == old.id
        assert registry.async_get(old.entity_id).name == "Do not delete my automation target"
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert registry.async_get(old.entity_id).id == old.id


async def test_corrupt_store_blocks_setup_without_reassigning_entities(
    hass, mock_api_client, mock_config_entry_data,
):
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, unique_id=MOCK_REMI_ID)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    old = registry.async_get_or_create("switch", DOMAIN, f"{MOCK_REMI_ID}_alarm_old", config_entry=entry)
    await alarm_identity_store(hass, entry.entry_id).async_save({"remi_id": "another-device"})
    with patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client):
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert registry.async_get(old.entity_id).id == old.id
    mock_api_client.get_events.assert_not_awaited()
