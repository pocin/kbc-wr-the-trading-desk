"""
KBC Related stuff

"""
import json
from functools import partial
import logging
import sys
import csv
from pathlib import Path
import os
from ttdwr.client import KBCTTDClient
from keboola.docker import Config
import itertools
import voluptuous as vp

logger = logging.getLogger(__name__)

FNAME_ADGROUPS = 'create_adgroups.csv'
FNAME_CAMPAIGNS = 'create_campaigns.csv'
FNAME_UPDATE_ADGROUPS = 'update_adgroups.csv'
FNAME_UPDATE_CAMPAIGNS = 'update_campaigns.csv'

def main():
    logger.info("Hello, world!")


def validate_config(params):
    schema = vp.Schema({
        "login": str,
        "#password": str,
        vp.Optional("debug"): bool,
        "base_url": str,
    })
    return schema(params)


def _main(datadir):
    cfg = Config(datadir)
    params = validate_config(cfg.get_parameters())
    _datadir = Path(datadir)
    intables = _datadir / 'in/tables'
    if params.get('debug'):
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    path_csv_log = _datadir / 'out/tables/tdd_writer_log.csv'

    client = KBCTTDClient(login=params['login'],
                          password=params['#password'],
                          path_csv_log=path_csv_log)

    final_action = decide_action(intables)
    with client:
        final_action(client=client)

def decide_action(intables):
    tables = set(os.listdir(str(intables)))
    if FNAME_ADGROUPS in tables and FNAME_CAMPAIGNS in tables:
        logger.info("Found both '%s' and '%s'. "
                     "Will create campaigns and their adgroups afterwards",
                     FNAME_ADGROUPS,
                     FNAME_CAMPAIGNS)
        return partial(
            create_campaigns_and_adgroups,
            path_csv_campaigns=FNAME_CAMPAIGNS,
            path_csv_adgroups=FNAME_ADGROUPS)

    elif FNAME_ADGROUPS in tables:
        logger.info("Found only '%s' Will create only adgroups",
                     FNAME_ADGROUPS)
        return partial(create_adgroups, path_to_csv=FNAME_ADGROUPS)

    elif FNAME_CAMPAIGNS in tables:
        logger.info("Found only '%s' Will create only campaigns",
                     FNAME_CAMPAIGNS)
        return partial(create_campaigns, path_to_csv=FNAME_CAMPAIGNS)
    else:
        raise ttdwr.exceptions.TTDInternalError(
            "Don't know what action to perform. Found tables '%s'".format(
                tables))



def load_csv_data(path_to_csv):
    with open(path_to_csv) as f:
        rdr = csv.DictReader(f)
        yield from rdr

def create_adgroups(client, path_to_csv):
    for adgrp in load_csv_data(path_to_csv):
        payload = json.loads(adgrp['payload'])
        client.create_adgroup(payload)

def create_campaigns(client, path_to_csv):
    for campaign in load_csv_data(path_to_csv):
        payload = json.loads(campaign['payload'])
        client.create_campaign(payload)

def group_adgroups_to_campaigns(iterable_of_adgroups):
    """convert an iterable of {"campaign_id": .., "payload": ...} into
    {"<capaign_id": [list of payloads]}

    """
    grouped = itertools.groupby(
        sorted(iterable_of_adgroups,
               key=lambda grp: grp["CampaignId"]),
        lambda grp: grp["CampaignId"])
    mapping = {}
    for key, values in grouped:
        mapping[key] = [value["payload"]
                        for value
                        in values]
    return mapping


def create_campaigns_and_adgroups(client, path_csv_campaigns, path_csv_adgroups):
    campaigns = load_csv_data(path_csv_campaigns)
    # for now load into memory, there shouldn't be too many of them
    adgroups = group_adgroups_to_campaigns(load_csv_data(path_csv_adgroups))
    for campaign in campaigns:
        campaign_payload = json.loads(campaign['payload'])
        placeholder_campaign_id = campaign['CampaignId']
        new_campaign = client.create_campaign(campaign_payload)
        real_campaign_id = new_campaign['CampaignId']
        related_adgroups = adgroups[placeholder_campaign_id]
        for adgroup in related_adgroups:
            adgroup_payload = json.loads(adgroup['payload'])
            adgroup_payload['CampaignId'] = real_campaign_id
            client.create_adgroup(adgroup_payload)
