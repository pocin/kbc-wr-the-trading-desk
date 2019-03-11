"""
KBC Related stuff

"""
import csv
import itertools
import json
import logging
import os
import sys
from functools import partial
from pathlib import Path
from typing import Dict, Tuple, List
import voluptuous as vp

import ttdwr
from ttdapi.client import TTDClient
from ttdapi.exceptions import TTDApiError

logger = logging.getLogger(__name__)

FNAME_ADGROUPS = 'create_adgroups.csv'
FNAME_CAMPAIGNS = 'create_campaigns.csv'
FNAME_UPDATE_ADGROUPS = 'update_adgroups.csv'
FNAME_UPDATE_CAMPAIGNS = 'update_campaigns.csv'
FNAME_CLONE_CAMPAIGNS = 'clone_campaigns.csv'
FNAME_PUT_ADGROUPS = 'put_adgroups.csv'

def main(params, datadir):
    _datadir = Path(datadir)
    intables = _datadir / 'in/tables'
    if params.get('debug'):
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    client = TTDClient(
        login=params['login'],
        password=params['#password'],
        base_url=params.get("base_url", "https://api.thetradedesk.com/v3/")
    )

    final_action = decide_action(_datadir, params)
    with client:
        final_action(client=client)


def validate_config(params):
    schema = vp.Schema({
        "login": str,
        "#password": str,
        vp.Optional("debug"): bool,
        "base_url": str,
        vp.Optional("do_not_fail"): bool
    })
    return schema(params)


def decide_action(datadir: Path, params: dict):
    datadir = Path(datadir)
    intables = datadir / 'in/tables'
    outtables = datadir / 'out/tables'
    tables = set(os.listdir(str(intables)))
    if FNAME_ADGROUPS in tables and FNAME_CAMPAIGNS in tables:
        logger.info("Found both '%s' and '%s'. "
                    "Will create campaigns and their adgroups afterwards",
                    FNAME_ADGROUPS,
                    FNAME_CAMPAIGNS)
        return partial(
            create_campaigns_and_adgroups,
            path_csv_campaigns=intables / FNAME_CAMPAIGNS,
            path_csv_adgroups=intables / FNAME_ADGROUPS)

    elif FNAME_ADGROUPS in tables:
        logger.info("Found only '%s' Will create only adgroups",
                    FNAME_ADGROUPS)
        return partial(create_adgroups,
                       path_to_csv=intables / FNAME_ADGROUPS)

    elif FNAME_CAMPAIGNS in tables:
        logger.info("Found only '%s' Will create only campaigns",
                    FNAME_CAMPAIGNS)
        return partial(create_campaigns,
                       path_to_csv=intables / FNAME_CAMPAIGNS)

    elif FNAME_CLONE_CAMPAIGNS in tables:
        logger.info("Found %s, cloning campaigns", FNAME_CLONE_CAMPAIGNS)
        return partial(clone_campaigns,
                       path_to_csv=intables / FNAME_CLONE_CAMPAIGNS,
                       outdir=outtables,
                       do_not_fail=params.get('do_not_fail', False))
    elif FNAME_PUT_ADGROUPS in tables:
        logger.info("Found %s, putting adgroups", FNAME_PUT_ADGROUPS)
        return partial(put_adgroups,
                       path_to_csv=intables / FNAME_PUT_ADGROUPS,
                       outdir=outtables)
    else:
        raise ttdwr.exceptions.TTDInternalError(
            "Don't know what action to perform. Found tables '{}'".format(
                tables))

def load_csv_data(path_to_csv):
    with open(path_to_csv) as f:
        rdr = csv.DictReader(f)
        yield from rdr

def create_adgroups(client, path_to_csv):
    for adgrp in load_csv_data(path_to_csv):
        payload = json.loads(adgrp['payload'])
        logger.info("Creating adgroup %s", payload['AdGroupName'])
        try:
            new_adgrp = client.create_adgroup(payload)
        except:
            logger.info("payload was\n:%s", json.dumps(payload))
            raise
        logger.info("Success: Created '%s' as AdGroupId= '%s'",
                    payload['AdGroupName'], new_adgrp['AdGroupId'])

def create_campaigns(client, path_to_csv):
    for campaign in load_csv_data(path_to_csv):
        payload = json.loads(campaign['payload'])
        logger.info("Creating Campaign %s", payload['CampaignName'])
        try:
            new_campaign = client.create_campaign(payload)
        except:
            logger.info("payload was\n:%s", json.dumps(payload))
            raise
        logger.info("Success: Created '%s' as AdGroupId= '%s'",
                    payload['CampaignName'], new_campaign['CampaignId'])


