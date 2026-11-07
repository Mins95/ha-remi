"""Music controls must never invent playback state or tracks."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.media_player import MediaType, RepeatMode
from homeassistant.exceptions import ServiceValidationError

from custom_components.urbanhello_remi_unofficial.api import RemiApiError
from custom_components.urbanhello_remi_unofficial.media_player import RemiMediaPlayer, async_setup_entry
from custom_components.urbanhello_remi_unofficial.const import DOMAIN


@pytest.fixture
def player():
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.remi = {"objectId": "remi1", "name": "REMI", "online": True, "alive": True, "volume": 50, "musicMode": 2, "musicPath": "Music/b.mp3:42"}
    coordinator.client.get_music_library = AsyncMock(return_value=[
        {"full_path": "Music/a.mp3", "path": "Music", "name": "A"},
        {"full_path": "Music/b.mp3", "path": "Music", "name": "B"},
        {"full_path": "Other/x.mp3", "path": "Other", "name": "X"},
        {"full_path": "Music/c.mp3", "path": "Music", "name": "C"},
    ])
    coordinator.client.async_play_music = AsyncMock()
    coordinator.client.async_media_command = AsyncMock()
    coordinator.client.update_remi = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()
    return RemiMediaPlayer(coordinator)


async def test_platform_setup(hass, player):
    hass.data[DOMAIN] = {"entry": player.coordinator}
    added = MagicMock()
    await async_setup_entry(hass, MagicMock(entry_id="entry"), added)
    assert added.call_args.args[0][0].unique_id == "remi1_music_player"


async def test_browse_metadata_unknown_playback(player):
    library = await player.async_browse_media()
    assert len(library.children) == 4
    assert library.children[1].media_content_id == "Music/b.mp3"
    assert player.media_title == "B"
    assert player.media_content_id == "Music/b.mp3"
    assert player.state is None
    assert player.media_duration is None
    assert player.media_position is None
    assert player.volume_level == 0.5
    assert player.repeat == RepeatMode.ONE


async def test_empty_library_no_invented_track(player):
    player.coordinator.client.get_music_library.return_value = []
    assert (await player.async_browse_media()).children == []
    with pytest.raises(ServiceValidationError):
        await player.async_play_media(MediaType.MUSIC, "Music/missing.mp3")
    player.coordinator.client.async_play_music.assert_not_called()


async def test_library_failure_preserves_cache_and_blocks_write(player):
    await player.async_browse_media()
    player.coordinator.client.get_music_library.side_effect = RemiApiError("failed")
    with pytest.raises(RemiApiError):
        await player.async_play_media(MediaType.MUSIC, "Music/b.mp3")
    assert player.media_title == "B"
    player.coordinator.client.async_play_music.assert_not_called()


async def test_play_pause_stop_never_set_state(player):
    await player.async_play_media(MediaType.MUSIC, "Music/a.mp3")
    await player.async_media_pause()
    await player.async_media_stop()
    assert player.state is None
    player.coordinator.client.async_play_music.assert_awaited_once_with("Music/a.mp3")
    assert [call.args[0] for call in player.coordinator.client.async_media_command.call_args_list] == ["pause", "stop"]


async def test_play_after_pause_reselects_known_track(player):
    await player.async_media_pause()
    player.coordinator.remi["musicPath"] = "pause:12"
    await player.async_media_play()
    player.coordinator.client.async_play_music.assert_awaited_once_with("Music/b.mp3")
    assert player.state is None


async def test_next_previous_use_neighbor_paths_and_no_wrap(player):
    await player.async_media_next_track()
    player.coordinator.client.async_play_music.assert_awaited_with("Music/c.mp3")
    await player.async_media_previous_track()
    player.coordinator.client.async_play_music.assert_awaited_with("Music/a.mp3")
    player.coordinator.remi["musicPath"] = "Music/c.mp3:1"
    with pytest.raises(ServiceValidationError):
        await player.async_media_next_track()


@pytest.mark.parametrize("value", [None, "", "pause:1", "stop:2", "play:3", "Music/a.mp3:1000", "Music/a.mp3:bad", "Music/a.mp3:١"])
def test_command_mailbox_is_not_track_or_playing_state(player, value):
    player.coordinator.remi["musicPath"] = value
    assert player.media_content_id is None
    assert player.media_title is None
    assert player.state is None


@pytest.mark.parametrize("value", [True, None, "1", -0.1, 1.1, float("nan"), float("inf"), 10**1000])
async def test_invalid_volume_no_write(player, value):
    with pytest.raises(ServiceValidationError):
        await player.async_set_volume_level(value)
    player.coordinator.client.update_remi.assert_not_called()


async def test_volume_repeat_and_failed_write(player):
    await player.async_set_volume_level(0.27)
    player.coordinator.client.update_remi.assert_awaited_with({"volume": 27})
    await player.async_set_repeat(RepeatMode.ALL)
    player.coordinator.client.update_remi.assert_awaited_with({"musicMode": 3})
    player.coordinator.async_request_refresh.reset_mock()
    player.coordinator.client.async_media_command.side_effect = RemiApiError("failed")
    with pytest.raises(RemiApiError):
        await player.async_media_stop()
    player.coordinator.async_request_refresh.assert_not_called()


@pytest.mark.parametrize("field", ["online", "alive"])
def test_offline_unavailable(player, field):
    player.coordinator.remi[field] = False
    assert not player.available
