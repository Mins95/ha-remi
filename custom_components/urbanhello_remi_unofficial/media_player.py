"""Cloud music controls, without claiming unreported playback telemetry."""
from __future__ import annotations

import math
from typing import Any

from homeassistant.components.media_player import (
    BrowseMedia, MediaClass, MediaPlayerEntity, MediaPlayerEntityFeature,
    MediaType, RepeatMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity
from .media_api import validate_music_path, validation_error

_REPEAT_TO_MODE = {RepeatMode.OFF: 0, RepeatMode.ONE: 2, RepeatMode.ALL: 3}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Add one player for the selected REMI."""
    async_add_entities([RemiMediaPlayer(hass.data[DOMAIN][entry.entry_id])])


class RemiMediaPlayer(RemiEntity, MediaPlayerEntity):
    """Control files already on REMI; cloud commands are not playback states."""

    _attr_translation_key = "music_player"
    _attr_icon = "mdi:speaker"
    _attr_supported_features = (
        MediaPlayerEntityFeature.BROWSE_MEDIA | MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.PLAY | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.REPEAT_SET
    )

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._remi_id}_music_player"
        self._library: list[dict[str, Any]] = []
        self._selected_path: str | None = None

    @property
    def available(self) -> bool:
        return self.device_available

    @property
    def state(self) -> None:
        """REMI's musicPath mailbox does not confirm playing/paused/idle."""
        return None

    @property
    def volume_level(self) -> float | None:
        value = self.coordinator.remi.get("volume")
        if type(value) in (int, float) and 0 <= value <= 100 and math.isfinite(value):
            return value / 100
        return None

    @property
    def repeat(self) -> RepeatMode | None:
        value = self.coordinator.remi.get("musicMode")
        if type(value) is not int:
            return None
        return {0: RepeatMode.OFF, 1: RepeatMode.OFF, 2: RepeatMode.ONE, 3: RepeatMode.ALL}.get(value)

    def _reported_path(self) -> str | None:
        value = self.coordinator.remi.get("musicPath")
        if not isinstance(value, str):
            return None
        path, separator, nonce = value.rpartition(":")
        if separator:
            if not nonce.isascii() or not nonce.isdecimal() or len(nonce) > 3:
                return None
            value = path
        try:
            return validate_music_path(value, allow_empty=False)
        except ServiceValidationError:
            return None

    @property
    def media_content_id(self) -> str | None:
        """Expose the cloud-selected path, without implying it is playing."""
        return self._reported_path()

    @property
    def media_content_type(self) -> MediaType | None:
        return MediaType.MUSIC if self._reported_path() else None

    @property
    def media_title(self) -> str | None:
        path = self._reported_path()
        if path is None:
            return None
        return next((item["name"] for item in self._library if item["full_path"] == path), path.rsplit("/", 1)[-1])

    async def _refresh_library(self) -> list[dict[str, Any]]:
        # Assignment happens only after a complete successful read.
        self._library = await self.coordinator.client.get_music_library()
        return self._library

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None,
    ) -> BrowseMedia:
        """Browse only the selected device's library, including a valid empty list."""
        if media_content_id not in (None, "", "library"):
            raise validation_error("unsupported_media_selection")
        library = await self._refresh_library()
        return BrowseMedia(
            title=self.coordinator.remi.get("name") or "REMI",
            media_class=MediaClass.DIRECTORY,
            media_content_id="library", media_content_type=MediaType.MUSIC,
            can_play=False, can_expand=True, children_media_class=MediaClass.TRACK,
            children=[BrowseMedia(
                title=item["name"], media_class=MediaClass.TRACK,
                media_content_id=item["full_path"], media_content_type=MediaType.MUSIC,
                can_play=True, can_expand=False,
            ) for item in library],
        )

    async def async_play_media(self, media_type: str, media_id: str, **kwargs: Any) -> None:
        """Play an existing file, never fetch or upload a URL."""
        if media_type not in (MediaType.MUSIC, MediaType.TRACK):
            raise validation_error("unsupported_media_selection")
        path = validate_music_path(media_id, allow_empty=False)
        library = await self._refresh_library()
        if not any(item["full_path"] == path for item in library):
            raise validation_error("music_track_not_found")
        await self._play_path(path)

    async def _play_path(self, path: str) -> None:
        await self.coordinator.client.async_play_music(path)
        # This remembers a selection for Play after Pause; state stays unknown.
        self._selected_path = path
        await self.coordinator.async_request_refresh()

    async def async_media_play(self) -> None:
        """Start the selected file again; resume position is not reported."""
        path = self._reported_path() or self._selected_path
        if path is None:
            raise validation_error("music_track_not_selected")
        await self.async_play_media(MediaType.MUSIC, path)

    async def async_media_pause(self) -> None:
        path = self._reported_path()
        if path is not None:
            self._selected_path = path
        await self.coordinator.client.async_media_command("pause")
        await self.coordinator.async_request_refresh()

    async def async_media_stop(self) -> None:
        await self.coordinator.client.async_media_command("stop")
        await self.coordinator.async_request_refresh()

    async def _adjacent_track(self, offset: int) -> None:
        path = self._reported_path() or self._selected_path
        library = await self._refresh_library()
        current = next((item for item in library if item["full_path"] == path), None)
        if current is None:
            raise validation_error("music_track_not_selected")
        playlist = [item for item in library if item["path"] == current["path"]]
        index = playlist.index(current) + offset
        if not 0 <= index < len(playlist):
            raise validation_error("music_track_boundary")
        await self._play_path(playlist[index]["full_path"])

    async def async_media_next_track(self) -> None:
        await self._adjacent_track(1)

    async def async_media_previous_track(self) -> None:
        await self._adjacent_track(-1)

    async def async_set_volume_level(self, volume: float) -> None:
        if type(volume) not in (int, float) or not 0 <= volume <= 1 or not math.isfinite(volume):
            raise validation_error("invalid_media_volume")
        await self.coordinator.client.update_remi({"volume": round(volume * 100)})
        await self.coordinator.async_request_refresh()

    async def async_set_repeat(self, repeat: str) -> None:
        if repeat not in _REPEAT_TO_MODE:
            raise validation_error("unknown_music_mode")
        await self.coordinator.client.update_remi({"musicMode": _REPEAT_TO_MODE[repeat]})
        await self.coordinator.async_request_refresh()
