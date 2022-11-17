import json
import requests
import sys
import time

import requests.exceptions as r_exceptions

from loguru import logger as log
from multibajajmgt.common import write_to_json
from multibajajmgt.config import (
    DATETIME_FORMAT,
    DPMC_SESSION_LIFETIME,
    DPMC_SERVER_PASSWORD as SERVER_PASSWORD,
    DPMC_SERVER_URL as SERVER_URL,
    DPMC_SERVER_USERNAME as SERVER_USERNAME,
    SOURCE_DIR
)
from multibajajmgt.exceptions import DataNotFoundError, InvalidIdentityError, JSONDecodeError

CONN_RETRY_MAX = 5
GET_HELP_URL = f"{SERVER_URL}/Help/GetHelp"

TOKEN_FILE = f"{SOURCE_DIR}/client/dpmc/token.json"

retry_count = 0
base_headers = {
    "authority": "erp.dpg.lk",
    "sec-ch-ua": "'Google Chrome';v='93', ' Not;A Brand';v='99', 'Chromium';v='93'",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest",
    "sec-ch-ua-mobile": "'?0'",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/93.0.4577.63 Safari/537.36",
    "sec-ch-ua-platform": "'macOS'",
    "origin": SERVER_URL,
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "accept-language": "en-US,en;q=0.9",
    "dnt": "1",
    "sec-gpc": "1"
}


def _authenticate():
    """ Fetch and store(in token.json) cookie for DPMC server.
    """
    log.info("Authenticate DPMC client to setup a session.")
    headers = base_headers | {"referer": SERVER_URL}
    payload = {
        "strUserName": SERVER_USERNAME,
        "strPassword": SERVER_PASSWORD
    }
    session = requests.Session()
    try:
        session.post(SERVER_URL, headers = headers, data = payload)
        cookie = session.cookies
        # noinspection PyProtectedMember
        token = {
            "cookie": f".AspNetCore.Session={cookie.get_dict()['.AspNetCore.Session']}",
            "created_at": cookie._now,
            "expires_at": cookie._now + DPMC_SESSION_LIFETIME
        }
        write_to_json(TOKEN_FILE, token)
    except Exception:
        log.critical("Failed to authenticate while fetching a session.")


def configure():
    """ Validate and if expired renew the session cookie.
    """
    log.info("Configure DPMC client session.")
    try:
        with open(TOKEN_FILE, "r") as file:
            file_data = json.load(file)
        if "cookie" not in file_data or "expires_at" not in file_data:
            return _authenticate()
        expired_at = file_data["expires_at"]
        if int(time.time()) >= expired_at:
            log.warning("Cookie expired at {}.", time.strftime(DATETIME_FORMAT, time.localtime(expired_at)))
            return _authenticate()
    except FileNotFoundError:
        return _authenticate()


def _call(url, payload = None):
    """ Base function to send requests to the DPMC server.

    :param url: str, url for the request.
    :param payload: dict, None or data to be created/updated.
    :return: dict, json response payload.
    """
    log.debug("Send request to url: {} with payload: {}.", url, payload)
    with open(TOKEN_FILE, "r") as file:
        token = json.load(file)
    headers = base_headers | {"referer": f"{SERVER_URL}/Application/Home/PADEALER",
                              "cookie": token["cookie"]}
    try:
        response = requests.post(url = url, headers = headers, data = payload)
        response.raise_for_status()
    except r_exceptions.HTTPError as e:
        log.error("Invalid Response Status received: {}.", e)
        sys.exit(0)
    except r_exceptions.ConnectionError as e:
        raise r_exceptions.ConnectionError("Connection issue occurred: {}.", e)
    except r_exceptions.RequestException as e:
        log.error("Something went wrong with the request: {}.", e)
        sys.exit(0)
    else:
        if response.text == "LOGOUT":
            log.warning("Session expired.")
            configure()
            return _call(url, payload)
        try:
            return response.json()
        except JSONDecodeError:
            return None


def _retry_request(request_func, *args):
    """ Retry a failed reqeust (eg: closed by peer).

    :param request_func: function ref, function pointer to be retired.
    :param args: tuple, parameters for the request_func.
    :return: function call,
    """
    log.warning("Connection timed out for: {} Retrying Request.", args)
    global retry_count
    retry_count = retry_count + 1
    if retry_count <= CONN_RETRY_MAX:
        return request_func(*args)
    else:
        log.error("Connection retried for {} times, but still failed.", retry_count)
        sys.exit(0)


