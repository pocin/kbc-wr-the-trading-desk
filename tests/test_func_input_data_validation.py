"""
Sort of functional tests for parsing input

"""
import pytest
import json

from tdd.models import _prepare_create_adgroup_data, _prepare_create_campaign_data
import tdd.models


@pytest.fixture
def conn(tmpdir):
    db_path = tmpdir.join('tmp_master_database.sqlite3')
    conn = tdd.models._init_database(db_path.strpath)
    return conn

def test_validating_creating_adgroup(tmpdir, conn):
    """One campaign can have multiple adgroups
    """
    incsv_contents = """CampaignID,tempAdgroupID,path,value
42,tempA,AdGroupName,"Test adgroup"
42,tempA,Description,"Test adgroup desc"
42,tempA,IsEnabled,True
42,tempA,IndustryCategoryID,42
42,tempA,RTBAttributes__BudgetSettings__Budget__Amount,1000
42,tempA,RTBAttributes__BudgetSettings__Budget__CurrencyCode,USD
42,tempA,RTBAttributes__BudgetSettings__DailyBudget__Amount,1000
42,tempA,RTBAttributes__BudgetSettings__DailyBudget__CurrencyCode,USD
42,tempA,RTBAttributes__BudgetSettings__PacingEnabled,True
42,tempA,RTBAttributes__BaseBidCPM__CurrencyCode,USD
42,tempA,RTBAttributes__BaseBidCPM__Amount,1000
42,tempA,RTBAttributes__MaxBidCPM__CurrencyCode,USD
42,tempA,RTBAttributes__MaxBidCPM__Amount,1000
42,tempA,RTBAttributes__CreativeIds___0,12
42,tempA,RTBAttributes__CreativeIds___1,12
42,tempA,RTBAttributes__CreativeIds___2,12
42,tempA,RTBAttributes__AudienceTargeting__AudienceId,666
42,tempA,RTBAttributes__ROIGoal__CPAInAdvertiserCurrency__CurrencyCode,USD
42,tempA,RTBAttributes__ROIGoal__CPAInAdvertiserCurrency__Amount,1000
42,tempA,RTBAttributes__AutoOptimizationSettings__IsSiteAutoOptimizationEnabled,True
42,tempA,RTBAttributes__AutoOptimizationSettings__IsUseClicksAsConversionsEnabled,True
42,tempA,RTBAttributes__AutoOptimizationSettings__IsBaseBidAutoOptimizationEnabled,True
42,tempA,RTBAttributes__AutoOptimizationSettings__IsUseSecondaryConversionsEnabled,True
42,tempA,RTBAttributes__AutoOptimizationSettings__IsSupplyVendorAutoOptimizationEnabled,True
42,tempA,RTBAttributes__AutoOptimizationSettings__IsCreativeAutoOptimizationEnabled,True
42,tempA,RTBAttributes__AutoOptimizationSettings__IsAudienceAutoOptimizationEnabled,True
42,tempB,AdGroupName,"Test adgroup2"
42,tempB,Description,"Test adgroup desc"
42,tempB,IsEnabled,True
42,tempB,IndustryCategoryID,42
42,tempB,RTBAttributes__BudgetSettings__Budget__Amount,1000
42,tempB,RTBAttributes__BudgetSettings__Budget__CurrencyCode,USD
42,tempB,RTBAttributes__BudgetSettings__DailyBudget__Amount,1000
42,tempB,RTBAttributes__BudgetSettings__DailyBudget__CurrencyCode,USD
42,tempB,RTBAttributes__BudgetSettings__PacingEnabled,True
42,tempB,RTBAttributes__BaseBidCPM__CurrencyCode,USD
42,tempB,RTBAttributes__BaseBidCPM__Amount,1000
42,tempB,RTBAttributes__MaxBidCPM__CurrencyCode,USD
42,tempB,RTBAttributes__MaxBidCPM__Amount,1000
42,tempB,RTBAttributes__CreativeIds___0,12
42,tempB,RTBAttributes__CreativeIds___1,12
42,tempB,RTBAttributes__CreativeIds___2,12
42,tempB,RTBAttributes__AudienceTargeting__AudienceId,666
42,tempB,RTBAttributes__ROIGoal__CPAInAdvertiserCurrency__CurrencyCode,USD
42,tempB,RTBAttributes__ROIGoal__CPAInAdvertiserCurrency__Amount,1000
42,tempB,RTBAttributes__AutoOptimizationSettings__IsSiteAutoOptimizationEnabled,True
42,tempB,RTBAttributes__AutoOptimizationSettings__IsUseClicksAsConversionsEnabled,True
42,tempB,RTBAttributes__AutoOptimizationSettings__IsBaseBidAutoOptimizationEnabled,True
42,tempB,RTBAttributes__AutoOptimizationSettings__IsUseSecondaryConversionsEnabled,True
42,tempB,RTBAttributes__AutoOptimizationSettings__IsSupplyVendorAutoOptimizationEnabled,True
42,tempB,RTBAttributes__AutoOptimizationSettings__IsCreativeAutoOptimizationEnabled,True
42,tempB,RTBAttributes__AutoOptimizationSettings__IsAudienceAutoOptimizationEnabled,True"""
    incsv = tmpdir.join('input.csv')
    incsv.write(incsv_contents)

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

    adgroups = list(_prepare_create_adgroup_data(incsv.strpath))
    assert (adgroups[0] == expected[0]) or (adgroups[0] == expected[1])
    assert (adgroups[1] == expected[0]) or (adgroups[1] == expected[1])


    tdd.models._adgroup_data_into_db(adgroups, conn)
    curr = conn.cursor()
    for adgrp in curr.execute("SELECT * FROM adgroups;"):
        if adgrp['adgroup_id'] == 'tempA':
            assert json.loads(adgrp['payload'])["Description"] == "Test adgroup desc"
        if adgrp['adgroup_id'] == 'tempB':
            assert json.loads(adgrp['payload'])["Description"] == "Test adgroup desc"


def test_creating_campaign_validation(tmpdir):

    incsv_contents = '''CampaignID,path,value
temporary,AdvertiserId,42
temporary,CampaignName,TEST
temporary,Description,TEST
temporary,Budget__Amount,1000
temporary,Budget__CurrencyCode,USD
temporary,DailyBudget__Amount,1000
temporary,DailyBudget__CurrencyCode,USD
temporary,StartDate,2017
temporary,EndDate,2017
temporary,CampaignConversionReportingColumns___0,"{""TrackingTagId"": 1, ""ReportingColumnId"": 11}"
temporary,CampaignConversionReportingColumns___1,"{""TrackingTagId"": 1, ""ReportingColumnId"": 11}"
'''
    incsv = tmpdir.join('input.csv')
    incsv.write(incsv_contents)

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

    for campaign in _prepare_create_campaign_data(incsv.strpath):
        assert campaign == expected
