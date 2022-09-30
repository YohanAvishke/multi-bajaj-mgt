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
        log.error("Invalid Response received: ", e)
        sys.exit(0)
    except r_exceptions.ConnectionError as e:
        message = "Connection failed"
        raise r_exceptions.ConnectionError(message, e)
    except r_exceptions.RequestException as e:
        log.error("Something went wrong with the request: ", e)
        sys.exit(0)
    else:
        response = response.json()
        if response["STATE"] == "FALSE":
            raise DataNotFoundError(f"Response failed due to invalid Request payload: {payload}", response)
        response = response["DATA"]
        if not response["dblSellingPrice"]:
            raise ProductRefExpired(f"Response failed due to expired Request payload: {payload}", response)
        return response


def _authenticate():
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
    log.debug("Configuring DPMC client")
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
    except FileNotFoundError as e:
        _refresh_token()


def _refresh_token():
    _authenticate()
    configure()


def _retry_request(request_func, *args):
    global retry_count
    retry_count = retry_count + 1
    if retry_count <= CONN_RETRY_MAX:
        request_func(*args)
    else:
        message = f"Connection retried for {CONN_RETRY_MAX} times, but still failed"
        log.error(message)
        raise RetryTimeout(message)


def inquire_product_data(ref_id):
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
        response_data = _call(PRODUCT_INQUIRY_URL, f"{SERVER_URL}/Application/Home/PADEALER", payload)
        return response_data
    except r_exceptions.ConnectionError as e:
        log.warning("Connection timed out. Restarting service")
        try:
            # Calculate retry count and resend the request
            _retry_request(inquire_product_data, ref_id)
        except RetryTimeout as e:
            message = f"Product data inquiring timed out, for Reference ID: {ref_id}"
            log.error(message, e)
            raise RetryTimeout(message, e)
    except ProductRefExpired as e:
        message = f"Inquiring data failed, for expired Reference ID: {ref_id}"
        raise InvalidIdentityError(message, e)
    except DataNotFoundError as e:
        message = f"Inquiring data failed, for invalid Reference ID: {ref_id}"
        raise InvalidIdentityError(message, e)
