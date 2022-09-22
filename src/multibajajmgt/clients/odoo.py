import random
import json
import logging
import requests
import pandas as pd

from multibajajmgt.logger import configure_logging
from multibajajmgt.config import (
    SERVER_URL, SERVER_USERNAME, SERVER_API_KEY, DATABASE_NAME,
)

log = logging.getLogger(__name__)
user_id = None


def _json_rpc(url, method, params):
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "id": random.randint(0, 1000000000),
        "params": params,
    }
    try:
        response = requests.post(url = url,
                                 headers = {"Content-Type": "application/json"},
                                 data = json.dumps(data).encode())
        response.raise_for_status()
        response = response.json()
        if "error" in response:
            raise Exception(response["error"])
        return response["result"]
    except requests.exceptions.HTTPError as e:
        log.error("Invalid response: ", e)
    except requests.exceptions.RequestException as e:
        log.error("Something went wrong with the request: ", e)


def _call(url, service, method, *args):
    return _json_rpc(url, "call", {"service": service, "method": method, "args": args})


def _authenticate():
    log.info("Authenticating odoo-client and setting up the user-id")
    global user_id
    user_id = _call(f"{SERVER_URL}/jsonrpc", "common", "login", DATABASE_NAME, SERVER_USERNAME, SERVER_API_KEY)



if __name__ == "__main__":
    configure_logging()
    _authenticate()
    fetch_price_report()
