"""
Sort of functional tests for parsing input

"""
import pytest

from tdd.models import prepare_create_adgroup_data

def test_validating_creating_campaign(tmpdir):
    incsv_contents = """CampaignID,path,value
42,AdGroupName,"Test adgroup"
42,Description,"Test adgroup desc"
42,IsEnabled,True
42,IndustryCategoryID,42
42,RTBAttributes__BudgetSettings__Budget__Amount,1000
42,RTBAttributes__BudgetSettings__Budget__CurrencyCode,USD
42,RTBAttributes__BudgetSettings__DailyBudget__Amount,1000
42,RTBAttributes__BudgetSettings__DailyBudget__CurrencyCode,USD
42,RTBAttributes__BudgetSettings__PacingEnabled,True
42,RTBAttributes__BaseBidCPM__CurrencyCode,USD
42,RTBAttributes__BaseBidCPM__Amount,1000
42,RTBAttributes__MaxBidCPM__CurrencyCode,USD
42,RTBAttributes__MaxBidCPM__Amount,1000
42,RTBAttributes__CreativeIds___0,12
42,RTBAttributes__CreativeIds___1,12
42,RTBAttributes__CreativeIds___2,12
42,RTBAttributes__AudienceTargeting__AudienceId,666
42,RTBAttributes__ROIGoal__CPAInAdvertiserCurrency__CurrencyCode,USD
42,RTBAttributes__ROIGoal__CPAInAdvertiserCurrency__Amount,1000
42,RTBAttributes__AutoOptimizationSettings__IsSiteAutoOptimizationEnabled,True
42,RTBAttributes__AutoOptimizationSettings__IsUseClicksAsConversionsEnabled,True
42,RTBAttributes__AutoOptimizationSettings__IsBaseBidAutoOptimizationEnabled,True
42,RTBAttributes__AutoOptimizationSettings__IsUseSecondaryConversionsEnabled,True
42,RTBAttributes__AutoOptimizationSettings__IsSupplyVendorAutoOptimizationEnabled,True
42,RTBAttributes__AutoOptimizationSettings__IsCreativeAutoOptimizationEnabled,True
42,RTBAttributes__AutoOptimizationSettings__IsAudienceAutoOptimizationEnabled,True"""
    incsv = tmpdir.join('input.csv')
    incsv.write(incsv_contents)

    money = {
        "Amount": 1000.0,
        "CurrencyCode": "USD"
    }
    expected = {
        "CampaignID": "42",
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
    }

    for adgroup in prepare_create_adgroup_data(incsv.strpath, id_column='CampaignID'):
        assert adgroup == expected