def inquire_product_price(ref_id):
    """ Fetch price of a product.

    :param ref_id: str, product's part number.
    :return: dict, response data.
    """
    log.debug("Fetch product price for {}.", ref_id)
    payload = {
        "strPartNo_PAItemInq": ref_id,
        "strFuncType": "INVENTORYDATA",
        "strPADealerCode_PAItemInq": "AC2011063676",
        "STR_FORM_ID": "00602",
        "STR_FUNCTION_ID": "IQ",
        "STR_PREMIS": "KGL",
        "STR_INSTANT": "DLR",
        "STR_APP_ID": "00011"
    }
    try:
        response = _call(f"{SERVER_URL}/PADEALER/PADLRItemInquiry/Inquire", payload)
    except r_exceptions.ConnectionError:
        # Retry each request for maximum of 5 times
        return _retry_request(inquire_product_price, ref_id)
    else:
        if response["STATE"] == "FALSE":
            raise InvalidIdentityError("Failed to fetch price. Incorrect ID: {}, Response: {}.", ref_id, response)
        product = response["DATA"]
        if not product["dblSellingPrice"]:
            raise InvalidIdentityError("Failed to fetch price. Expired ID: {}, Response: {}.", ref_id, response)
        price = {
            "STR_PART_CODE": product["strPartNo_PAItemInq"],
            "INT_UNIT_COST": float(product["dblSellingPrice"])
        }
        return price


def inquire_product_line(ref_id):
    """ Fetch a product.

    :param ref_id: str, product's part number.
    :return: dict, data.
    """
    log.debug("Fetch product line for {}.", ref_id)
    payload = {
        "strDealerCode_PADLROrder": "AC2011063676",
        "strPADealerShipCat_PADLROrder": "KDLR",
        "strPartCode_PADLROrder": ref_id,
        "strInstanceId_PADLROrder": "BAJ",
        "strInqType_PADLROrder": "PARTPRICE",
        "STR_FORM_ID": "00596",
        "STR_FUNCTION_ID": "CR",
        "STR_PREMIS": "KGL",
        "STR_INSTANT": "DLR",
        "STR_APP_ID": "00011"
    }
    try:
        data = _call(f"{SERVER_URL}/PADealer/PADLROrder/Inquire", payload)
    except r_exceptions.ConnectionError:
        return _retry_request(inquire_product_line, ref_id)
    else:
        if not data or data["STATE"] == "FALSE":
            raise InvalidIdentityError("Failed to fetch line. Incorrect ID: {}, Response: {}.", ref_id, data)
        data = data["DATA"]
        product = {
            "STR_PART_CODE": data["strPartCode_PADLROrder"],
            "INT_UNIT_COST": data["dblRetailPrice_PADLROrder"]
        }
        # Get line from either Bajaj or KTM (for expired products)
        product_lines = data['lstPADLRProductlineDetails_PADLROrder']
        line = None
        if len(product_lines) == 1:
            line = product_lines[0]
            line = {
                "STR_PROD_HIER_CODE": line["strMakeCode"],
                "STR_VEHICLE_TYPE_CODE": line["strProductlineCode"],
                "STR_VEHICLE_TYPE": line["strProductlineDesc"],
                "STR_VEHICLE_MODEL_CODE": line["strModelCode"],
                "STR_VEHICLE_MODEL": line["strModelDesc"],
            }
        else:
            for elem in data['lstPADLRProductlineDetails_PADLROrder']:
                if elem["strMakeCode"] == "BAJ":
                    line = {
                        "STR_PROD_HIER_CODE": elem["strMakeCode"],
                        "STR_VEHICLE_TYPE_CODE": elem["strProductlineCode"],
                        "STR_VEHICLE_TYPE": elem["strProductlineDesc"],
                        "STR_VEHICLE_MODEL_CODE": elem["strModelCode"],
                        "STR_VEHICLE_MODEL": elem["strModelDesc"],
                    }
                    break
        return product | line


def inquire_product_category(ref_id):
    """ Fetch category of a product.

    :param ref_id: str, product's part number.
    :return: dict, data.
    """
    log.debug("Fetch product category for {}.", ref_id)
    payload = {
        "strInstance": "DLR",
        "strPremises": "KGL",
        "strAppID": "00011",
        "strFORMID": "00596",
        "strHELP_TITEL": "Part Details",
        "arrFIELD_NAME": ["STR_PART_NO", "STR_DESC", "STR_CAT_CODE", "STR_PROD_HIER_CODE"],
        "arrDISPLAY_NAME": ["STR_PART_CODE", "STR_DESC", "STR_CAT_CODE", "STR_PROD_HIER_CODE"],
        "arrSEARCH_TEXT": ["STR_PART_NO", ref_id],
        "strLIMIT": "0",
        "strARCHIVE": "TRUE",
        "strAPI_URL": "api/Modules/PADealer/PADLROrder/PartList"
    }
    try:
        category = _call(f"{SERVER_URL}/Help/EnterPress", payload)
        if category == "NO DATA FOUND":
            raise InvalidIdentityError("Failed to fetch Category. Incorrect ID: {}, Response: {}.", ref_id, category)
        categories = json.loads(category)
        if len(categories) == 1:
            category = categories[0]
        else:
            for elem in categories:
                if elem["STR_PROD_HIER_CODE"] == "BAJ":
                    category = elem
                    break
        return category
    except r_exceptions.ConnectionError:
        return _retry_request(inquire_product_category, ref_id)


