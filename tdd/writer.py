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

    writer = TDDWriter(login=params['login'],
                       password=params['#password'],
                       path_csv_log=path_csv_log)

    path_campaigns = intables / 'create_campaigns.csv'
    # TODO: maybe we actually need to load it into memory
    # to match campaigns and adgroups based on common ID (hash)?
    campaign_data = tdd.models._prepare_create_campaign_data(path_campaigns)

    path_adgroup = intables / 'crate_adgroup.csv'
    # at this point the adgroup code doesn't contain the campaign id
    # (which is unknown, yet)
    logging.info("Validating AdGroup input @ %s", path_adgroup)
    for _ in writer.validate_adgroup_input(path_adgroup):
        pass
    logging.info("AdGroup input seems to be OK")

    # TODO: how to actually link campaign to adgroup[s] (is this 1:N?)
    # in original tables?

class TDDWriter(KBCTDDClient):
    """
    Implements
    - config file processing logic
    - partial input validation
    """

    def create_campaign(self):
        # TODO: ignore campaign ID if present
        raise NotImplementedError()

    def create_adgroup(self):
        raise NotImplementedError()
    def create_campaign_and_adgroup(self, campaign_payload, adgroup_payload):
        """
        This expects that adgroup_payload is actually valid

        """
        new_campaign = self.create_campaign(campaign_payload)
        adgroup_payload['CampaignID'] = new_campaign['CampaignID']
        self.create_adgroup(adgroup_payload)
