import logging
import requests
import json
import time

from multibajajmgt.common import write_to_json
from multibajajmgt.config import (
    DPMC_SERVER_URL as SERVER_URL,
    DPMC_SERVER_USERNAME as SERVER_USERNAME,
    DPMC_SERVER_PASSWORD as SERVER_PASSWORD, SOURCE_DIR, DATETIME_FORMAT,
)

log = logging.getLogger(__name__)

PRODUCT_INQUIRY_URL = f"{SERVER_URL}/PADEALER/PADLRItemInquiry/Inquire"

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
        response = response.json()
        if "error" in response:
            raise Exception(response["error"])
        return response
    except requests.exceptions.HTTPError as e:
        log.error("Invalid response: ", e)
    except requests.exceptions.ConnectionError as e:
        log.error("Connection failed: ", e)
        raise requests.exceptions.ConnectionError("Connection failed")
    except requests.exceptions.RequestException as e:
        log.error("Something went wrong with the request: ", e)


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
        "expires-at": session.cookies._now + 7200
    }
    write_to_json(F"{SOURCE_DIR}/clients/dpmc/token.json", token_data)


def configure():
    log.debug("Configuring DPMC client")
    global cookie
    try:
        with open(f"{SOURCE_DIR}/clients/dpmc/token.json", "r") as file:
            file_data = json.load(file)
            # does cookie exist in the data
            if ".AspNetCore.Session" in file_data:
                # is the cookie expired
                now = int(time.time())
                if "expires-at" in file_data and now < file_data["expires-at"]:
                    cookie = f".AspNetCore.Session={file_data['.AspNetCore.Session']}"
                else:
                    log.warning(
                        f"Cookie expired at {time.strftime(DATETIME_FORMAT, time.localtime(file_data['expires-at']))}")
                    _authenticate()
                    configure()
            else:
                _authenticate()
                configure()
    except FileNotFoundError as e:
        _authenticate()
        configure()


def product_inquiry(ref_id):
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
        _call(PRODUCT_INQUIRY_URL, f"{SERVER_URL}/Application/Home/PADEALER", payload)
    except requests.exceptions.ConnectionError as e:
        log.error("Connection timed out. Restarting service...", e)
        product_inquiry(ref_id)


configure()
