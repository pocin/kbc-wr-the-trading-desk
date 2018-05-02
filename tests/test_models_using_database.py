import json
import pytest
import tdd.models

@pytest.fixture
def conn(tmpdir):
    db_path = tmpdir.join('tmp_master_database.sqlite3')
    conn = tdd.models._init_database(db_path.strpath)
    curr = conn.cursor()
    tdd.models._create_tables(curr)
    conn.commit()
    return conn



def test_creating_tables(tmpdir):
    db_path = tmpdir.join('tmp_database.sqlite3')
    conn = tdd.models._init_database(db_path.strpath)

    curr = conn.cursor()
    tdd.models._create_tables(curr)
    conn.commit()

    curr = conn.cursor()
    tables = curr.execute("SELECT * FROM sqlite_master WHERE type='table'")
    tables = tables.fetchall()
    assert len(tables) == 2
    for table in tables:
        assert table['name'] in ('campaigns', 'adgroups')

def test_inserting_campaign(conn):
    curr = conn.cursor()
    payload = {"foo": "bar"}
    inserted = tdd.models.insert_campaign(curr, '42', payload)
    conn.commit()

    curr = conn.cursor()
    curr.execute("SELECT * FROM campaigns")
    campaign = curr.fetchone()
    assert campaign['campaign_id'] == '42'
    assert campaign['payload'] == '{"foo": "bar"}'
    assert json.loads(campaign['payload']) == {"foo": "bar"}


def test_inserting_adgroup(conn):
    curr = conn.cursor()
    payload = {"foo": "bar", "baz": 42}
    tdd.models.insert_adgroup(curr, '42', 'tempA', payload)
    tdd.models.insert_adgroup(curr, '42', 'tempB', payload)
    conn.commit()

    curr = conn.cursor()
    curr.execute("SELECT * FROM adgroups ORDER BY adgroup_id;")
    ada, adb = curr.fetchall()

    assert ada['campaign_id'] == '42'
    assert adb['campaign_id'] == '42'

    assert ada['adgroup_id'] == 'tempA'
    assert adb['adgroup_id'] == 'tempB'

    assert json.loads(ada['payload'])['baz'] == 42
