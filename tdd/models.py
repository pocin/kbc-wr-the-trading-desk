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

class BaseModel(dict):

    _schema_path = None

    def __init__(self):
        super().__init__(self._from_file(self._schema_path))

    def _from_file(self, io):
        """update current schema from file

        Args:
            io either file-like object or (str) /path/to/schema.json
        """
        if not hasattr(io, 'read'):
            with open(io, 'r') as fin:
                data = json.load(fin)
        elif hasattr(io, 'read'):
            data = json.load(io)
        else:
            raise ValueError(
                "io Must be path/to/schema.json or filelike object")

        return data

    @property
    def schema_path(self):
        return type(self)._schema_path

    @schema_path.setter
    def schema_path(self, path):
        self._schema_path = path



reusable_dtypes = {
    "_money": {
        "type": "object",
        "properties": {
            "Amount": {
                "type": "number"
            },
            "CurrencyCode": {
                "type": "string",
                "enum": ["USD"]
            }
        }
    }
}

campaign_schema = {
    "$schema": "ttp://json-schema.org/schema#",
    "definitions": {
        "_money": reusable_dtypes['_money']
    },
    "required": ["Budget", "StartDate", "EndDate", "DailyBudget"],
    "type": "object",
    "properties": {
        "Budget": {
            "$ref": "#/definitions/_money"
        },
        "StartDate": {
            "format": "date-time",
            "description": "2018-04-10T11:37:46.4780952+00:00",
            "type": "string"
        },
        "EndDate": {
            "format": "date-time",
            "description": "2018-04-10T11:37:46.4780952+00:00",
            "type": "string"
        },
        "BudgetInImpressions": {
            "anyOf": [{
                "type": "number"
            }, {
                "type": "null"
            }]
        },
        "DailyBudgetInImpressions": {
            "anyOf": [{
                "type": "number"
            }, {
                "type": "null"
            }]
        },
        "DailyBudget": {
            "$ref": "#/definitions/_money"
        },
    },
}

create_adgroup = {
    "$schema": "ttp://json-schema.org/schema#",
    "type": "object",
    "required": ["CampaignID", "AdGroupName", "IndustryCategoryID"],
    "properties": {
        "CampaignID": {"type": "string"},
        "IndustryCategoryID": {"type": "number"},
        "RTBAdGroupAttributes": {
            "type": "object",
            "properties": {
                "BudgetSettings": {
                    "type": "object",
                    "properties": {
                        "Budget": reusable_dtypes['_money'],
                        "BudgetInImpressions": {"type": "number"},
                        "DailyBudget": reusable_dtypes['_money'],
                        "DailyBudgetInImpressions": {"type": "number"}}
                },
                "BaseBidCPM": {"type": "string"},
                "MaxBidCPM": {"type": "string"}
            }
        }
    }
}
