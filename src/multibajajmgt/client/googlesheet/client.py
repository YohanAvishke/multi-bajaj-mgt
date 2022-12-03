import json
import os.path
import sys

import pandas as pd

from google.auth.exceptions import RefreshError
# noinspection PyPackageRequirements
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
# noinspection PyPackageRequirements
from google.auth.transport.requests import Request
# noinspection PyPackageRequirements
from google.oauth2.credentials import Credentials
from loguru import logger as log
from multibajajmgt.common import write_to_json
from multibajajmgt.config import SOURCE_DIR
from multibajajmgt.enums import (
    BasicFieldName as BaseField,
    InvoiceField as InvoField
)
from tenacity import retry, retry_if_exception_type, stop_after_attempt
from typing import Any

service: Any

CLIENT_DIR = f"{SOURCE_DIR}/client/googlesheet"
TOKEN_FILE = f"{CLIENT_DIR}/token.json"
CREDENTIAL_FILE = f"{CLIENT_DIR}/credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "18kz-I9F90_vL60zHbGmtl8LMiAnJzy2nN_2DHzjJMIw"
RANGE_NAME = "A:D"


@retry(retry = retry_if_exception_type(RefreshError),
       reraise = True,
       stop = stop_after_attempt(1))
def configure():
    """ Validate credentials, fetch token and set service.
    """
    log.info("Configure Google Sheet client.")
    credentials = None
    global service
    if os.path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except RefreshError:
                log.warning("Refresh token expired or revoked. Deleting token file.")
                os.remove(TOKEN_FILE)
                log.debug("Retry configuration.")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIAL_FILE, SCOPES)
            credentials = flow.run_local_server(port = 0)
        write_to_json(TOKEN_FILE, json.loads(credentials.to_json()))
    service = build("sheets", "v4", credentials = credentials)


def inquire_sales_invoices():
    """ Fetch sales data from the columns of the spreadsheet.

    :return: pandas dataframe, column data.
    """
    log.debug("Fetch Sales Invoices.")
    # If not already configured
    if not service:
        try:
            configure()
        except RefreshError as e:
            log.error("Failed to refresh expired token due to: {}", e)
            sys.exit(0)
    sheet = service.spreadsheets()
    request = sheet.values().get(spreadsheetId = SPREADSHEET_ID, range = RANGE_NAME)
    response = request.execute()
    values = response.get("values", [])
    if values:
        return pd.DataFrame(columns = [InvoField.part_code, InvoField.part_qty, InvoField.date, BaseField.status],
                            data = values)
    else:
        log.warning("No data found in the sheet.")
