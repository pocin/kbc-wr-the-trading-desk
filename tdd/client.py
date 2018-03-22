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

    def __init__(self, login, password):
        super().__init__()
        self._login = login
        self._password = password

        self._token = None

    def _build_url(self, endpoint):
        return urljoin(self.base_url, endpoint.lstrip("/"))

    @property
    def token(self):
        """Get or reuse token"""
        if self._token is None:
            self._get_token()
        return self._token


    @token.setter
    def token(self, new_token):
        logging.debug("Setting new access token")
        self._token = new_token

    def _get_token(self, expires_in=90):

        logging.debug("Getting new access token")
        data = {
            "Login": self._login,
            "Password": self._password,
            "TokenExpirationInMinutes": expires_in
        }

        resp = self.post(self._build_url('authentication'), json=data)
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
