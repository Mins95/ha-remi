"""Register and update the bundled card independently of native REMI controls."""
from __future__ import annotations

import asyncio
from hashlib import sha256
import json
import logging
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.const import EVENT_COMPONENT_LOADED
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

CARD_PATH = "/urbanhello-remi/remi-card.js"
LOADER_PATH = "/urbanhello-remi/remi-loader.js"
_DATA_KEY = f"{DOMAIN}_frontend"
_LOGGER = logging.getLogger(__name__)


def get_asset_urls() -> tuple[str, str]:
    """Read files in HA's executor; a same-version source change changes both URLs."""
    root = Path(__file__).parent
    version = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["version"]
    if not isinstance(version, str) or not version:
        raise ValueError("Invalid integration version")
    assets = root / "www"
    revision = sha256(
        (assets / "remi-card.js").read_bytes()
        + b"\0" + (assets / "remi-loader.js").read_bytes()
    ).hexdigest()[:12]
    query = urlencode({"v": version, "card": revision})
    return f"{CARD_PATH}?{query}", f"{LOADER_PATH}?{query}"


def _is_bundled_card(url: object) -> bool:
    """Never manage another origin's script or another card's resource."""
    if not isinstance(url, str):
        return False
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    return not parts.scheme and not parts.netloc and parts.path == CARD_PATH


async def _async_register_card_resource(hass: HomeAssistant, card_url: str) -> None:
    """Preserve the resource ID on upgrade; leave YAML and unrelated items alone."""
    try:
        lovelace = hass.data.get(LOVELACE_DATA)
        resources = lovelace.get("resources") if isinstance(lovelace, dict) else getattr(lovelace, "resources", None)
        if not isinstance(resources, ResourceStorageCollection):
            return
        # An unloaded collection can look empty even if the user added our card.
        await resources.async_get_info()
        matches = [item for item in resources.async_items() if _is_bundled_card(item.get("url"))]
        if not matches:
            await resources.async_create_item({"url": card_url, "res_type": "module"})
            return
        current = matches[0]
        if current.get("url") != card_url or current.get("type") != "module":
            await resources.async_update_item(current["id"], {"url": card_url, "res_type": "module"})
        for duplicate in matches[1:]:
            await resources.async_delete_item(duplicate["id"])
    except Exception as err:
        # A dashboard problem must never prevent native controls from loading.
        _LOGGER.warning("Could not update the REMI dashboard resource (%s); the fallback loader remains enabled", type(err).__name__)


def _defer_until_frontend(hass: HomeAssistant, state: dict) -> None:
    """Support a later frontend setup without enabling UI on a headless instance."""
    if state.get("unsubscribe") is not None:
        return

    @callback
    def component_loaded(event) -> None:
        if event.data.get("component") in {"frontend", "http", "lovelace"}:
            hass.async_create_task(async_setup_frontend(hass))

    state["unsubscribe"] = hass.bus.async_listen(EVENT_COMPONENT_LOADED, component_loaded)


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Refresh the asset/resource URLs without rewriting dashboard configuration."""
    state = hass.data.setdefault(_DATA_KEY, {"lock": asyncio.Lock(), "paths_registered": False})
    if "frontend" not in hass.config.components or not hasattr(hass, "http"):
        _defer_until_frontend(hass, state)
        return
    async with state["lock"]:
        try:
            card_url, loader_url = await hass.async_add_executor_job(get_asset_urls)
            if not state["paths_registered"]:
                assets = Path(__file__).parent / "www"
                await hass.http.async_register_static_paths([
                    StaticPathConfig(CARD_PATH, str(assets / "remi-card.js"), False),
                    StaticPathConfig(LOADER_PATH, str(assets / "remi-loader.js"), False),
                ])
                state["paths_registered"] = True
            if state.get("loader_url") != loader_url:
                # Install recovery before waiting for resource storage I/O.
                frontend.add_extra_js_url(hass, loader_url)
                if previous := state.get("loader_url"):
                    try:
                        frontend.remove_extra_js_url(hass, previous)
                    except KeyError:
                        pass
                state["loader_url"] = loader_url
            await _async_register_card_resource(hass, card_url)
            state["card_url"] = card_url
            if "lovelace" in hass.config.components:
                if unsubscribe := state.pop("unsubscribe", None):
                    unsubscribe()
            else:
                _defer_until_frontend(hass, state)
        except Exception as err:
            _LOGGER.warning("Could not load the REMI card (%s); native REMI controls remain available", type(err).__name__)
