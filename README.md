# The trade desk writer (STILL UNDER HEAVY DEV)

Can create campaigns and adgroups

# Configuration
```javascript
{
  "debug": true,
  "login": "foo",
  "#password": "foo"
}
```

The writer behavior is driven by the input tables you provide.
The TTD api accepts some deeply nested JSONs. However this component accepts data in `csv` format ([the KBC common interface](https://developers.keboola.com/extend/common-interface/folders/)).

The writer currently supports these operations.
- Creating campaigns
- Creating adgroups
- Creating campaign immediately followed by creating adgroup for the new id
- TODO: Updating existing campaign
- TODO: Updating existing adgroup

The writer logs all requests to csv and stdout/stderr to enable CDC

## Input table structure

The csv always has a `payload` column. It's value is a csv-escaped json string representing the JSON request payload as found in the docs https://apisb.thetradedesk.com/v3/doc/

In python you can get the csv from json as such
```python
import csv
import json

data = [{"CampaignId": "1234"}, {"CampaignId": "56678"}]
with open("data.csv", 'w') as f:
    wr = csv.DictWriter(f, fieldnames=["payload"])
    wr.writeheader()
    for row in data:
        wr.writerow({"payload": json.dumps(row)})
```

which would end up in this
```
payload
"{""CampaignId"": ""1234""}"
"{""CampaignId"": ""56678""}"
```
## Create adgroups
make a csv `/data/in/tables/create_adgroups.csv` which contains one column `"payload"`. The payload values correspond 1:1 to these https://apisb.thetradedesk.com/v3/doc/api/post-adgroup

## Create Campaigns
make a csv `/data/in/tables/create_campaigns.csv` containing the standard `"payload"` column.
 The payload values correspond 1:1 to these https://apisb.thetradedesk.com/v3/doc/api/post-campaign
 
## Create campaign and adgroup
This happens when tables
- `/data/in/tables/create_campaigns.csv` with columns `CampaignId,payload`
- `/data/in/tables/create_adgroups.csv` with columns `CampaignId,payload`
tables are present.

This is the detailed workflow:

1. Take a campaign (all rows with the same `CampaignId`) from `create_campaigns.csv`. At this point the `CampaignId` doesn't exist and is just a dummy placeholder value (must be unique within the dataset, though)
2. All adgroups (zero or more (more adgroups for one campaign are distinguished by the `AdGroupId` column)) with the same `CampaignId` from table `create_adgroups.csv` are fetched.
3. Make an API request to create the Campaign within TTD. Use the returned `CampaignId` instead of the dummy `CampaignId` when making the requests to create the adgroups. 



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


# Changelog

| version | changes                                              |
|---------|------------------------------------------------------|
|   0.0.3 | uses jsontangle to convert flattened csvs into jsons |
|         |                                                      |