def inquire_products_by_invoice(invoice, grn):
    """ Fetch products by invoice data.

    Payload should be altered depending on the availability of grn id
        if grn and invoice id exists:
          "strMode" = "GRN", "STR_FUNCTION_ID" = "IQ"
          "strGRNno" = @grn
        else only invoice id exists:
          "strMode" = "INVOICE", "STR_FUNCTION_ID" = "CR"

    :param invoice: str, invoice id.
    :param grn: str, grn id.
    :return: dict, data.
    """
    log.debug("Fetch products of Invoice: {}.", invoice)
    payload = {
        "STR_INSTANT": "DLR",
        "STR_PREMIS": "KGL",
        "STR_APP_ID": "00011",
        "STR_FORM_ID": "00605",
        "strMode": "GRN" if grn else "INVOICE",
        "STR_FUNCTION_ID": "IQ" if grn else "CR",
        "strInvoiceNo": f"{invoice}",
        "strPADealerCode": "AC2011063676"
    }
    if grn:
        payload["strGRNno"] = grn
    try:
        response = _call(f"{SERVER_URL}/PADEALER/PADLRGOODRECEIVENOTE/Inquire", payload)
    except r_exceptions.ConnectionError as e:
        log.error(e)
        sys.exit(0)
    else:
        if response["STATE"] == "FALSE":
            raise DataNotFoundError("Failed to fetch products. Incorrect Invoice ID: {} or GRN ID: {}. Response: {}.",
                                    invoice, grn, response)
        product_data = response["DATA"]
        return product_data


def _inquire_goodreceivenote(payload):
    """ Base function to fetch invoice advanced data.

    :return: dict, data.
    """
    base_payload = {
        "strInstance": "DLR",
        "strPremises": "KGL",
        "strAppID": "00011",
        "strFORMID": "00605",
        "strSEARCH_TEXT": "",
        "strLIMIT": "0",
        "strARCHIVE": "TRUE",
        "strOTHER_WHERE_CONDITION": "",
        "strTITEL": "",
        "strAll_DATA": "true",
        "strSchema": ""
    }
    payload = base_payload | payload
    try:
        response_data = _call(GET_HELP_URL, payload)
    except r_exceptions.ConnectionError as e:
        log.error(e)
        sys.exit(0)
    else:
        if response_data == "NO DATA FOUND":
            raise DataNotFoundError("Failed to fetch grn data. Incorrect ID: {}. Response: {}",
                                    payload['strSearch'], response_data)
        return json.loads(response_data)


def inquire_goodreceivenote_by_grn_ref(col, ref_id):
    """ Fetch invoice advanced data by grn.

    :param col: str, DPMCFieldName depending on @ref_id.
    :param ref_id: str, either invoice/order id.
    :return: dict, data.
    """
    log.debug("Fetch Invoice using GRN ID: {}.", ref_id)
    try:
        return _inquire_goodreceivenote(
                {"strFIELD_NAME": ",STR_DEALER_CODE,STR_GRN_NO,STR_ORDER_NO,STR_INVOICE_NO,INT_TOTAL_GRN_VALUE",
                 "strHIDEN_FIELD_INDEX": ",0",
                 "strDISPLAY_NAME": ",STR_DEALER_CODE,GRN No,Order No,Invoice No,Total GRN Value",
                 "strSearch": f"{ref_id}",
                 "strSEARCH_FIELD_NAME": "STR_GRN_NO",
                 "strColName": f"{col}",
                 "strORDERBY": "STR_GRN_NO",
                 "strAPI_URL": "api/Modules/Padealer/Padlrgoodreceivenote/List"})
    except DataNotFoundError as e:
        raise DataNotFoundError(e)


def inquire_goodreceivenote_by_order_ref(col, ref_id):
    """ Fetch invoice advanced data by order.

        :param col: str, DPMCFieldName depending on @ref_id.
        :param ref_id: str, either invoice/order/mobile id.
        :return: dict, data.
        """
    log.debug("Fetch Invoice using Order ID: {}.", ref_id)
    try:
        return _inquire_goodreceivenote(
                {"strFIELD_NAME": ",DISTINCT STR_DLR_ORD_NO,STR_INVOICE_NO,STR_MOBILE_INVOICE_NO",
                 "strHIDEN_FIELD_INDEX": "",
                 "strDISPLAY_NAME": ",Order No,Invoice No,Mobile Invoice No",
                 "strSearch": f"{ref_id}",
                 "strSEARCH_FIELD_NAME": "STR_DLR_ORD_NO",
                 "strColName": f"{col}",
                 "strORDERBY": "STR_DLR_ORD_NO",
                 "strOTHER_WHERE_CONDITION": "",
                 "strAPI_URL": "api/Modules/Padealer/Padlrgoodreceivenote/DealerPAPendingGRNNo"})
    except DataNotFoundError as e:
        raise DataNotFoundError(e)
