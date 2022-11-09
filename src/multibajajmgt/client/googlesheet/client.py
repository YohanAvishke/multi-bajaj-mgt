import json
import os.path
import pandas as pd

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
from typing import Any

service: Any

CLIENT_DIR = f"{SOURCE_DIR}/client/googlesheet"
TOKEN_FILE = f"{CLIENT_DIR}/token.json"
CREDENTIAL_FILE = f"{CLIENT_DIR}/credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "18kz-I9F90_vL60zHbGmtl8LMiAnJzy2nN_2DHzjJMIw"
RANGE_NAME = "A:D"


def configure():
    """ Validate credentials, fetch token and set service.
    """
    log.info("Configuring Google Sheet client")
    credentials = None
    global service
    if os.path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIAL_FILE, SCOPES)
            credentials = flow.run_local_server(port = 0)
        write_to_json(TOKEN_FILE, json.loads(credentials.to_json()))
    service = build("sheets", "v4", credentials = credentials)


def inquire_sales_invoices():
    """ Fetch sales data from the columns of the spreadsheet.

    :return: pandas dataframe, column data
    """
    log.debug("Fetching non uploaded sales invoices")
    # If not already configured
    if not service:
        configure()
    sheet = service.spreadsheets()
    request = sheet.values().get(spreadsheetId = SPREADSHEET_ID, range = RANGE_NAME)
    response = request.execute()
    values = response.get("values", [])
    if values:
        return pd.DataFrame(columns = [InvoField.part_code, InvoField.part_qty, InvoField.date, BaseField.status],
                            data = values)
    else:
        log.warning("No data found in the sheet")
