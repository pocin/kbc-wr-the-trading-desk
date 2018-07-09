"""
KBC Related stuff

"""
import json
import logging
import sys
from pathlib import Path
import os
from ttdwr.client import KBCTTDClient
import ttdwr.models
from keboola.docker import Config
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
        "action": vp.Any("sandbox", "production", "verify_inputs")
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

    db = prepare_data(intables)
    final_action = decide_action(intables)
    action = params['action']
    if action == 'verify_inputs':
        logger.info("exitting, action == 'verify_inputs' ")
        return
    elif action == 'sandbox':
        client.base_url = 'https://apisb.thetradedesk.com/v3'
    elif action == 'production':
        client.base_url = 'https://api.thetradedesk.com/v3'
    with client:
        final_action(client, db)

def decide_action(intables):
    tables = set(os.listdir(str(intables)))
    if FNAME_ADGROUPS in tables and FNAME_CAMPAIGNS in tables:
        logger.info("Found both '%s' and '%s'. "
                     "Will create campaigns and their adgroups afterwards",
                     FNAME_ADGROUPS,
                     FNAME_CAMPAIGNS)
        return create_campaigns_and_adgroups

    elif FNAME_ADGROUPS in tables:
        logger.info("Found only '%s' Will create only adgroups",
                     FNAME_ADGROUPS)
        return create_adgroups

    elif FNAME_CAMPAIGNS in tables:
        logger.info("Found only '%s' Will create only campaigns",
                     FNAME_CAMPAIGNS)
        return create_campaigns
    else:
        raise ttdwr.exceptions.TTDInternalError(
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
    logger.info("Preparing input data")
    db_conn = ttdwr.models._init_database(path=db_path)

    path_campaigns = intables / FNAME_CAMPAIGNS
    if path_campaigns.is_file():
        logger.info("Preparing creation of campaign data %s", path_campaigns)
        campaign_data = ttdwr.models._prepare_create_campaign_data(path_campaigns)
        ttdwr.models._campaign_data_into_db(campaign_data, db_conn)

    path_adgroup = intables / FNAME_ADGROUPS
    if path_adgroup.is_file():
        logger.info("Preparing creation of adgroup data %s", path_adgroup)
        adgroup_data = ttdwr.models._prepare_create_adgroup_data(path_adgroup)
        ttdwr.models._adgroup_data_into_db(adgroup_data, db_conn)

    path_update_campaigns = intables/ FNAME_UPDATE_CAMPAIGNS
    if path_update_campaigns.is_file():
        if path_campaigns.is_file():
            raise ttdwr.exceptions.TTDConfigError(
                "Cant create and update campaigns within same writer config."
                " Split it into two!")
        logger.info("Preparing data for updating campaigns %s", path_update_campaigns)
        update_campaign_data = ttdwr.models._prepare_update_campaign_data(path_update_campaigns)
        ttdwr.models._campaign_data_into_db(update_campaign_data, db_conn)

    path_update_adgroups = intables/ FNAME_UPDATE_ADGROUPS
    if path_update_adgroups.is_file():
        if path_adgroup.is_file():
            raise ttdwr.exceptions.TTDConfigError(
                "Cant create and update adgroups within same writer config. "
                "Split it into two!")
        logger.info("Preparing data for updating adgroups %s", path_update_adgroups)
        update_campaign_data = ttdwr.models._prepare_update_adgroup_data(path_update_adgroups)
        ttdwr.models._adgroup_data_into_db(update_campaign_data, db_conn)
    return db_conn

def create_adgroups(client, db):
    adgroups = ttdwr.models.query_adgroups(db, campaign_id=None)
    for adgrp in adgroups:
        payload = json.loads(adgrp['payload'])
        payload['CampaignId'] = adgrp['campaign_id']
        client.create_adgroup(payload)

def create_campaigns(client, db):
    campaigns = ttdwr.models.query_campaigns(db)
    for campaign in campaigns:
        payload = json.loads(campaign['payload'])
        client.create_campaign(payload)

def create_campaigns_and_adgroups(client, db):
    campaigns = ttdwr.models.query_campaigns(db)
    for campaign in campaigns:
        campaign_payload = json.loads(campaign['payload'])
        placeholder_campaign_id = campaign['campaign_id']
        new_campaign = client.create_campaign(campaign_payload)
        real_campaign_id = new_campaign['CampaignId']
        related_adgroups = ttdwr.models.query_adgroups(
            db,
            campaign_id=placeholder_campaign_id)
        for adgroup in related_adgroups:
            adgroup_payload = json.loads(adgroup['payload'])
            adgroup_payload['CampaignId'] = real_campaign_id
            client.create_adgroup(adgroup_payload)
