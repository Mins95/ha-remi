"""Bundled card upgrades against Home Assistant's real resource collection."""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection, ResourceYAMLCollection
from homeassistant.const import EVENT_COMPONENT_LOADED

from custom_components.urbanhello_remi_unofficial import frontend as subject


@pytest.fixture
def resources(hass, monkeypatch):
    collection = ResourceStorageCollection(hass, MagicMock())
    monkeypatch.setattr(collection.store, "async_load", AsyncMock(return_value={"items": []}))
    monkeypatch.setattr(collection.store, "async_delay_save", MagicMock())
    hass.data[LOVELACE_DATA] = SimpleNamespace(resources=collection)
    return collection


@pytest.fixture
def frontend_hass(hass, resources):
    hass.config.components.update({"frontend", "http", "lovelace"})
    hass.http = SimpleNamespace(async_register_static_paths=AsyncMock())
    return hass


@pytest.fixture
def asset_urls():
    with patch.object(subject, "get_asset_urls", return_value=(
        subject.CARD_PATH + "?v=test&card=new", subject.LOADER_PATH + "?v=test&card=new",
    )) as mock:
        yield mock


@pytest.fixture
def loader_registration():
    with patch.object(subject.frontend, "add_extra_js_url") as add, patch.object(subject.frontend, "remove_extra_js_url") as remove:
        yield add, remove


def _seed(resources, records):
    resources.store.async_load.return_value = {"items": deepcopy(records)}


def _card(identifier="manual", url=None, kind="module"):
    return {"id": identifier, "url": url or subject.CARD_PATH + "?v=old", "type": kind}


def test_asset_revision_changes_for_sources_and_manifest_version(tmp_path, monkeypatch):
    (tmp_path / "www").mkdir()
    (tmp_path / "manifest.json").write_text(json.dumps({"version": "0.5.0-beta.1"}))
    card = tmp_path / "www" / "remi-card.js"
    loader = tmp_path / "www" / "remi-loader.js"
    card.write_text("card")
    loader.write_text("loader")
    monkeypatch.setattr(subject, "__file__", str(tmp_path / "frontend.py"))
    first = subject.get_asset_urls()
    card.write_text("corrected card")
    changed_card = subject.get_asset_urls()
    loader.write_text("corrected loader")
    changed_loader = subject.get_asset_urls()
    (tmp_path / "manifest.json").write_text(json.dumps({"version": "0.5.0-beta.2"}))
    changed_version = subject.get_asset_urls()
    for index in (0, 1):
        assert first[index] != changed_card[index] != changed_loader[index] != changed_version[index]
    assert urlsplit(first[0]).query == urlsplit(first[1]).query
    assert len(parse_qs(urlsplit(first[0]).query)["card"][0]) == 12


@pytest.mark.parametrize("url", [None, 3, "https://example.org" + subject.CARD_PATH, "//example.org" + subject.CARD_PATH, "http://[", "/local/remi-card.js", subject.LOADER_PATH])
def test_external_unrelated_and_malformed_resources_are_not_owned(url):
    assert not subject._is_bundled_card(url)


async def test_new_install_and_concurrent_calls_add_one_resource(frontend_hass, resources, asset_urls, loader_registration):
    await asyncio.gather(*(subject.async_setup_frontend(frontend_hass) for _ in range(5)))
    assert len(resources.async_items()) == 1
    assert resources.async_items()[0]["type"] == "module"
    assert resources.async_items()[0]["url"] == asset_urls.return_value[0]
    frontend_hass.http.async_register_static_paths.assert_awaited_once()
    paths = frontend_hass.http.async_register_static_paths.call_args.args[0]
    assert [path.url_path for path in paths] == [subject.CARD_PATH, subject.LOADER_PATH]
    assert all(path.cache_headers is False for path in paths)
    loader_registration[0].assert_called_once_with(frontend_hass, asset_urls.return_value[1])


async def test_unloaded_manual_resource_upgraded_without_changing_id(frontend_hass, resources, asset_urls, loader_registration):
    _seed(resources, [_card()])
    assert not resources.loaded
    await subject.async_setup_frontend(frontend_hass)
    assert resources.loaded
    assert resources.async_items() == [_card(url=asset_urls.return_value[0])]


