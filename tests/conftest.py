import pytest
import tdd.models
import logging

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def conn(tmpdir):
    db_path = tmpdir.join('tmp_master_database.sqlite3')
    conn = tdd.models._init_database(db_path.strpath)
    return conn

@pytest.fixture
def conn_with_records(tmpdir):
    db_path = tmpdir.join('tmp_master_database.sqlite3')
    conn = tdd.models._init_database(db_path.strpath)

    curr = conn.cursor()
    payload = {"foo": "bar", "baz": 42}
    tdd.models.insert_campaign(curr, 'campA', payload)
    tdd.models.insert_adgroup(curr, 'campA', 'adgrpA', payload)
    tdd.models.insert_adgroup(curr, 'campA', 'adgrpB', payload)
    tdd.models.insert_adgroup(curr, 'campA', 'adgrpC', payload)
    conn.commit()
    return conn


@pytest.fixture
def valid_adgroup_csv(tmpdir):

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
    incsv = tmpdir.join('create_adgroups.csv')
    incsv.write(incsv_contents)

    return incsv.strpath

@pytest.fixture
def valid_campaign_csv(tmpdir):
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
    incsv = tmpdir.join('create_campaigns.csv')
    incsv.write(incsv_contents)

    return incsv.strpath
