"""
The client should be able to perform generic interactions with the API

communicate
"""
import logging
from urllib.parse import urljoin
from hashlib import md5
import sys
import time
from io import StringIO
import requests
import csv

from tdd.exceptions import TDDConfigError

logger = logging.getLogger(__name__)

class BaseTDDClient(requests.Session):
    """
    The TDD Client can
    - authenticate with username/password and get a token.
    -  cache existing tokens and seamlessly get new ones
    -  perform authenticated requests
    - [TODO] implements retry policy on 500
    - reuses underlying TCP connection for better performance


    The authentication headers are automatically used for each request,
    they are updated whenever a access_token is set


    Do not use this client for any nonthetradedesk urls otherwise your
    token will be exposed

    """

    def __init__(self, login, password,
                 token_expires_in=90,
                 base_url="https://apisb.thetradedesk.com/v3/"):
        super().__init__()
        self.base_url = base_url
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
        logger.debug("Setting new access token")
        self._token = new_token

        logger.debug("Updating TTD-Auth header")
        self.headers.update({"TTD-Auth": new_token})

    def _refresh_token(self, expires_in=90):

        logger.debug("Getting new access token")
        data = {
            "Login": self._login,
            "Password": self._password,
            "TokenExpirationInMinutes": expires_in
        }

        resp = self.request("POST", self._build_url('authentication'), json=data)
        try:
            resp.raise_for_status()
        except requests.HTTPError as err:
            logger.error(err)
            logger.error(resp.text)
            if err.response.status_code == 401:
                raise TDDConfigError(resp.text)
            else:
                raise

        self.token = resp.json()["Token"]

    def _request(self, method, url, *args, **kwargs):
        """Do authenticated HTTP request

        Implements retry on expired access token

        Returns:
            requests.Response object
        """

        # auth headers are set when requesting token
        resp = self.request(method, url, *args, **kwargs)
        try:
            resp.raise_for_status()
        except requests.HTTPError as err:
            if err.response.status_code == 403:
                # token expired
                logger.debug("Token expired or invalid, trying again")
                self._refresh_token()
                try:
                    resp2 = self.request(method, url, *args, **kwargs)
                    resp2.raise_for_status()
                except requests.HTTPError as err:
                    logger.error(err.response.text)
                    raise
                else:
                    return resp2
            else:
                logger.error(err.response.text)
                raise
        else:
            return resp

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

class TDDClient(BaseTDDClient):
    """
    Contains shortcut methods for some endpoints (create_campaign, etc...)

    But still doesn't contain any kbc related logic.
    """
    def create_campaign(self, data):
        return self.post('/campaign', json=data)

    def create_adgroup(self, data):
        return self.post('/adgroup')

    def update_adgroup(self, data):
        return self.post('/adgroup')

    def get_sitelist(self, id_):
        return self.get('/sitelist/{}'.format(id_))

class KBCTDDClient(TDDClient):
    """
    Client tailored for Keboola Connection

    Has helper methods for logging requests directly into csv
    """
    def __init__(self, login, password, path_csv_log,
                 token_expires_in=90,
                 base_url="https://apisb.thetradedesk.com/v3/"):
        """
        Args:
            path_log: "/data/out/tables/tdd_writer_log.csv" will be a valid csv with all api calls logged
        """
        super().__init__(login, password, token_expires_in=token_expires_in, base_url=base_url)
        self.path_csv_log = path_csv_log
        self.cdc_logger = self.init_cdc_logging(path_csv_log)
        # don't know how to hook this up to a context manager (we already have one)

    def init_cdc_logging(self, log_path):
        """
        We want to log every response to a csv and stdout/err
        """
        cdc_logger = logging.getLogger(__name__ + '_cdc')
        cdc_logger.propagate = False
        # all requests are logged in csv
        self.csv_log_header = ["type","timestamp", "pk", "http_status", "url",
                               "request", "response"]
        csv_formatter = logging.Formatter('%(name)s,%(asctime)s,%(pk)s,%(http_status)s,'
                                          '%(url)s,%(request_body)s,%(message)s',
                                          datefmt='%Y-%m-%dT%H:%M:%S')

        csv_handler = logging.FileHandler(log_path, 'w')
        csv_handler.setFormatter(csv_formatter)

        # all requests are logged to stdout as well (kbc logs)
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setFormatter(csv_formatter)

        cdc_logger.addHandler(stdout_handler)
        cdc_logger.addHandler(csv_handler)
        cdc_logger.setLevel(logging.INFO)
        return cdc_logger

    @staticmethod
    def _csv_quote(text):
        buff = StringIO()
        wr = csv.writer(buff)
        wr.writerow([text])
        return buff.getvalue().strip()

    def log_response(self, resp):
        """csv-escape given text and write to the csv log

        """
        self.cdc_logger.info(self._csv_quote(resp.text),
                             extra={
                                 'http_status': resp.status_code,
                                 'pk': self._make_pk_from_response(resp),
                                 'url': resp.url,
                                 'request_body': self._csv_quote(resp.request.body.decode('utf8')) or ''
                             })

    @staticmethod
    def _make_pk_from_response(resp):
        return md5(resp.request.body or b'' + str(time.time()).encode('ascii')).hexdigest()

    def _request(self, method, url, *args, **kwargs):
        try:
            resp = super()._request(method, url, *args, **kwargs)
        except requests.HTTPError as err:
            # I think this will ultimately double log the errors, but
            # it quite makes sense. As the root logger doesn't know about
            # cdc logger at all
            self.log_response(err.response)
            raise
        else:
            self.log_response(resp)
            return resp