async def test_duplicate_cleanup_preserves_other_origins_and_resources(frontend_hass, resources, asset_urls, loader_registration):
    others = [_card("external", "https://example.org" + subject.CARD_PATH), _card("other", "/local/other.js")]
    _seed(resources, others + [_card(kind="js"), _card("duplicate")])
    await subject.async_setup_frontend(frontend_hass)
    assert resources.async_items() == others + [_card(url=asset_urls.return_value[0])]


async def test_repeated_setup_rehashes_sources_and_keeps_resource_identity(frontend_hass, resources, asset_urls, loader_registration):
    await subject.async_setup_frontend(frontend_hass)
    first_id = resources.async_items()[0]["id"]
    old_loader = asset_urls.return_value[1]
    asset_urls.return_value = (subject.CARD_PATH + "?v=test&card=changed", subject.LOADER_PATH + "?v=test&card=changed")
    await subject.async_setup_frontend(frontend_hass)
    assert resources.async_items() == [_card(first_id, asset_urls.return_value[0])]
    frontend_hass.http.async_register_static_paths.assert_awaited_once()
    loader_registration[1].assert_called_once_with(frontend_hass, old_loader)


async def test_yaml_resources_are_not_modified(frontend_hass, asset_urls, loader_registration):
    records = [_card()]
    yaml = ResourceYAMLCollection(deepcopy(records))
    frontend_hass.data[LOVELACE_DATA] = SimpleNamespace(resources=yaml)
    await subject.async_setup_frontend(frontend_hass)
    assert yaml.async_items() == records
    loader_registration[0].assert_called_once()


async def test_legacy_lovelace_container(frontend_hass, resources, asset_urls, loader_registration):
    frontend_hass.data[LOVELACE_DATA] = {"resources": resources}
    await subject.async_setup_frontend(frontend_hass)
    assert len(resources.async_items()) == 1


async def test_loader_registered_before_storage_wait(frontend_hass, resources, asset_urls, loader_registration):
    entered, release = asyncio.Event(), asyncio.Event()

    async def delayed_read():
        entered.set()
        await release.wait()
        return {"items": []}

    resources.store.async_load.side_effect = delayed_read
    task = asyncio.create_task(subject.async_setup_frontend(frontend_hass))
    await asyncio.wait_for(entered.wait(), 5)
    loader_registration[0].assert_called_once()
    assert not task.done()
    release.set()
    await task


async def test_source_reads_run_outside_event_loop(frontend_hass, resources, loader_registration):
    loop_thread = threading.get_ident()
    observed = []

    def checked_urls():
        observed.append(threading.get_ident())
        assert observed[-1] != loop_thread
        return subject.CARD_PATH + "?card=hash", subject.LOADER_PATH + "?card=hash"

    with patch.object(subject, "get_asset_urls", side_effect=checked_urls):
        await subject.async_setup_frontend(frontend_hass)
    assert len(observed) == 1


@pytest.mark.parametrize("failure", ["assets", "static", "storage"])
async def test_frontend_failures_nonfatal_and_sanitized(frontend_hass, resources, asset_urls, loader_registration, caplog, failure):
    if failure == "assets":
        asset_urls.side_effect = OSError("private-file-path")
    elif failure == "static":
        frontend_hass.http.async_register_static_paths.side_effect = OSError("private-file-path")
    else:
        resources.store.async_load.side_effect = OSError("private-file-path")
    await subject.async_setup_frontend(frontend_hass)
    assert "OSError" in caplog.text
    assert "private-file-path" not in caplog.text
    if failure == "storage":
        loader_registration[0].assert_called_once()


async def test_cancellation_is_not_swallowed(frontend_hass, resources, asset_urls, loader_registration):
    resources.store.async_load.side_effect = asyncio.CancelledError
    with pytest.raises(asyncio.CancelledError):
        await subject.async_setup_frontend(frontend_hass)


async def test_headless_defers_without_reading_assets_and_later_loads(hass, resources, asset_urls, loader_registration):
    hass.http = SimpleNamespace(async_register_static_paths=AsyncMock())
    await subject.async_setup_frontend(hass)
    await subject.async_setup_frontend(hass)
    asset_urls.assert_not_called()
    assert subject._DATA_KEY in hass.data
    hass.config.components.update({"frontend", "http", "lovelace"})
    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {"component": "frontend"})
    await hass.async_block_till_done()
    hass.http.async_register_static_paths.assert_awaited_once()
    assert len(resources.async_items()) == 1
    assert "unsubscribe" not in hass.data[subject._DATA_KEY]
