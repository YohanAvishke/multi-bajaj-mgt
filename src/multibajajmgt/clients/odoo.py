import random
import json
import logging
import requests

from multibajajmgt.config import (
    ODOO_SERVER_URL as SERVER_URL,
    ODOO_SERVER_USERNAME as SERVER_USERNAME,
    ODOO_SERVER_API_KEY as SERVER_API_KEY,
    ODOO_DATABASE_NAME as DATABASE_NAME,
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
    global user_id
    if not user_id:
        log.info("Authenticating odoo-client and setting up the user-id")
        user_id = _call(f"{SERVER_URL}/jsonrpc", "common", "login", DATABASE_NAME, SERVER_USERNAME, SERVER_API_KEY)


def fetch_product_external_id(db_id_list, limit = 0):
    """
    External ids are necessary for importing data
    :param limit: limit result count
    :param db_id_list: products database reference id
    :return: dataframe of dicts
    """
    log.info("Fetching product external ids from 'ir.model.data'")
    domain = ["&", ["model", "=", "product.template"],
              ["res_id", "in", db_id_list]]
    fields = ["res_id", "name", "module"]
    _authenticate()
    data = _call(
            f"{SERVER_URL}/jsonrpc", "object", "execute_kw",
            DATABASE_NAME, user_id, SERVER_API_KEY,
            "ir.model.data", "search_read",
            [domain, fields], {"limit": limit}
    )
    return data


def fetch_all_dpmc_prices(limit = 0):
    """
    All(qty>=0 and qty<0) prices belonging to dpmc pos categories(bajaj, 2w, 3w, qute)
    :param limit: limit result count
    :return: dataframe of dicts
    """
    log.info("Fetching product prices from 'product.template'")
    domain = ["&", ["available_in_pos", "=", True],
              "|", "|", "|", ["pos_categ_id", "ilike", "bajaj"],
              ["pos_categ_id", "ilike", "2w"],
              ["pos_categ_id", "ilike", "3w"],
              ["pos_categ_id", "ilike", "qute"]]
    fields = ["id", "default_code", "list_price", "standard_price"]
    _authenticate()
    data = _call(
            f"{SERVER_URL}/jsonrpc", "object", "execute_kw",
            DATABASE_NAME, user_id, SERVER_API_KEY,
            "product.template", "search_read", [domain, fields], {"limit": limit}
    )
    return data
