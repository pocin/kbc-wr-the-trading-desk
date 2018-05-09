import json
import pytest
import ttdwr.models


def test_creating_tables(tmpdir):
    db_path = tmpdir.join('tmp_database.sqlite3')
    conn = ttdwr.models._init_database(db_path.strpath)

    curr = conn.cursor()
    tables = curr.execute("SELECT * FROM sqlite_master WHERE type='table'")
    tables = tables.fetchall()
    assert len(tables) == 2
    for table in tables:
        assert table['name'] in ('campaigns', 'adgroups')

def test_inserting_campaign(conn):
    curr = conn.cursor()
    payload = {"foo": "bar"}
    inserted = ttdwr.models.insert_campaign(curr, 'temporary', payload)
    conn.commit()

    curr = conn.cursor()
    curr.execute("SELECT * FROM campaigns")
    campaign = curr.fetchone()
    assert campaign['campaign_id'] == 'temporary'
    assert campaign['payload'] == '{"foo": "bar"}'
    assert json.loads(campaign['payload']) == {"foo": "bar"}


def test_inserting_adgroup(conn):
    curr = conn.cursor()
    payload = {"foo": "bar", "baz": 42}
    ttdwr.models.insert_adgroup(curr, 'temporary', 'tempA', payload)
    ttdwr.models.insert_adgroup(curr, 'temporary', 'tempB', payload)
    conn.commit()

    curr = conn.cursor()
    curr.execute("SELECT * FROM adgroups ORDER BY adgroup_id;")
    ada, adb = curr.fetchall()

    assert ada['campaign_id'] == 'temporary'
    assert adb['campaign_id'] == 'temporary'

    assert ada['adgroup_id'] == 'tempA'
    assert adb['adgroup_id'] == 'tempB'

    assert json.loads(ada['payload'])['baz'] == 42

def test_querying_campaigns(conn_with_records):
    campaigns = ttdwr.models.query_campaigns(conn_with_records)
    campaign = next(campaigns)
    assert campaign['campaign_id'] == 'campA'
    assert campaign['payload'] is not None
    with pytest.raises(IndexError):
        campaign['adgroup_id']
    with pytest.raises(StopIteration):
        next(campaigns)



def test_querying_adgroups(conn_with_records):
    adgroups = list(ttdwr.models.query_adgroups(conn_with_records, campaign_id='campA'))
    assert len(adgroups) == 3
    for adgroup in adgroups:
        assert adgroup['campaign_id'] == 'campA'
        assert adgroup['adgroup_id'] in ("adgrpA", "adgrpB", "adgrpC")
        assert adgroup['payload'] is not None

def test_querying_all_adgroups(conn_with_records):
    adgroups = list(ttdwr.models.query_adgroups(conn_with_records, campaign_id=None))
    assert len(adgroups) == 4
