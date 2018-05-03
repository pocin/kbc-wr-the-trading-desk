"""
KBC Related stuff

"""
import logging
import sys
from pathlib import Path
from tdd.client import KBCTDDClient
import tdd.models
from keboola.docker import Config

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

    path_campaigns = intables / 'create_campaigns.csv'
    if path_campaigns.is_file():
        logging.info("Preparing campaign data %s", path_campaigns)
        campaign_data = tdd.models._prepare_create_campaign_data(path_campaigns)
        tdd.models._campaign_data_into_db(campaign_data, db_conn)

    path_adgroup = intables / 'create_adgroups.csv'
    logging.debug("looking for tables in %s", intables)
    if path_adgroup.is_file():
        logging.info("Preparing adgroup data %s", path_adgroup)
        adgroup_data = tdd.models._prepare_create_adgroup_data(path_adgroup)
        tdd.models._adgroup_data_into_db(adgroup_data, db_conn)

    return db_conn
