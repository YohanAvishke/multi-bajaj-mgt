import random
import json
import logging
import requests

from multibajajmgt.config import (
    ODOO_SERVER_URL as SERVER_URL,
    ODOO_SERVER_USERNAME as SERVER_USERNAME,
    ODOO_SERVER_API_KEY as SERVER_API_KEY,
    ODOO_DATABASE_NAME as DATABASE_NAME
)

log = logging.getLogger(__name__)
user_id = None


def _json_rpc(url, method, params):
    """Create Requests to Odoo's JSON-RPC server

    Common wrapper method for all calls

    :param url: string, url of the endpoint
    :param method: string
    :param params: list, params for the payload of the request
    :return: json dict, response body
    """
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
    """Method to setup JSON RPC call's Arguments.

    :param url: string, url of the endpoint
    :param service: string, final part of the subdirectory(of the url)
    :param method: string, method to be executed on the request
    :param args: tuple, args for the payload's params of the request(authentication info, module name, etc.)
    :return: json dict, response body
    """
    return _json_rpc(url, "call", {"service": service, "method": method, "args": args})


def _authenticate():
    """ Get User-ID to verify Username and API Key.

    Save the User-ID for future Requests from the Client.
    """
    global user_id
    if not user_id:
        log.info("Authenticating odoo-client and setting up the user-id")
        user_id = _call(f"{SERVER_URL}/jsonrpc", "common", "login", DATABASE_NAME, SERVER_USERNAME, SERVER_API_KEY)


def fetch_product_external_id(db_id_list, limit = 0):
    """Fetch External IDs for a list of product.template Primary Keys.

    External IDs are necessary for importing data to the products of the server.

    :param db_id_list: list, product.template primary keys
    :param limit: int, limit the result count
    :return: pandas dataframe, a list of dicts with ir.model.data rows
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
    """Fetch every single Product Prices of DPMC POS Category.

    If available_qty >= 0 or available_qty < 0 retrieve their prices.
    All products should belonging to DPMC's POS categories (Bajaj, 2W, 3W, QUTE)

    :param limit: int, limit the result count
    :return: pandas dataframe, a list of dicts with product.template rows containing sales price and cost
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
