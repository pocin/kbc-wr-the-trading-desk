from tdd.writer import main
import requests
import logging

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO)
        main()
    except (ValueError, KeyError, requests.HTTPError) as err:
        logging.error(err)
    except:
        logging.exception("Internal error")
