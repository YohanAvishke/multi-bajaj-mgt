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
from multibajajmgt.exceptions import InvalidDataFormatReceived
from multibajajmgt.product.models import Product

user_id, token, session_id, csrf_token = None, None, None, None


def _json_rpc(url, method, params):
    """ Create Requests to Odoo's JSON-RPC server.

    Common wrapper method for all calls.

    :param url: string, url of the endpoint
    :param method: string
    :param params: list, params for the payload of the request
    :return: dict, response body
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
    """ Create request to export CSV data from Odoo server.

    Common wrapper method for all calls.

    :param url: string, url of the endpoint
    :param data: dict, to filter exporting data
    :return: dict, response body
    """
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
    """ Function to set up JSON RPC call's arguments.

    :param url: string, url of the endpoint
    :param service: string, final part of the subdirectory(of the url)
    :param method: string, method to be executed on the request
    :param args: tuple, args for the payload's params of the request(authentication info, module name, etc.)
    :return: dict, response body
    """
    return _json_rpc(url, "call", {"service": service, "method": method, "args": args})


def _export_call(url, model, domain, ids, fields):
    """ Function to set up Odoo export call's arguments.

    :param url: string, url of the endpoint
    :param model: string, table model name
    :param domain: list, filtering conditions
    :param ids: list, product's db id list for filtering
    :param fields: list, table columns to be returned
    :return: dict, response body
    """
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


def _fetch_prices(domain, product_ids):
    """ Basic function to fetch prices.

    :param domain: list, filtering conditions
    :param product_ids: list, product's db id list for filtering
    :return: dict, price data
    """
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


def fetch_all_dpmc_prices(product_ids = False):
    """ Fetch all product prices from DPMC POS category.

    :param product_ids: list, product's db id list for filtering
    :return: dict, dpmc price data
    """
    log.debug("Fetching all dpmc product prices from 'product.template'")
    domain = [
        "&",
        ["available_in_pos", "=", True],
        "|", "|", "|",
        ["pos_categ_id", "ilike", "bajaj"], ["pos_categ_id", "ilike", "2w"], ["pos_categ_id", "ilike", "3w"],
        ["pos_categ_id", "ilike", "qute"]
    ]
    data = _fetch_prices(domain, product_ids)
    return data


def fetch_all_thirdparty_prices(product_ids = False):
    """ Fetch all product prices from all POS category except DPMC.

    :param product_ids: list, product's db id list for filtering
    :return: dict, third-party price data
    """
    log.debug("Fetching all third-party product prices from 'product.template'")
    domain = [
        "&",
        ["available_in_pos", "=", True],
        "&", "&", "&",
        ["pos_categ_id", "not ilike", "bajaj"], ["pos_categ_id", "not ilike", "2w"],
        ["pos_categ_id", "not ilike", "3w"], ["pos_categ_id", "not ilike", "qute"]
    ]
    data = _fetch_prices(domain, product_ids)
    return data


def _fetch_stock(domain):
    """ Base method to fetch stock

    :param domain: list, pos category filter
    :return: dict, dict of list with product data
    """
    fields = [
        {"name": "product_variant_id/product_variant_id/id", "label": "Product/Product/ID"},
        {"name": "default_code", "label": "Internal Reference"},
        {"name": "qty_available", "label": "Quantity_On_Hand"}
    ]
    data = _export_call(
            f"{SERVER_URL}/web/export/csv",
            "product.template", domain, False, fields
    )
    return data


def fetch_all_stock():
    """ Fetch product stock from all POS categories.

    :return: dict, dict of list with product data
    """
    log.debug("Fetching all stock from 'product.template'")
    domain = [["available_in_pos", "=", True]]
    return _fetch_stock(domain)


def fetch_dpmc_stock():
    """ Fetch product stock from DPMC POS category.

    :return: dict, dict of list with product data
    """
    log.debug("Fetching DPMC stock from 'product.template'")
    domain = [
        "&",
        ["available_in_pos", "=", True],
        "|", "|", "|",
        ["pos_categ_id", "ilike", "bajaj"], ["pos_categ_id", "ilike", "2w"],
        ["pos_categ_id", "ilike", "3w"], ["pos_categ_id", "ilike", "qute"]
    ]
    return _fetch_stock(domain)


def fetch_thirdparty_stock():
    """ Fetch product stock from non DPMC POS categories.

    :return: dict, dict of list with product data
    """
    log.debug("Fetching Third Party stock from 'product.template'")
    domain = [
        "&",
        ["available_in_pos", "=", True],
        "&", "&", "&",
        ["pos_categ_id", "not ilike", "bajaj"], ["pos_categ_id", "not ilike", "2w"],
        ["pos_categ_id", "not ilike", "3w"], ["pos_categ_id", "not ilike", "qute"]
    ]
    return _fetch_stock(domain)


def fetch_pos_category(categ_name):
    """ Fetch a pos category's information.

    :param categ_name: string, name of a category
    :return: dict, a pos category data
    """
    log.debug("Fetching POS category from 'pos.category'")
    domain = [["name", "=", categ_name]]
    fields = ["name", "parent_id", "sequence"]
    data = _call(
            f"{SERVER_URL}/jsonrpc", "object", "execute_kw",
            DATABASE_NAME, user_id, SERVER_API_KEY,
            "pos.category", "search_read",
            [domain, fields])
    if len(data) == 1:
        return data
    else:
        message = f"Invalid data {data} for category name {categ_name}"
        raise InvalidDataFormatReceived(message)


def create_product(product: Product):
    """ Create a product.

    :param product: Product, product data
    :return: int, created product's database id
    """
    log.debug("Creating product for 'product.template'")
    data_upload = {
        "type": "product",
        "name": product.name,
        "description": product.name,
        "default_code": product.default_code,
        "barcode": product.barcode,
        "image_1920": product.image,
        "attribute_line_ids": [],
        # prices
        "list_price": product.price,
        "standard_price": product.price,
        "taxes_id": [[6, False, []]],
        # category
        "categ_id": product.categ_id,
        "pos_categ_id": product.pos_categ_id,
        # flags
        "sale_ok": True,
        "purchase_ok": True,
        "active": True,
        "available_in_pos": True,
        "to_weight": False,
        "__last_update": False,
    }
    data = _call(
            f"{SERVER_URL}/jsonrpc", "object", "execute_kw",
            DATABASE_NAME, user_id, SERVER_API_KEY,
            "product.template", "create", [data_upload])
    return data


def fetch_sale_report(from_date,
                      to_date = None,
                      offset = 0,
                      limit = None,
                      order_by = False) -> dict:
    """ Fetch sales report of product's order quantity grouped by date.

    Since Odoo server uses Time zone: Etc/UTC (UTC, +0000).
    Args from_date and to_date should be altered accordingly.

    :param from_date: string, filter start date
    :param to_date: string, filter end date
    :param offset: int, dp start row
    :param limit: None/int, row count
    :param order_by: False/string, row ordering
    :return: dict, data
    """
    log.debug("Fetching ordered products from 'sale.report'")
    domain = [["date", ">", from_date]]
    if to_date:
        domain.insert(0, "&")
        domain.append(["date", "<=", to_date])
    fields = ["product_uom_qty:sum"]
    group_by = ["product_id", "date:day"]
    lazy = False
    data = _call(f"{SERVER_URL}/jsonrpc", "object", "execute_kw",
                 DATABASE_NAME, user_id, SERVER_API_KEY, "sale.report", "read_group",
                 [domain, fields, group_by, offset, limit, order_by, lazy])
    return data