def stream_to_csv(outpath, stream, columns=None):
    with open(outpath, 'w') as outf:
        wr = csv.DictWriter(outf, fieldnames=columns)
        wr.writerows(stream)
    return outpath

def _peek_at_header(path_csv):
    with open(path_csv) as f:
        return csv.DictReader(f).fieldnames


def clone_campaigns(client, path_to_csv, outdir, do_not_fail=False):
    outpath = Path(outdir) / 'clone_campaigns.csv'
    header = _peek_at_header(path_to_csv)

    with open(outpath, 'w') as outf:
        wr = csv.DictWriter(outf, fieldnames=header + ['response'])
        wr.writeheader()
        for campaign in load_csv_data(path_to_csv):
            # a helper variable to prettify logging output
            _log_row = {
                k: v
                for k, v
                in campaign.items()
                if k != 'payload'
            }
            try:
                resp = client.post('/campaign/clone',
                                   json=json.loads(campaign['payload']))
            except TTDApiError as err:
                # A failover mechanism that enables the extractor
                # to finish (and output csvs with previously created )
                if do_not_fail:
                    logger.info(
                        ("row %s returned error '%s'. Logging and continuing,"
                         " since do_not_fail=True"),
                        _log_row,
                        err
                    )
                    resp = err.response.json()
                else:
                    raise
            else:
                logger.info(
                    "row %s created with reference_id %s",
                    {
                        k: v
                        for k, v
                        in campaign.items()
                        if k != 'payload'
                    },
                    resp['ReferenceId']
                        )
            campaign['response'] = json.dumps(resp)
            wr.writerow(campaign)
    return outpath


def put_adgroups(client, path_to_csv, outdir):
    outpath = outdir / 'put_adgroups.csv'
    header = _peek_at_header(path_to_csv)
    with open(outpath, 'w') as outf:
        wr = csv.DictWriter(outf, fieldnames=header + ['response'])
        wr.writeheader()

        for adgroup in load_csv_data(path_to_csv):
            resp = client.put(
                '/adgroup',
                json=json.loads(adgroup['payload']))
            adgroup['response'] = json.dumps(resp)
            wr.writerow(adgroup)
    return outpath


def group_adgroups_to_campaigns(iterable_of_adgroups):
    """convert an iterable of {"campaign_id": .., "payload": ...} into
    {"<capaign_id": [list of payloads]}

    """
    grouped = itertools.groupby(
        sorted(iterable_of_adgroups,
               key=lambda grp: grp["dummy_campaign_id"]),
        lambda grp: grp["dummy_campaign_id"])
    mapping = {}
    for key, values in grouped:
        mapping[key] = [value
                        for value
                        in values]
    return mapping


def create_campaigns_and_adgroups(
        client,
        path_csv_campaigns,
        path_csv_adgroups)-> Tuple[dict, List[dict]]:
    campaigns = load_csv_data(path_csv_campaigns)
    # for now load into memory, there shouldn't be too many of them
    adgroups = group_adgroups_to_campaigns(load_csv_data(path_csv_adgroups))
    created_adgroups = []
    for campaign in campaigns:
        campaign_payload = json.loads(campaign['payload'])
        placeholder_campaign_id = campaign['dummy_campaign_id']
        logger.info("Creating campaign '%s'", campaign_payload['CampaignName'])
        new_campaign = client.create_campaign(campaign_payload)
        real_campaign_id = new_campaign['CampaignId']
        logger.info("Success. The CampaignId is '%s'", real_campaign_id)
        related_adgroups = adgroups[placeholder_campaign_id]
        for adgroup in related_adgroups:
            adgroup_payload = json.loads(adgroup['payload'])
            adgroup_payload['CampaignId'] = real_campaign_id
            logger.info("Creating Adgroup '%s' for campaign %s",
                        adgroup_payload['AdGroupName'],
                        real_campaign_id)
            try:
                new_adgroup = client.create_adgroup(adgroup_payload)
            except:
                logger.info("Error, Payload was\n%s", json.dumps(adgroup_payload))
                raise
            logger.info("Success: '%s' has ttd adgroup id '%s'", adgroup_payload['AdGroupName'], new_adgroup['AdGroupId'])
            created_adgroups.append(new_adgroup)
    return new_campaign, created_adgroups
