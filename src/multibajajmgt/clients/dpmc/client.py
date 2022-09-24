import logging
import requests
import json

from multibajajmgt.common import write_to_json
from multibajajmgt.config import (
    DPMC_SERVER_URL as SERVER_URL,
    DPMC_SERVER_USERNAME as SERVER_USERNAME,
    DPMC_SERVER_PASSWORD as SERVER_PASSWORD, SOURCE_DIR,
)

log = logging.getLogger(__name__)

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
    global cookie
    if not cookie:
        _authenticate()
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
    write_to_json(F"{SOURCE_DIR}/clients/dpmc/token.json", session.cookies.get_dict())


def configure():
    log.debug("Configuring DPMC client")
    global cookie
    try:
        with open(f"{SOURCE_DIR}/clients/dpmc/token.json", "r") as file:
            file_data = json.load(file)
            if ".AspNetCore.Session" in file_data:
                cookie = f".AspNetCore.Session={file_data['.AspNetCore.Session']}"
            else:
                _authenticate()
    except FileNotFoundError as error:
        _authenticate()
    return


if __name__ == "__main__":
    configure()
    print(cookie)
