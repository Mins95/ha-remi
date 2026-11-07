"""Protocol and isolation tests for cloud music commands."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.urbanhello_remi_unofficial.api import RemiApiClient, RemiApiError
from custom_components.urbanhello_remi_unofficial.media_api import (
    RemiMediaApiMixin, remi_pointer, validate_music_path,
)

TRACK = {"objectId": "track1", "REMI": remi_pointer("remi1"), "path": "MyMP3Music", "file": "Lullaby.mp3", "name": "Lullaby", "index": 0}


class Client(RemiMediaApiMixin):
    remi_id = "remi1"

    def __init__(self):
        self._request = AsyncMock(return_value={"results": [deepcopy(TRACK)]})
        self.update_remi = AsyncMock(return_value={"updatedAt": "now"})


@pytest.mark.parametrize("value", [None, 1, "", "/Music/a.mp3", "https://example.org/a.mp3", "../a", "Music/../a", "Music//a", "Music\\a", "a\n", "stop", "pause", "play", "random_1", "a:1", "a" * 513])
def test_path_rejects_commands_urls_and_traversal(value):
    with pytest.raises(ServiceValidationError):
        validate_music_path(value, allow_empty=False)


def test_path_preserves_unicode_and_spaces():
    assert validate_music_path("Mes musiques/Étoiles 01.mp3") == "Mes musiques/Étoiles 01.mp3"
    assert validate_music_path("") == ""


async def test_scoped_library_metadata():
    client = Client()
    tracks = await client.get_music_library()
    payload = client._request.call_args.args[2]
    assert payload["where"] == {"REMI": {"$select": {
        "query": {"className": "Remi", "where": {"objectId": "remi1"}},
        "key": "objectId",
    }}}
    assert payload["_method"] == "GET"
    assert payload["limit"] == 201
    assert tracks == [{"object_id": "track1", "name": "Lullaby", "path": "MyMP3Music", "file": "Lullaby.mp3", "full_path": "MyMP3Music/Lullaby.mp3", "index": 0}]


@pytest.mark.parametrize("response", [{}, {"results": None}, {"results": {}}, {"results": [None]}, {"results": [TRACK, TRACK]}, {"results": [TRACK] * 201}])
async def test_malformed_or_partial_library_not_empty(response):
    client = Client()
    client._request.return_value = response
    with pytest.raises(RemiApiError):
        await client.get_music_library()


async def test_empty_library_is_valid():
    client = Client()
    client._request.return_value = {"results": []}
    assert await client.get_music_library() == []


@pytest.mark.parametrize("owner", [None, "another", {"className": "Remi", "objectId": "another"}, {"className": "Other", "objectId": "remi1"}])
async def test_library_refuses_other_device(owner):
    client = Client()
    client._request.return_value = {"results": [{**TRACK, "REMI": owner}]}
    with pytest.raises(RemiApiError):
        await client.get_music_library()


async def test_music_string_owner_must_match_selected_device():
    client = Client()
    client._request.return_value = {"results": [{**TRACK, "REMI": "remi1"}]}
    assert (await client.get_music_library())[0]["full_path"] == "MyMP3Music/Lullaby.mp3"


async def test_missing_target_never_requests():
    client = Client()
    client.remi_id = None
    with pytest.raises(ServiceValidationError):
        await client.get_music_library()
    with pytest.raises(ServiceValidationError):
        await client.async_media_command("pause")
    client._request.assert_not_called()
    client.update_remi.assert_not_called()


async def test_serialization_nonce_and_no_consecutive_duplicates():
    client = Client()
    with patch("custom_components.urbanhello_remi_unofficial.media_api.random.randrange", return_value=999):
        await asyncio.gather(client.async_media_command("pause"), client.async_media_command("stop"), client.async_play_music("Music/a.mp3"))
    assert [call.args[0] for call in client.update_remi.call_args_list] == [
        {"musicPath": "pause:999"}, {"musicPath": "stop:0"}, {"musicPath": "Music/a.mp3:999"},
    ]


@pytest.mark.parametrize("command", ["play", "next", "previous", "get_status", "pause:1"])
async def test_unproved_commands_rejected(command):
    client = Client()
    with pytest.raises(ServiceValidationError):
        await client.async_media_command(command)
    client.update_remi.assert_not_called()


async def test_write_failure_not_replayed():
    client = Client()
    client.update_remi.side_effect = RemiApiError("timeout")
    with pytest.raises(RemiApiError):
        await client.async_media_command("pause")
    client.update_remi.assert_awaited_once()


async def test_cloud_library_read_uses_bounded_retry_policy():
    client = RemiApiClient("user", "password", MagicMock())
    client.set_remi_id("remi1")
    client._request_once = AsyncMock(side_effect=[TimeoutError(), {"results": []}])
    with patch("custom_components.urbanhello_remi_unofficial.api.asyncio.sleep", new=AsyncMock()):
        assert await client.get_music_library() == []
    assert client._request_once.await_count == 2


async def test_music_write_timeout_is_not_retried_by_http_layer():
    client = RemiApiClient("user", "password", MagicMock())
    client.set_remi_id("remi1")
    client._request_once = AsyncMock(side_effect=TimeoutError())
    with pytest.raises(RemiApiError):
        await client.async_play_music("Music/a.mp3")
    client._request_once.assert_awaited_once()
