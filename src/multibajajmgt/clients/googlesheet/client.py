import json
import os.path
import pandas as pd
import logging

from datetime import date
from typing import Any
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from multibajajmgt.common import write_to_json
from multibajajmgt.config import SOURCE_DIR
from multibajajmgt.enums import (
    BasicFieldName as Field
)

log = logging.getLogger(__name__)
service: Any

CLIENT_DIR = f"{SOURCE_DIR}/clients/googlesheet"
TOKEN_FILE = f"{CLIENT_DIR}/token.json"
CREDENTIAL_FILE = f"{CLIENT_DIR}/credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "18kz-I9F90_vL60zHbGmtl8LMiAnJzy2nN_2DHzjJMIw"
RANGE_NAME = "A:D"


def configure():
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


def fetch_sheet_data():
    if not service:
        configure()
    sheet = service.spreadsheets()
    request = sheet.values().get(spreadsheetId = SPREADSHEET_ID, range = RANGE_NAME)
    response = request.execute()
    values = response.get("values", [])

    if not values:
        log.warning("No data found in the sheet")
    else:
        return pd.DataFrame(columns = [Field.part_code, Field.part_qty, Field.date, Field.status], data = values)


configure()
fetch_sheet_data()
print()
