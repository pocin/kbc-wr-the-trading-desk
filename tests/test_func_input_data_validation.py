"""
Sort of functional tests for parsing input

"""
import json
from pathlib import Path
import pytest

from tdd.models import _prepare_create_adgroup_data, _prepare_create_campaign_data
import tdd.writer


def test_validating_creating_adgroup(valid_adgroup_csv, conn):
    """One campaign can have multiple adgroups
    """
    money = {
        "Amount": 1000.0,
        "CurrencyCode": "USD"
    }
    expected = [{
        "CampaignID": "42",
        "tempAdgroupID": "tempA",
        "AdGroupName": "Test adgroup",
        "Description": "Test adgroup desc",
        "IsEnabled": True,
        "IndustryCategoryID": 42,
        "RTBAttributes": {
            "BudgetSettings": {
                "Budget": money,
                "DailyBudget": money,
                "PacingEnabled": True},
            "BaseBidCPM": money,
            "MaxBidCPM": money,
            "CreativeIds": [12, 12, 12],
            "AudienceTargeting": {"AudienceId": 666},
            "ROIGoal": {"CPAInAdvertiserCurrency": money},
            "AutoOptimizationSettings": {
                "IsBaseBidAutoOptimizationEnabled": True,
                "IsAudienceAutoOptimizationEnabled": True,
                "IsSiteAutoOptimizationEnabled": True,
                "IsCreativeAutoOptimizationEnabled": True,
                "IsSupplyVendorAutoOptimizationEnabled": True,
                "IsUseClicksAsConversionsEnabled": True,
                "IsUseSecondaryConversionsEnabled": True
            }
        }
    }, {
        "CampaignID": "42",
        "tempAdgroupID": "tempB",
        "AdGroupName": "Test adgroup2",
        "Description": "Test adgroup desc",
        "IsEnabled": True,
        "IndustryCategoryID": 42,
        "RTBAttributes": {
            "BudgetSettings": {
                "Budget": money,
                "DailyBudget": money,
                "PacingEnabled": True},
            "BaseBidCPM": money,
            "MaxBidCPM": money,
            "CreativeIds": [12, 12, 12],
            "AudienceTargeting": {"AudienceId": 666},
            "ROIGoal": {"CPAInAdvertiserCurrency": money},
            "AutoOptimizationSettings": {
                "IsBaseBidAutoOptimizationEnabled": True,
                "IsAudienceAutoOptimizationEnabled": True,
                "IsSiteAutoOptimizationEnabled": True,
                "IsCreativeAutoOptimizationEnabled": True,
                "IsSupplyVendorAutoOptimizationEnabled": True,
                "IsUseClicksAsConversionsEnabled": True,
                "IsUseSecondaryConversionsEnabled": True
            }
        }
    }
    ]

    adgroups = list(_prepare_create_adgroup_data(valid_adgroup_csv))
    assert (adgroups[0] == expected[0]) or (adgroups[0] == expected[1])
    assert (adgroups[1] == expected[0]) or (adgroups[1] == expected[1])


    tdd.models._adgroup_data_into_db(adgroups, conn)
    curr = conn.cursor()
    for adgrp in curr.execute("SELECT * FROM adgroups;"):
        if adgrp['adgroup_id'] == 'tempA':
            assert json.loads(adgrp['payload'])["Description"] == "Test adgroup desc"
        if adgrp['adgroup_id'] == 'tempB':
            assert json.loads(adgrp['payload'])["Description"] == "Test adgroup desc"


def test_creating_campaign_validation(valid_campaign_csv):


    money = {
        "Amount": 1000.0,
        "CurrencyCode": "USD"
    }
    expected = {
        "CampaignID": "temporary",
        "AdvertiserId": 42,
        "CampaignName": "TEST",
        "Description": "TEST",
        "Budget": money,
        "DailyBudget": money,
        "StartDate": "2017",
        "EndDate": "2017",
        "CampaignConversionReportingColumns": [
            {"TrackingTagId": 1,
             "ReportingColumnId": 11},
            {"TrackingTagId": 1,
             "ReportingColumnId": 11}
        ]
    }

    # Either jsontangle must parse nested jsons
    # OR the nested json will be a string and Voluptuos schema will load the json

    # Depends if the nested jsons need to be dynamic or static?

    for campaign in _prepare_create_campaign_data(valid_campaign_csv):
        assert campaign == expected

def test_func_loading_adgroup_data(valid_adgroup_csv, tmpdir):
    datadir = Path(valid_adgroup_csv).parent

    db = tdd.writer.prepare_data(datadir, db_path=tmpdir.join('db.sqlite3').strpath)

    # at this point I expect a database to have serialized adgroup data
    # but empty campaigns

    with db:
        adgroups = db.execute("SELECT * FROM adgroups").fetchall()
        assert len(adgroups) == 2
        assert adgroups[0]['campaign_id'] == '42'

