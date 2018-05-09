import pytest
import ttdwr.models
import logging


@pytest.fixture
def conn(tmpdir):
    db_path = tmpdir.join('tmp_master_database.sqlite3')
    conn = ttdwr.models._init_database(db_path.strpath)
    return conn

@pytest.fixture
def conn_with_records(tmpdir):
    db_path = tmpdir.join('tmp_master_database.sqlite3')
    conn = ttdwr.models._init_database(db_path.strpath)

    curr = conn.cursor()
    payload = {"foo": "bar", "baz": 42}
    ttdwr.models.insert_campaign(curr, 'campA', payload)
    ttdwr.models.insert_adgroup(curr, 'campA', 'adgrpA', payload)
    ttdwr.models.insert_adgroup(curr, 'campA', 'adgrpB', payload)
    ttdwr.models.insert_adgroup(curr, 'campA', 'adgrpC', payload)
    ttdwr.models.insert_adgroup(curr, 'campB', 'adgrpX', payload)
    conn.commit()
    return conn


@pytest.fixture
def valid_adgroup_csv(tmpdir):

    incsv_contents = """CampaignId,AdgroupId,path,value
temporary,tempA,AdGroupName,"Test adgroup"
temporary,tempA,Description,"Test adgroup desc"
temporary,tempA,IsEnabled,True
temporary,tempA,IndustryCategoryId,42
temporary,tempA,RTBAttributes__BudgetSettings__Budget__Amount,1000
temporary,tempA,RTBAttributes__BudgetSettings__Budget__CurrencyCode,USD
temporary,tempA,RTBAttributes__BudgetSettings__DailyBudget__Amount,1000
temporary,tempA,RTBAttributes__BudgetSettings__DailyBudget__CurrencyCode,USD
temporary,tempA,RTBAttributes__BudgetSettings__PacingEnabled,True
temporary,tempA,RTBAttributes__BaseBidCPM__CurrencyCode,USD
temporary,tempA,RTBAttributes__BaseBidCPM__Amount,1000
temporary,tempA,RTBAttributes__MaxBidCPM__CurrencyCode,USD
temporary,tempA,RTBAttributes__MaxBidCPM__Amount,1000
temporary,tempA,RTBAttributes__CreativeIds___0,12
temporary,tempA,RTBAttributes__CreativeIds___1,12
temporary,tempA,RTBAttributes__CreativeIds___2,12
temporary,tempA,RTBAttributes__AudienceTargeting__AudienceId,666
temporary,tempA,RTBAttributes__ROIGoal__CPAInAdvertiserCurrency__CurrencyCode,USD
temporary,tempA,RTBAttributes__ROIGoal__CPAInAdvertiserCurrency__Amount,1000
temporary,tempA,RTBAttributes__AutoOptimizationSettings__IsSiteAutoOptimizationEnabled,True
temporary,tempA,RTBAttributes__AutoOptimizationSettings__IsUseClicksAsConversionsEnabled,True
temporary,tempA,RTBAttributes__AutoOptimizationSettings__IsBaseBidAutoOptimizationEnabled,True
temporary,tempA,RTBAttributes__AutoOptimizationSettings__IsUseSecondaryConversionsEnabled,True
temporary,tempA,RTBAttributes__AutoOptimizationSettings__IsSupplyVendorAutoOptimizationEnabled,True
temporary,tempA,RTBAttributes__AutoOptimizationSettings__IsCreativeAutoOptimizationEnabled,True
temporary,tempA,RTBAttributes__AutoOptimizationSettings__IsAudienceAutoOptimizationEnabled,True
temporary,tempB,AdGroupName,"Test adgroup2"
temporary,tempB,Description,"Test adgroup desc"
temporary,tempB,IsEnabled,True
temporary,tempB,IndustryCategoryId,42
temporary,tempB,RTBAttributes__BudgetSettings__Budget__Amount,1000
temporary,tempB,RTBAttributes__BudgetSettings__Budget__CurrencyCode,USD
temporary,tempB,RTBAttributes__BudgetSettings__DailyBudget__Amount,1000
temporary,tempB,RTBAttributes__BudgetSettings__DailyBudget__CurrencyCode,USD
temporary,tempB,RTBAttributes__BudgetSettings__PacingEnabled,True
temporary,tempB,RTBAttributes__BaseBidCPM__CurrencyCode,USD
temporary,tempB,RTBAttributes__BaseBidCPM__Amount,1000
temporary,tempB,RTBAttributes__MaxBidCPM__CurrencyCode,USD
temporary,tempB,RTBAttributes__MaxBidCPM__Amount,1000
temporary,tempB,RTBAttributes__CreativeIds___0,12
temporary,tempB,RTBAttributes__CreativeIds___1,12
temporary,tempB,RTBAttributes__CreativeIds___2,12
temporary,tempB,RTBAttributes__AudienceTargeting__AudienceId,666
temporary,tempB,RTBAttributes__ROIGoal__CPAInAdvertiserCurrency__CurrencyCode,USD
temporary,tempB,RTBAttributes__ROIGoal__CPAInAdvertiserCurrency__Amount,1000
temporary,tempB,RTBAttributes__AutoOptimizationSettings__IsSiteAutoOptimizationEnabled,True
temporary,tempB,RTBAttributes__AutoOptimizationSettings__IsUseClicksAsConversionsEnabled,True
temporary,tempB,RTBAttributes__AutoOptimizationSettings__IsBaseBidAutoOptimizationEnabled,True
temporary,tempB,RTBAttributes__AutoOptimizationSettings__IsUseSecondaryConversionsEnabled,True
temporary,tempB,RTBAttributes__AutoOptimizationSettings__IsSupplyVendorAutoOptimizationEnabled,True
temporary,tempB,RTBAttributes__AutoOptimizationSettings__IsCreativeAutoOptimizationEnabled,True
temporary,tempB,RTBAttributes__AutoOptimizationSettings__IsAudienceAutoOptimizationEnabled,True"""
    incsv = tmpdir.join('create_adgroups.csv')
    incsv.write(incsv_contents)

    return incsv.strpath

@pytest.fixture
def valid_campaign_csv(tmpdir):
    incsv_contents = '''CampaignId,path,value
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
    incsv = tmpdir.join('create_campaigns.csv')
    incsv.write(incsv_contents)

    return incsv.strpath
