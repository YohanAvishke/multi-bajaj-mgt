import random
import json
import requests

from loguru import logger as log
from multibajajmgt.config import (
    SOURCE_DIR,
    ODOO_SERVER_URL as SERVER_URL,
    ODOO_SERVER_USERNAME as SERVER_USERNAME,
    ODOO_SERVER_API_KEY as SERVER_API_KEY,
    ODOO_DATABASE_NAME as DATABASE_NAME
)
from multibajajmgt.common import write_to_json

user_id, token, session_id, csrf_token = None, None, None, None


def _json_rpc(url, method, params):
    """Create Requests to Odoo's JSON-RPC server.

    Common wrapper method for all calls.

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
        log.error("Invalid response: {}", e)
    except requests.exceptions.RequestException as e:
        log.error("Something went wrong with the request: {}", e)


def _export_request(url, data):
    payload = {
        "data": json.dumps(data),
        "token": token,
        "csrf_token": csrf_token
    }
    try:
        response = requests.get(url = url,
                                headers = {"Cookie": f"fileToken={token}; tz=Asia/Colombo; frontend_lang=en_US; "
                                                     f"session_id={session_id}"},
                                data = payload)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as e:
        log.error("Invalid response: {}", e)
    except requests.exceptions.RequestException as e:
        log.error("Something went wrong with the request: {}", e)


def _call(url, service, method, *args):
    """Method to setup JSON RPC call's Arguments.

    :param url: string, url of the endpoint
    :param service: string, final part of the subdirectory(of the url)
    :param method: string, method to be executed on the request
    :param args: tuple, args for the payload's params of the request(authentication info, module name, etc.)
    :return: json dict, response body
    """
    return _json_rpc(url, "call", {"service": service, "method": method, "args": args})


def _export_call(url, model, domain, ids, fields):
    return _export_request(url, {"model": model, "domain": domain, "ids": ids, "fields": fields,
                                 "import_compat": False})


def _authenticate():
    """ Get User-ID to verify Username and API Key.

    Save the User-ID for future Requests from the Client.
    """
    log.info("Authenticating odoo-client and setting up the user-id")
    data = _call(f"{SERVER_URL}/jsonrpc", "common", "login", DATABASE_NAME, SERVER_USERNAME, SERVER_API_KEY)
    write_to_json(F"{SOURCE_DIR}/client/odoo/token.json", {"user-id": data})


def configure():
    """ Setup Odoo client with credentials.

    Configure credentials and create a token file.
    """
    log.info("Configuring Odoo client")
    global user_id
    global token
    global session_id
    global csrf_token
    try:
        with open(f"{SOURCE_DIR}/client/odoo/token.json", "r") as file:
            file_data = json.load(file)
            if "user-id" in file_data:
                user_id = file_data["user-id"]
            else:
                _authenticate()
            token = file_data["token"]
            session_id = file_data["session-id"]
            csrf_token = file_data["csrf-token"]
    except FileNotFoundError:
        _authenticate()


def fetch_all_dpmc_prices(product_ids = False):
    log.info("Fetching all dpmc product prices from 'product.template'")
    domain = [
        "&",
        ["available_in_pos", "=", True],
        "|", "|", "|",
        ["pos_categ_id", "ilike", "bajaj"], ["pos_categ_id", "ilike", "2w"], ["pos_categ_id", "ilike", "3w"],
        ["pos_categ_id", "ilike", "qute"]
    ]
    fields = [
        {"name": "id", "label": "External ID"},
        {"name": "default_code", "label": "Internal Reference"},
        {"name": "list_price", "label": "Old Sales Price"},
        {"name": "standard_price", "label": "Old Cost"}
    ]
    data = _export_call(
            f"{SERVER_URL}/web/export/csv",
            "product.template", domain, product_ids, fields
    )
    return data


def fetch_all_stock():
    """ Fetch every single Product stock from all categories.

    :return: dict, a list of dicts with product.template rows containing quantity available
    """
    log.info("Fetching all stock from 'product.template'")
    domain = [["available_in_pos", "=", True]]
    fields = [
        {"name": "product_variant_id/product_variant_id/id", "label": "Product/Product/ID"},
        {"name": "default_code", "label": "Internal Reference"},
        {"name": "qty_available", "label": "Quantity On Hand"}
    ]
    data = _export_call(
            f"{SERVER_URL}/web/export/csv",
            "product.template", domain, False, fields
    )
    return data
