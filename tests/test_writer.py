import ttdwr.writer
from pathlib import Path

def test_deciding_action_creating_campaigns(tmpdir):
    intables = tmpdir.mkdir('in').mkdir('tables')
    camp = intables.join(ttdwr.writer.FNAME_CAMPAIGNS)
    camp.write("foo")
    action = ttdwr.writer.decide_action(Path(tmpdir.strpath), {})

    # it's a partial
    assert action.func == ttdwr.writer.create_campaigns

def test_deciding_action_creating_adgroups(tmpdir):
    intables = tmpdir.mkdir('in').mkdir('tables')
    adg = intables.join(ttdwr.writer.FNAME_ADGROUPS)
    adg.write("foo")
    action = ttdwr.writer.decide_action(Path(tmpdir.strpath), {})
    # it's a partial
    assert action.func == ttdwr.writer.create_adgroups

def test_deciding_actions_adgroups_and_campaigns(tmpdir):
    intables = tmpdir.mkdir('in').mkdir('tables')
    adg = intables.join(ttdwr.writer.FNAME_ADGROUPS)
    adg.write("foo")
    camp = intables.join(ttdwr.writer.FNAME_CAMPAIGNS)
    camp.write("foo")

    action = ttdwr.writer.decide_action(tmpdir.strpath, {})

    # it's a partial
    assert action.func == ttdwr.writer.create_campaigns_and_adgroups

def test_grouping_related_adgroups():
    raw_data = [
        {
            "dummy_campaign_id": 1,
            "payload": {"foobar": 1}
        },
        {
            "dummy_campaign_id": 2,
            "payload": {"foobar": 3}
        },
        {
            "dummy_campaign_id": 1,
            "payload": {"foobar": 2}
        },
        {
            "dummy_campaign_id": 2,
            "payload": {"foobar": 4}
        }
    ]

    expected = {
        1: [
            {
                "dummy_campaign_id": 1,
                "payload": {"foobar": 1}
            },
            {
                "dummy_campaign_id": 1,
                "payload": {"foobar": 2}
            }
        ],
        2: [
            {
                "dummy_campaign_id": 2,
                "payload": {"foobar": 3}
            },
            {
                "dummy_campaign_id": 2,
                "payload": {"foobar": 4}
            }
        ]
    }

    mapping = ttdwr.writer.group_adgroups_to_campaigns(raw_data)
    assert mapping == expected
