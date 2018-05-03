import tdd.writer

def test_deciding_action_creating_campaigns(tmpdir):
    camp = tmpdir.join(tdd.writer.FNAME_CAMPAIGNS)
    camp.write("foo")
    action = tdd.writer.decide_action(tmpdir.strpath)
    assert action == tdd.writer.create_campaigns

def test_deciding_action_creating_adgroups(tmpdir):
    adg = tmpdir.join(tdd.writer.FNAME_ADGROUPS)
    adg.write("foo")
    action = tdd.writer.decide_action(tmpdir.strpath)
    assert action == tdd.writer.create_adgroups

def test_deciding_actions_adgroups_and_campaigns(tmpdir):
    adg = tmpdir.join(tdd.writer.FNAME_ADGROUPS)
    adg.write("foo")
    camp = tmpdir.join(tdd.writer.FNAME_CAMPAIGNS)
    camp.write("foo")

    action = tdd.writer.decide_action(tmpdir.strpath)

    assert action == tdd.writer.create_campaigns_and_adgroups
