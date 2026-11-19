"""Persistence, freshness and read-only catchup for the REMI sleep archive."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.history import RemiHistoryCoordinator
from custom_components.urbanhello_remi_unofficial.history_api import RemiHistoryError
from custom_components.urbanhello_remi_unofficial.history_store import CONF_HISTORY_NIGHTS, history_store

from .test_history import LOG, REMI_ID


def dated_log(days_ago):
    day = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {
        **deepcopy(LOG), "objectId": f"log-{days_ago}", "timestamp": day.isoformat(),
        "updatedAt": day.isoformat(), "sleepInfo": None,
    }


def coordinator_for(hass, entry, logs):
    client = SimpleNamespace(
        remi_id=REMI_ID, get_history_logs=AsyncMock(return_value=logs),
        get_history_sleep_info=AsyncMock(return_value=[]),
        get_history_file=AsyncMock(return_value=bytes([160]) * 720),
        request_history_sync=AsyncMock(),
    )
    device = SimpleNamespace(remi={"objectId": REMI_ID, "timezone": "Europe/Paris"}, faces=[])
    return RemiHistoryCoordinator(hass, client, device, entry=entry)


async def test_archive_restores_curves_without_network_even_when_score_absent(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    first = coordinator_for(hass, entry, [dated_log(1)])
    await first.async_refresh()
    await first._backfill
    fetched_at = first.data["fetched_at"]
    stored = await history_store(hass, entry.entry_id).async_load()
    assert "https://" not in str(stored)
    assert "sleepInfo" not in str(stored)
    await first.async_shutdown()

    restored = coordinator_for(hass, entry, [])
    assert await restored.async_load_archive()
    result = await restored.async_get_history(report_id="log-1")
    restored.client.get_history_logs.assert_not_called()
    restored.client.get_history_file.assert_not_called()
    assert result["source"] == "local_archive"
    assert result["fetched_at"] == fetched_at
    report = result["logs"][0]
    assert report["sleep_score"] is None
    assert report["series_available"]
    assert report["series"]["temperature"]["samples"][0]["value"] == pytest.approx(21.3725)
    assert report["series"]["light"]["status"] == "missing"
    restored.client.request_history_sync.side_effect = RemiHistoryError()
    restored.client.get_history_logs.side_effect = RemiHistoryError()
    refreshed = await restored.async_get_history(sync=True)
    assert refreshed["sync_status"] == "failed"
    assert refreshed["source"] == "local_archive" and refreshed["fetched_at"] == fetched_at
    with pytest.raises(RemiHistoryError):
        await restored.async_get_history(report_id="unknown", sync=True)
    restored.client.request_history_sync.assert_awaited_once()


async def test_retention_reduction_and_disable_purge_cached_data_offline(hass):
    entry = MockConfigEntry(domain=DOMAIN, options={CONF_HISTORY_NIGHTS: 3})
    source = coordinator_for(hass, entry, [dated_log(i) for i in range(6)])
    await source.async_refresh()
    await source._backfill
    assert len(source._archive.reports) == 3
    shorter = MockConfigEntry(domain=DOMAIN, entry_id=entry.entry_id, options={CONF_HISTORY_NIGHTS: 1})
    reduced = coordinator_for(hass, shorter, [])
    assert await reduced.async_load_archive()
    assert list(reduced._archive.reports) == ["log-0"]
    optout = MockConfigEntry(domain=DOMAIN, entry_id=entry.entry_id, options={CONF_HISTORY_NIGHTS: 0})
    disabled = coordinator_for(hass, optout, [])
    assert not await disabled.async_load_archive()
    assert await history_store(hass, entry.entry_id).async_load() is None
    await disabled.async_refresh()
    assert await history_store(hass, entry.entry_id).async_load() is None


async def test_backfill_is_bounded_retries_revisions_and_preserves_last_good_file(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    logs = [dated_log(i) for i in range(4)]
    history = coordinator_for(hass, entry, logs)
    await history.async_refresh()
    await history._backfill
    assert history.client.get_history_file.await_count == 4
    await history.async_refresh()
    await history._backfill
    assert history.client.get_history_file.await_count == 8
    await history.async_refresh()
    await history._backfill
    assert history.client.get_history_file.await_count == 8
    logs[0]["updatedAt"] = datetime.now(timezone.utc).isoformat()
    history.client.get_history_file.side_effect = RemiHistoryError()
    await history.async_refresh()
    await history._backfill
    response = await history.async_get_history(report_id="log-0")
    old = response["logs"][0]["series"]["temperature"]
    assert old["outdated"] and old["source"] == "local_archive"
    assert old["samples"][0]["raw_value"] == 160
    offline = coordinator_for(hass, entry, [])
    assert await offline.async_load_archive()
    assert (await offline.async_get_history(report_id="log-0"))["logs"][0]["series"]["temperature"]["outdated"]
    history.client.get_history_file.side_effect = None
    history.client.get_history_file.return_value = bytes([170]) * 720
    await history.async_refresh()
    await history._backfill
    updated = (await history.async_get_history(report_id="log-0"))["logs"][0]
    assert updated["series"]["temperature"]["samples"][0]["raw_value"] == 170
    history.client.request_history_sync.assert_not_awaited()


async def test_another_device_cannot_read_this_entry_archive(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    first = coordinator_for(hass, entry, [dated_log(0)])
    await first.async_refresh()
    await first._backfill
    other = coordinator_for(hass, entry, [])
    other._archive.remi_id = "different-remi"
    assert not await other.async_load_archive()
    assert not other._archive.reports


async def test_empty_replacement_does_not_erase_previous_curve(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    log = dated_log(0)
    original_export = log["updatedAt"]
    history = coordinator_for(hass, entry, [log])
    await history.async_refresh()
    await history._backfill
    log["updatedAt"] = datetime.now(timezone.utc).isoformat()
    history.client.get_history_file.return_value = b""
    await history.async_refresh()
    await history._backfill
    report = (await history.async_get_history(report_id="log-0"))["logs"][0]
    assert report["series"]["temperature"]["outdated"]
    assert report["series"]["temperature"]["updated_at"] == original_export
    assert report["series"]["temperature"]["received_at"]
    assert report["series"]["temperature"]["samples"][0]["raw_value"] == 160
    del log["tempData"]
    del log["data"]
    await history.async_refresh()
    await history._backfill
    report = (await history.async_get_history(report_id="log-0"))["logs"][0]
    assert report["series_available"]
    assert report["series"]["temperature"]["source"] == "local_archive"
    assert report["series"]["temperature"]["outdated"]


async def test_options_flow_updates_retention(hass, enable_custom_integrations):
    entry = MockConfigEntry(domain=DOMAIN, options={"existing": True})
    entry.add_to_hass(hass)
    with patch.object(hass.config_entries, "async_reload", new_callable=AsyncMock):
        flow = await hass.config_entries.options.async_init(entry.entry_id)
        assert flow["step_id"] == "init"
        result = await hass.config_entries.options.async_configure(flow["flow_id"], {CONF_HISTORY_NIGHTS: 7})
    assert result["data"] == {"existing": True, CONF_HISTORY_NIGHTS: 7}
