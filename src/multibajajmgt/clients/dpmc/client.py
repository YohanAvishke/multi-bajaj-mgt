import logging
import sys
import requests
import requests.exceptions as r_exceptions
import json
import time

from multibajajmgt.common import write_to_json
from multibajajmgt.config import (
    DATETIME_FORMAT,
    DPMC_SERVER_URL as SERVER_URL,
    DPMC_SERVER_USERNAME as SERVER_USERNAME,
    DPMC_SERVER_PASSWORD as SERVER_PASSWORD, SOURCE_DIR, DPMC_SESSION_LIFETIME
)
from multibajajmgt.exceptions import *

log = logging.getLogger(__name__)

PRODUCT_INQUIRY_URL = f"{SERVER_URL}/PADEALER/PADLRItemInquiry/Inquire"
GET_HELP_URL = "https://erp.dpg.lk/Help/GetHelp"
CONN_RETRY_MAX = 5

retry_count = 0
cookie = None
headers = {
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


def _call(url, referer, payload = None):
    """ Base function for requests to the DPMC server

    :param url: string, url for the request
    :param referer: string, base url
    :param payload: dict, None or data to be created/updated
    :return: dict, json response payload
    """
    global headers
    headers |= {
        "referer": referer,
        "cookie": cookie
    }
    try:
        response = requests.post(url = url,
                                 headers = headers,
                                 data = payload)
        response.raise_for_status()
    except r_exceptions.HTTPError as e:
        log.error("Invalid Response Status received: ", e)
        sys.exit(0)
    except r_exceptions.ConnectionError as e:
        raise r_exceptions.ConnectionError("Connection issue occurred", e)
    except r_exceptions.RequestException as e:
        log.error("Something went wrong with the request: ", e)
        sys.exit(0)
    else:
        if response.text == "LOGOUT":
            log.warning("Session expired")
            configure()
            return _call(url, referer, payload)
        return response.json()


def _authenticate():
    """ Fetch and store(in token.json) cookie for DPMC server
    """
    log.info("Authenticating DPMC-ERP Client and setting up the Cookie")
    global headers
    headers |= {"referer": SERVER_URL}
    payload = {
        "strUserName": SERVER_USERNAME,
        "strPassword": SERVER_PASSWORD
    }
    session = requests.Session()
    session.post(SERVER_URL, headers = headers, data = payload)
    token_data = session.cookies.get_dict()
    token_data |= {
        "created-at": session.cookies._now,
        "expires-at": session.cookies._now + DPMC_SESSION_LIFETIME
    }
    write_to_json(F"{SOURCE_DIR}/clients/dpmc/token.json", token_data)


def configure():
    """ Validate and attach login session to request header
    """
    log.info("Configuring DPMC client")
    global cookie
    try:
        with open(f"{SOURCE_DIR}/clients/dpmc/token.json", "r") as file:
            file_data = json.load(file)
            # Does cookie exist in the data
            if ".AspNetCore.Session" in file_data:
                # is the cookie expired
                now = int(time.time())
                if "expires-at" in file_data and now < file_data["expires-at"]:
                    cookie = f".AspNetCore.Session={file_data['.AspNetCore.Session']}"
                else:
                    log.warning(
                            f"Cookie expired at "
                            f"{time.strftime(DATETIME_FORMAT, time.localtime(file_data['expires-at']))}")
                    _refresh_token()
            else:
                _refresh_token()
    except FileNotFoundError:
        _refresh_token()


def _refresh_token():
    """ Wrapper for fetch,save and configure session
    """
    _authenticate()
    configure()


def _retry_request(request_func, *args):
    """ Retry a failed reqeust(eg: closed by peer)

    :param request_func: function, function pointer to be retired
    :param args: tuple, parameters for the request_func
    :return: function call
    """
    log.warning(f"Connection timed out for: {args} Retrying Request")
    global retry_count
    retry_count = retry_count + 1
    if retry_count <= CONN_RETRY_MAX:
        return request_func(*args)
    else:
        message = f"Connection retried for {retry_count} times, but still failed"
        log.error(message)
        sys.exit(0)


def inquire_product_by_id(ref_id):
    """ Fetch product by product id.

    :param ref_id: string, product's part number
    :return: dict, data
    """
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
        response = _call(PRODUCT_INQUIRY_URL, f"{SERVER_URL}/Application/Home/PADEALER", payload)
    except r_exceptions.ConnectionError:
        # Retry each request for maximum of 5 times
        _retry_request(inquire_product_by_id, ref_id)
    except ProductRefExpired as e:
        raise InvalidIdentityError(f"Inquiring data failed, for expired Reference ID: {ref_id}", e)
    else:
        if response["STATE"] == "FALSE":
            raise InvalidIdentityError(f"Inquiring data failed, for incorrect Reference ID: {ref_id}", response)
        product_data = response["DATA"]
        if not product_data["dblSellingPrice"]:
            raise InvalidIdentityError(f"Inquiring data failed, for expired Reference ID: {ref_id}", response)
        return product_data


def inquire_product_by_invoice(invoice, grn):
    """ Fetch products by invoice data.

    :param invoice: string, invoice id
    :param grn: string, grn id
    :return: dict, data
    """
    # Payload should be altered depending on the availability of grn id
    # If grn and invoice id exists:
    #   "strMode" = "GRN", "STR_FUNCTION_ID" = "IQ"
    #   "strGRNno" = @grn
    # else only invoice id exists:
    #   "strMode" = "INVOICE", "STR_FUNCTION_ID" = "CR"
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
        response = _call(f"{SERVER_URL}/PADEALER/PADLRGOODRECEIVENOTE/Inquire",
                         f"{SERVER_URL}/Application/Home/PADEALER", payload)
    except r_exceptions.ConnectionError as e:
        log.error(e)
        sys.exit(0)
    else:
        if response["STATE"] == "FALSE":
            raise DataNotFoundError(f"Inquiring data failed, for incorrect Invoice ID: {invoice} and GRN ID: {grn}",
                                    response)
        product_data = response["DATA"]
        return product_data


def _inquire_goodreceivenote(referer, payload):
    """ Base function to fetch invoice advanced data

    :param referer: string, url
    :param payload: dict,
    :return: dict, data
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
        response_data = _call(GET_HELP_URL, referer, payload)
    except r_exceptions.ConnectionError as e:
        log.error(e)
        sys.exit(0)
    else:
        if response_data == "NO DATA FOUND":
            raise DataNotFoundError(f"Inquiring grn data failed, for incorrect Reference ID: {payload['strSearch']}",
                                    response_data)
        return json.loads(response_data)


def inquire_goodreceivenote_by_grn_ref(col, ref_id):
    """ Fetch invoice advanced data by grn

    :param col: string, DPMCFieldName depending on @ref_id
    :param ref_id: string, either invoice/order id
    :return: dict, data
    """
    try:
        return _inquire_goodreceivenote(
                f"{SERVER_URL}/Application/Home/PADEALER",
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
    """ Fetch invoice advanced data by order

        :param col: string, DPMCFieldName depending on @ref_id
        :param ref_id: string, either invoice/order/mobile id
        :return: dict, data
        """
    try:
        return _inquire_goodreceivenote(
                SERVER_URL,
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
