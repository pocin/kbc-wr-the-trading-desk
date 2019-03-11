# The trade desk writer (STILL UNDER HEAVY DEV)

Can create campaigns and adgroups

# Configuration
```javascript
{
  "debug": true,
  "login": "foo",
  "#password": "foo",
  "base_url": "https://api.thetradedesk.com/v3/"
}
```

`base_url` (essentially choose from `https://api.thetradedesk.com/v3/` and `https://apisb.thetradedesk.com/v3/`)

The writer behavior is driven by the input tables you provide.
The TTD api accepts some deeply nested JSONs. However this component accepts data in `csv` format ([the KBC common interface](https://developers.keboola.com/extend/common-interface/folders/)).

The writer currently supports these operations.
- Creating campaigns
- Creating adgroups
- Creating campaign immediately followed by creating adgroup for the new id
- Cloning campaigns based off a campaign template

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

which would end up looking like this
```bash
$ cat data.csv
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
- `/data/in/tables/create_campaigns.csv` with columns `dummy_campaign_id,payload`
- `/data/in/tables/create_adgroups.csv` with columns `dummy_campaign_id,payload`
are present.

This is what happens under the hood:

1. Take a campaign from `create_campaigns.csv`. At this point the `dummy_campaign_id` is just a dummy placeholder value (must be unique within the dataset, though)
2. All adgroups with the same `dummy_campaign_id` from table `create_adgroups.csv` are fetched.
3. API request to create the Campaign within TTD is made. The returned (real) `CampaignId` is used instead of the dummy one, when making the requests to create the adgroups.

## Clone campaigns

POST: https://api.thetradedesk.com/v3/campaign/clone

### input
#### tables
`in/tables/clone_campaigns.csv`
```csv
payload,my_id
{json_payload},foobar
```

- column "payload" is mandatory and contains the full payload that will be sent
  to the API
- you can add as many other columns as you wish, they will be simply copied over
  to the output table. This can be used to match your internal ID to the newly
  created TTD id
#### `config.json`
In addition to the standard fields, you can add 
```
{
   "do_not_fail": True
}
```
to the config.json. This enables the writer to continue when a clone request fails. Logs the error response into the `response` column and finishes successfully. This is useful if you get 400/500 error in the middle of processing of the csv to save the already created reference ids (otherwise you would have to fish them out of the logs manually). The option defaults to `False` if omitted


### output 
`out/tables/clone_campaigns.csv`
```csv
my_id,payload,response
foobar,{json_payload},response_json}
```
where 
- `my_id` is copied over from input csv (along with all the extra columns)
- `reference_id` is returned from from the api

##  Put adgroup
PUT https://api.thetradedesk.com/v3/adgroup

### input
`in/tables/put_adgroups.csv`
```csv
payload[,my_id,any_optional,columns]
{foo: bar}[,foobar,copied,from_input]
```
payload will be used as-is as the payload for the PUT request
### output
`out/tables/put_adgroups.csv`
```csv
response[,my_id,any_optional,columns]
{json returned_from_api},foobar,copied_from_input
```

where
- `response` is what is returned from the api
- `my_id,any_optional_columns` is carried over from the input csv


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
|   0.0.4 | Disable csv logging                                 |
|   0.0.3 | uses jsontangle to convert flattened csvs into jsons |
