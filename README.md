# The trading desk writer (STILL UNDER HEAVY DEV)

Can create campaigns and adgroups

# Configuration
```javascript
{
  "debug": true,
  "dry_run": true,
  "login": "foo",
  "#password": "foo"
}
```
set `dry_run` to `True` if you just want to test that your input tables will serialize without making any api calls.

The writer behavior is driven by the input tables you provide.
The TTD api accepts some deeply nested JSONs. However this component accepts data in `csv` format ([the KBC common interface](https://developers.keboola.com/extend/common-interface/folders/)).

To create nested JSONs out of flat CSVs, the [jsontangle](https://github.com/pocin/jsontangle) library was developed and is used.
Check out it's documentation for the details on the DSL grammar. It might be worthwhile to install it while developing transformations to verify that the fields are correct.

The writer currently supports these operations.
- Creating campaigns
- Creating adgroups
- Creating campaign immediately followed by creating adgroup for the new id
- TODO: Updating existing campaign
- TODO: Updating existing adgroup

In general, the writer behavior is as follows:
1. load the input tables
2. serialize csv -> json
3. verify the serialization went ok and the final json has all the fields that the API requires + cast datatypes (as per the TTD documentation). This is by no means 100%, you can see the schema [here](./tdd/models.py)
4. If all is good, acutally start making requests
5. Log all requests into csv which are then uploaded back to kbc Storage

## Create adgroups
check `ttdwr.models.CreateAdGroupSchema` for the schema which is being checked.

This is a csv template `/data/in/tables/create_adgroups.csv`

```
CampaignId,AdgroupId,path,value
42,whateverA,AdGroupName,"Test adgroup"
42,whateverA,Description,"Test adgroup desc"
42,whateverA,IsEnabled,True
42,whateverA,IndustryCategoryId,42
42,whateverA,RTBAttributes__BudgetSettings__Budget__Amount,1000
42,whateverA,RTBAttributes__BudgetSettings__Budget__CurrencyCode,USD
42,whateverA,RTBAttributes__BudgetSettings__DailyBudget__Amount,1000
42,whateverA,RTBAttributes__BudgetSettings__DailyBudget__CurrencyCode,USD
42,whateverA,RTBAttributes__BudgetSettings__PacingEnabled,True
42,whateverA,RTBAttributes__BaseBidCPM__CurrencyCode,USD
42,whateverA,RTBAttributes__BaseBidCPM__Amount,1000
42,whateverA,RTBAttributes__MaxBidCPM__CurrencyCode,USD
42,whateverA,RTBAttributes__MaxBidCPM__Amount,1000
42,whateverA,RTBAttributes__CreativeIds___0,12
42,whateverA,RTBAttributes__CreativeIds___1,12
42,whateverA,RTBAttributes__CreativeIds___2,12
42,whateverA,RTBAttributes__AudienceTargeting__AudienceId,666
42,whateverA,RTBAttributes__ROIGoal__CPAInAdvertiserCurrency__CurrencyCode,USD
42,whateverA,RTBAttributes__ROIGoal__CPAInAdvertiserCurrency__Amount,1000
42,whateverA,RTBAttributes__AutoOptimizationSettings__IsSiteAutoOptimizationEnabled,True
42,whateverA,RTBAttributes__AutoOptimizationSettings__IsUseClicksAsConversionsEnabled,True
42,whateverA,RTBAttributes__AutoOptimizationSettings__IsBaseBidAutoOptimizationEnabled,True
42,whateverA,RTBAttributes__AutoOptimizationSettings__IsUseSecondaryConversionsEnabled,True
42,whateverA,RTBAttributes__AutoOptimizationSettings__IsSupplyVendorAutoOptimizationEnabled,True
42,whateverA,RTBAttributes__AutoOptimizationSettings__IsCreativeAutoOptimizationEnabled,True
42,whateverA,RTBAttributes__AutoOptimizationSettings__IsAudienceAutoOptimizationEnabled,True
```

which will be internally compiled into
```
{
        "CampaignId": "42",
        "AdgroupId": "whateverA", #this is just a temporary placeholder and is not sent to the API!
        "AdGroupName": "Test adgroup",
        "Description": "Test adgroup desc",
        "IsEnabled": True,
        "IndustryCategoryId": 42,
        "RTBAttributes": {
            "BudgetSettings": {
                "Budget": money,
                "DailyBudget": money,
                "PacingEnabled": True},
            "BaseBidCPM": {"Amount": 1000.0, "CurrencyCode": "USD"},
            "MaxBidCPM": {"Amount": 1000.0, "CurrencyCode": "USD"},
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
```


the column `AdgroupId` is an arbitrary unique string grouping all rows for given `CampaignId-Adgroup` combination.  
e.g.: One campaign (id 42) can have multiple adgroups (`whateverA` and `whateverB`)

```
CampaignId,AdgroupId,path,value
42,whateverA,AdGroupName,"first adgroup for campaign 42"
...
42,whateverA,RTBAttributes__AutoOptimizationSettings__IsAudienceAutoOptimizationEnabled,True
42,whateverB,AdGroupName,"second adgroup for campaign 42"
...
42,whateverB,RTBAttributes__AutoOptimizationSettings__IsAudienceAutoOptimizationEnabled,True
```



to attempt and compile the csv -> json locally try
```
$ git clone https://github.com/pocin/kbc-wr-the-trading-desk && cd kbc-wr-the-trading-desk
$ cp /your/path/to/create_campaigns.csv ./data
$ docker-compose run --rm dev
/code # python3
>>> import ttdwr.models
>>> path_campaigns = './data/create_campaigns.csv'
>>> serialized = ttdwr.models._prepare_create_campaign_data(path_campaign)
>>> for adgroup in serialized:
...     print(adgroup)

```

## Create Campaigns

check `ttdwr.models.CreateCampaignSchema` for the schema which is being checked.

This csv template `/data/in/tables/create_campaigns.csv`
```
CampaignId,path,value
temporary_but_unique,AdvertiserId,42
temporary_but_unique,CampaignName,TEST
temporary_but_unique,Description,TEST
temporary_but_unique,Budget__Amount,1000
temporary_but_unique,Budget__CurrencyCode,USD
temporary_but_unique,DailyBudget__Amount,1000
temporary_but_unique,DailyBudget__CurrencyCode,USD
temporary_but_unique,StartDate,2017
temporary_but_unique,EndDate,2017
temporary_but_unique,CampaignConversionReportingColumns___0,"{""TrackingTagId"": 1, ""ReportingColumnId"": 11}"
temporary_but_unique,CampaignConversionReportingColumns___1,"{""TrackingTagId"": 2, ""ReportingColumnId"": 22}"
```
would serialize into
```

{
  "CampaignId": "temporary_but_unique", #not sent to the api! used to identify all rows in csv
  "AdvertiserId": 42,
  "CampaignName": "TEST",
  "Description": "TEST",
  "Budget": {"Amount": 1000.0, "CurrencyCode": "USD"},
  "DailyBudget": {"Amount": 1000.0, "CurrencyCode": "USD"},
  "StartDate": "2017",
  "EndDate": "2017",
  "CampaignConversionReportingColumns": [
      {"TrackingTagId": 2,
        "ReportingColumnId": 22},
      {"TrackingTagId": 1,
        "ReportingColumnId": 11}
  ]
}

``` 
At this point, serializing something into a a list of nested dictionaries is complicated and [jsontangle]() doesn't support this.
For this reason, the `CampaignConversionReportingColumns` (an array of objects) is actually a json serialized into string (with all `"` double quotes properly escaped).  
I.e. this string (a value in the csv column) `"{""TrackingTagId"": 2, ""ReportingColumnId"": 22}"` will be serialized into this object `{"TrackingTagId": 2, "ReportingColumnId": 22}"`

The `CampaignId` is just a placeholder to group all the rows for given campaign together and is ignored.


## Create campaign and adgroup
This happens when both `/data/in/tables/create_campaigns.csv` and `/data/in/tables/create_adgroups.csv` tables are present.
This is the detailed workflow:

1. Take a campaign (all rows with the same `CampaignId`) from `create_campaigns.csv`. At this point the `CampaignId` doesn't exist and is just a dummy placeholder value (must be unique within the dataset, though)
2. All adgroups (zero or more (more adgroups for one campaign are distinguished by the `AdgroupId` column)) with the same `CampaignId` from table `create_adgroups.csv` are fetched.
3. Make an API request to create the Campaign. Use the returned `CampaignId` instead of the dummy one when making the requests to create the adgroups.

# Development
## Run locally
```
$ docker-compose run --rm dev
# gets you an interactive shell
# mounts the ./data/ folder to /data/
```

## Run tests
```
make test
# after dev session is finished to clean up containers..
make clean 
```
