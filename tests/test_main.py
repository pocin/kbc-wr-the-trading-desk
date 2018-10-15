import pytest
import logging
from ttdwr.writer import main, create_campaigns_and_adgroups
from pathlib import Path

def test_creating_campaigns_and_adgroups(tmpdir, create_campaigns_adgroups_csvs):
    path_campaigns, path_adgroups = create_campaigns_adgroups_csvs

    class MockClient:
        def __init__(self):
            self.adgroup_ids = iter(["a{}".format(i) for i in range(10)])
        def create_campaign(self, payload):
            return {"CampaignId": "real_campaign"}
        def create_adgroup(self, payload):
            return {
                "CampaignId": payload["CampaignId"],
                "AdgroupId": next(self.adgroup_ids)
            }


    client = MockClient()
    campaign, adgroups = create_campaigns_and_adgroups(
        client,
        path_campaigns,
        path_adgroups)
    assert campaign['CampaignId']
    for i, adgrp in enumerate(adgroups):
        assert adgrp['AdgroupId'] == 'a{}'.format(i)

