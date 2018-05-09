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

from ttdwr.exceptions import TTDConfigError
from ttdapi.client import TTDClient

logger = logging.getLogger(__name__)


class KBCTTDClient(TTDClient):
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
