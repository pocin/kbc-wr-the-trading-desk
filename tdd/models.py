"""
Models for csv-json serialization and partial validation

use jsonschema to validate data against the model schema
"""
import json
import csv
import voluptuous as vp
from collections import defaultdict


def csv_to_json(io):
    """Convert input csv into [possibly] nested json

    No type checking or validation is done!

    the rules are:
    nesting separator is by __ (aka "the dunder")
    foo__bar,baz  --> {"foo": {"bar": None}, "baz":None}

    Arguments:
        io: either /path/to/input.csv or filelike object
    """
    with open(io, 'r') as fin:
        reader = csv.DictReader(fin)
        for line in reader:
            nested_line = _nest_json(line)
            yield nested_line


def _nest_json(obj):
    """nesting json into 1 level
    {"foo__bar": 42} -> {"foo":{"bar":42}}
    but not (ATM)
    {"foo__bar_baz__qux": 42} -> {"foo":{"bar_baz":{"qux":42}}}

    """
    new = defaultdict(dict)
    for key, val in obj.items():
        if '__' in key:
            # do we want to go infinitely deep?
            lvl1, lvl2 = key.split('__', maxsplit=1)
            new[lvl1][lvl2] = val
        else:
            # just copy this, no nesting needed
            new[key] = val
    return new


def validate_json(obj, schema):
    """validate and coerce given json object according to given voluptuous.Schema

    Raises voluptuous.Invalid on error
    Args:
        obj (a python representation of JSON structure)
        schema (voluptuous.Schema)
    """
    return schema(obj)


def validate_input_csv(path_csv, schema):
    """Serialize csv to json, coerce dtypes and validate everything is ok

    after the first pass is ok, we can actually use the output to
    make requests
    Args:
        path_csv(str): path/to/input/csv
        schema: instance of (voluptuous.Schema) to which the data in the
            input csv must conform

    Returns: a generator yielding json objects (serialized from input csv)
    """
    json_lines = csv_to_json(path_csv)
    for line in json_lines:
        yield schema(line)


reusable_dtypes = {
    "_money": {
        "Amount": vp.Coerce(float),
        "CurrencyCode": "USD"
    }
}

# "description": "2018-04-10T11:37:46.4780952+00:00",
CreateCampaignSchema = vp.Schema(
    {
        "StartDate": str,
        "EndDate": str,
        "Budget": reusable_dtypes['_money'],
        "DailyBudget": reusable_dtypes['_money'],
        vp.Optional("BudgetInImpressions"): vp.Any(None, vp.Coerce(int)),
        vp.Optional("DailyBudgetInImpressions"): vp.Any(None, vp.Coerce(int))
    },
    extra=True,
    required=True)

CreateAdGroupSchema = vp.Schema(
    {
        "AdGroupName": str,
        vp.Optional("CampaignID"): str,
        "IndustryCategoryID": vp.Coerce(int),
        "IsEnabled": bool,
        "RTBAttributes": {
            "RTBAdGroupAttributes": vp.Schema(
                {
                    "BudgetSettings": vp.Schema(
                        {
                            "Budget": reusable_dtypes['_money'],
                            "BudgetInImpressions": vp.Coerce(int),
                            "DailyBudget": reusable_dtypes['_money'],
                            "DailyBudgetInImpressions": vp.Coerce(int)
                        },
                        extra=vp.ALLOW_EXTRA,
                        required=False),
                    "BaseBidCPM": reusable_dtypes['_money'],
                    "MaxBidCPM": reusable_dtypes['_money']
                })
        }
    },
    extra=vp.ALLOW_EXTRA,
    required=True)
