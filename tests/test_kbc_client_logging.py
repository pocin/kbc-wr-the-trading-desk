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

from tdd.client import KBCTDDClient

def test_csv_quoting():
    tests = [
        ('Hello, world', '"Hello, world"'),
        (32, "32")
    ]
    for txt, expected in tests:
        assert KBCTDDClient._csv_quote(txt) == expected

def test_csv_logging_json_string(tmpdir, caplog):
    log = tmpdir.join('sample_log.csv')

    client = KBCTDDClient(login='foo', password='bar', path_csv_log=log.strpath)

    Response = namedtuple("Response", "status_code, text")
    resp = Response(200, '["Hello, world!"]')
    client.log_response(resp)

    log_content = log.read()
    rdr = csv.DictReader(StringIO(log.read()), fieldnames=client.csv_log_header)
    line = next(rdr)
    assert json.loads(line['response']) == ['Hello, world!']
    assert line['http_status'] == "200"

def test_csv_logging_json(tmpdir, caplog):
    log = tmpdir.join('sample_log.csv')

    client = KBCTDDClient(login='foo', password='bar', path_csv_log=log.strpath)

    Response = namedtuple("Response", "status_code, text")
    resp = Response(200, '["Hello, world!"]')
    client.log_response(resp)
    log_content = log.read()
    assert log_content.endswith('200,"[""Hello, world!""]"\n')


def test_every__request_is_logged(tmpdir):
    log = tmpdir.join('sample_log.csv')

    client = KBCTDDClient(login='foo', password='bar',
                          path_csv_log=log.strpath,
                          base_url=None)

    client.token = 'fake'
    resp = client._request("GET", 'https://httpbin.org/get', params={'foo':'bar'})

    log_content = log.read()
    rdr = csv.DictReader(StringIO(log.read()), fieldnames=client.csv_log_header)
    line = next(rdr)
    resp_json = json.loads(line['response'])
    assert resp_json['args'] == {'foo':'bar'}
    assert resp_json['headers']['Ttd-Auth'] == 'fake'
    with pytest.raises(StopIteration):
        next(rdr)
