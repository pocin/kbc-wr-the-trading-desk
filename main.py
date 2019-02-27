from ttdwr.writer import main, validate_config
from ttdapi.exceptions import TTDApiError, TTDApiPermissionsError, TTDClientError
import sys
import requests
import logging
import os
from keboola.docker import Config

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        datadir = os.getenv("KBC_DATADIR") or '/data/'
        cfg = Config(datadir)
        params = validate_config(cfg.get_parameters())
        main(params, datadir)
    except (ValueError, KeyError, requests.HTTPError, TTDApiError, TTDApiPermissionsError) as err:
        logging.exception("Something went wrong:")
        sys.exit(1)
    except:
        logging.exception("Internal error")
        sys.exit(2)
