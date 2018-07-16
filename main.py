from ttdwr.writer import main, validate_config
import sys
import requests
import logging
import os
from keboola.docker import Config

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        datadir = os.getenv("KBC_DATADIR")
        cfg = Config(datadir)
        params = validate_config(cfg.get_parameters())
        main(params, datadir)
    except (ValueError, KeyError, requests.HTTPError) as err:
        logging.error(err)
    except:
        logging.exception("Internal error")
