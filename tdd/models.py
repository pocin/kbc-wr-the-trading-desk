"""
Models for csv-json serialization and partial validation

use voluptuous to validate data against the model schema

While parsing the csvs, the validated jsons are dumped into local sqlite
database.
If an error is thrown in the process, we know there was a mistake. If it
passess sucesfully, then the data should be ok and we can proceed with making
API requests.


The temp database contains tables

campaigns
 - campaign_id
 - payload

adgroups
 - campaign_id
 - adgroup_id
 - payload

In both cases, the payload should be processed with json.loads()
- the payload is validated and coerced against the schema
- doesn't contain any Id's the ids were factored out (into *_id columns)
  of the payload in the previous step
"""
import json
import csv
from functools import reduce
from operator import itemgetter
from itertools import groupby
import sqlite3
import os
import voluptuous as vp
from collections import defaultdict
import jsontangle
import logging
from tdd.exceptions import TTDConfigError

logger = logging.getLogger(__name__)

def _column_to_row_format(values, id_columns=None):
    """
    After groupby we get a
    [
    {'path': "foo__bar", "value": 42, 'id': 1},
    ...
    ]
    which we need to convert into
    [{'foo__bar': 42}, ...]

    or
    [{'foo__bar': 42, 'id': 1}, ...]
    if id_columns is not None
    """
    for row in values:
        # {'path': "foo__bar", "value": 42, 'id': 1},
        formatted_group = {row['path']: row['value']}
        if id_columns:
            for col in id_columns:
                formatted_group[col] = row[col]
        yield formatted_group


def csv_to_json(io, id_column, include_id_column=True):
    """Convert input csv into [possibly] nested json

    No type checking or validation is done!

    the rules are:
    nesting separator is by __ (aka "the dunder")
    foo__bar,baz  --> {"foo": {"bar": "baz"}}

    Arguments:
        io: either /path/to/input.csv or filelike object
        id_column (list): a list of column[s] upon which the group by will be performed.
    """

    logger.info("Parsing %s", io)
    if not isinstance(id_column, list):
        raise TTDConfigError("Must specify a list of id_column on which to perform group by")
    else:
        pk = itemgetter(*id_column)
    with open(io, 'r') as fin:
        reader = csv.DictReader(fin)
        REQUIRED_COLUMNS = ['path', 'value'] + id_column
        for col in REQUIRED_COLUMNS:
            if col not in reader.fieldnames:
                raise TTDConfigError("the file '{}' must include column '{}'".format(io, col))
        rows = sorted(reader, key=pk)
        for pk, values in groupby(rows, pk):
            cleaned_values = _column_to_row_format(values, id_column if include_id_column else None)
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
        "CampaignId": str,
        "AdvertiserId": vp.Coerce(int),
        "CampaignName": str,
        "Description": str,
        "Budget": reusable_dtypes['_money'],
        "DailyBudget": reusable_dtypes['_money'],
        "StartDate": str, # Coerce to datetimes
        "EndDate": str, # Coerce to datetimes
        "CampaignConversionReportingColumns": vp.Any([], [_CampaignReportingColumns])
    },
    extra=True,
    required=True)

CreateAdGroupSchema = vp.Schema(
    {
        "CampaignId": str,
        "AdGroupName": str,
        "Description": str,
        "IsEnabled": vp.Coerce(bool),
        "IndustryCategoryId": vp.Coerce(int),
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

def _prepare_create_adgroup_data(path_csv):
    """ parse input campaign csv and return cleaned rows

    we can be sure all data is ok only after the whole generator is consumed!!!

    the returned generator yields dict which can be sent to the api:
        {'CampaignId': 42, "RTBAttributes": {"BudgetSettings": ...}, }
    """
    # we can be sure all data is ok only after the whole generator is consumed!!!
    yield from validate_input_csv(
            path_csv,
            schema=CreateAdGroupSchema,
            id_column=['CampaignId', 'AdgroupId'],
            include_id_column=True)




def _prepare_create_campaign_data(path_csv):
    """ parse input campaign csv and return cleaned rows

    we can be sure all data is ok only after the whole generator is consumed!!!
    """
    yield from validate_input_csv(
        path_csv,
        schema=CreateCampaignSchema,
        id_column=["CampaignId"],
        include_id_column=True)



def _init_database(path='/tmp/tddwriter_data.sqlite3', overwrite=True):
    logger.debug("Creating database for storing parsed data")
    if overwrite:
        try:
            os.remove(path)
        except OSError:
            logger.debug("%s exists, overwriting!", path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    conn.commit()
    return conn

def _create_tables(conn):
    create_campaigns = """
    CREATE TABLE "campaigns" (
    campaign_id CHAR(255) PRIMARY KEY NOT NULL,
    payload TEXT NOT NULL
    );
    """
    create_adgroups = """
    CREATE TABLE "adgroups" (
        campaign_id TEXT NOT NULL,
        adgroup_id TEXT NOT NULL,
        payload TEXT NOT NULL,
        PRIMARY KEY (campaign_id, adgroup_id));
    """

    with conn:
        conn.execute(create_campaigns)
        conn.execute(create_adgroups)


def insert_campaign(cursor, campaign_id, payload):
    query = "INSERT INTO campaigns(campaign_id, payload) VALUES (?,?);"
    return cursor.execute(query, (campaign_id, json.dumps(payload)))

def insert_adgroup(cursor, campaign_id, adgroup_id, payload):
    query = "INSERT INTO adgroups(campaign_id, adgroup_id, payload) VALUES (?, ?, ?);"
    return cursor.execute(query, (campaign_id, adgroup_id, json.dumps(payload)))


def _campaign_data_into_db(campaign_data, conn):
    """
    Args:
        campaign_data: an iterable of dicts reperesenting the serialized
            payloads which can be sent to the API.
            Created by _prepare_create_campaign_data()
        conn: a connection to the database


    """
    logger.debug("Inserting campaign data into tmp database")
    cursor = conn.cursor()
    for row in campaign_data:
        cid = row.pop('CampaignId')
        insert_campaign(cursor,
                        campaign_id=cid,
                        payload=row)

    conn.commit()

def _adgroup_data_into_db(adgroup_data, conn):
    """ insert adgroups into database
    Args:
        adgroup_data: an iterable of dicts reperesenting the serialized
            payloads which can be sent to the API.
            Created by _prepare_create_adgroup_data()
        conn: a connection to the database

    """
    logger.debug("Inserting adgroup data into tmp database")
    cursor = conn.cursor()
    for row in adgroup_data:
        cid = row.pop('CampaignId')
        adid = row.pop('AdgroupId')
        insert_adgroup(cursor,
                       campaign_id=cid,
                       adgroup_id=adid,
                       payload=row)
    conn.commit()

def query_campaigns(conn):
    q = """SELECT * FROM campaigns;"""

    cursor = conn.cursor()
    for row in cursor.execute(q):
        yield row


def query_adgroups(conn, campaign_id=None):
    if campaign_id is not None:
        q = """SELECT * FROM adgroups WHERE campaign_id=?;"""
        cursor = conn.cursor()
        for row in cursor.execute(q, (campaign_id, )):
            yield row
    else:
        q = """SELECT * FROM adgroups;"""
        cursor = conn.cursor()
        for row in cursor.execute(q):
            yield row
