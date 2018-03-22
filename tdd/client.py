"""
The client should be able to perform generic interactions with the API

communicate
"""
import logging
from urllib.parse import urljoin

import requests

from tdd.exceptions import ConfigError

class TDDClient(requests.Session):
    """
    The TDD Client can
    - authenticate with username/password and get a token.
    - [TODO] cache existing tokens and seamlessly get new ones
    - [TODO] perform authenticated requests
    - [TODO] implements retry policy on 500
    - reuses underlying TCP connection for better performance

    """
    base_url = "https://apisb.thetradedesk.com/v3/"

    def __init__(self, login, password, token_expires_in=90):
        super().__init__()
        self._login = login
        self._password = password
        self.token_expires_in = token_expires_in

        self._token = None

    def _build_url(self, endpoint):
        return urljoin(self.base_url, endpoint.lstrip("/"))

    @property
    def token(self):
        """Get or reuse token"""
        if self._token is None:
            self._refresh_token(self.token_expires_in)
        return self._token

    @token.setter
    def token(self, new_token):
        """Set access token + update auth headers"""
        logging.debug("Setting new access token")
        self._token = new_token

        logging.debug("Updating TTD-Auth header")
        self.headers.update({"TTD-Auth": new_token})

    def _refresh_token(self, expires_in=90):

        logging.debug("Getting new access token")
        data = {
            "Login": self._login,
            "Password": self._password,
            "TokenExpirationInMinutes": expires_in
        }

        resp = self.request("POST", self._build_url('authentication'), json=data)
        try:
            resp.raise_for_status()
        except requests.HTTPError as err:
            logging.error(err)
            logging.error(resp.text)
            if err.response.status_code == 401:
                raise ConfigError(resp.text)
            else:
                raise

        self.token = resp.json()["Token"]

    def _request(self, method, url, *args, **kwargs):
        """Do authenticated HTTP request

        Implements retry on expired access token

        Returns:
            requests.Response object
        """

        try:
            resp = self.request(method, url, *args, **kwargs)
            resp.raise_for_status()
        except requests.HTTPError as err:
            if err.response.status_code == 403:
                # token expired
                logging.debug("Token expired or invalid, trying again")
                self._refresh_token()
                try:
                    resp2 = self.request(method, url, *args, **kwargs)
                    resp2.raise_for_status()
                except requests.HTTPError as err:
                    logging.error(err.response.text)
                    raise
                else:
                    return resp2
            else:
                logging.error(err.response.text)
                raise

    def get(self, endpoint, *args, **kwargs):
        """Make an authenticated get request against the API endpoint

        Args:
            standard requests.get() parameters

        Returns:
            json response
        """
        return self._request("GET", self._build_url(endpoint), *args, **kwargs).json()


    def post(self, endpoint, *args, **kwargs):
        """Make an authenticated POST request against the API endpoint

        Args:
            standard requests.post() parameters

        Returns:
            json response
        """
        return self._request("POST", self._build_url(endpoint), *args, **kwargs).json()

    def put(self, endpoint, *args, **kwargs):
        """Make an authenticated POST request against the API endpoint

        Args:
            standard requests.put() parameters

        Returns:
            json response
        """

        return self._request("PUT", self._build_url(endpoint), *args, **kwargs).json()
