import os
import logging

import pytest
from tdd.client import BaseTDDClient
import tdd.exceptions

LOGIN = os.environ['TDD_USERNAME']
PASSWORD = os.environ['TDD_PASSWORD']

# @pytest.fixture(scope='module')
# def client():
#     return TDDClient(login=LOGIN, password=PASSWORD)

def test_client_raises_config_error_on_wrong_credentials():
    client = BaseTDDClient(login='foo', password="Nonexistent")
    with pytest.raises(tdd.exceptions.ConfigError) as excinfo:
        client.token

    assert "invalid credentials" in str(excinfo.value).lower()

def test_client_can_authenticate():
    client = BaseTDDClient(login=LOGIN, password=PASSWORD)
    old_token = client.token
    assert old_token is not None

    # assert that invoking the token again doesn't fetch a new one
    assert client.token == old_token

    # delete the token
    client.token = None
    # make sure we get a new one
    new_token = client.token
    assert new_token != old_token and new_token is not None

def test_building_urls():
    client = BaseTDDClient("foo", "bar")
    client.base_url = "api.com/v3/"
    tests = [
        ("/campaign/get", "api.com/v3/campaign/get"),
        ("campaign/get", "api.com/v3/campaign/get"),
        ("campaign/get", "api.com/v3/campaign/get"),
    ]
    for endpoint, expected in tests:
        assert client._build_url(endpoint) == expected

def test_client_fails_on_unauthorized_resource():
    endpoint = "category/industrycategories"
    client = BaseTDDClient(login="non", password="existing")
    client.token = "INVALID"

    # this makes an authorized GET without retry on failed refresh_token
    # we use request("GET") because client.get is overriden
    resp = client.request("GET", client._build_url(endpoint))
    assert resp.status_code == 403
    assert "auth token is not valid or has expired" in resp.json()["Message"]

def test_client_refreshes_token_after_403_request(caplog):
    endpoint = "category/industrycategories"
    client = BaseTDDClient(login=LOGIN, password=PASSWORD)
    client.token = "INVALID"

    with caplog.at_level(logging.DEBUG):
        resp = client._request("GET", client._build_url(endpoint))

    assert "Token expired or invalid, trying again" in caplog.text
    # eventually succeeds after 1st try
    assert client.token is not None and client.token != "INVALID"
    assert resp.status_code == 200

    # next request reuses existing token
    resp2 = client._request("GET", client._build_url(endpoint))
    assert resp2.status_code == 200

def test_making_client_get_request_succeeds():
    endpoint = "category/industrycategories"
    client = BaseTDDClient(login=LOGIN, password=PASSWORD)
    data = client.get(endpoint)
    assert isinstance(data, dict)
