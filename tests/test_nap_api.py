"""Timer-profile scoping, validation and write-safety tests."""
from __future__ import annotations

from copy import deepcopy
from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.urbanhello_remi_unofficial.api import RemiApiError
from custom_components.urbanhello_remi_unofficial.media_api import remi_pointer
from custom_components.urbanhello_remi_unofficial.nap_api import RemiNapApiMixin

PROFILE = {"objectId": "nap1", "remi": remi_pointer("remi1"), "name": "Nap", "duration": [1, 30]}


class Client(RemiNapApiMixin):
    remi_id = "remi1"

    def __init__(self):
        self._request = AsyncMock(return_value={"results": [deepcopy(PROFILE)]})


async def test_list_is_scoped_read_and_empty_is_valid():
    client = Client()
    assert await client.get_naps() == [PROFILE]
    payload = client._request.call_args.args[2]
    assert payload["where"] == {"remi": remi_pointer("remi1")}
    assert payload["_method"] == "GET"
    assert payload["limit"] == 101
    client._request.return_value = {"results": []}
    assert await client.get_naps() == []


@pytest.mark.parametrize("response", [{}, {"results": None}, {"results": [None]}, {"results": [PROFILE, PROFILE]}, {"results": [PROFILE] * 101}, {"results": [{**PROFILE, "remi": remi_pointer("another")}]}])
async def test_invalid_list_rejected_not_treated_as_empty(response):
    client = Client()
    client._request.return_value = response
    with pytest.raises(RemiApiError):
        await client.get_naps()


async def test_create_checks_limit_and_owner_without_command():
    client = Client()
    client._request.side_effect = [{"results": []}, {"objectId": "new"}]
    result = await client.create_nap({"name": "Afternoon", "duration": [1, 15], "lengthStart": 10})
    assert result == {"objectId": "new"}
    assert client._request.call_args.args == ("POST", "/parse/classes/Nap", {
        "name": "Afternoon", "duration": [1, 15], "lengthStart": 10,
        "remi": remi_pointer("remi1"),
    })


async def test_five_profile_limit_prevents_write():
    client = Client()
    client._request.return_value = {"results": [{**PROFILE, "objectId": f"nap{i}"} for i in range(5)]}
    with pytest.raises(ServiceValidationError):
        await client.create_nap({"name": "Sixth", "duration": [0, 30]})
    client._request.assert_awaited_once()


@pytest.mark.parametrize("fields", [
    {}, {"name": ""}, {"duration": [24, 0]}, {"duration": [0, 60]},
    {"duration": [True, 0]}, {"duration": [1]}, {"brightness": 100.5},
    {"volumeStart": -1}, {"volumeEnd": 101}, {"sleepAid": True},
    {"sleepAid": 2}, {"lengthStart": 1.5}, {"lengthEnd": 1441},
    {"musicPathStart": "https://example.org/file.mp3"},
    {"remi": remi_pointer("another")}, {"objectId": "other"},
    {"face": {"objectId": "foreign"}},
])
async def test_invalid_update_never_reads_or_writes(fields):
    client = Client()
    with pytest.raises(ServiceValidationError):
        await client.update_nap("nap1", fields)
    client._request.assert_not_called()


@pytest.mark.parametrize("method", ["update_nap", "delete_nap"])
@pytest.mark.parametrize("records", [[], [{**PROFILE, "remi": remi_pointer("another")}], [{**PROFILE, "objectId": "other"}], [PROFILE, PROFILE]])
async def test_mutations_must_prove_owner(method, records):
    client = Client()
    client._request.return_value = {"results": records}
    args = ("nap1", {"name": "Changed"}) if method == "update_nap" else ("nap1",)
    with pytest.raises((ServiceValidationError, RemiApiError)):
        await getattr(client, method)(*args)
    client._request.assert_awaited_once()


async def test_update_is_patch_and_failed_write_not_retried():
    client = Client()
    client._request.side_effect = [{"results": [PROFILE]}, RemiApiError("timeout")]
    with pytest.raises(RemiApiError):
        await client.update_nap("nap1", {"lengthEnd": 15})
    assert client._request.await_count == 2
    assert client._request.call_args.args == ("PUT", "/parse/classes/Nap/nap1", {"lengthEnd": 15})


async def test_delete_scopes_then_deletes_once():
    client = Client()
    client._request.side_effect = [{"results": [PROFILE]}, {}]
    await client.delete_nap("nap1")
    first = client._request.call_args_list[0].args[2]
    assert first["where"] == {"remi": remi_pointer("remi1"), "objectId": "nap1"}
    assert client._request.call_args.args == ("DELETE", "/parse/classes/Nap/nap1")


@pytest.mark.parametrize("value", ["../other", "", None, "x/y", "x?query"])
async def test_id_cannot_escape_endpoint(value):
    client = Client()
    with pytest.raises(ServiceValidationError):
        await client.delete_nap(value)
    client._request.assert_not_called()
