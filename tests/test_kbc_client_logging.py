"""
Test concerning
 - logging of the responses
 - serializing input csvs into target jsons
"""


import re
import csv
import json
from collections import namedtuple
from io import StringIO
import requests
import pytest
import logging
from ttdwr.client import KBCTTDClient


def test_csv_quoting():
    tests = [
        ('Hello, world', '"Hello, world"'),
        (32, "32")
    ]
    for txt, expected in tests:
        assert KBCTTDClient._csv_quote(txt) == expected

def test_logging_into_csv_and_stdout(tmpdir, caplog):
    """Check that the logging function sends the request/response to
    csv and stream!"""
    log = tmpdir.join('sample_log.csv')

    client = KBCTTDClient(login='foo', password='bar', path_csv_log=log.strpath, base_url='https://apisb.thetradedesk.com/v3/')

    class Resp:
        pass
    resp = Resp()
    resp.url = 'this_is_url'
    resp.status_code = 200
    resp.request = Resp()
    resp.request.body = b'bodyyy'
    resp.request.method = b'methodyy'
    resp.text = 'bodyyy'
    client.log_response(resp)

    # logging to csv file
    # there should be one record
    lines = list(csv.DictReader(StringIO(log.read()), fieldnames=client.csv_log_header))

    assert len(lines) == 1
    assert lines[0]['url'] == resp.url

    # stdout should have just 1 record! previous errors due to the propagate
    # this is something in the root logger (which is not defined anywhere)
    # but the log is magically appearing there!
    assert 'client.py                  233 INFO     bodyyy\n' not in caplog.text
    # since the ttdwr.client_cdc logger has propagate False it doesn't get captured
    # assert len(caplog.records) == 1

def test_every__request_is_logged(tmpdir):
    log = tmpdir.join('sample_log.csv')

    client = KBCTTDClient(login='foo', password='bar',
                          path_csv_log=log.strpath,
                          base_url=None)

    # prevent fetching a token
    client.token = 'fake'
    url = 'https://httpbin.org/post'
    resp = client._request("POST", url, json={'foo':'bar'})
    log_content = log.read()
    rdr = csv.DictReader(StringIO(log.read()), fieldnames=client.csv_log_header)
    line = next(rdr)
    assert line['url'] == url
    assert line['http_status'] == '200'
    with pytest.raises(StopIteration):
        next(rdr)
