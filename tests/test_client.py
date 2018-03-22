import pytest
import os

from tdd.client import TDDClient
import tdd.exceptions

@pytest.fixture(scope="module")
def credentials():
    return {
        "login": os.environ['TDD_USERNAME'],
        "password": os.environ['TDD_PASSWORD']
    }

def test_client_raises_config_error_on_wrong_credentials():
    client = TDDClient(login='foo', password="Nonexistent")
    with pytest.raises(tdd.exceptions.ConfigError) as excinfo:
        client.token

    assert "invalid credentials" in str(excinfo.value).lower()

def test_client_can_authenticate(credentials):
    client = TDDClient(**credentials)
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
    client = TDDClient("foo", "bar")
    client.base_url = "api.com/v3/"
    tests = [
        ("/campaign/get", "api.com/v3/campaign/get"),
        ("campaign/get", "api.com/v3/campaign/get"),
        ("campaign/get", "api.com/v3/campaign/get"),
    ]
    for endpoint, expected in tests:
        assert client._build_url(endpoint) == expected

# def test_client_can_be_created_with_token():
#     client = TDDClient(token="foobar")
#     assert client.token = "foobar"
