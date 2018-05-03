"""
KBC Related stuff

"""
import json
import logging
import sys
from pathlib import Path
import os
from tdd.client import KBCTDDClient
import tdd.models
from keboola.docker import Config
from enum import Enum

Action = Enum("Action", "campaigns adgroups campaigns_and_adgroups")

ACTIONS = {
}

FNAME_ADGROUPS = 'create_adgroups.csv'
FNAME_CAMPAIGNS = 'create_campaigns.csv'

def main():
    logging.info("Hello, world!")



def _main(datadir):
    cfg = Config(datadir)
    params = cfg.get_parameters()
    _datadir = Path(datadir)
    intables = _datadir / 'in/tables'
    if params.get('debug'):
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    path_csv_log = _datadir / 'out/tables/tdd_writer_log.csv'

    client = KBCTDDClient(login=params['login'],
                          password=params['#password'],
                          path_csv_log=path_csv_log)

    db = prepare_data(intables)
    final_action = decide_action(intables)
    with client:
        final_action(client, db)

def decide_action(intables):
    tables = set(os.listdir(str(intables)))
    if FNAME_ADGROUPS in tables and FNAME_CAMPAIGNS in tables:
        logging.info("Bound both '%s' and '%s'. "
                     "Will create campaigns and their adgroups afterwards",
                     FNAME_ADGROUPS,
                     FNAME_CAMPAIGNS)
        return create_campaigns_and_adgroups

    elif FNAME_ADGROUPS in tables:
        logging.info("Found only '%s' Will create only adgroups",
                     FNAME_ADGROUPS)
        return create_adgroups

    elif FNAME_CAMPAIGNS in tables:
        logging.info("Found only '%s' Will create only campaigns",
                     FNAME_CAMPAIGNS)
        return create_campaigns
    else:
        raise tdd.exceptions.TDDInternalError(
            "Don't know what action to perform. Found tables '%s'".format(
                tables))



def prepare_data(intables, db_path='/tmp/tdd_writer_database.sqlite3'):
    """
    Load csvs
    Serialize to json
    Validate
    Prepare database
    Load into db

    return connection to database

    once this function is finished we can be certain that the data is correct (to the extent covered by the defined schemas)

    """
    logging.info("Preparing input data")
    db_conn = tdd.models._init_database(path=db_path)

    path_campaigns = intables / FNAME_CAMPAIGNS
    if path_campaigns.is_file():
        logging.info("Preparing campaign data %s", path_campaigns)
        campaign_data = tdd.models._prepare_create_campaign_data(path_campaigns)
        tdd.models._campaign_data_into_db(campaign_data, db_conn)

    path_adgroup = intables / FNAME_ADGROUPS
    if path_adgroup.is_file():
        logging.info("Preparing adgroup data %s", path_adgroup)
        adgroup_data = tdd.models._prepare_create_adgroup_data(path_adgroup)
        tdd.models._adgroup_data_into_db(adgroup_data, db_conn)

    return db_conn

def create_adgroups(client, db):
    adgroups = tdd.models.query_adgroups(db, campaign_id=None)
    for adgrp in adgroups:
        payload = json.loads(adgrp['payload'])
        payload['CampaignId'] = adgrp['campaign_id']
        client.create_adgroup(payload)

def create_campaigns(client, db):
    campaigns = tdd.models.query_campaigns(db)
    for campaign in campaigns:
        payload = json.loads(campaign['payload'])
        client.create_campaign(payload)

def create_campaigns_and_adgroups(client, db):
    campaigns = tdd.models.query_campaigns(db)
    for campaign in campaigns:
        campaign_payload = json.loads(campaign['payload'])
        campaign_id = campaign['campaign_id']
        client.create_campaign(campaign_payload)
        related_adgroups = tdd.models.query_adgroups(
            db,
            campaign_id=campaign_id)
        for adgroup in related_adgroups:
            adgroup_payload = json.loads(adgroup['payload'])
            adgroup_payload['CampaignId'] = campaign_id
