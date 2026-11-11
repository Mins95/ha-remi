"""DataUpdateCoordinator for the UrbanHello Remi integration."""
from __future__ import annotations

import asyncio
import logging
from time import monotonic
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RemiApiClient, RemiApiError, RemiAuthError
from .alarm_identity import AlarmIdentityMap, AlarmIdentityStorageError
from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)
_FIRMWARE_METADATA_INTERVAL_SECONDS = 3600
_FIRMWARE_METADATA_RETRY_SECONDS = 300


class RemiDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the Remi API and stores all device data."""

    def __init__(self, hass: HomeAssistant, client: RemiApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client
        self.faces: list[dict[str, Any]] = []
        self.config_params: dict[str, Any] = {}
        self._config_checked_at: float | None = None
        self._config_retry_at: float | None = None
        self.events_available = False
        self.alarm_identities = AlarmIdentityMap(client.remi_id)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest data from the Remi API."""
        try:
            remi, events = await asyncio.gather(
                self.client.get_remi(),
                self.client.get_events(),
                return_exceptions=True,
            )
            # A rejected account needs repair even if the other read succeeded.
            for result in (remi, events):
                if isinstance(result, RemiAuthError):
                    self.events_available = False
                    raise result
            if isinstance(remi, BaseException):
                self.events_available = False
                raise remi
            if isinstance(events, BaseException):
                self.events_available = False
                if not isinstance(events, RemiApiError):
                    raise events
                _LOGGER.debug("Could not refresh REMI alarms; retaining the previous snapshot")
                events = self.events
            else:
                try:
                    self.events_available = await self.alarm_identities.async_reconcile(events)
                except (AlarmIdentityStorageError, OSError, HomeAssistantError):
                    self.events_available = False
                    _LOGGER.error("Could not safely persist REMI alarm identities; retaining the previous snapshot")
                if not self.events_available:
                    events = self.events
            if self._config_due():
                try:
                    await self._async_refresh_config()
                except RemiAuthError as err:
                    raise ConfigEntryAuthFailed(
                        translation_domain=DOMAIN, translation_key="reauth_required"
                    ) from err
                except RemiApiError:
                    # A firmware metadata failure must not discard valid device data.
                    _LOGGER.debug("Could not refresh REMI firmware metadata")
            return {"remi": remi, "events": events}
        except RemiAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="reauth_required"
            ) from err
        except RemiApiError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="cannot_refresh_device"
            ) from err

    def _config_due(self) -> bool:
        """Retry failed metadata after a pause, otherwise refresh it hourly."""
        now = monotonic()
        if self._config_retry_at is not None:
            return now >= self._config_retry_at
        return (
            self._config_checked_at is None
            or now - self._config_checked_at >= _FIRMWARE_METADATA_INTERVAL_SECONDS
        )

    async def async_setup(self) -> None:
        """Fetch static data (faces, config) once at setup."""
        try:
            self.faces = await self.client.get_faces()
            await self._async_refresh_config()
        except RemiAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="reauth_required"
            ) from err
        except RemiApiError as err:
            _LOGGER.warning("Could not fetch static Remi data: %s", err)

    async def _async_refresh_config(self) -> None:
        """Refresh cached informational firmware configuration."""
        try:
            config = await self.client.get_config()
        except RemiAuthError:
            # Authentication needs repair, not a delayed metadata retry.
            raise
        except RemiApiError:
            self._config_retry_at = monotonic() + _FIRMWARE_METADATA_RETRY_SECONDS
            raise
        self.config_params = config.get("params", {})
        self._config_checked_at = monotonic()
        self._config_retry_at = None

    async def async_check_firmware(self) -> None:
        """Read firmware metadata and device state; never request installation."""
        try:
            await self._async_refresh_config()
        except RemiAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="reauth_required"
            ) from err
        except RemiApiError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="cannot_check_firmware"
            ) from err
        await self.async_refresh()
        if not self.last_update_success:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="cannot_refresh_firmware"
            )

    @property
    def remi(self) -> dict[str, Any]:
        """Return the current Remi device state."""
        if self.data is None:
            return {}
        return self.data.get("remi", {})

    @property
    def events(self) -> list[dict[str, Any]]:
        """Return the current list of alarm events."""
        if self.data is None:
            return []
        return self.data.get("events", [])

    @property
    def latest_firmware_version(self) -> int | None:
        """Return the latest firmware version from server config."""
        return self.config_params.get("default_firmware_update_version")
