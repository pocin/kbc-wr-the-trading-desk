"""
Models for csv-json serialization and partial validation

use jsonschema to validate data against the model schema
"""
import json
import csv
from functools import reduce
from operator import itemgetter
from itertools import groupby
import voluptuous as vp
from collections import defaultdict
import jsontangle
import logging
from tdd.exceptions import TDDConfigError


def csv_to_json(io, id_column, include_id_column=True):
    """Convert input csv into [possibly] nested json

    No type checking or validation is done!

    the rules are:
    nesting separator is by __ (aka "the dunder")
    foo__bar,baz  --> {"foo": {"bar": "baz"}}

    Arguments:
        io: either /path/to/input.csv or filelike object
        id_column (optional): column upon which the group by will be performed.
    """
    logging.info("Parsing %s", io)
    if id_column is None:
        raise TDDConfigError("Must specify an id_column on which to perform group by")
    else:
        pk = itemgetter(id_column)
    with open(io, 'r') as fin:
        reader = csv.DictReader(fin)
        REQUIRED_COLUMNS = ['path', id_column, 'value']
        for col in REQUIRED_COLUMNS:
            if col not in reader.fieldnames:
                raise TDDConfigError("the file '{}' must include column '{}'".format(io, col))
        rows = sorted(reader, key=pk)
        for pk, values in groupby(rows, pk):
            if include_id_column:
                cleaned_values = ({id_column: row[id_column],
                                   row['path']: row['value']}
                                  for row
                                  in values)
            else:
                cleaned_values = ({row['path']: row['value']}
                                  for row
                                  in values)
            yield jsontangle.tangle(cleaned_values)


def validate_json(obj, schema):
    """validate and coerce given json object according to given voluptuous.Schema

    Raises voluptuous.Invalid on error
    Args:
        obj (a python representation of JSON structure)
        schema (voluptuous.Schema)
    """
    return schema(obj)


def validate_input_csv(path_csv, schema, id_column, include_id_column=False):
    """Serialize csv to json, coerce dtypes and validate everything is ok

    after the first pass is ok, we can actually use the output to
    make requests
    Args:
        path_csv(str): path/to/input/csv
        primary_key(str): name of the primary key column to group by
        schema: instance of (voluptuous.Schema) to which the data in the
            input csv must conform

    Returns:
        a generator yielding json objects (serialized from input csv)
            validated and coerced according to the schema
    """
    json_lines = csv_to_json(path_csv, id_column=id_column)
    for line in json_lines:
        yield schema(line)


reusable_dtypes = {
    "_money": {
        "Amount": vp.Coerce(float),
        "CurrencyCode": "USD"
    }
}

def _CampaignReportingColumns(jsonstr):
    schema = vp.Schema(
            {
                "TrackingTagId": vp.Coerce(int),
                "ReportingColumnId": vp.Coerce(int)
            },
        extra=True,
        required=True)
    return schema(json.loads(jsonstr))

# "description": "2018-04-10T11:37:46.4780952+00:00",
CreateCampaignSchema = vp.Schema(
    {
        "CampaignID": str,
        "AdvertiserId": vp.Coerce(int),
        "CampaignName": str,
        "Description": str,
        "Budget": reusable_dtypes['_money'],
        "DailyBudget": reusable_dtypes['_money'],
        "StartDate": str, # Coerce to datetimes
        "EndDate": str, # Coerce to datetimes
        vp.Optional("CampaignConversionReportingColumns"): vp.Any([], [_CampaignReportingColumns])
    },
    extra=True,
    required=True)

CreateAdGroupSchema = vp.Schema(
    {
        "CampaignID": str,
        "AdGroupName": str,
        "Description": str,
        "IsEnabled": vp.Coerce(bool),
        "IndustryCategoryID": vp.Coerce(int),
        "RTBAttributes": {
            "BudgetSettings": vp.Schema({
                "Budget": reusable_dtypes['_money'],
                "DailyBudget": reusable_dtypes['_money'],
                "PacingEnabled": vp.Coerce(bool)}),
            "BaseBidCPM": reusable_dtypes['_money'],
            "MaxBidCPM": reusable_dtypes['_money'],
            vp.Optional("CreativeIds"): vp.Any([], [vp.Coerce(int)]),
            "AudienceTargeting": {"AudienceId": vp.Coerce(int)},
            "ROIGoal": {
                "CPAInAdvertiserCurrency": reusable_dtypes['_money']
            },
            "AutoOptimizationSettings": {
                "IsBaseBidAutoOptimizationEnabled": vp.Coerce(bool),
                "IsAudienceAutoOptimizationEnabled": vp.Coerce(bool),
                "IsSiteAutoOptimizationEnabled": vp.Coerce(bool),
                "IsCreativeAutoOptimizationEnabled": vp.Coerce(bool),
                "IsSupplyVendorAutoOptimizationEnabled": vp.Coerce(bool),
                "IsUseClicksAsConversionsEnabled": vp.Coerce(bool),
                "IsUseSecondaryConversionsEnabled": vp.Coerce(bool)
            }
        }
    },
    extra=vp.ALLOW_EXTRA,
    required=True)

def prepare_create_adgroup_data(path_csv):

    # Pass the dataset once (so we don't have to store it in memory)
    for _ in validate_input_csv(
            path_csv,
            schema=CreateAdGroupSchema,
            id_column='CampaignID',
            include_id_column=True):
        pass

    # If the previous step was ok, then we can actually start serving the values
    # maybe I can convert the input csv to list straight away??? TODO: benchmark
    yield from validate_input_csv(
        path_csv,
        schema=CreateAdGroupSchema,
        id_column='CampaignID',
        include_id_column=True)

def prepare_create_campaign_data(path_csv):

    # Pass the dataset once (so we don't have to store it in memory)
    for _ in validate_input_csv(
            path_csv,
            schema=CreateCampaignSchema,
            id_column="CampaignID",
            include_id_column=True):
        pass

    # If the previous step was ok, then we can actually start serving the values
    # maybe I can convert the input csv to list straight away??? TODO: benchmark
    yield from validate_input_csv(
        path_csv,
        schema=CreateCampaignSchema,
        id_column="CampaignID",
        include_id_column=True)
