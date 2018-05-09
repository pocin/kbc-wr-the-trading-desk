import ttdwr.writer

def test_deciding_action_creating_campaigns(tmpdir):
    camp = tmpdir.join(ttdwr.writer.FNAME_CAMPAIGNS)
    camp.write("foo")
    action = ttdwr.writer.decide_action(tmpdir.strpath)
    assert action == ttdwr.writer.create_campaigns

def test_deciding_action_creating_adgroups(tmpdir):
    adg = tmpdir.join(ttdwr.writer.FNAME_ADGROUPS)
    adg.write("foo")
    action = ttdwr.writer.decide_action(tmpdir.strpath)
    assert action == ttdwr.writer.create_adgroups

def test_deciding_actions_adgroups_and_campaigns(tmpdir):
    adg = tmpdir.join(ttdwr.writer.FNAME_ADGROUPS)
    adg.write("foo")
    camp = tmpdir.join(ttdwr.writer.FNAME_CAMPAIGNS)
    camp.write("foo")

    action = ttdwr.writer.decide_action(tmpdir.strpath)

    assert action == ttdwr.writer.create_campaigns_and_adgroups
